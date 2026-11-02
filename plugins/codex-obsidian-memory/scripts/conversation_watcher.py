"""No-window, local-only title watcher. No scheduler or transcript access."""
from __future__ import annotations

import argparse
import os
import time
from pathlib import Path


def run(interval: float = 2, cycles: int | None = None) -> int:
    from conversations import load_state, sync_titles
    from memory_core import integration_dir, load_config
    marker = integration_dir() / "conversation-watcher.lock"
    marker.parent.mkdir(parents=True, exist_ok=True)
    # An OS lock is released on crashes; a stale heartbeat never steals a lease.
    handle = marker.open("a+b")
    try:
        if os.name == "nt":
            import msvcrt
            if marker.stat().st_size == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return 0
    try:
        count = 0
        while cycles is None or count < cycles:
            if not Path(__file__).is_file():
                break  # Plugin removal must not leave its worker running.
            config = load_config()
            if not config.get("enabled") or not any(e.get("title_sync", True) for e in load_state()["entries"].values()):
                break
            marker.touch()
            try:
                sync_titles(config)
            except (OSError, ValueError):
                pass  # Metadata may be temporarily busy; notes and originals are retained.
            count += 1
            if cycles is None or count < cycles:
                time.sleep(interval)
    finally:
        handle.close()
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--interval", type=float, default=2)
    parser.add_argument("--cycles", type=int)
    args = parser.parse_args()
    os.environ["CODEX_OBSIDIAN_MEMORY_CONFIG"] = str(args.config.resolve())
    raise SystemExit(run(max(0.1, args.interval), args.cycles))
