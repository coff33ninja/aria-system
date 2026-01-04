import os
import time
from typing import List, Optional

# Simple file-backed round-robin key manager. Safe for single-host use.
# State file stores the last-used index as an integer. A lock file is used
# to avoid concurrent writers. If the lock is stale (older than STALE_SECONDS)
# it will be removed.

STATE_FILE = ".gemini_key_idx"
LOCK_FILE = ".gemini_key_lock"
STALE_SECONDS = 60


def _read_keys(env_name: str = "GEMINI_API_KEYS") -> List[str]:
    raw = os.getenv(env_name, "") or ""
    return [k.strip() for k in raw.split(",") if k.strip()]


def _acquire_lock(lock_path: str, timeout: int = 5) -> bool:
    start = time.time()
    while True:
        try:
            # Try to create the lock file atomically
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w") as fh:
                fh.write(f"pid:{os.getpid()}\n{time.time()}\n")
            return True
        except FileExistsError:
            # check if lock is stale
            try:
                mtime = os.path.getmtime(lock_path)
                if time.time() - mtime > STALE_SECONDS:
                    try:
                        os.remove(lock_path)
                    except Exception:
                        pass
            except Exception:
                pass
            if time.time() - start > timeout:
                return False
            time.sleep(0.1)


def _release_lock(lock_path: str) -> None:
    try:
        if os.path.exists(lock_path):
            os.remove(lock_path)
    except Exception:
        pass


def pick_next_key(env_name: str = "GEMINI_API_KEYS", state_file: str = STATE_FILE, lock_file: str = LOCK_FILE) -> Optional[str]:
    keys = _read_keys(env_name)
    if not keys:
        return None

    # Acquire lock
    locked = _acquire_lock(lock_file, timeout=5)
    if not locked:
        # fallback: pick a random key to avoid blocking
        import random

        return random.choice(keys)

    try:
        # read last index
        last = -1
        if os.path.exists(state_file):
            try:
                with open(state_file, "r") as fh:
                    content = fh.read().strip()
                    last = int(content)
            except Exception:
                last = -1

        next_index = (last + 1) % len(keys)

        # write next_index back to state file
        try:
            with open(state_file, "w") as fh:
                fh.write(str(next_index))
        except Exception:
            # ignore write errors; selection can continue
            pass

        return keys[next_index]
    finally:
        _release_lock(lock_file)


def pick_and_set_key(env_name: str = "GEMINI_API_KEYS") -> Optional[str]:
    """Pick the next API key and set it for both OpenAI and Google plugins."""
    key = pick_next_key(env_name=env_name)
    if key:
        # Set for both plugins — Google plugin uses GOOGLE_API_KEY
        os.environ["GOOGLE_API_KEY"] = key
        os.environ["OPENAI_API_KEY"] = key  # Keep for compatibility
    return key
