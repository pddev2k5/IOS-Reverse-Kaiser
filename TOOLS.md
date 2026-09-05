# Tools

## Overview

IOS REVERSE KAISER uses a tool adapter system that provides graceful fallback when tools are unavailable.

## Tool Adapter Architecture

```
Capability
    ↓
Tool Selector
    ↓
Fallback Chain: [IDA] → [Ghidra] → [Python Parser]
    ↓
Tool Adapter
    ↓
Safe Subprocess Execution
```

## Available Adapters

### Core Tools (Always Available)

| Tool | Purpose | Status |
|------|---------|--------|
| Python Parser | Pure Python Mach-O parsing | ✓ IMPLEMENTED |

### Optional Tools

| Tool | Purpose | Platform | Required? |
|------|---------|----------|-----------|
| ipsw | Mach-O inspection | All | No |
| otool | Mach-O commands | macOS | No |
| plutil | plist parsing | macOS | No |
| codesign | Code signing verification | macOS | No |
| nm | Symbol listing | macOS | No |
| strings | String extraction | All | No |
| swift-demangle | Swift symbol demangling | All | No |

### Commercial Tools

| Tool | Purpose | Status | Required? |
|------|---------|--------|-----------|
| IDA Pro | Deep disassembly | Contract defined | No |
| Ghidra | Alternative disassembly | Contract defined | No |
| radare2/rizin | CLI reversing | Contract defined | No |

## Tool Adapter Contract

All adapters implement `ToolAdapterContract`:

```python
class ToolAdapterContract(ABC):
    @property
    def adapter_id(self) -> str: ...
    @property
    def version(self) -> str: ...
    @property
    def tool_name(self) -> str: ...

    def availability() -> ToolAvailability: ...
    def health_check() -> AdapterHealth: ...
    def tool_version() -> Optional[str]: ...

    def execute(
        capability_id: str,
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterExecutionResult: ...

    def execute_raw(...) -> AdapterExecutionResult: ...
    def normalize_output(...) -> Any: ...
```

## Tool Availability States

| State | Meaning |
|-------|---------|
| `available` | Tool is working |
| `unavailable` | Tool not installed |
| `misconfigured` | Tool installed but not configured |
| `degraded` | Tool works but with limitations |
| `unsupported_platform` | Tool not available on this platform |
| `session_required` | Tool requires interactive session |
| `auth_required` | Tool requires authentication |
| `unknown` | Cannot determine status |

## Failure Classification

| Classification | Meaning | Retryable? |
|---------------|---------|------------|
| `tool_not_found` | Tool not installed | No |
| `timeout` | Operation timed out | Yes |
| `process_error` | Tool crashed | Yes |
| `parse_error` | Output parsing failed | No |
| `permission_error` | Access denied | No |
| `resource_limit` | Out of memory/time | Yes |
| `partial_output` | Output truncated | Yes |
| `session_lost` | Interactive session lost | Yes |

## Adapter Categories

### Core Adapters (`ios_reverse/adapters/core/`)

| Adapter | Tool | Purpose |
|---------|------|---------|
| `file_adapter.py` | Python | File operations |
| `unzip_adapter.py` | Python | IPA extraction |
| `plutil_adapter.py` | plutil | plist parsing |
| `codesign_adapter.py` | codesign | Code signing |
| `find_adapter.py` | Python | File finding |

### Mach-O Adapters (`ios_reverse/adapters/macho/`)

| Adapter | Tool | Purpose | Platform |
|---------|------|---------|----------|
| `parser_adapter.py` | Python | Mach-O parsing | All |
| `otool_adapter.py` | otool | Mach-O commands | macOS |
| `nm_adapter.py` | nm | Symbol listing | macOS |
| `strings_adapter.py` | strings | String extraction | All |

### Language Adapters (`ios_reverse/adapters/objc/`, `swift/`)

| Adapter | Tool | Purpose |
|---------|------|---------|
| `objc_adapter.py` | Python | ObjC metadata |
| `swift_adapter.py` | Python | Swift metadata |
| `swift_demangler.py` | swift-demangle | Swift demangling |

### Analysis Adapters (`ios_reverse/adapters/analysis/`)

| Adapter | Tool | Purpose |
|---------|------|---------|
| `network_adapter.py` | Python | Network analysis |
| `architecture_adapter.py` | Python | Architecture analysis |
| `callflow_adapter.py` | Python | Call flow analysis |
| `crypto_adapter.py` | Python | Crypto detection |
| `anti_analysis_adapter.py` | Python | Anti-analysis detection |

## Tool Role Classification

| Role | Meaning | Usage |
|------|---------|-------|
| `REQUIRED` | Must have for this capability | Tool absence = fail |
| `OPTIONAL` | Enhancement if available | Fallback if absent |
| `FALLBACK` | Alternative tool | Used when primary unavailable |

## Platform Matrix

| Feature | Windows | Linux | macOS |
|---------|---------|--------|--------|
| IPA unzip | ✓ | ✓ | ✓ |
| Mach-O Python parsing | ✓ | ✓ | ✓ |
| ObjC/Swift static metadata | ✓ | ✓ | ✓ |
| Component graph | ✓ | ✓ | ✓ |
| Network static analysis | ✓ | ✓ | ✓ |
| otool | ✗ | ✗ | ✓ |
| plutil | ✗ | ✗ | ✓ |
| codesign | ✗ | ✗ | ✓ |
| nm | ✗ | ✗ | ✓ |
| strings | ✓ | ✓ | ✓ |
| ipsw | ✓ | ✓ | ✓ |
| IDA Pro | ✓ | ✓ | ✓ |
| Ghidra | ✓ | ✓ | ✓ |
| radare2 | ✓ | ✓ | ✓ |

## Tool Health Service

The tool health service monitors adapter status:

```python
from ios_reverse.adapters import get_health_service

health = get_health_service()
report = health.generate_report()

# Example output:
{
  "platform": "windows",
  "total_adapters": 15,
  "summary": {
    "available_count": 10,
    "unavailable_count": 3,
    "degraded_count": 2
  }
}
```

## Configuration

### Tool Path Configuration

```python
# config.py
TOOL_PATHS = {
    "ipsw": "/path/to/ipsw",
    "otool": "/usr/bin/otool",
    "strings": "/usr/bin/strings",
}
```

### Timeout Configuration

```python
TOOL_TIMEOUTS = {
    "default": 60000,  # 60 seconds
    "macho.analysis": 120000,  # 2 minutes
    "network.endpoints": 180000,  # 3 minutes
}
```

### Fallback Configuration

```python
FALLBACK_CHAINS = {
    "macho.symbols": ["nm", "python_parser"],
    "macho.disassemble": ["ida", "ghidra", "rizin"],
}
```

## Safety Features

### Subprocess Security

- No `shell=True` usage
- Path injection detection
- Command validation
- Timeout enforcement
- Output size limits (50MB stdout, 10MB stderr)

### Error Handling

- All failures classified
- Retryable failures identified
- Graceful degradation
- Detailed error reporting

## Adding a New Adapter

1. Create adapter class implementing `ToolAdapterContract`
2. Register in tool selector with fallback chain
3. Add to health service
4. Write tests for availability and fallback
5. Document in this file

## Known Limitations

| Tool | Limitation |
|------|------------|
| IDA Pro | Requires separate license |
| Ghidra | Headless mode only |
| Runtime provider | Requires jailbreak/Frida |
