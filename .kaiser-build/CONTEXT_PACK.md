# Context Pack

## Active Files

### Core Framework
- `ios_reverse/core/__init__.py` - Main framework exports
- `ios_reverse/core/artifact.py` - Artifact model
- `ios_reverse/core/evidence.py` - Evidence system

### Models
- `ios_reverse/models/__init__.py` - All models
- `ios_reverse/models/macho.py` - Mach-O model (P04.2)
- `ios_reverse/models/foundation.py` - Foundation models (P04.1)
- `ios_reverse/models/objc.py` - Objective-C model (P04.3)
- `ios_reverse/models/swift.py` - Swift model (P04.3)
- `ios_reverse/models/components.py` - Component model (P04.4)
- `ios_reverse/models/network.py` - Network model (P04.5)
- `ios_reverse/models/architecture.py` - Architecture model (P04.5)
- `ios_reverse/models/callflow.py` - Callflow model (P04.5)
- `ios_reverse/models/crypto.py` - Crypto model (P04.6)
- `ios_reverse/models/anti_analysis.py` - Anti-analysis model (P04.6)
- `ios_reverse/models/coverage.py` - Coverage model (P04.7)
- `ios_reverse/models/coverage_policy.py` - Coverage policy (P04.7)
- `ios_reverse/models/report.py` - Report model (P04.7)

### Adapters
- `ios_reverse/adapters/base.py` - Adapter base classes
- `ios_reverse/adapters/macho/__init__.py` - Mach-O adapters (P04.2)
- `ios_reverse/adapters/foundation.py` - Foundation adapters
- `ios_reverse/adapters/objc/__init__.py` - ObjC adapter (P04.3)
- `ios_reverse/adapters/swift/__init__.py` - Swift adapter (P04.3)
- `ios_reverse/adapters/components/__init__.py` - Component adapters (P04.4)
- `ios_reverse/adapters/analysis/__init__.py` - Analysis adapters (P04.5, P04.6)

### Renderers (P04.7)
- `ios_reverse/renderers/__init__.py` - Renderer exports
- `ios_reverse/renderers/report_renderer.py` - JSON and Markdown renderers

### Capabilities
- `ios_reverse/capabilities/__init__.py` - Exports all capabilities
- `ios_reverse/capabilities/base.py` - Capability base classes
- `ios_reverse/capabilities/foundation.py` - CAP-001 to CAP-006 (P04.1)
- `ios_reverse/capabilities/macho_binary.py` - CAP-007 to CAP-013 (P04.2)
- `ios_reverse/capabilities/objc_metadata.py` - CAP-014, CAP-015 (P04.3)
- `ios_reverse/capabilities/swift_metadata.py` - CAP-016, CAP-017 (P04.3)
- `ios_reverse/capabilities/framework_inventory.py` - CAP-018 (P04.4)
- `ios_reverse/capabilities/dylib_inventory.py` - CAP-019 (P04.4)
- `ios_reverse/capabilities/extension_inventory.py` - CAP-020 (P04.4)
- `ios_reverse/capabilities/component_graph.py` - EP-04.4E (orchestration)
- `ios_reverse/capabilities/network_framework_detection.py` - CAP-021 (P04.5)
- `ios_reverse/capabilities/network_endpoint_discovery.py` - CAP-022 (P04.5)
- `ios_reverse/capabilities/architecture_detection.py` - CAP-024 (P04.5)
- `ios_reverse/capabilities/callflow_reconstruction.py` - CAP-026 (P04.5)
- `ios_reverse/capabilities/crypto_detection.py` - CAP-028 (P04.6)
- `ios_reverse/capabilities/anti_analysis_detection.py` - CAP-030 (P04.6)
- `ios_reverse/capabilities/coverage_auditor.py` - CAP-031 (P04.7)

### Tests
- `tests/test_capabilities.py` - P04.1 tests (68)
- `tests/test_capabilities_macho_binary.py` - P04.2 tests (29)
- `tests/test_capabilities_objc_swift.py` - P04.3 tests (48)
- `tests/test_capabilities_component_inventory.py` - P04.4 tests (47)
- `tests/test_capabilities_network_architecture.py` - P04.5 tests (52)
- `tests/test_capabilities_crypto_anti_analysis.py` - P04.6 tests (40)

