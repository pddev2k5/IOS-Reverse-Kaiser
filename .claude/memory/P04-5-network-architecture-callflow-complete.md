---
name: p04-5-network-architecture-callflow-complete
description: P04.5 Network + Architecture + Callflow completed
metadata:
  type: project
---

# P04.5 Complete: Network + Architecture + Callflow

## Summary
Completed P04.5 with 4 capabilities for network framework detection, endpoint discovery, architecture detection, and callflow reconstruction.

## What Was Built

### Models (3)
- `ios_reverse/models/network.py` - Network model with EvidenceStrength, EndpointCandidate, etc.
- `ios_reverse/models/architecture.py` - Architecture model with ArchitectureRole, EvidenceLevel
- `ios_reverse/models/callflow.py` - Callflow model with FlowAnchor, CallEdge, etc.

### Adapters (3)
- `ios_reverse/adapters/analysis/network_adapter.py` - Network analysis
- `ios_reverse/adapters/analysis/architecture_adapter.py` - Architecture analysis
- `ios_reverse/adapters/analysis/callflow_adapter.py` - Callflow analysis

### Capabilities (4)
| CAP ID | Name | Purpose |
|--------|------|---------|
| CAP-021 | network.framework_detection | Framework presence detection |
| CAP-022 | network.endpoint_discovery | Endpoint candidates from evidence |
| CAP-024 | architecture.detection | Architecture component detection |
| CAP-026 | callflow.reconstruct | Callflow reconstruction |

## Key Design Decisions

### Evidence Strength Hierarchy
- STRING_HINT < REFERENCE < STRUCTURAL < CORRELATED < VERIFIED
- URL in strings alone → STRING_HINT, NOT VERIFIED

### Framework Presence ≠ Usage
- Framework binary present ≠ app uses it
- Presence tracked separately from usage

### Physical vs Logical Architecture
- P04.4 ComponentGraph: physical (Frameworks, Dylibs)
- P04.5 ArchitectureModel: logical (Services, ViewControllers)

### Callflow Anchors
- Anchor-driven reconstruction
- Unresolved targets remain explicit
- Selector reference ≠ confirmed call

## Test Results
- **244 passed, 2 skipped** - All tests pass
- P04.5 specific: 52 tests

## Why This Matters
- Network endpoint discovery with evidence tracking
- Architecture role classification
- Callflow reconstruction with unresolved tracking
- Foundation for login-flow analysis

## How to Apply
```python
from ios_reverse.capabilities import NetworkFrameworkDetectionCapability
from ios_reverse.capabilities import NetworkEndpointDiscoveryCapability
from ios_reverse.capabilities import ArchitectureDetectionCapability
from ios_reverse.capabilities import CallflowReconstructCapability
```

## Links
- [[p04-4-component-inventory-complete]] - P04.4 builds physical components
- [[p04-3-objc-swift-complete]] - Metadata layer for P04.5
