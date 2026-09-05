# IOS REVERSE KAISER — Workflow Schema

## Workflow Definition

A workflow is a declarative DAG (Directed Acyclic Graph) that defines the execution plan for an intent.

---

## Workflow Schema

```json
{
  "id": "string (e.g., 'workflow-dump')",
  "version": "semver",
  "name": "string",
  "description": "string",
  
  "intent": "string",
  "accepted_artifacts": ["array of artifact types"],
  
  "depth_profiles": {
    "quick": { "extends": null },
    "standard": { "extends": "quick" },
    "deep": { "extends": "standard" },
    "full": { "extends": "deep" }
  },
  
  "nodes": [
    {
      "id": "string",
      "name": "string",
      "capability": "string (capability ID)",
      "depends_on": ["array of node IDs"],
      "conditions": {
        "artifact_required": "string (optional)",
        "depth_minimum": "string (optional)"
      },
      "allowed_agents": ["array of agent roles"],
      "tool_override": "string (optional)",
      "timeout_ms": "number",
      "retry_policy": {
        "max_retries": "number",
        "backoff_ms": "number"
      },
      "stop_conditions": {
        "on_failure": "continue | abort | skip_dependents",
        "time_limit_ms": "number (optional)"
      }
    }
  ],
  
  "edges": [
    {
      "from": "string (node ID)",
      "to": "string (node ID)",
      "type": "success | always"
    }
  ],
  
  "capabilities_used": ["array of capability IDs"],
  
  "allowed_agents": ["array of agent roles"],
  
  "conditions": {
    "required_artifacts": ["array"],
    "excluded_artifacts": ["array"]
  },
  
  "fallbacks": {
    "on_skipped_node": "string (alternative node ID)",
    "on_failed_tool": "string (alternative tool)"
  },
  
  "success_conditions": {
    "required_nodes": ["array of node IDs"],
    "minimum_coverage": "number (0-100)"
  },
  
  "stop_conditions": {
    "max_time_ms": "number",
    "max_cost_units": "number"
  },
  
  "outputs": {
    "primary": "string (artifact type)",
    "secondary": ["array of artifact types"]
  },
  
  "coverage_requirements": {
    "dimensions": ["array of coverage dimensions"],
    "thresholds": {
      "dimension_name": "number (0-100)"
    }
  }
}
```

---

## Workflow Definitions

### workflow-unpack

```yaml
id: workflow-unpack
version: 1.0.0
intent: unpack
depth_profiles:
  quick:
    nodes:
      - id: validate
        capability: ipa.validate
        conditions:
          artifact_required: ipa
      - id: extract
        capability: ipa.unpack
        depends_on: [validate]
  standard:
    extends: quick
    nodes:
      - id: inventory
        capability: bundle.inventory
        depends_on: [extract]
      - id: plist
        capability: plist.extract
        depends_on: [extract]
```

### workflow-dump

```yaml
id: workflow-dump
version: 1.0.0
intent: dump
depth_profiles:
  standard:
    nodes:
      - id: validate
        capability: ipa.validate
      - id: unpack
        capability: ipa.unpack
        depends_on: [validate]
      - id: plist
        capability: plist.extract
        depends_on: [unpack]
      - id: entitlements
        capability: entitlements.extract
        depends_on: [unpack]
      - id: frameworks
        capability: framework.inventory
        depends_on: [unpack]
      - id: dylibs
        capability: dylib.inventory
        depends_on: [unpack]
      - id: extensions
        capability: extension.inventory
        depends_on: [unpack]
      - id: symbols
        capability: binary.symbols
        depends_on: [unpack]
      - id: strings
        capability: binary.strings
        depends_on: [unpack]
      - id: objc
        capability: objc.metadata
        depends_on: [unpack]
      - id: swift
        capability: swift.metadata
        depends_on: [unpack]
  full:
    extends: standard
    additional_nodes:
      - id: all_macho
        capability: macho.slices
        depends_on: [unpack]
      - id: all_load_commands
        capability: macho.load_commands
        depends_on: [all_macho]
      - id: deep_objc
        capability: objc.deep_metadata
        depends_on: [objc]
      - id: deep_swift
        capability: swift.deep_metadata
        depends_on: [swift]
      - id: all_imports
        capability: binary.imports
        depends_on: [all_macho]
      - id: all_exports
        capability: binary.exports
        depends_on: [all_macho]
      - id: coverage_audit
        capability: coverage.audit
        depends_on: [all_macho, deep_objc, deep_swift]
```

### workflow-network

```yaml
id: workflow-network
version: 1.0.0
intent: network
depth_profiles:
  quick:
    nodes:
      - id: discovery
        capability: network.discovery
  standard:
    extends: quick
    nodes:
      - id: frameworks
        capability: network.framework_detect
      - id: endpoints
        capability: network.endpoint_extract
  full:
    extends: standard
    nodes:
      - id: full_endpoints
        capability: network.endpoint_extract
        tool_override: ipsw
      - id: correlate
        capability: callflow.reconstruct
```

### workflow-crypto

```yaml
id: workflow-crypto
version: 1.0.0
intent: crypto
depth_profiles:
  quick:
    nodes:
      - id: identify
        capability: crypto.identify
  standard:
    extends: quick
    nodes:
      - id: analyze
        capability: crypto.identify
        tool_override: strings
  deep:
    extends: standard
    nodes:
      - id: decompile
        capability: binary.abstract
        tool_override: Ghidra
```

---

## Coverage Dimensions

For full/deep workflows, coverage is measured across these dimensions:

| Dimension | Description | Threshold (full) |
|----------|-------------|-----------------|
| main_binary | Main executable analyzed | 100% |
| embedded_binaries | All embedded binaries | 100% |
| frameworks | All frameworks | 100% |
| dylibs | All dylibs | 100% |
| extensions | All extensions | 100% |
| macho_slices | All architecture slices | 100% |
| objc_metadata | ObjC metadata extracted | 100% |
| swift_metadata | Swift metadata extracted | 100% |
| imports | All imports captured | 90% |
| exports | All exports captured | 90% |
| symbols | All symbols captured | 90% |
| strings | Strings extracted | 95% |
| network_endpoints | All endpoints documented | 80% |

---

## Workflow Registry

The workflow registry is the source of truth for all workflow definitions:

```json
{
  "registry_version": "1.0.0",
  "workflows": [
    {
      "id": "workflow-unpack",
      "version": "1.0.0",
      "file": "workflows/workflow-unpack.yaml"
    },
    {
      "id": "workflow-dump",
      "version": "1.0.0",
      "file": "workflows/workflow-dump.yaml"
    },
    // ... other workflows
  ]
}
```

---

## Version

| Field | Value |
|-------|-------|
| Version | 1.0 |
| Phase | P02 |
| Status | LOCKED |

---

*This document defines the workflow schema.*
