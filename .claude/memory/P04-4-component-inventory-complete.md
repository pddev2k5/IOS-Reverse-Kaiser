---
name: p04-4-component-inventory-complete
description: P04.4 Component inventory capabilities completed
metadata:
  type: project
---

# P04.4 Complete: Component Inventory

## Summary
Completed all 3 component inventory capabilities (CAP-018 through CAP-020) with unified component graph and eligible executable set.

## What Was Built

### Model (1)
- `ios_reverse/models/components.py` - Complete component model with ComponentType, Classification, DependencyState, EdgeType

### Adapters (4)
- `ios_reverse/adapters/components/base.py` - ComponentTraversal utilities, safe traversal, system framework detection
- `ios_reverse/adapters/components/framework_adapter.py` - Framework discovery and classification
- `ios_reverse/adapters/components/dylib_adapter.py` - Dylib discovery and parsing
- `ios_reverse/adapters/components/extension_adapter.py` - Extension discovery and point detection

### Capabilities (4)
| ID | Name | Purpose |
|----|------|---------|
| CAP-018 | framework.inventory | Framework discovery and normalization |
| CAP-019 | dylib.inventory | Dylib discovery and normalization |
| CAP-020 | extension.inventory | Extension discovery and classification |
| EP-04.4E | component.graph | Unified graph + eligible_executables |

## Key Design Decisions

### Containment ≠ Linkage
- **CONTAINS**: Bundle structure (PlugIns/, Frameworks/ directories)
- **LOADS**: Mach-O LC_LOAD_DYLIB relationships

### System Dependencies Separate
- System frameworks (UIKit, Foundation) tracked in system_dependencies
- NOT counted in eligible_executables
- Prevents inflation of coverage metrics

### Stable Component IDs
- Based on SHA-256(name:artifact_id:bundle_path)
- Not paths - ensures stability across renames

### Evidence-Driven Resolution
- @rpath/@loader_path resolution is evidence-based
- Unresolved dependencies remain explicit
- No fabricated components

## Test Results
- **192 passed, 2 skipped** - All tests pass
- 47 P04.4-specific tests
- P04.3 (48 tests), P04.2 (29 tests), P04.1 (68 tests) remain green

## Why This Matters
- Answers "what components belong to this app"
- Foundation for dump-full coverage
- Enables per-binary analysis
- Supports dependency graph construction
- IDA/Ghidra target selection

## How to Apply
```python
from ios_reverse.capabilities import ComponentGraphCapability
```

## Links
- [[p04-3-objc-swift-complete]] - Metadata layer that P04.4 builds upon
- [[p04-2-macho-binary-complete]] - Mach-O analysis that P04.4 uses
