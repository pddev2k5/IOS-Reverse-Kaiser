# EP-05A: P05 Pre-Flight

**Date**: 2026-09-04
**Phase**: P05 - Workflow Maps
**Subphase**: EP-05A

## Summary

Pre-flight compatibility check between P04 (capabilities) and P05 (workflows).

## Pre-Flight Checklist

### 1. Load Canonical Capability Registry ✓
- 31 capability IDs (CAP-001 to CAP-031)
- 27 implemented, 4 reserved
- All canonical names verified

### 2. Load Intent Registry
- Intents to support:
  - unpack, inspect, dump, decompile
  - macho, objc, swift
  - network, login-flow
  - crypto, anti-analysis
  - ida, runtime
  - report, full

### 3. Load Depth Model
- quick: Minimal scope
- standard: Common scope
- deep: Extended scope
- full: Maximum scope with coverage audit

### 4. Load Complexity Model
- From P03: LOW, MEDIUM, HIGH, VERY_HIGH
- To be integrated with workflow selection

### 5. Load Workflow Schema
- To be defined in P05.2

### 6. Verify P03 Workflow Engine Matches P04 Contracts
- Check P03 engine compatibility
- Document any needed adjustments

## P04 Capability Summary

| Domain | Capabilities | Status |
|--------|-------------|--------|
| foundation | 6 | ✓ IMPLEMENTED |
| macho | 3 | ✓ IMPLEMENTED |
| binary | 4 | ✓ IMPLEMENTED |
| objective_c | 2 | ✓ IMPLEMENTED |
| swift | 2 | ✓ IMPLEMENTED |
| components | 3 | ✓ IMPLEMENTED |
| network | 2 | ✓ IMPLEMENTED |
| architecture | 1 | ✓ IMPLEMENTED |
| callflow | 1 | ✓ IMPLEMENTED |
| crypto | 1 | ✓ IMPLEMENTED |
| anti_analysis | 1 | ✓ IMPLEMENTED |
| coverage | 1 | ✓ IMPLEMENTED |

## Compatibility Analysis

### Workflow-to-Capability Mapping

| Workflow | Primary Capabilities | Dependencies |
|----------|-------------------|--------------|
| unpack | artifact_detect, ipa_validate, ipa_unpack, bundle_inventory | None |
| inspect | All foundation + component inventory | unpack |
| dump | All macho/binary + ObjC/Swift + coverage | unpack, inspect |
| macho | macho.* | unpack |
| objc | objc.* | macho |
| swift | swift.* | macho |
| network | network.*, architecture, callflow | dump |
| login-flow | network, architecture, callflow | network |
| crypto | crypto.* | dump |
| anti-analysis | anti_analysis.* | dump |
| ida | (deferred to P09) | dump |
| runtime | (deferred to P09) | dump |
| decompile | decompiler adapter (deferred) | macho |
| report | coverage, renderers | All applicable |
| full | All capabilities | All dependencies |

### Potential Issues

1. **Login-flow dependencies**: Requires network + architecture + callflow which are all implemented
2. **IDA/Runtime**: These are marked as deferred in P09 - workflows should declare BLOCKED status
3. **Decompile**: Requires decompiler adapter which is deferred to P09

### P03 Engine Compatibility

Need to verify:
- P03 workflow engine inputs/outputs match P04 capability contracts
- State persistence format compatible with new models
- Resume logic works with new coverage model

## Pre-Flight Actions Required

1. Create workflow schema (P05.2)
2. Create workflow registry
3. Define each workflow DAG
4. Integrate with P03 workflow engine or create new engine
5. Implement workflow validator
6. Add integration tests

## Decision Points

### Should workflows use P03 workflow engine or new implementation?

**Decision**: Extend P03 workflow engine to support new workflow schema.

**Rationale**: P03 already provides state persistence, resume, and orchestration primitives. Extending is more efficient than rebuilding.

### How to handle deferred capabilities (IDA, runtime, decompile)?

**Decision**: Define workflows with BLOCKED/DEFERRED status for steps requiring unimplemented adapters.

**Rationale**: Workflow structure should be complete even if execution is blocked.

## Next Steps

1. Create workflow schema (P05.2)
2. Create workflow registry (P05.2)
3. Build each workflow (P05.3 - P05.15)
