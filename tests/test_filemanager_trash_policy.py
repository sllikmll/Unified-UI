from __future__ import annotations

import json
import threading
import time

from services.fileops.job_models import FileOpJob
from services.fileops.ops_delete import run_job_delete
from services.fileops.runtime import FileOpsRuntime
from services.fs_common import local as localfs


def test_trash_cfg_preserves_explicit_zero_max_bytes(monkeypatch):
    monkeypatch.setenv("XKEEN_TRASH_MAX_BYTES", "0")
    monkeypatch.setenv("XKEEN_TRASH_MAX_GB", "3")

    assert localfs._trash_cfg()["max_bytes"] == 0


def test_trash_cfg_allows_zero_max_gb_when_bytes_unset(monkeypatch):
    monkeypatch.delenv("XKEEN_TRASH_MAX_BYTES", raising=False)
    monkeypatch.setenv("XKEEN_TRASH_MAX_GB", "0")

    assert localfs._trash_cfg()["max_bytes"] == 0


def test_local_soft_delete_is_hard_when_trash_max_is_zero(monkeypatch):
    removed = []

    monkeypatch.setattr(localfs, "_local_resolve_nofollow", lambda path, roots: "/sandbox/file.txt")
    monkeypatch.setattr(localfs, "_local_is_in_trash_abs", lambda path, roots: False)
    monkeypatch.setattr(
        localfs,
        "_local_trash_stats",
        lambda roots, force_refresh=False, force_purge=False: {
            "enabled": False,
            "max_bytes": 0,
            "ttl_days": 30,
        },
    )
    monkeypatch.setattr(localfs, "_local_remove_entry", lambda path, roots, recursive=False: removed.append((path, recursive)))
    monkeypatch.setattr(localfs, "_tree_size_bytes", lambda path: (_ for _ in ()).throw(AssertionError("size should not be read")))
    monkeypatch.setattr(localfs, "_local_move_to_trash", lambda path, roots: (_ for _ in ()).throw(AssertionError("should not move to trash")))

    info = localfs._local_soft_delete("/sandbox/file.txt", ["/sandbox"])

    assert info["mode"] == "hard"
    assert info["reason"] == "trash_disabled"
    assert removed == [("/sandbox/file.txt", True)]


def test_local_soft_delete_is_hard_when_trash_ttl_is_zero(monkeypatch):
    removed = []

    monkeypatch.setattr(localfs, "_local_resolve_nofollow", lambda path, roots: "/sandbox/file.txt")
    monkeypatch.setattr(localfs, "_local_is_in_trash_abs", lambda path, roots: False)
    monkeypatch.setattr(
        localfs,
        "_local_trash_stats",
        lambda roots, force_refresh=False, force_purge=False: {
            "enabled": False,
            "max_bytes": 1024,
            "ttl_days": 0,
        },
    )
    monkeypatch.setattr(localfs, "_local_remove_entry", lambda path, roots, recursive=False: removed.append((path, recursive)))
    monkeypatch.setattr(localfs, "_tree_size_bytes", lambda path: (_ for _ in ()).throw(AssertionError("size should not be read")))
    monkeypatch.setattr(localfs, "_local_move_to_trash", lambda path, roots: (_ for _ in ()).throw(AssertionError("should not move to trash")))

    info = localfs._local_soft_delete("/sandbox/file.txt", ["/sandbox"])

    assert info["mode"] == "hard"
    assert info["reason"] == "trash_disabled"
    assert removed == [("/sandbox/file.txt", True)]


def test_trash_stats_ttl_zero_forces_purge_even_with_fresh_cache(monkeypatch):
    purges = []

    monkeypatch.setattr(
        localfs,
        "_trash_cfg",
        lambda: {
            "max_bytes": 1024,
            "ttl_days": 0,
            "warn_ratio": 0.9,
            "stats_cache_seconds": 60,
            "purge_interval_seconds": 3600,
        },
    )
    monkeypatch.setattr(
        localfs,
        "_local_trash_purge_expired",
        lambda roots, ttl_days: purges.append(ttl_days) or {"purged": 2, "meta_purged": 2, "errors": []},
    )
    monkeypatch.setattr(localfs, "_local_trash_used_bytes", lambda roots: (0, False))
    monkeypatch.setattr(localfs, "_TRASH_LAST_PURGE_TS", time.time())
    monkeypatch.setitem(localfs._TRASH_STATS_CACHE, "ts", time.time())
    monkeypatch.setitem(localfs._TRASH_STATS_CACHE, "data", {"cached": True})

    stats = localfs._local_trash_stats(["/sandbox"])

    assert purges == [0]
    assert stats["enabled"] is False
    assert stats["purge"]["purged"] == 2


def test_trash_purge_ttl_zero_removes_existing_entries(tmp_path, monkeypatch):
    trash_root = tmp_path / "trash"
    meta_dir = trash_root / localfs._TRASH_META_DIRNAME
    meta_dir.mkdir(parents=True)
    item = trash_root / "old-file.txt"
    item.write_text("stale", encoding="utf-8")
    meta = meta_dir / f"{item.name}.json"
    meta.write_text(json.dumps({"deleted_ts": int(time.time()) - 5}), encoding="utf-8")

    monkeypatch.setattr(localfs, "_local_trash_dirs", lambda roots: (str(trash_root), str(meta_dir)))

    result = localfs._local_trash_purge_expired([str(tmp_path)], ttl_days=0)

    assert result["purged"] == 1
    assert result["meta_purged"] == 1
    assert not item.exists()
    assert not meta.exists()


def test_fileops_delete_reports_disabled_trash_policy():
    def progress_set(job, **kwargs):
        if job.progress is None:
            job.progress = {}
        job.progress.update(kwargs)

    def job_set_state(job, state, error=None):
        job.state = state
        job.error = error

    runtime = FileOpsRuntime(
        mgr=None,
        local_roots=["/sandbox"],
        now_fn=lambda: 123.0,
        job_set_state=job_set_state,
        progress_set=progress_set,
        local_soft_delete=lambda path, roots, hard=False: {
            "mode": "hard",
            "reason": "trash_disabled",
            "trash": {"enabled": False, "max_bytes": 0, "ttl_days": 0},
        },
        lftp_quote=lambda value: value,
    )
    job = FileOpJob(
        job_id="job-1",
        op="delete",
        created_ts=100.0,
        progress={},
        cancel_flag=threading.Event(),
    )
    spec = {
        "src": {"target": "local"},
        "sources": [{"path": "/sandbox/file.txt", "name": "file.txt", "is_dir": False}],
        "options": {},
    }

    run_job_delete(job, spec, runtime)

    trash = job.progress["trash"]
    assert job.state == "done"
    assert trash["summary"]["disabled"] == 1
    assert trash["summary"]["permanent"] == 1
    assert "Корзина отключена" in trash["notice"]
    assert any("Корзина отключена" in note for note in job.progress["notes"])