### Workflows (P05)
- `ios_reverse/workflows/__init__.py` - Workflow exports
- `ios_reverse/workflows/schema.py` - Workflow schema and models
- `ios_reverse/workflows/definitions.py` - All 15 workflow definitions
- `ios_reverse/workflows/registry.py` - Workflow registry
- `ios_reverse/workflows/validator.py` - Workflow validator
- `tests/test_workflows.py` - P05 workflow tests (50)
- `tests/test_capabilities_coverage_reporting.py` - P04.7 tests (46)
- `tests/test_engine.py` - P03 engine tests

### Agents (P06)
- `ios_reverse/agents/__init__.py` - Agent exports
- `ios_reverse/agents/model.py` - Agent models
- `ios_reverse/agents/registry.py` - Agent registry
- `ios_reverse/agents/selector.py` - Agent selector
- `ios_reverse/agents/scheduler.py` - Task scheduler
- `ios_reverse/agents/validator.py` - Evidence validator
- `ios_reverse/agents/context.py` - Context pack generator
- `tests/test_agents.py` - P06 agent tests (35)

### Workspace (P07)
- `ios_reverse/workspace/__init__.py` - Workspace exports
- `ios_reverse/workspace/model.py` - Case models
- `ios_reverse/workspace/manager.py` - Case manager, locking
- `ios_reverse/workspace/evidence.py` - Evidence/claims stores
- `ios_reverse/workspace/resume.py` - Resume engine
- `ios_reverse/workspace/context_pack.py` - Context pack, living docs
- `tests/test_workspace.py` - P07 workspace tests (30)

### Integrity (P08)
- `ios_reverse/models/provenance.py` - Provenance graph model
- `ios_reverse/workspace/integrity.py` - Integrity checker
- `ios_reverse/workspace/trace.py` - Trace API
- `tests/test_integrity.py` - P08 integrity tests (28)

### Adapters (P09)
- `ios_reverse/adapters/contract.py` - Canonical adapter contract
- `ios_reverse/adapters/selector.py` - Tool selector, health service
- `ios_reverse/adapters/base.py` - Base adapter classes
- `ios_reverse/adapters/core/` - Core tool adapters
- `ios_reverse/adapters/macho/` - Mach-O tool adapters
- `ios_reverse/adapters/analysis/` - Analysis adapters
- `ios_reverse/adapters/components/` - Component adapters
- `tests/test_adapters.py` - P09 adapter tests (33)

### Reliability (P10)
- `tests/test_reliability.py` - P10 reliability tests (28)
- `.kaiser-build/RELIABILITY_SCORECARD.md` - Reliability scorecard

## Canonical Capability Registry

