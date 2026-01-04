# Test Mem0 Reference

This document covers the Mem0 testing script in `test_mem0.py`.

## Overview

A utility script for testing Mem0 memory operations. Used for development and debugging of the memory system.

## Package Dependencies

```
mem0ai
python-dotenv
```

## Key Imports

```python
from dotenv import load_dotenv
from mem0 import MemoryClient
import json
```

| Import | Type | Purpose |
|--------|------|---------|
| `load_dotenv` | Function | Load environment variables from .env |
| `MemoryClient` | Class | Synchronous Mem0 client (vs AsyncMemoryClient in agent.py) |

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `MEM0_API_KEY` | Mem0 API key (loaded via dotenv) |

### Constants

```python
user_name = 'David'  # Test user ID
```

## Functions

### add_memory()

Add test conversation to memory.

```python
def add_memory():
    """Add sample conversation messages to Mem0."""
```

**Sample Data:**
```python
messages_formatted = [
    {"role": "user", "content": "I really like Linkin Park."},
    {"role": "assistant", "content": "That is a good choice."},
    {"role": "user", "content": "I think so too."},
    {"role": "assistant", "content": "What is your favorite song by them?"},
]
mem0.add(messages_formatted, user_id="David")
```

### get_memory_by_query()

Search memories by query.

```python
def get_memory_by_query() -> str:
    """Search Mem0 for user preferences and return formatted JSON."""
```

**Query:** `"What are {user_name}'s preferences?"`

**Returns:** JSON string of memories:
```json
[
  {
    "memory": "David likes Linkin Park",
    "updated_at": "2025-01-04T10:30:00.000000-07:00"
  }
]
```

## Usage

### Run from Command Line

```bash
python test_mem0.py
```

Executes `get_memory_by_query()` and prints results.

### Import and Use

```python
from test_mem0 import add_memory, get_memory_by_query

# Add test data
add_memory()

# Query memories
memories = get_memory_by_query()
print(memories)
```

## Mem0 Client Comparison

| Feature | MemoryClient | AsyncMemoryClient |
|---------|--------------|-------------------|
| Used in | test_mem0.py | agent.py |
| Async | No | Yes |
| Methods | `.add()`, `.search()`, `.get_all()` | `await .add()`, `await .search()`, `await .get_all()` |

## Memory Structure

Mem0 returns memories with:

```python
{
    "id": "unique-id",
    "memory": "Extracted fact or preference",
    "user_id": "David",
    "updated_at": "2025-01-04T10:30:00.000000-07:00",
    # ... other metadata
}
```

The script extracts only `memory` and `updated_at` for display.
