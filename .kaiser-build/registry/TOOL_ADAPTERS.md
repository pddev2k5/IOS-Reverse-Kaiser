# IOS REVERSE KAISER — Tool Adapter Schema

## Tool Adapter Design

Tool adapters abstract external tools behind capability interfaces.

### Design Principles

1. **Abstract interfaces**: Capabilities don't call tools directly
2. **Conditional escalation**: Use lightest sufficient tool
3. **Version checking**: Verify tool availability
4. **Graceful degradation**: Fall back when tools unavailable

---

## Tool Adapter Schema

```json
{
  "id": "string",
  "name": "string",
  "version": "semver",
  
  "tool_command": "string",
  
  "capabilities_provided": ["array of capability IDs"],
  
  "requirements": {
    "os": ["macos | linux | windows"],
    "tools": ["array of required system tools"],
    "environment": ["array of required environment variables"]
  },
  
  "capabilities": {
    "capability_id": {
      "commands": {
        "default": ["array of command parts"],
        "quick": ["array (optional)"],
        "standard": ["array (optional)"],
        "deep": ["array (optional)"],
        "full": ["array (optional)"]
      },
      "output_format": "json | text | yaml | structured",
      "timeout_ms": "number"
    }
  },
  
  "fallback": {
    "tool": "string (alternative tool ID)",
    "capabilities": ["array of capability IDs that can fallback"]
  },
  
  "version_check": {
    "command": ["array of command parts"],
    "min_version": "string",
    "pattern": "string (regex to extract version)"
  }
}
```

---

## Tool Adapter Registry

### Core Tools

| ID | Name | Capabilities | Platform | Priority |
|----|------|-------------|----------|----------|
| T001 | file | artifact detection | macos,linux | 1 |
| T002 | unzip | IPA extraction | macos,linux | 1 |
| T003 | plutil | Plist parsing | macos | 1 |
| T004 | codesign | Entitlements | macos | 1 |
| T005 | strings | String extraction | macos,linux | 1 |
| T006 | nm | Symbol extraction | macos,linux | 1 |
| T007 | otool | Mach-O analysis | macos | 1 |
| T008 | lipo | Fat binary | macos | 1 |
| T009 | find | File enumeration | macos,linux | 1 |

### Recommended Tools

| ID | Name | Capabilities | Platform | Priority |
|----|------|-------------|----------|----------|
| T010 | ipsw | class-dump, Mach-O | macos | 2 |
| T011 | swift-demangle | Swift demangling | macos | 2 |
| T012 | ghidra | Decompilation | macos,linux | 2 |
| T013 | radare2 | Binary analysis | macos,linux | 2 |

### Optional Tools

| ID | Name | Capabilities | Platform | Priority |
|----|------|-------------|----------|----------|
| T014 | ida-pro-mcp | IDA analysis | macos,linux | 3 |
| T015 | frida | Runtime | macos,linux | 3 |

---

## Adapter Definitions

### T002: unzip

```json
{
  "id": "T002",
  "name": "unzip",
  "version": "1.0.0",
  
  "tool_command": "unzip",
  
  "capabilities_provided": ["ipa.unpack", "ipa.validate"],
  
  "requirements": {
    "os": ["macos", "linux"],
    "tools": [],
    "environment": []
  },
  
  "capabilities": {
    "ipa.validate": {
      "commands": {
        "default": ["unzip", "-t", "{artifact}"]
      },
      "output_format": "text",
      "timeout_ms": 30000
    },
    "ipa.unpack": {
      "commands": {
        "default": ["unzip", "-q", "-o", "{artifact}", "-d", "{output_dir}"]
      },
      "output_format": "text",
      "timeout_ms": 120000
    }
  },
  
  "fallback": null,
  
  "version_check": {
    "command": ["unzip", "-v"],
    "min_version": "6.0",
    "pattern": "UnZip [0-9]+\\.[0-9]+"
  }
}
```

### T003: plutil

```json
{
  "id": "T003",
  "name": "plutil",
  "version": "1.0.0",
  
  "tool_command": "plutil",
  
  "capabilities_provided": ["plist.extract", "entitlements.extract"],
  
  "requirements": {
    "os": ["macos"],
    "tools": [],
    "environment": []
  },
  
  "capabilities": {
    "plist.extract": {
      "commands": {
        "default": ["plutil", "-convert", "json", "-o", "{output_json}", "{input_plist}"],
        "pretty": ["plutil", "-p", "{input_plist}"]
      },
      "output_format": "json",
      "timeout_ms": 10000
    },
    "entitlements.extract": {
      "commands": {
        "default": ["plutil", "-convert", "json", "-o", "{output_json}", "{input_entitlements}"]
      },
      "output_format": "json",
      "timeout_ms": 10000
    }
  },
  
  "fallback": null,
  
  "version_check": {
    "command": ["plutil"],
    "min_version": "1.0",
    "pattern": null
  }
}
```

