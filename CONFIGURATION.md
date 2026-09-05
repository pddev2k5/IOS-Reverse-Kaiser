# Configuration

## Overview

IOS REVERSE KAISER uses Python configuration files for customization.

## Configuration File

Create `config.py` in the project root:

```python
from ios_reverse.config import Config

# Override defaults
config = Config()
config.WORKSPACE_ROOT = "workspace"
config.TOOL_TIMEOUTS["default"] = 120000
config.ENABLE_DEBUG = False
```

## Configuration Options

### Case Workspace

| Option | Default | Description |
|--------|---------|-------------|
| `WORKSPACE_ROOT` | `"workspace"` | Root directory for case workspaces |
| `CASES_DIR` | `"workspace/cases"` | Directory for case data |
| `MAX_CONTEXT_SIZE` | `512 * 1024` | Max context pack size (512KB) |

### Tool Paths

| Option | Default | Description |
|--------|---------|-------------|
| `TOOL_PATHS` | `{}` | Custom tool executable paths |
| `IPSW_PATH` | `None` | Path to ipsw executable |
| `OTOOL_PATH` | `None` | Path to otool (macOS) |
| `PLUTIL_PATH` | `None` | Path to plutil (macOS) |

### Timeouts (milliseconds)

| Option | Default | Description |
|--------|---------|-------------|
| `TOOL_TIMEOUTS["default"]` | `60000` | Default tool timeout |
| `TOOL_TIMEOUTS["macho"]` | `120000` | Mach-O analysis timeout |
| `TOOL_TIMEOUTS["network"]` | `180000` | Network analysis timeout |

### Evidence

| Option | Default | Description |
|--------|---------|-------------|
| `MAX_EVIDENCE_SIZE` | `10 * 1024 * 1024` | Max evidence file size (10MB) |
| `EVIDENCE_COMPRESSION` | `True` | Compress large evidence |

### Provenance

| Option | Default | Description |
|--------|---------|-------------|
| `MAX_GRAPH_NODES` | `10000` | Max provenance graph nodes |
| `MAX_GRAPH_DEPTH` | `100` | Max ancestor/descendant depth |

### Agent Budget

| Option | Default | Description |
|--------|---------|-------------|
| `BUDGET_QUICK` | `1` | Max agents for quick depth |
| `BUDGET_STANDARD` | `2` | Max agents for standard depth |
| `BUDGET_DEEP` | `4` | Max agents for deep depth |
| `BUDGET_FULL` | `6` | Max agents for full depth |

### Checkpoint

| Option | Default | Description |
|--------|---------|-------------|
| `CHECKPOINT_INTERVAL` | `60` | Seconds between checkpoints |
| `MAX_CHECKPOINTS` | `10` | Max checkpoints to retain |
| `LOCK_TIMEOUT` | `3600` | Lock stale timeout (1 hour) |

### Reporting

| Option | Default | Description |
|--------|---------|-------------|
| `REPORT_FORMATS` | `["json", "markdown"]` | Output formats |
| `REPORT_INCLUDE_PROVENANCE` | `True` | Include provenance in reports |
| `REPORT_INCLUDE_RAW` | `False` | Include raw evidence |

### Debug

| Option | Default | Description |
|--------|---------|-------------|
| `ENABLE_DEBUG` | `False` | Enable debug logging |
| `DEBUG_AGENTS` | `False` | Log agent actions |
| `DEBUG_TOOLS` | `False` | Log tool executions |

## Environment Variables

| Variable | Description |
|---------|-------------|
| `IOS_REVERSE_WORKSPACE` | Override workspace root |
| `IOS_REVERSE_TOOL_PATH` | Tool search path |
| `IOS_REVERSE_DEBUG` | Enable debug mode |

## Platform-Specific Configuration

### Windows

```python
# Windows-specific paths
config.TOOL_PATHS = {
    "strings": "C:\\Tools\\strings.exe",
    "ipsw": "C:\\Tools\\ipsw.exe",
}
```

### macOS

```python
# macOS can use system tools
config.TOOL_PATHS = {
    "otool": "/usr/bin/otool",
    "plutil": "/usr/bin/plutil",
    "codesign": "/usr/bin/codesign",
    "nm": "/usr/bin/nm",
}
```

## Configuration Precedence

1. Environment variables (highest)
2. `config.py` in project root
3. Default values (lowest)

## Verifying Configuration

```bash
python -c "from ios_reverse.config import Config; c = Config(); print(c.as_dict())"
```
