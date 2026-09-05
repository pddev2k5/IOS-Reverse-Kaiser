# EP-10A: P10 Test Inventory

**Date**: 2026-09-04
**Phase**: P10 - Testing + Reliability
**Subphase**: EP-10A

## Test Inventory Summary

| Category | Count |
|----------|-------|
| P00-P09 Tests | 543 |
| P10 Reliability Tests | 28 |
| Total | 571 |
| Skipped | 2 |

## Test Categories

### By Phase

| Phase | Tests | File |
|-------|-------|------|
| P04 Capabilities | ~110 | test_capabilities_*.py |
| P05 Workflows | ~90 | test_workflows.py |
| P06 Agents | ~80 | test_agents.py |
| P07 Workspace | ~50 | test_workspace.py |
| P08 Integrity | ~28 | test_integrity.py |
| P09 Adapters | ~33 | test_adapters.py |
| P10 Reliability | ~28 | test_reliability.py |

### By Type

| Type | Status | Count |
|------|--------|-------|
| unit | ✓ COVERED | ~400 |
| contract | ✓ COVERED | ~50 |
| integration | ✓ COVERED | ~100 |
| regression | ✓ COVERED | ~20 |
| determinism | ✓ COVERED | ~10 |
| reliability | ✓ COVERED | ~28 |
| chaos | ✓ COVERED | ~15 |
| live_tool | ⊘ SKIPPED | 2 |

## Subsystem Coverage

### Command/Routing ✓
- Workflow routing tests
- Depth differential tests
- Scope leakage tests

### Capabilities ✓
- Capability contract tests
- Framework inventory tests
- Component graph tests

### Workflows ✓
- Workflow validation tests
- Node dependency tests
- Intent routing tests

### Agents ✓
- Agent selection tests
- Budget enforcement tests
- Task scheduling tests

### Case Workspace ✓
- Case creation/loading tests
- Evidence store tests
- Claims store tests
- Checkpoint tests

### Resume ✓
- Resume plan tests
- Node state tests
- Stale detection tests

### Evidence/Claims ✓
- Evidence lifecycle tests
- Claim transition tests
- Conflict handling tests

### Provenance ✓
- Graph construction tests
- Ancestor/descendant tests
- Serialization tests

### Tool Adapters ✓
- Tool availability tests
- Failure classification tests
- Fallback chain tests
- Selector tests

### Reliability ✓ (P10)
- Workflow routing regression
- Malformed artifact handling
- Claim/evidence chaos
- Provenance graph stress
- Checkpoint corruption
- Repeated resume
- Determinism
- Idempotency

## Risk Assessment

| Subsystem | Risk Level | Gap |
|-----------|-----------|-----|
| Workflow Routing | LOW | Well tested |
| Capability Execution | LOW | Well tested |
| Agent Scheduling | MEDIUM | Budget edge cases |
| Case Persistence | LOW | Checkpoint tests |
| Evidence Integrity | MEDIUM | Complex state |
| Tool Adapters | MEDIUM | Live tool coverage |
| Resume | MEDIUM | Cold resume paths |
| Performance | LOW | Smoke tests only |

## Missing Scenarios (Known)

1. **Live tool integration** - Skipped due to tool availability
2. **Large-scale performance** - Only smoke tests
3. **Cross-platform** - Windows primary focus
4. **Memory profiling** - Not implemented

## P10 Additions

28 new reliability tests covering:
- Workflow routing regression
- Claim/evidence chaos
- Provenance stress
- Checkpoint corruption
- Resume equivalence
- Determinism
- Idempotency