### T006: nm

```json
{
  "id": "T006",
  "name": "nm",
  "version": "1.0.0",
  
  "tool_command": "nm",
  
  "capabilities_provided": ["binary.symbols", "objc.metadata", "swift.metadata", "binary.imports", "binary.exports"],
  
  "requirements": {
    "os": ["macos", "linux"],
    "tools": [],
    "environment": []
  },
  
  "capabilities": {
    "binary.symbols": {
      "commands": {
        "default": ["nm", "-g", "{binary}"],
        "defined": ["nm", "-gU", "{binary}"],
        "undefined": ["nm", "-gu", "{binary}"]
      },
      "output_format": "text",
      "timeout_ms": 60000
    },
    "objc.metadata": {
      "commands": {
        "default": ["nm", "-g", "{binary}", "|", "grep", "-E", "OBJC_CLASS|OBJC_METACLASS"]
      },
      "output_format": "text",
      "timeout_ms": 60000
    },
    "swift.metadata": {
      "commands": {
        "default": ["nm", "-g", "{binary}", "|", "grep", "-E", "$s|_TtC|__T"]
      },
      "output_format": "text",
      "timeout_ms": 60000
    }
  },
  
  "fallback": {
    "tool": "T010",
    "capabilities": ["objc.metadata", "swift.metadata"]
  },
  
  "version_check": {
    "command": ["nm", "--version"],
    "min_version": "2.0",
    "pattern": "GNU nm"
  }
}
```

### T010: ipsw

```json
{
  "id": "T010",
  "name": "ipsw",
  "version": "1.0.0",
  
  "tool_command": "ipsw",
  
  "capabilities_provided": ["objc.metadata", "objc.deep_metadata", "swift.metadata", "swift.demangle", "macho.basic", "macho.slices"],
  
  "requirements": {
    "os": ["macos"],
    "tools": ["go"],
    "environment": []
  },
  
  "capabilities": {
    "objc.metadata": {
      "commands": {
        "default": ["ipsw", "class-dump", "{binary}"]
      },
      "output_format": "text",
      "timeout_ms": 120000
    },
    "swift.metadata": {
      "commands": {
        "default": ["ipsw", "class-dump", "{binary}", "--swift"]
      },
      "output_format": "text",
      "timeout_ms": 120000
    },
    "macho.basic": {
      "commands": {
        "default": ["ipsw", " macho", "info", "{binary}"]
      },
      "output_format": "json",
      "timeout_ms": 30000
    }
  },
  
  "fallback": null,
  
  "version_check": {
    "command": ["ipsw", "version"],
    "min_version": "3.0",
    "pattern": "[0-9]+\\.[0-9]+\\.[0-9]+"
  }
}
```

---

## Tool Selection Logic

### Capability → Tool Resolution

```python
def resolve_tool(capability_id, depth, available_tools):
    # 1. Find adapters that provide this capability
    candidates = [a for a in adapters 
                 if capability_id in a.capabilities_provided]
    
    # 2. Filter by availability
    candidates = [a for a in candidates 
                 if is_tool_available(a.tool_command)]
    
    # 3. Sort by priority (lower = preferred)
    candidates.sort(key=lambda a: a.priority)
    
    # 4. Return highest priority available
    return candidates[0] if candidates else None
```

### Escalation Logic

```python
def escalate_tool(capability_id, depth, available_tools):
    # 1. Try default tool
    tool = resolve_tool(capability_id, depth, available_tools)
    if tool:
        return tool
    
    # 2. Try fallback tool
    for adapter in adapters:
        if capability_id in adapter.fallback.capabilities:
            fallback_tool = adapter.fallback.tool
            if is_tool_available(fallback_tool):
                return get_adapter(fallback_tool)
    
    # 3. Return None (tool unavailable)
    return None
```

---

## Version

| Field | Value |
|-------|-------|
| Version | 1.0 |
| Phase | P02 |
| Status | LOCKED |

---

*This document defines the tool adapter schema.*
