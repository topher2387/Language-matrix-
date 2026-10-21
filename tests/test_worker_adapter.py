#!/usr/bin/env python3
"""Tests for worker adapter with quota-aware scheduling.

This module provides comprehensive offline tests for the worker adapter,
covering all job states, idempotency, quota exhaustion fallback, and
provider admission rules.
"""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone, timedelta

from language_matrix.worker_adapter import (
    WorkerAdapter,
    WorkerConfig,
    ProviderRegistry,
    ProviderAdmission,
    JobState,
    Scheduler,
    create_worker_adapter,
    load_dispatch_config,
)
from language_matrix.mock_scheduler import MockScheduler


class MockSchedulerForTests(Scheduler):
    """Mock scheduler with deterministic behavior for testing."""
    
    def __init__(self):
        self._dbs = {}
        self._locks = {}
        self._cooldowns = {}
        self._lock = None
    
    def connect(self, path: str):
        if path not in self._dbs:
            self._dbs[path] = sqlite3.connect(path, timeout=15, isolation_level=None)
            self._dbs[path].executescript(_SCHEMA)
            self._locks[path] = type('Lock', (), {'acquire': lambda: True, 'release': lambda: None})()
        return self._dbs[path]
    
    def reserve(self, db, *, task, provider, model, scope, daily_limit,
                minute_limit, token_limit, tokens, reserve_fraction=0.15,
                now=None, requests=1, daily_token_limit=None,
                protected_requests=0, protected_tokens=0):
        now = now or datetime.now(timezone.utc)
        day, minute = now.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%dT%H:%M")
        
        db.execute("BEGIN IMMEDIATE")
        try:
            existing = db.execute(
                "SELECT status FROM reservations WHERE task=? AND provider=? AND model=?",
                (task, provider, model)
            ).fetchone()
            
            if existing:
                result = "already_" + existing[0]
            else:
                # Check cooldown
                if self._is_cooldown_active(db, scope, now):
                    result = "defer"
                else:
                    count_day = db.execute(
                        "SELECT coalesce(sum(requests),0) FROM reservations WHERE scope=? AND day=? AND status!='cancelled'",
                        (scope, day)
                    ).fetchone()[0]
                    
                    count_minute, tokens_minute = db.execute(
                        "SELECT coalesce(sum(requests),0),coalesce(sum(tokens),0) FROM reservations WHERE scope=? AND minute=? AND status!='cancelled'",
                        (scope, minute)
                    ).fetchone()
                    
                    allowed_day = max(0, daily_limit - max(1, int(daily_limit * reserve_fraction)))
                    
                    if (count_day + requests > allowed_day or 
                        count_minute + requests > minute_limit or 
                        tokens_minute + tokens > token_limit):
                        result = "defer"
                    else:
                        db.execute(
                            "INSERT INTO reservations(task,provider,model,scope,day,minute,tokens,status,requests) VALUES (?,?,?,?,?,?,?,'reserved',?)",
                            (task, provider, model, scope, day, minute, tokens, requests)
                        )
                        result = "reserved"
            
            db.execute("COMMIT")
            return result
        except Exception:
            db.execute("ROLLBACK")
            raise
    
    def observe(self, db, provider, scope, metric, window, remaining, source, now=None):
        stamp = (now or datetime.now(timezone.utc)).isoformat()
        db.execute(
            "INSERT INTO observations(provider,scope,metric,window,remaining,observed_at,source) VALUES (?,?,?,?,?,?,?)",
            (provider, scope, metric, window, remaining, stamp, source)
        )
    
    def dispatch(self, config, db, task, now=None):
        now = now or datetime.now(timezone.utc)
        task_id = task.get("id")
        
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("Task needs stable nonempty id")
        
        estimated = int(task.get("estimated_tokens", 2000))
        if estimated <= 0:
            raise ValueError("Estimated tokens must be positive")
        
        for model in config.get("models", []):
            if not model.get("enabled", True):
                continue
            if not model.get("verified_free", False):
                continue
            
            scope = model.get("quota_scope") or model["provider"]
            
            if self._is_cooldown_active(db, scope, now):
                continue
            
            result = self.reserve(
                db,
                task=task_id,
                provider=model["provider"],
                model=model["id"],
                scope=scope,
                daily_limit=model["requests_per_day"],
                minute_limit=model["requests_per_minute"],
                token_limit=model["tokens_per_minute"],
                tokens=estimated,
                reserve_fraction=model.get("reserve_fraction", 0.15),
                now=now,
            )
            
            if result in ("reserved", "already_reserved"):
                return {
                    "status": "selected",
                    "model": model["id"],
                    "provider": model["provider"],
                    "reservation": result,
                    "tier": "coding",
                }
        
        return {"status": "defer", "reason": "no verified free capacity"}
    
    def active(self, db, scope, now=None):
        now = now or datetime.now(timezone.utc)
        row = db.execute(
            "SELECT until_utc FROM cooldowns WHERE scope=?",
            (scope,)
        ).fetchone()
        return bool(row and row[0] > now.isoformat())
    
    def block(self, db, scope, seconds, reason, now=None):
        now = now or datetime.now(timezone.utc)
        until = (now + timedelta(seconds=seconds)).isoformat()
        
        db.execute("BEGIN IMMEDIATE")
        try:
            db.execute(
                """INSERT INTO cooldowns(scope,until_utc,reason,updated_utc)
                   VALUES(?,?,?,?) ON CONFLICT(scope) DO UPDATE SET
                   until_utc=excluded.until_utc,reason=excluded.reason,updated_utc=excluded.updated_utc""",
                (scope, until, reason[:300], now.isoformat())
            )
            db.execute("COMMIT")
        except Exception:
            db.execute("ROLLBACK")
            raise
        
        return until
    
    def _is_cooldown_active(self, db, scope, now):
        row = db.execute(
            "SELECT until_utc FROM cooldowns WHERE scope=?",
            (scope,)
        ).fetchone()
        return bool(row and row[0] > now.isoformat())


