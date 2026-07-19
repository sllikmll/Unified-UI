"""Small background job runner for latency probes.

Latency probes intentionally run outside the request handler: on router builds
the UI server can be a single gevent loop, so a blocking probe would stall
regular status polling until every node times out.
"""

from __future__ import annotations

import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Callable, Dict


try:
    _MAX_WORKERS = max(1, min(int(os.environ.get("UNIFIED_LATENCY_JOB_WORKERS", "2") or "2"), 8))
except Exception:
    _MAX_WORKERS = 2


_EXECUTOR = ThreadPoolExecutor(max_workers=_MAX_WORKERS)
_JOBS: Dict[str, "LatencyJob"] = {}
_LOCK = Lock()
_MAX_JOB_AGE_SECONDS = 1800


@dataclass
class LatencyJob:
    id: str
    status: str = "queued"
    result: Dict[str, Any] | None = None
    error: str = ""
    created_at: float = field(default_factory=time.time)
    finished_at: float | None = None

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "ok": self.status != "error",
            "job_id": self.id,
            "status": self.status,
            "created_at": self.created_at,
            "finished_at": self.finished_at,
        }
        if self.result is not None:
            payload["result"] = self.result
        if self.error:
            payload["error"] = self.error
        return payload


def cleanup_latency_jobs() -> None:
    now = time.time()
    with _LOCK:
        old_ids = [
            job_id
            for job_id, job in _JOBS.items()
            if job.finished_at is not None and (now - float(job.finished_at)) > _MAX_JOB_AGE_SECONDS
        ]
        for job_id in old_ids:
            _JOBS.pop(job_id, None)


def get_latency_job(job_id: str) -> LatencyJob | None:
    cleanup_latency_jobs()
    key = str(job_id or "").strip()
    if not key:
        return None
    with _LOCK:
        return _JOBS.get(key)


def create_latency_job(fn: Callable[[], Dict[str, Any]]) -> LatencyJob:
    job = LatencyJob(id=uuid.uuid4().hex)
    with _LOCK:
        _JOBS[job.id] = job

    def _run() -> None:
        with _LOCK:
            current = _JOBS.get(job.id)
            if current is None:
                return
            current.status = "running"
        try:
            result = fn()
            if not isinstance(result, dict):
                result = {"ok": False, "error": "latency job returned invalid result"}
            with _LOCK:
                current = _JOBS.get(job.id)
                if current is None:
                    return
                current.result = result
                current.status = "finished"
                current.finished_at = time.time()
        except Exception as exc:
            with _LOCK:
                current = _JOBS.get(job.id)
                if current is None:
                    return
                current.error = str(exc)
                current.status = "error"
                current.finished_at = time.time()

    _EXECUTOR.submit(_run)
    cleanup_latency_jobs()
    return job
