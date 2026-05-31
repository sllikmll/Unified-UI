from __future__ import annotations

import time


def test_latency_job_runs_callable_and_exposes_result():
    from services.latency_jobs import create_latency_job, get_latency_job

    job = create_latency_job(lambda: {"ok": True, "value": 42})

    current = None
    deadline = time.time() + 3
    while time.time() < deadline:
        current = get_latency_job(job.id)
        if current and current.status == "finished":
            break
        time.sleep(0.02)

    assert current is not None
    assert current.status == "finished"
    assert current.to_dict()["result"] == {"ok": True, "value": 42}