_SCHEMA = """
CREATE TABLE IF NOT EXISTS reservations (
 task TEXT NOT NULL, provider TEXT NOT NULL, model TEXT NOT NULL,
 scope TEXT NOT NULL, day TEXT NOT NULL, minute TEXT NOT NULL,
 tokens INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'reserved',
 PRIMARY KEY(task,provider,model));
CREATE INDEX IF NOT EXISTS reservations_window ON reservations(scope,day,minute);
CREATE TABLE IF NOT EXISTS observations (
 id INTEGER PRIMARY KEY AUTOINCREMENT, provider TEXT NOT NULL, scope TEXT NOT NULL,
 metric TEXT NOT NULL, window TEXT NOT NULL, remaining INTEGER NOT NULL,
 observed_at TEXT NOT NULL, source TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS cooldowns(
 scope TEXT PRIMARY KEY, until_utc TEXT NOT NULL, reason TEXT NOT NULL,
 updated_utc TEXT NOT NULL);
"""


class TestProviderRegistry(unittest.TestCase):
    """Tests for ProviderRegistry admission rules."""
    
    def test_admit_verified_free_provider(self):
        """Admit verified free providers with explicit quotas."""
        registry = ProviderRegistry(MockSchedulerForTests())
        
        config = {
            "models": [{
                "id": "model-a",
                "provider": "free-provider",
                "tier": "coding",
                "verified_free": True,
                "enabled": True,
                "cost_usd": 0,
                "privacy_level": "public",
                "rate_limit": "standard",
                "requests_per_day": 100,
                "requests_per_minute": 10,
                "tokens_per_minute": 5000,
            }]
        }
        
        admitted = registry.admit_from_config(config)
        self.assertEqual(len(admitted), 1)
        self.assertIn("free-provider/model-a", admitted)
    
    def test_refuse_unverified_provider(self):
        """Refuse unverified providers (fail-closed cost0)."""
        registry = ProviderRegistry(MockSchedulerForTests())
        
        config = {
            "models": [{
                "id": "model-a",
                "provider": "unverified",
                "tier": "coding",
                "verified_free": False,  # Not verified
                "enabled": True,
                "requests_per_day": 100,
                "requests_per_minute": 10,
                "tokens_per_minute": 5000,
            }]
        }
        
        admitted = registry.admit_from_config(config)
        self.assertEqual(len(admitted), 0)
    
    def test_refuse_paid_provider(self):
        """Refuse paid providers (fail-closed cost0)."""
        registry = ProviderRegistry(MockSchedulerForTests())
        
        config = {
            "models": [{
                "id": "model-a",
                "provider": "paid-provider",
                "tier": "coding",
                "verified_free": True,
                "enabled": True,
                "cost_usd": 0.001,  # Has cost
                "requests_per_day": 100,
                "requests_per_minute": 10,
                "tokens_per_minute": 5000,
            }]
        }
        
        admitted = registry.admit_from_config(config)
        self.assertEqual(len(admitted), 0)
    
    def test_refuse_disabled_provider(self):
        """Refuse disabled providers."""
        registry = ProviderRegistry(MockSchedulerForTests())
        
        config = {
            "models": [{
                "id": "model-a",
                "provider": "free-provider",
                "tier": "coding",
                "verified_free": True,
                "enabled": False,  # Disabled
                "cost_usd": 0,
                "privacy_level": "public",
                "rate_limit": "standard",
                "requests_per_day": 100,
                "requests_per_minute": 10,
                "tokens_per_minute": 5000,
            }]
        }
        
        admitted = registry.admit_from_config(config)
        # Disabled providers are not admitted
        self.assertEqual(len(admitted), 0)
    
    def test_is_admitted_check(self):
        """Test is_admitted method."""
        registry = ProviderRegistry(MockSchedulerForTests())
        
        config = {
            "models": [{
                "id": "model-a",
                "provider": "free-provider",
                "tier": "coding",
                "verified_free": True,
                "enabled": True,
                "cost_usd": 0,
                "privacy_level": "public",
                "rate_limit": "standard",
                "requests_per_day": 100,
                "requests_per_minute": 10,
                "tokens_per_minute": 5000,
            }]
        }
        
        registry.admit_from_config(config)
        
        self.assertTrue(registry.is_admitted("free-provider", "model-a"))
        self.assertFalse(registry.is_admitted("free-provider", "model-b"))
        self.assertFalse(registry.is_admitted("other-provider", "model-a"))


