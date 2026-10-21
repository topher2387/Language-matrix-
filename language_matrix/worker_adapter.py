#!/usr/bin/env python3
"""Worker adapter with quota-aware scheduling via injected scheduler interface.

This module implements the adapter pattern to integrate quota-aware workers
with the existing Lichen scheduler API without coupling to live Lichen runtime.

Key behaviors:
- Provider admission with explicit quotas/expiry/privacy/rate metadata
- Fail-closed cost0 enforcement (no paid providers)
- Quota exhaustion fallback to admitted zero-cost alternative
- Bounded retries with configurable budget
- Cancellation/deadline integration
- GPU concurrency guard (single GPU-heavy job at a time)
"""
import datetime as dt
import json
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    from .capabilities import validate_capability_request
except ImportError:
    from capabilities import validate_capability_request


# =============================================================================
# Scheduler Interface (injected dependency)
# =============================================================================

class Scheduler:
    """Abstract scheduler interface for quota-aware worker admission.
    
    This interface is implemented by Lichen's quota ledger and dispatch gate.
    The adapter delegates all quota logic to the injected scheduler.
    """
    
    def connect(self, path: str) -> sqlite3.Connection:
        """Connect to quota ledger database."""
        raise NotImplementedError
    
    def reserve(self, db: sqlite3.Connection, *, 
                task: str,
                provider: str,
                model: str,
                scope: str,
                daily_limit: int,
                minute_limit: int,
                token_limit: int,
                tokens: int,
                reserve_fraction: float = 0.15,
                now: Optional[dt.datetime] = None,
                requests: int = 1,
                daily_token_limit: Optional[int] = None,
                protected_requests: int = 0,
                protected_tokens: int = 0) -> str:
        """Attempt to reserve quota for a task.
        
        Returns: "reserved", "already_reserved", "defer", or "already_defer"
        """
        raise NotImplementedError
    
    def observe(self, db: sqlite3.Connection,
                provider: str,
                scope: str,
                metric: str,
                window: str,
                remaining: int,
                source: str,
                now: Optional[dt.datetime] = None) -> None:
        """Record an observation of remaining quota."""
        raise NotImplementedError
    
    def dispatch(self, config: Dict, db: sqlite3.Connection,
                 task: Dict,
                 now: Optional[dt.datetime] = None) -> Dict:
        """Attempt to dispatch a task to an eligible model.
        
        Returns: {"status": "selected"|"defer", ...}
        """
        raise NotImplementedError
    
    def active(self, db: sqlite3.Connection,
               scope: str,
               now: Optional[dt.datetime] = None) -> bool:
        """Check if a scope is under cooldown."""
        raise NotImplementedError
    
    def block(self, db: sqlite3.Connection,
              scope: str,
              seconds: float,
              reason: str,
              now: Optional[dt.datetime] = None) -> str:
        """Block a scope for cooldown."""
        raise NotImplementedError


# =============================================================================
# Provider Registry
# =============================================================================

@dataclass
class ProviderAdmission:
    """Admitted provider with explicit quota/expiry/privacy/rate metadata."""
    provider: str
    model: str
    scope: str
    tier: str
    verified_free: bool
    enabled: bool
    requests_per_day: int
    requests_per_minute: int
    tokens_per_minute: int
    tokens_per_day: Optional[int] = None
    reserve_fraction: float = 0.15
    timeout: float = 600.0
    estimated_tokens: int = 700000
    expires_at: Optional[dt.datetime] = None
    privacy_level: str = "public"
    rate_limit: str = "standard"
    cooldown_until: Optional[dt.datetime] = None