| CAP ID | Name | Domain | Phase | Status |
|--------|------|--------|-------|--------|
| CAP-001 | foundation.artifact_detect | foundation | P04.1 | IMPLEMENTED |
| CAP-002 | foundation.ipa_validate | foundation | P04.1 | IMPLEMENTED |
| CAP-003 | foundation.ipa_unpack | foundation | P04.1 | IMPLEMENTED |
| CAP-004 | foundation.bundle_inventory | foundation | P04.1 | IMPLEMENTED |
| CAP-005 | foundation.plist_extract | foundation | P04.1 | IMPLEMENTED |
| CAP-006 | foundation.entitlements_extract | foundation | P04.1 | IMPLEMENTED |
| CAP-007 | macho.basic | macho | P04.2 | IMPLEMENTED |
| CAP-008 | macho.slices | macho | P04.2 | IMPLEMENTED |
| CAP-009 | macho.load_commands | macho | P04.2 | IMPLEMENTED |
| CAP-010 | binary.imports | binary | P04.2 | IMPLEMENTED |
| CAP-011 | binary.exports | binary | P04.2 | IMPLEMENTED |
| CAP-012 | binary.symbols | binary | P04.2 | IMPLEMENTED |
| CAP-013 | binary.strings | binary | P04.2 | IMPLEMENTED |
| CAP-014 | objc.metadata | objective_c | P04.3 | IMPLEMENTED |
| CAP-015 | objc.deep_metadata | objective_c | P04.3 | IMPLEMENTED |
| CAP-016 | swift.metadata | swift | P04.3 | IMPLEMENTED |
| CAP-017 | swift.demangle | swift | P04.3 | IMPLEMENTED |
| CAP-018 | framework.inventory | components | P04.4 | IMPLEMENTED |
| CAP-019 | dylib.inventory | components | P04.4 | IMPLEMENTED |
| CAP-020 | extension.inventory | components | P04.4 | IMPLEMENTED |
| CAP-021 | network.framework_detection | network | P04.5 | IMPLEMENTED |
| CAP-022 | network.endpoint_discovery | network | P04.5 | IMPLEMENTED |
| CAP-023 | network.evidence | network | P04.5 | RESERVED |
| CAP-024 | architecture.detection | architecture | P04.5 | IMPLEMENTED |
| CAP-025 | architecture.classification | architecture | P04.5 | RESERVED |
| CAP-026 | callflow.reconstruct | callflow | P04.5 | IMPLEMENTED |
| CAP-027 | callflow.anchor_analysis | callflow | P04.5 | RESERVED |
| CAP-028 | crypto.detection | crypto | P04.6 | IMPLEMENTED |
| CAP-029 | crypto.primitive_analysis | crypto | P04.6 | RESERVED |
| CAP-030 | anti.analysis_detection | anti_analysis | P04.6 | IMPLEMENTED |
| CAP-031 | coverage.calculation | coverage | P04.7 | IMPLEMENTED |

**Total**: 27 implemented, 4 reserved (31 total)

## Current Phase

**P11 COMPLETE → P12 NEXT**

## Phase Status

| Subphase | Status |
|----------|--------|
| P00 | ✓ COMPLETE |
| P01 | ✓ COMPLETE |
| P02 | ✓ COMPLETE |
| P03 | ✓ COMPLETE |
| P04 | ✓ COMPLETE |
| P05 | ✓ COMPLETE |
| P06 | ✓ COMPLETE |
| P07 | ✓ COMPLETE |
| P08 | ✓ COMPLETE |
| P09 | ✓ COMPLETE |
| P10 | ✓ COMPLETE |
| P11 | ✓ COMPLETE |
| P12 | NEXT |

## Test Summary
- P11 Documentation: Complete
- Total: 571 passed, 2 skipped

## Evidence Strength Hierarchy

| Level | Description |
|-------|-------------|
| STRING_HINT | Found in strings only |
| REFERENCE | Referenced by code |
| STRUCTURAL | From parsing structures |
| CORRELATED | Correlated with other evidence |
| VERIFIED | Confirmed by analysis |

## Coverage States

| State | Meaning |
|-------|---------|
| COVERED | Successfully analyzed |
| PARTIAL | Partially analyzed |
| FAILED | Attempted but unsuccessful |
| NOT_APPLICABLE | Not applicable for target |
| NOT_ATTEMPTED | Eligible but not attempted |
| UNKNOWN | Unknown state |

## Key Distinctions

- **Physical vs Logical**: ComponentGraph (P04.4) vs ArchitectureModel (P04.5)
- **Containment vs Linkage**: CONTAINS vs LOADS edges
- **Framework Presence vs Usage**: Presence != confirmed usage
- **Endpoint Candidate vs Verified**: STRING_HINT != VERIFIED
- **Selector Reference vs Confirmed Call**: reference != confirmed
- **Heuristic vs Structural**: Naming vs inheritance evidence
- **Library Presence vs Usage**: Framework linked != app uses it
- **Indicator vs Verified Mechanism**: String/path != confirmed protection
- **Binary Encryption vs Application Crypto**: LC_ENCRYPTION_INFO != AES/HMAC
- **NOT_ATTEMPTED vs FAILED**: Eligible but not run vs attempted but failed
- **execution_success vs coverage_complete**: All nodes succeeded vs all targets attempted

## Environment
- Platform: Windows 11 Pro
- Python: 3.12.1
- Test: 330 passed, 2 skipped
