# IOS REVERSE KAISER — Capability Registry Schema

## Capability Definition

A capability is an atomic, independently callable operation that:
- Emits structured output
- Records provenance
- Returns explicit success/failure state
- Does not broaden scope

---

## Capability Schema

```json
{
  "id": "string (e.g., 'ipa.unpack')",
  "name": "string (human-readable)",
  "description": "string",
  "domain": "string (e.g., 'foundation', 'macho')",
  "version": "semver",
  
  "inputs": {
    "required": ["array of input names"],
    "optional": ["array of input names"]
  },
  
  "outputs": {
    "structured": ["array of output types"],
    "artifacts": ["array of artifact types"]
  },
  
  "intent_map": ["array of intents this capability serves"],
  
  "depth_map": {
    "quick": { "coverage": "minimal", "tools": ["array"] },
    "standard": { "coverage": "normal", "tools": ["array"] },
    "deep": { "coverage": "extended", "tools": ["array"] },
    "full": { "coverage": "complete", "tools": ["array"] }
  },
  
  "dependencies": ["array of capability IDs"],
  
  "tool_requirements": {
    "required": ["array of tool names"],
    "optional": ["array of tool names"]
  },
  
  "provenance_required": true,
  
  "failure_modes": ["array of possible failure reasons"]
}
```

---

## Capability Registry (31 Planned)

### Domain: Foundation (6)

| ID | Name | Intent Map | Tool Requirements |
|----|------|-----------|-------------------|
| CAP-001 | foundation.artifact_detect | inspect, dump | file, unzip |
| CAP-002 | ipa.validate | unpack, dump | unzip, file |
| CAP-003 | ipa.unpack | unpack, dump | unzip |
| CAP-004 | bundle.inventory | dump | find |
| CAP-005 | plist.extract | dump | plutil |
| CAP-006 | entitlements.extract | dump | codesign, plutil |

### Domain: Mach-O Analysis (3)

| ID | Name | Intent Map | Tool Requirements |
|----|------|-----------|-------------------|
| CAP-010 | macho.basic | macho, dump | file, lipo |
| CAP-011 | macho.slices | macho, dump | lipo, otool |
| CAP-012 | macho.load_commands | macho, dump | otool |

### Domain: Binary Analysis (4)

| ID | Name | Intent Map | Tool Requirements |
|----|------|-----------|-------------------|
| CAP-020 | binary.imports | dump, decompile | nm, otool |
| CAP-021 | binary.exports | dump, decompile | nm |
| CAP-022 | binary.symbols | dump | nm, strings |
| CAP-023 | binary.strings | dump | strings |

### Domain: Metadata ObjC/Swift (5)

| ID | Name | Intent Map | Tool Requirements |
|----|------|-----------|-------------------|
| CAP-030 | objc.metadata | objc, dump | ipsw, nm |
| CAP-031 | objc.deep_metadata | objc, dump-full | ipsw, nm, strings |
| CAP-032 | swift.metadata | swift, dump | ipsw, nm |
| CAP-033 | swift.demangle | swift, dump | swift-demangle |
| CAP-034 | swift.deep_metadata | swift, dump-full | ipsw, nm, strings |

### Domain: Framework/Dylib/Extension (3)

| ID | Name | Intent Map | Tool Requirements |
|----|------|-----------|-------------------|
| CAP-040 | framework.inventory | dump | find |
| CAP-041 | dylib.inventory | dump | find |
| CAP-042 | extension.inventory | dump | find |

### Domain: Architecture (1)

| ID | Name | Intent Map | Tool Requirements |
|----|------|-----------|-------------------|
| CAP-050 | architecture.discovery | macho, dump | lipo, file |

### Domain: Network Analysis (3)

| ID | Name | Intent Map | Tool Requirements |
|----|------|-----------|-------------------|
| CAP-060 | network.discovery | network | strings |
| CAP-061 | network.framework_detect | network | strings, otool |
| CAP-062 | network.endpoint_extract | network, network-full | strings, ipsw |

### Domain: Callflow (1)

| ID | Name | Intent Map | Tool Requirements |
|----|------|-----------|-------------------|
| CAP-070 | callflow.reconstruct | login-flow, runtime | ipsw, Ghidra |

### Domain: Crypto (1)

| ID | Name | Intent Map | Tool Requirements |
|----|------|-----------|-------------------|
| CAP-080 | crypto.identify | crypto | strings, nm |

### Domain: Anti-Analysis (1)

| ID | Name | Intent Map | Tool Requirements |
|----|------|-----------|-------------------|
| CAP-090 | anti_analysis.scan | anti-analysis | strings |

### Domain: Abstraction (1)

| ID | Name | Intent Map | Tool Requirements |
|----|------|-----------|-------------------|
| CAP-100 | runtime.abstract | runtime | Frida |

### Domain: Reporting (2)

| ID | Name | Intent Map | Tool Requirements |
|----|------|-----------|-------------------|
| CAP-110 | report.generate | report | — |
| CAP-111 | coverage.audit | dump-full, full | — |

---

## Capability Output Format

All capabilities MUST emit structured output in this format:

```json
{
  "capability_id": "string",
  "capability_version": "semver",
  "execution_timestamp": "ISO8601",
  
  "status": "success | failure | skipped",
  "error": "string (if failure)",
  
  "provenance": {
    "case_id": "string",
    "workflow_id": "string",
    "node_id": "string",
    "tool": "string",
    "input_artifacts": ["array of paths"],
    "output_artifacts": ["array of paths"],
    "evidence_refs": ["array of evidence IDs"]
  },
  
  "output": {
    "structured": { /* capability-specific data */ },
    "artifacts": ["array of created artifact paths"]
  },
  
  "metadata": {
    "execution_time_ms": "number",
    "depth_used": "string",
    "tools_invoked": ["array"]
  }
}
```

---

## Provenance Requirements

Every capability execution MUST record:

1. **Case ID**: The case this belongs to
2. **Workflow ID**: The workflow that invoked this capability
3. **Node ID**: The specific node in the workflow
4. **Tool**: The tool adapter used
5. **Input Artifacts**: What was consumed
6. **Output Artifacts**: What was produced
7. **Evidence Refs**: Evidence IDs for claims

---

## Tool Requirements

### Required Tools (Core)

| Tool | Purpose | Package |
|------|---------|---------|
| file | Artifact detection | coreutils |
| unzip | IPA extraction | unzip |
| plutil | Plist parsing | Xcode CLI |
| codesign | Entitlements extraction | Xcode CLI |
| strings | String extraction | binutils |
| nm | Symbol extraction | binutils |
| otool | Mach-O analysis | Xcode CLI |
| lipo | Fat binary handling | Xcode CLI |
| find | File enumeration | coreutils |

### Recommended Tools

| Tool | Purpose | Package |
|------|---------|---------|
| ipsw | Class dump, Mach-O analysis | blacktop/tap/ipsw |
| swift-demangle | Swift symbol demangling | swift |
| Ghidra | Decompilation, xref analysis | ghidra |

### Optional Tools

| Tool | Purpose | Package |
|------|---------|---------|
| IDA Pro MCP | Advanced binary analysis | ida-pro-mcp |
| Frida | Runtime instrumentation | frida |

---

## Version

| Field | Value |
|-------|-------|
| Version | 1.0 |
| Phase | P02 |
| Status | LOCKED |

---

*This document defines the capability registry schema.*