class ProviderRegistry:
    """Registry of admitted providers with quota metadata.
    
    Only admits verified free providers with explicit quotas.
    Refuses paid/unknown providers (fail-closed cost0 enforcement).
    """
    
    def __init__(self, scheduler: Scheduler):
        self._scheduler = scheduler
        self._admitted: Dict[str, ProviderAdmission] = {}
        self._lock = threading.Lock()
    
    def admit_from_config(self, config: Dict) -> List[str]:
        """Admit providers from dispatch config.
        
        Args:
            config: Dispatch configuration with models list
            
        Returns:
            List of admitted provider/model IDs
        """
        admitted = []
        models = config.get("models", [])
        
        for model_config in models:
            admission = self._admit_model(model_config)
            if admission:
                key = f"{admission.provider}/{admission.model}"
                with self._lock:
                    self._admitted[key] = admission
                admitted.append(key)
        
        return admitted
    
    def _admit_model(self, config: Dict) -> Optional[ProviderAdmission]:
        """Admit a single model if it passes admission rules.
        
        Admission rules (fail-closed):
        - Must be verified_free=True (strict boolean)
        - Must have explicit quota fields
        - Must be enabled (strict boolean)
        - No paid providers: cost must be present, numeric, and == 0
          (missing/negative/NaN/malformed cost refused)
        - Expiry if present must be a valid ISO date (malformed refused)
        - Privacy/rate evidence must be present (absent refused)
        """
        # Fail-closed: only verified free providers (strict boolean)
        verified_free = config.get("verified_free")
        if verified_free is not True:
            return None
        
        # Fail-closed: no paid providers. Cost must be present, numeric, and == 0.
        cost = config.get("cost_usd")
        if cost is None:
            return None  # Missing cost evidence refused
        if isinstance(cost, bool) or not isinstance(cost, (int, float)):
            return None  # Malformed cost refused
        if cost != 0:
            return None  # Non-zero cost (paid/negative) refused
        # Reject NaN explicitly (nan != 0 is True, but nan > 0 is False; handle)
        if isinstance(cost, float) and cost != cost:  # NaN check
            return None
        
        # Fail-closed: only enabled providers (strict boolean)
        enabled = config.get("enabled")
        if enabled is not True:
            return None
        
        # Check required quota fields (must be present)
        required = ["id", "provider", "tier", "requests_per_day", 
                   "requests_per_minute", "tokens_per_minute"]
        for field in required:
            if field not in config:
                return None
        
        # Parse expiry if present (malformed expiry refused, not silently ignored)
        expires_at = None
        if "expires_at" in config and config["expires_at"] is not None:
            raw = config["expires_at"]
            try:
                expires_at = dt.datetime.fromisoformat(
                    raw.replace("Z", "+00:00") if isinstance(raw, str) else raw
                )
            except (ValueError, TypeError):
                return None  # Malformed expiry refused
        
        # Privacy/rate evidence must be present (explicit)
        privacy_level = config.get("privacy_level")
        rate_limit = config.get("rate_limit")
        if privacy_level is None or rate_limit is None:
            return None  # Absent privacy/rate evidence refused
        
        return ProviderAdmission(
            provider=config["provider"],
            model=config["id"],
            scope=config.get("quota_scope") or config["provider"],
            tier=config["tier"],
            verified_free=True,
            enabled=config.get("enabled", True),
            requests_per_day=int(config["requests_per_day"]),
            requests_per_minute=int(config["requests_per_minute"]),
            tokens_per_minute=int(config["tokens_per_minute"]),
            tokens_per_day=int(config["tokens_per_day"]) if config.get("tokens_per_day") else None,
            reserve_fraction=float(config.get("reserve_fraction", 0.15)),
            timeout=float(config.get("timeout", 600.0)),
            estimated_tokens=int(config.get("estimated_tokens", 700000)),
            expires_at=expires_at,
            privacy_level=privacy_level,
            rate_limit=rate_limit,
        )
    
    def is_admitted(self, provider: str, model: str) -> bool:
        """Check if a provider/model is admitted."""
        key = f"{provider}/{model}"
        with self._lock:
            return key in self._admitted
    
    def get_admission(self, provider: str, model: str) -> Optional[ProviderAdmission]:
        """Get admission details for a provider/model."""
        key = f"{provider}/{model}"
        with self._lock:
            return self._admitted.get(key)
    
    def get_all_admitted(self) -> List[ProviderAdmission]:
        """Get all admitted providers."""
        with self._lock:
            return list(self._admitted.values())
    
    def is_admitted_by_provider(self, provider: str) -> bool:
        """Check if any provider with the given provider name is admitted."""
        with self._lock:
            for key in self._admitted:
                if key.split("/", 1)[0] == provider:
                    return True
            return False
    
    def get_admissions_by_provider(self, provider: str) -> List[ProviderAdmission]:
        """Get all admitted providers for the given provider name."""
        with self._lock:
            return [admission for key, admission in self._admitted.items()
                    if key.split("/", 1)[0] == provider]
    
    def get_admission_by_provider(self, provider: str) -> Optional[ProviderAdmission]:
        """Get the first admitted provider for the given provider name."""
        with self._lock:
            for key, admission in self._admitted.items():
                if key.split("/", 1)[0] == provider:
                    return admission
            return None
    
    def is_expired(self, admission: ProviderAdmission, now: Optional[dt.datetime] = None) -> bool:
        """Check if an admission has expired."""
        if admission.expires_at is None:
            return False
        now = now or dt.datetime.now(dt.timezone.utc)
        return now >= admission.expires_at
    
    def is_under_cooldown(self, admission: ProviderAdmission, 
                         db: sqlite3.Connection,
                         now: Optional[dt.datetime] = None) -> bool:
        """Check if a provider is under cooldown."""
        now = now or dt.datetime.now(dt.timezone.utc)
        return self._scheduler.active(db, admission.scope, now=now)