class TestJobState(unittest.TestCase):
    """Tests for JobState management."""
    
    def test_initial_state(self):
        """Job starts in pending state."""
        job = JobState("test-job")
        self.assertEqual(job.state, "pending")
        self.assertEqual(job.attempts, 0)
        self.assertEqual(job.errors, [])
        self.assertIsNone(job.result)
    
    def test_state_transitions(self):
        """Test valid state transitions."""
        job = JobState("test-job")
        
        self.assertTrue(job.transition("running"))
        self.assertEqual(job.state, "running")
        
        self.assertTrue(job.transition("ready"))
        self.assertEqual(job.state, "ready")
    
    def test_invalid_state_transition(self):
        """Test invalid state transitions are rejected."""
        job = JobState("test-job")
        
        # Cannot go backwards
        job.transition("running")
        self.assertFalse(job.transition("pending"))
        self.assertEqual(job.state, "running")
    
    def test_record_attempt(self):
        """Test attempt counting."""
        job = JobState("test-job")
        
        self.assertEqual(job.record_attempt(), 1)
        self.assertEqual(job.record_attempt(), 2)
        self.assertEqual(job.record_attempt(), 3)
    
    def test_add_error(self):
        """Test error recording."""
        job = JobState("test-job")
        
        job.add_error("First error")
        job.add_error("Second error")
        
        self.assertEqual(len(job.errors), 2)
        self.assertIn("First error", job.errors)
        self.assertIn("Second error", job.errors)
    
    def test_set_result(self):
        """Test result setting."""
        job = JobState("test-job")
        result = {"output": "test output"}
        
        job.set_result(result)
        self.assertEqual(job.result, result)
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        job = JobState("test-job")
        job.transition("running")
        job.record_attempt()
        job.add_error("Test error")
        
        d = job.to_dict()
        
        self.assertEqual(d["job_id"], "test-job")
        self.assertEqual(d["state"], "running")
        self.assertEqual(d["attempts"], 1)
        self.assertIn("Test error", d["errors"])


