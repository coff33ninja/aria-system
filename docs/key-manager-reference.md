# Key Manager Reference

This document covers the API key rotation system in `key_manager.py`.

## Overview

A file-backed round-robin key manager for rotating through multiple Gemini API keys. Safe for single-host use with file locking to prevent concurrent access issues.

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEYS` | Comma-separated list of Gemini API keys |

### Constants

```python
STATE_FILE = ".gemini_key_idx"    # Stores last-used key index
LOCK_FILE = ".gemini_key_lock"    # Lock file for concurrent access
STALE_SECONDS = 60                # Lock considered stale after 60s
```

## Functions

### _read_keys()

Read API keys from environment variable.

```python
def _read_keys(env_name: str = "GEMINI_API_KEYS") -> List[str]:
    """Parse comma-separated keys from environment variable."""
```

**Returns:** List of trimmed, non-empty key strings

### _acquire_lock()

Acquire file lock for safe concurrent access.

```python
def _acquire_lock(lock_path: str, timeout: int = 5) -> bool:
    """
    Try to acquire lock file atomically.
    Removes stale locks older than STALE_SECONDS.
    """
```

**Parameters:**
- `lock_path`: Path to lock file
- `timeout`: Max seconds to wait for lock

**Returns:** True if lock acquired, False if timeout

### _release_lock()

Release the file lock.

```python
def _release_lock(lock_path: str) -> None:
    """Remove lock file if it exists."""
```

### pick_next_key()

Select the next API key in round-robin fashion.

```python
def pick_next_key(
    env_name: str = "GEMINI_API_KEYS",
    state_file: str = STATE_FILE,
    lock_file: str = LOCK_FILE
) -> Optional[str]:
    """
    Pick next key using round-robin rotation.
    Falls back to random selection if lock cannot be acquired.
    """
```

**Returns:** Next API key or None if no keys configured

**Algorithm:**
1. Read keys from environment
2. Acquire file lock
3. Read last-used index from state file
4. Calculate next index: `(last + 1) % len(keys)`
5. Write new index to state file
6. Release lock
7. Return selected key

### pick_and_set_key()

Pick next key and set it as `OPENAI_API_KEY`.

```python
def pick_and_set_key(env_name: str = "GEMINI_API_KEYS") -> Optional[str]:
    """
    Pick next key and export it as OPENAI_API_KEY.
    Used for Gemini API compatibility with OpenAI-style clients.
    """
```

**Returns:** Selected key or None

## Usage

### In agent.py

```python
from key_manager import pick_and_set_key

# At startup
try:
    chosen = pick_and_set_key()
    if chosen:
        logging.info("Selected Gemini API key")
except Exception:
    logging.debug("Key manager failed; continuing without setting key")
```

### Manual Key Selection

```python
from key_manager import pick_next_key

key = pick_next_key()
if key:
    # Use key directly
    client = SomeAPIClient(api_key=key)
```

## File Structure

After running, creates:

```
.gemini_key_idx    # Contains integer index (e.g., "2")
.gemini_key_lock   # Temporary lock file (removed after use)
```

## Concurrency Safety

- Uses atomic file creation (`O_CREAT | O_EXCL`) for locking
- Stale locks (>60s) are automatically removed
- Falls back to random selection if lock times out
- Safe for single-host, multi-process scenarios

## Example Setup

```bash
# .env file
GEMINI_API_KEYS=key1_abc123,key2_def456,key3_ghi789
```

Keys will rotate: key1 → key2 → key3 → key1 → ...