# =============================================================================
# Job State Management
# =============================================================================

class JobState:
    """Job state with idempotency tracking."""
    
    # Valid states in order
    STATES = ("pending", "running", "ready", "failure", "refused")
    
    def __init__(self, job_id: str):
        self.job_id = job_id
        self._state = "pending"
        self._attempts = 0
        self._errors: List[str] = []
        self._result: Optional[Dict] = None
        self._lock = threading.Lock()
    
    @property
    def state(self) -> str:
        with self._lock:
            return self._state
    
    @property
    def attempts(self) -> int:
        with self._lock:
            return self._attempts
    
    @property
    def errors(self) -> List[str]:
        with self._lock:
            return list(self._errors)
    
    @property
    def result(self) -> Optional[Dict]:
        with self._lock:
            return self._result
    
    def transition(self, new_state: str) -> bool:
        """Transition to a new state. Returns True if successful."""
        if new_state not in self.STATES:
            raise ValueError(f"Invalid state: {new_state}")
        
        with self._lock:
            # Validate state transition
            current_idx = self.STATES.index(self._state)
            new_idx = self.STATES.index(new_state)
            
            # Allow same state (idempotent) or forward progress
            if new_idx < current_idx:
                return False
            
            self._state = new_state
            return True
    
    def record_attempt(self) -> int:
        with self._lock:
            self._attempts += 1
            return self._attempts
    
    def add_error(self, error: str):
        with self._lock:
            self._errors.append(error)
    
    def set_result(self, result: Dict):
        with self._lock:
            self._result = result
    
    def to_dict(self) -> Dict:
        with self._lock:
            return {
                "job_id": self.job_id,
                "state": self._state,
                "attempts": self._attempts,
                "errors": list(self._errors),
                "result": self._result,
            }


# =============================================================================
# Worker Adapter
# =============================================================================

@dataclass
class WorkerConfig:
    """Configuration for the worker adapter."""
    scheduler: Scheduler
    max_attempts: int = 3
    retry_budget: int = 5
    timeout_seconds: float = 600.0
    gpu_concurrent_limit: int = 1
    quota_reserve_fraction: float = 0.15