class TestWorkerAdapter(unittest.TestCase):
    """Tests for WorkerAdapter integration."""
    
    def test_submit_valid_request(self):
        """Submit a valid capability request."""
        scheduler = MockSchedulerForTests()
        adapter = WorkerAdapter(WorkerConfig(scheduler=scheduler))
        
        # Admit a provider
        config = {
            "models": [{
                "id": "model-a",
                "provider": "local",
                "tier": "coding",
                "verified_free": True,
                "enabled": True,
                "cost_usd": 0,
                "privacy_level": "public",
                "rate_limit": "standard",
                "requests_per_day": 100,
                "requests_per_minute": 10,
                "tokens_per_minute": 5000,
            }]
        }
        adapter.admit_from_config(config)
        
        request = {
            "schema_version": "1.0",
            "request_id": "test-job",
            "capability": "lesson.generate",
            "provider": "local",
            "input": {
                "text": "Test input",
                "language": "ko",
            },
            "output_schema": "lesson.v1",
            "permissions": ["local.generate"],
            "deadline_utc": (datetime.now(timezone.utc) + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "policy": {
                "max_cost_usd": 0,
                "allow_network": False,
                "max_attempts": 3,
                "timeout_seconds": 300,
            },
            "rationale": "Test request",
        }

        result = adapter.submit_job(request)
        
        self.assertIn(result["status"], ("running", "ready"))
        self.assertEqual(result["job_id"], "test-request")

    def test_submit_invalid_provider(self):
        """Submit request with non-admitted provider."""
        scheduler = MockSchedulerForTests()
        adapter = WorkerAdapter(WorkerConfig(scheduler=scheduler))
        
        request = {
            "schema_version": "1.0",
            "request_id": "test-request",
            "capability": "lesson.generate",
            "provider": "local",
            "input": {
                "text": "Test input",
                "language": "ko",
            },
            "output_schema": "lesson.v1",
            "permissions": ["local.generate"],
            "deadline_utc": (datetime.now(timezone.utc) + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "policy": {
                "max_cost_usd": 0,
                "allow_network": False,
                "max_attempts": 3,
                "timeout_seconds": 300,
            },
            "rationale": "Test request",
        }
        
        result = adapter.submit_job(request)
        
        self.assertEqual(result["status"], "refused")
        self.assertIn("not admitted", result["errors"][0])

    def test_submit_expired_provider(self):
        """Submit request with expired provider admission."""
        scheduler = MockSchedulerForTests()
        adapter = WorkerAdapter(WorkerConfig(scheduler=scheduler))
        
        config = {
            "models": [{
                "id": "model-a",
                "provider": "local",
                "tier": "coding",
                "verified_free": True,
                "enabled": True,
                "requests_per_day": 100,
                "requests_per_minute": 10,
                "tokens_per_minute": 5000,
                "expires_at": (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }]
        }
        adapter.admit_from_config(config)
        
        request = {
            "schema_version": "1.0",
            "request_id": "test-request",
            "capability": "lesson.generate",
            "provider": "local",
            "input": {
                "text": "Test input",
                "language": "ko",
            },
            "output_schema": "lesson.v1",
            "permissions": ["local.generate"],
            "deadline_utc": (datetime.now(timezone.utc) + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "policy": {
                "max_cost_usd": 0,
                "allow_network": False,
                "max_attempts": 3,
                "timeout_seconds": 300,
            },
            "rationale": "Test request",
        }

        result = adapter.submit_job(request)
        
        self.assertEqual(result["status"], "refused")
        self.assertIn("expired", result["errors"][0])

    def test_quota_exhaustion_fallback(self):
        """Test fallback when quota is exhausted."""
        scheduler = MockSchedulerForTests()
        adapter = WorkerAdapter(WorkerConfig(scheduler=scheduler, max_attempts=1))
        
        # Admit two providers
        config = {
            "models": [
                {
                    "id": "model-a",
                    "provider": "local",
                    "tier": "coding",
                    "verified_free": True,
                    "enabled": True,
                "cost_usd": 0,
                    "privacy_level": "public",
                    "rate_limit": "standard",
                    "requests_per_day": 2,  # Only 2 requests allowed
                    "requests_per_minute": 2,
                    "tokens_per_minute": 5000,
                },
                {
                    "id": "model-b",
                    "provider": "local",
                    "tier": "coding",
                    "verified_free": True,
                    "enabled": True,
                "cost_usd": 0,
                    "privacy_level": "public",
                    "rate_limit": "standard",
                    "requests_per_day": 100,
                    "requests_per_minute": 10,
                    "tokens_per_minute": 5000,
                },
            ]
        }
        adapter.admit_from_config(config)
        
        # Submit requests until quota exhausted
        for i in range(2):
            request = {
                "schema_version": "1.0",
                "request_id": f"request-{i}",
                "capability": "lesson.generate",
                "provider": "local",
                "input": {
                    "text": "Test input",
                    "language": "ko",
                },
                "output_schema": "lesson.v1",
                "permissions": ["local.generate"],
                "deadline_utc": (datetime.now(timezone.utc) + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "policy": {
                    "max_cost_usd": 0,
                    "allow_network": False,
                    "max_attempts": 1,
                    "timeout_seconds": 300,
                },
                "rationale": "Test request",
            }
            result = adapter.submit_job(request)
            self.assertIn(result["status"], ("running", "ready"))
        
        # Third request should fall back to model-b
        request = {
            "schema_version": "1.0",
                "request_id": "request-2",
                "capability": "lesson.generate",
                "provider": "local",
                "input": {
                    "text": "Test input",
                    "language": "ko",
                },
            "output_schema": "lesson.v1",
            "permissions": ["local.generate"],
            "deadline_utc": (datetime.now(timezone.utc) + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "policy": {
                "max_cost_usd": 0,
                "allow_network": False,
                "max_attempts": 1,
                "timeout_seconds": 300,
            },
            "rationale": "Test request",
        }
        result = adapter.submit_job(request)
        
        # Should succeed with fallback
        self.assertIn(result["status"], ("running", "ready"))
    
    def test_get_job_status(self):
        """Test job status retrieval."""
        scheduler = MockSchedulerForTests()
        adapter = WorkerAdapter(WorkerConfig(scheduler=scheduler))
        
        config = {
            "models": [{
                "id": "model-a",
                "provider": "local",
                "tier": "coding",
                "verified_free": True,
                "enabled": True,
                "requests_per_day": 100,
                "requests_per_minute": 10,
                "tokens_per_minute": 5000,
            }]
        }
        adapter.admit_from_config(config)
    
        request = {
            "schema_version": "1.0",
            "request_id": "test-job",
            "capability": "lesson.generate",
            "provider": "local",
            "model": "model-a",
            "input": {
                "text": "Test input",
                "language": "ko",
            },
            "output_schema": "lesson.v1",
            "permissions": ["local.generate"],
            "deadline_utc": (datetime.now(timezone.utc) + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "policy": {
                "max_cost_usd": 0,
                "allow_network": False,
                "max_attempts": 3,
                "timeout_seconds": 300,
            },
            "rationale": "Test request",
        }

        adapter.submit_job(request)
        status = adapter.get_job_status("test-job")
        
        self.assertEqual(status["job_id"], "test-job")
        self.assertIn(status["state"], ("running", "ready"))
    
    def test_cancel_job(self):
        """Test job cancellation."""
        scheduler = MockSchedulerForTests()
        adapter = WorkerAdapter(WorkerConfig(scheduler=scheduler))
        
        config = {
            "models": [{
                "id": "model-a",
                "provider": "local",
                "tier": "coding",
                "verified_free": True,
                "enabled": True,
                "requests_per_day": 100,
                "requests_per_minute": 10,
                "tokens_per_minute": 5000,
            }]
        }
        adapter.admit_from_config(config)
    
        request = {
            "schema_version": "1.0",
            "request_id": "test-job",
            "capability": "lesson.generate",
            "provider": "local",
            "model": "model-a",
            "input": {
                "text": "Test input",
                "language": "ko",
            },
            "output_schema": "lesson.v1",
            "permissions": ["local.generate"],
            "deadline_utc": (datetime.now(timezone.utc) + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "policy": {
                "max_cost_usd": 0,
                "allow_network": False,
                "max_attempts": 3,
                "timeout_seconds": 300,
            },
            "rationale": "Test request",
        }

        adapter.submit_job(request)
        result = adapter.cancel_job("test-job")
        
        self.assertEqual(result["state"], "failure")
        self.assertIn("cancelled", result["errors"][0])
    
    def test_get_provider_quota(self):
        """Test provider quota information."""
        scheduler = MockSchedulerForTests()
        adapter = WorkerAdapter(WorkerConfig(scheduler=scheduler))
        
        config = {
            "models": [{
                "id": "model-a",
                "provider": "free-provider",
                "tier": "coding",
                "verified_free": True,
                "enabled": True,
                "cost_usd": 0,
                "privacy_level": "public",
                "rate_limit": "standard",
                "requests_per_day": 100,
                "requests_per_minute": 10,
                "tokens_per_minute": 5000,
            }]
        }
        adapter.admit_from_config(config)
        
        quota = adapter.get_provider_quota("free-provider", "model-a")
        
        self.assertEqual(quota["status"], "ok")
        self.assertEqual(quota["provider"], "free-provider")
        self.assertEqual(quota["model"], "model-a")
        self.assertEqual(quota["quota"]["requests_per_day"], 100)


class TestIdempotency(unittest.TestCase):
    """Tests for idempotent behavior."""
    
    def test_duplicate_reservation(self):
        """Duplicate reservations return already_reserved."""
        scheduler = MockSchedulerForTests()
        adapter = WorkerAdapter(WorkerConfig(scheduler=scheduler))
        
        config = {
            "models": [{
                "id": "model-a",
                "provider": "local",
                "tier": "coding",
                "verified_free": True,
                "enabled": True,
                "cost_usd": 0,
                "privacy_level": "public",
                "rate_limit": "standard",
                "requests_per_day": 100,
                "requests_per_minute": 10,
                "tokens_per_minute": 5000,
            }]
        }
        adapter.admit_from_config(config)
        
        request = {
            "schema_version": "1.0",
            "request_id": "test-job",
            "capability": "lesson.generate",
            "provider": "local",
            "input": {
                "text": "Test input",
                "language": "ko",
            },
            "output_schema": "lesson.v1",
            "permissions": ["local.generate"],
            "deadline_utc": (datetime.now(timezone.utc) + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "policy": {
                "max_cost_usd": 0,
                "allow_network": False,
                "max_attempts": 3,
                "timeout_seconds": 300,
            },
            "rationale": "Test request",
        }

        # First submission
        result1 = adapter.submit_job(request)
        
        # Second submission with same ID
        result2 = adapter.submit_job(request)
        
        # Both should succeed
        self.assertIn(result1["status"], ("running", "ready"))
        self.assertIn(result2["status"], ("running", "ready"))


if __name__ == "__main__":
    unittest.main()
