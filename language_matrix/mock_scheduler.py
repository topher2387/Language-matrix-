#!/usr/bin/env python3
"""Mock scheduler for offline testing of worker adapter.

This mock implements the Scheduler interface without requiring live Lichen runtime.
It uses in-memory SQLite for quota tracking.
"""
import datetime as dt
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .worker_adapter import Scheduler


class MockScheduler(Scheduler):
    """Mock scheduler for offline testing.
    
    This mock:
    - Uses in-memory SQLite for quota tracking
    - Supports deterministic reservation results
    - Tracks quota usage for testing
    - Supports cooldown simulation
    """
    
    def __init__(self):
        self._dbs: Dict[str, sqlite3.Connection] = {}
        self._locks: Dict[str, threading.Lock] = {}
        self._usage: Dict[str, Dict] = {}
        self._cooldowns: Dict[str, str] = {}
        self._lock = threading.Lock()
    
    def _get_db(self, path: str) -> sqlite3.Connection:
        """Get or create a database connection. Recreate if the cached
        connection was closed (e.g. by a prior short-lived cooldown check)."""
        with self._lock:
            db = self._dbs.get(path)
            if db is None or getattr(db, "closed", False):
                db = sqlite3.connect(path, timeout=15, isolation_level=None)
                db.execute("PRAGMA busy_timeout=15000")
                db.execute("PRAGMA journal_mode=WAL")
                db.executescript(_SCHEMA)
                self._dbs[path] = db
                self._locks[path] = threading.Lock()
            return self._dbs[path]
    
    def _get_lock(self, db: sqlite3.Connection) -> threading.Lock:
        """Get the lock for a database."""
        # For in-memory databases, use a consistent key
        if db.isolation_level is None and db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reservations'").fetchone():
            # In-memory database - use a consistent key
            return self._locks.get(":memory:", threading.Lock())
        # For file-based databases, use the path
        for path, d in self._dbs.items():
            if d == db:
                return self._locks.get(path, threading.Lock())
        return threading.Lock()
    
    def connect(self, path: str) -> sqlite3.Connection:
        """Connect to quota ledger database."""
        return self._get_db(path)
    
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
        """Attempt to reserve quota for a task."""
        now = now or dt.datetime.now(dt.timezone.utc)
        day, minute = now.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%dT%H:%M")
        
        lock = self._get_lock(db)
        with lock:
            db.execute("BEGIN IMMEDIATE")
            try:
                # Check for existing reservation
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
                        # Check quota limits
                        count_day = db.execute(
                            "SELECT coalesce(sum(requests),0) FROM reservations WHERE scope=? AND day=? AND status!='cancelled'",
                            (scope, day)
                        ).fetchone()[0]
                        
                        count_minute, tokens_minute = db.execute(
                            "SELECT coalesce(sum(requests),0),coalesce(sum(tokens),0) FROM reservations WHERE scope=? AND minute=? AND status!='cancelled'",
                            (scope, minute)
                        ).fetchone()
                        
                        allowed_day = max(0, daily_limit - max(1, int(daily_limit * reserve_fraction)) - protected_requests)
                        
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
    
    def observe(self, db: sqlite3.Connection,
                provider: str,
                scope: str,
                metric: str,
                window: str,
                remaining: int,
                source: str,
                now: Optional[dt.datetime] = None) -> None:
        """Record an observation of remaining quota."""
        stamp = (now or dt.datetime.now(dt.timezone.utc)).isoformat()
        db.execute(
            "INSERT INTO observations(provider,scope,metric,window,remaining,observed_at,source) VALUES (?,?,?,?,?,?,?)",
            (provider, scope, metric, window, remaining, stamp, source)
        )
    
    def dispatch(self, config: Dict, db: sqlite3.Connection,
                 task: Dict,
                 now: Optional[dt.datetime] = None) -> Dict:
        """Attempt to dispatch a task to an eligible model."""
        now = now or dt.datetime.now(dt.timezone.utc)
        task_id = task.get("id")
        
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("Task needs stable nonempty id")
        
        estimated = int(task.get("estimated_tokens", 2000))
        if estimated <= 0:
            raise ValueError("Estimated tokens must be positive")
        
        # Simple dispatch: try first enabled verified_free model
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
                    "tier": self._classify(task),
                }
        
        return {"status": "defer", "reason": "no verified free capacity"}
    
    def active(self, db: sqlite3.Connection,
               scope: str,
               now: Optional[dt.datetime] = None) -> bool:
        """Check if a scope is under cooldown."""
        now = now or dt.datetime.now(dt.timezone.utc)
        row = db.execute(
            "SELECT until_utc FROM cooldowns WHERE scope=?",
            (scope,)
        ).fetchone()
        return bool(row and row[0] > now.isoformat())
    
    def block(self, db: sqlite3.Connection,
              scope: str,
              seconds: float,
              reason: str,
              now: Optional[dt.datetime] = None) -> str:
        """Block a scope for cooldown."""
        now = now or dt.datetime.now(dt.timezone.utc)
        until = (now + dt.timedelta(seconds=seconds)).isoformat()
        
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
    
    def _is_cooldown_active(self, db: sqlite3.Connection, scope: str, 
                           now: dt.datetime) -> bool:
        """Check if a scope has active cooldown."""
        row = db.execute(
            "SELECT until_utc FROM cooldowns WHERE scope=?",
            (scope,)
        ).fetchone()
        return bool(row and row[0] > now.isoformat())
    
    def _classify(self, task: Dict) -> str:
        """Classify task complexity."""
        if task.get("escalate") or task.get("failed_attempts", 0) >= 2:
            return "reasoning"
        if task.get("complexity"):
            return task["complexity"]
        return "coding"


# Schema for mock database
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