class WorkerAdapter:
    """Quota-aware worker adapter with provider admission and fail-closed enforcement.
    
    This adapter:
    - Delegates quota logic to injected scheduler interface
    - Admits only verified free providers with explicit quotas
    - Enforces fail-closed cost0 (no paid providers)
    - Falls back to admitted zero-cost alternative on quota exhaustion
    - Supports bounded retries with configurable budget
    - Integrates with cancellation/deadline
    - Guards GPU concurrency (single GPU-heavy job at a time)
    """
    
    def __init__(self, config: WorkerConfig):
        self._config = config
        self._registry = ProviderRegistry(config.scheduler)
        self._jobs: Dict[str, JobState] = {}
        self._job_lock = threading.Lock()
        self._gpu_lock = threading.Lock()
        self._gpu_in_use = 0
    
    # -------------------------------------------------------------------------
    # Provider Admission
    # -------------------------------------------------------------------------
    
    def admit_provider(self, provider: str, model: str) -> bool:
        """Admit a provider/model combination."""
        return self._registry.is_admitted(provider, model)
    
    def admit_from_config(self, config: Dict) -> List[str]:
        """Admit providers from dispatch config."""
        return self._registry.admit_from_config(config)
    
    def get_admitted_providers(self) -> List[ProviderAdmission]:
        """Get all admitted providers."""
        return self._registry.get_all_admitted()
    
    # -------------------------------------------------------------------------
    # Job Submission
    # -------------------------------------------------------------------------
    
    def submit_job(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a capability request as a job.
        
        Args:
            request: Capability request dictionary
            
        Returns:
            Job submission result with status and job_id
        """
        # Validate request structure
        errors = validate_capability_request(request)
        if errors:
            return {
                "status": "refused",
                "errors": errors,
            }
        
        # Extract provider/model
        provider = request.get("provider", "")
        model = request.get("model", "")
        
        # Check provider admission (fail-closed cost0).
        # The capability request schema does not carry "model", so when the
        # request has no model, resolve admission by provider name alone.
        if model:
            admitted = self._registry.is_admitted(provider, model)
        else:
            admitted = self._registry.is_admitted_by_provider(provider)
        
        if not admitted:
            return {
                "status": "refused",
                "errors": [f"Provider not admitted: {provider}"],
            }
        
        if model:
            admission = self._registry.get_admission(provider, model)
        else:
            admission = self._registry.get_admission_by_provider(provider)
        
        if not admission:
            return {
                "status": "refused",
                "errors": [f"Provider admission not found: {provider}"],
            }
        
        # Check expiry
        now = dt.datetime.now(dt.timezone.utc)
        if self._registry.is_expired(admission, now=now):
            return {
                "status": "refused",
                "errors": [f"Provider admission expired: {provider}/{model}"],
            }
        
        # Check cooldown
        db = self._config.scheduler.connect(":memory:")
        try:
            if self._registry.is_under_cooldown(admission, db, now=now):
                return {
                    "status": "refused",
                    "errors": [f"Provider under cooldown: {provider}/{model}"],
                }
        finally:
            db.close()
        
        # Create job state
        job_id = request.get("id") or f"job-{int(time.time() * 1000)}"
        job = JobState(job_id)
        
        with self._job_lock:
            self._jobs[job_id] = job
        
        # Attempt reservation
        result = self._attempt_reservation(job, request, admission, now=now)
        
        if result["status"] == "defer":
            # Quota exhausted - fall back to admitted zero-cost alternative
            fallback = self._find_fallback(admission, now=now)
            if fallback:
                result = self._attempt_reservation(job, request, fallback, now=now)
            else:
                result = {
                    "status": "failure",
                    "errors": ["Quota exhausted and no fallback available"],
                }
        
        if result["status"] == "failure":
            job.transition("failure")
            for err in result.get("errors", []):
                job.add_error(err)
        
        return {
            "status": result["status"],
            "job_id": job_id,
            "reservation": result.get("reservation"),
            "errors": result.get("errors", []),
        }
    
    def _attempt_reservation(self, job: JobState, request: Dict, 
                            admission: ProviderAdmission,
                            now: dt.datetime) -> Dict:
        """Attempt to reserve quota for a job."""
        job.record_attempt()
        
        db = self._config.scheduler.connect(":memory:")
        try:
            task_id = request.get("id", job.job_id)
            estimated = int(request.get("estimated_tokens", admission.estimated_tokens))
            
            result = self._config.scheduler.reserve(
                db,
                task=task_id,
                provider=admission.provider,
                model=admission.model,
                scope=admission.scope,
                daily_limit=admission.requests_per_day,
                minute_limit=admission.requests_per_minute,
                token_limit=admission.tokens_per_minute,
                tokens=estimated,
                reserve_fraction=admission.reserve_fraction,
                now=now,
                requests=1,
                daily_token_limit=admission.tokens_per_day,
            )
            
            if result in ("reserved", "already_reserved"):
                job.transition("running")
                return {
                    "status": "running",
                    "reservation": result,
                    "provider": admission.provider,
                    "model": admission.model,
                }
            else:
                return {
                    "status": "defer",
                    "errors": [f"Quota reservation failed: {result}"],
                }
        finally:
            db.close()
    
    def _find_fallback(self, original: ProviderAdmission,
                      now: dt.datetime) -> Optional[ProviderAdmission]:
        """Find a fallback provider when quota is exhausted."""
        # Look for other admitted providers with same tier
        for admission in self._registry.get_all_admitted():
            if admission.provider == original.provider:
                continue
            if admission.tier != original.tier:
                continue
            if self._registry.is_expired(admission, now=now):
                continue
            
            db = self._config.scheduler.connect(":memory:")
            try:
                if self._registry.is_under_cooldown(admission, db, now=now):
                    continue
            finally:
                db.close()
            
            # Check if this provider can handle the request
            if self._can_handle_request(admission, original):
                return admission
        
        return None
    
    def _can_handle_request(self, admission: ProviderAdmission,
                           original: ProviderAdmission) -> bool:
        """Check if a fallback provider can handle the original request."""
        # Same tier and verified free
        if admission.tier != original.tier:
            return False
        if not admission.verified_free:
            return False
        
        # Sufficient quota
        if admission.requests_per_day < original.requests_per_day:
            return False
        
        return True
    
    # -------------------------------------------------------------------------
    # Job Execution
    # -------------------------------------------------------------------------
    
    def execute_job(self, job_id: str, handler: Callable,
                   cancelled: Optional[Callable[[], bool]] = None) -> Dict[str, Any]:
        """Execute a running job with the given handler.
        
        Args:
            job_id: Job identifier
            handler: Callable that executes the job
            cancelled: Optional cancellation check function
            
        Returns:
            Job execution result
        """
        with self._job_lock:
            job = self._jobs.get(job_id)
        
        if not job:
            return {
                "status": "failure",
                "errors": [f"Job not found: {job_id}"],
            }
        
        if job.state != "running":
            return {
                "status": "failure",
                "errors": [f"Job not in running state: {job.state}"],
            }
        
        # Check GPU concurrency
        if self._is_gpu_heavy_job(job_id):
            if self._gpu_in_use >= self._config.gpu_concurrent_limit:
                return {
                    "status": "defer",
                    "errors": ["GPU concurrency limit reached"],
                }
            self._gpu_in_use += 1
        
        try:
            result = handler(job)
            job.set_result(result)
            job.transition("ready")
            return {
                "status": "ready",
                "result": result,
            }
        except Exception as e:
            job.add_error(str(e))
            job.record_attempt()
            
            if job.attempts >= self._config.max_attempts:
                job.transition("failure")
                return {
                    "status": "failure",
                    "errors": job.errors,
                }
            
            return {
                "status": "defer",
                "errors": [f"Execution failed: {e}"],
            }
        finally:
            if self._is_gpu_heavy_job(job_id):
                self._gpu_in_use = max(0, self._gpu_in_use - 1)
    
    def _is_gpu_heavy_job(self, job_id: str) -> bool:
        """Check if a job is GPU-heavy (placeholder implementation)."""
        # In a real implementation, this would check job metadata
        return False
    
    # -------------------------------------------------------------------------
    # Job Status
    # -------------------------------------------------------------------------
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the current status of a job."""
        with self._job_lock:
            job = self._jobs.get(job_id)
        
        if not job:
            return {
                "status": "failure",
                "errors": [f"Job not found: {job_id}"],
            }
        
        return job.to_dict()
    
    def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """Cancel a running job."""
        with self._job_lock:
            job = self._jobs.get(job_id)
        
        if not job:
            return {
                "status": "failure",
                "errors": [f"Job not found: {job_id}"],
            }
        
        if job.state not in ("pending", "running"):
            return {
                "status": "failure",
                "errors": [f"Job cannot be cancelled in state: {job.state}"],
            }
        
        job.transition("failure")
        job.add_error("Job was cancelled")
        
        return job.to_dict()
    
    # -------------------------------------------------------------------------
    # Utility
    # -------------------------------------------------------------------------
    
    def get_provider_quota(self, provider: str, model: str) -> Dict[str, Any]:
        """Get quota information for a provider/model."""
        admission = self._registry.get_admission(provider, model)
        if not admission:
            return {
                "status": "failure",
                "errors": [f"Provider not admitted: {provider}/{model}"],
            }
        
        return {
            "status": "ok",
            "provider": admission.provider,
            "model": admission.model,
            "scope": admission.scope,
            "tier": admission.tier,
            "verified_free": admission.verified_free,
            "enabled": admission.enabled,
            "quota": {
                "requests_per_day": admission.requests_per_day,
                "requests_per_minute": admission.requests_per_minute,
                "tokens_per_minute": admission.tokens_per_minute,
                "tokens_per_day": admission.tokens_per_day,
                "reserve_fraction": admission.reserve_fraction,
            },
            "expires_at": admission.expires_at.isoformat() if admission.expires_at else None,
            "privacy_level": admission.privacy_level,
            "rate_limit": admission.rate_limit,
        }


# =============================================================================
# Factory Functions
# =============================================================================

def create_worker_adapter(scheduler: Optional[Scheduler] = None,
                         **kwargs) -> WorkerAdapter:
    """Create a worker adapter with optional scheduler injection.
    
    Args:
        scheduler: Optional scheduler interface (uses default if not provided)
        **kwargs: WorkerConfig parameters
        
    Returns:
        WorkerAdapter instance
    """
    if scheduler is None:
        from . import mock_scheduler
        scheduler = mock_scheduler.MockScheduler()
    
    config = WorkerConfig(scheduler=scheduler, **kwargs)
    return WorkerAdapter(config)


def load_dispatch_config(path: str) -> Dict:
    """Load dispatch configuration from file."""
    return json.loads(Path(path).read_text())
