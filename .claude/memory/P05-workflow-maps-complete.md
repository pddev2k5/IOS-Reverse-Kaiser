---
name: p05-workflow-maps-complete
description: P05 complete - declarative workflow layer built
metadata:
  type: project
---

# P05 Complete: Workflow Maps

## Summary
P05 (Workflow Maps) is COMPLETE. All quality gates passed.

## P05 Quality Gate Results

| Gate | Status |
|------|--------|
| Workflow Registry | ✓ PASS |
| Workflow Schema | ✓ PASS |
| Intent Mapping | ✓ PASS |
| Depth Profiles | ✓ PASS |
| Workflow DAGs | ✓ PASS |
| Narrow Workflows | ✓ PASS |
| Report Semantics | ✓ PASS |
| Full Composition | ✓ PASS |
| Tool/Agent Policies | ✓ PASS |
| P04 Integration | ✓ PASS |
| Tests | ✓ PASS |

## What Was Built

### 15 Workflows
- ios.unpack (LOW complexity)
- ios.inspect (MEDIUM)
- ios.dump (HIGH)
- ios.macho (MEDIUM)
- ios.objc (MEDIUM)
- ios.swift (MEDIUM)
- ios.network (HIGH)
- ios.login-flow (HIGH)
- ios.crypto (MEDIUM)
- ios.anti-analysis (MEDIUM)
- ios.report (LOW)
- ios.decompile (BLOCKED)
- ios.ida (BLOCKED)
- ios.runtime (BLOCKED)
- ios.full (VERY_HIGH)

### Key Features
- Declarative DAG structure
- Depth-controlled capability selection
- Scope leakage prevention
- Intent normalization
- Coverage policies per workflow
- Agent policies declared
- Resume support

## Test Results
- **50 workflow tests passed**
- **417 total tests passed**

## Why This Matters
- Complete workflow layer ready for P06
- All intents mapped to valid workflows
- Narrow workflows remain narrow
- Full intentionally composes broad domains

## How to Apply
```python
from ios_reverse.workflows import get_workflow, list_workflows
wf = get_workflow("ios.unpack")
```

## Links
- [[p04-capability-layer-complete]] - P04 Complete
- [[p03-engine-workflow-complete]] - P03 Complete
