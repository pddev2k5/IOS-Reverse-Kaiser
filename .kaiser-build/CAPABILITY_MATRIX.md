# Capability Registry Matrix

**Date**: 2026-09-04
**Phase**: P04.7 - Reporting + Coverage

## Registry Audit

This document provides a complete audit of CAP-001 through CAP-031.

| CAP ID | Canonical Name | Domain | Phase | Implementation File | Registered | Implemented | Contract Valid | Tests | Status | Notes |
|--------|---------------|--------|-------|-------------------|------------|-------------|----------------|-------|--------|-------|
| CAP-001 | foundation.artifact_detect | foundation | P04.1 | capabilities/foundation.py | ✓ | ✓ | ✓ | 68 | IMPLEMENTED | Foundation capability |
| CAP-002 | foundation.ipa_validate | foundation | P04.1 | capabilities/foundation.py | ✓ | ✓ | ✓ | - | IMPLEMENTED | |
| CAP-003 | foundation.ipa_unpack | foundation | P04.1 | capabilities/foundation.py | ✓ | ✓ | ✓ | - | IMPLEMENTED | |
| CAP-004 | foundation.bundle_inventory | foundation | P04.1 | capabilities/foundation.py | ✓ | ✓ | ✓ | - | IMPLEMENTED | |
| CAP-005 | foundation.plist_extract | foundation | P04.1 | capabilities/foundation.py | ✓ | ✓ | ✓ | - | IMPLEMENTED | |
| CAP-006 | foundation.entitlements_extract | foundation | P04.1 | capabilities/foundation.py | ✓ | ✓ | ✓ | - | IMPLEMENTED | |
| CAP-007 | macho.basic | macho | P04.2 | capabilities/macho_binary.py | ✓ | ✓ | ✓ | 29 | IMPLEMENTED | |
| CAP-008 | macho.slices | macho | P04.2 | capabilities/macho_binary.py | ✓ | ✓ | ✓ | - | IMPLEMENTED | |
| CAP-009 | macho.load_commands | macho | P04.2 | capabilities/macho_binary.py | ✓ | ✓ | ✓ | - | IMPLEMENTED | |
| CAP-010 | binary.imports | binary | P04.2 | capabilities/macho_binary.py | ✓ | ✓ | ✓ | - | IMPLEMENTED | |
| CAP-011 | binary.exports | binary | P04.2 | capabilities/macho_binary.py | ✓ | ✓ | ✓ | - | IMPLEMENTED | |
| CAP-012 | binary.symbols | binary | P04.2 | capabilities/macho_binary.py | ✓ | ✓ | ✓ | - | IMPLEMENTED | |
| CAP-013 | binary.strings | binary | P04.2 | capabilities/macho_binary.py | ✓ | ✓ | ✓ | - | IMPLEMENTED | |
| CAP-014 | objc.metadata | objective_c | P04.3 | capabilities/objc_metadata.py | ✓ | ✓ | ✓ | 48 | IMPLEMENTED | |
| CAP-015 | objc.deep_metadata | objective_c | P04.3 | capabilities/objc_metadata.py | ✓ | ✓ | ✓ | - | IMPLEMENTED | |
| CAP-016 | swift.metadata | swift | P04.3 | capabilities/swift_metadata.py | ✓ | ✓ | ✓ | - | IMPLEMENTED | |
| CAP-017 | swift.demangle | swift | P04.3 | capabilities/swift_metadata.py | ✓ | ✓ | ✓ | - | IMPLEMENTED | |
| CAP-018 | framework.inventory | components | P04.4 | capabilities/framework_inventory.py | ✓ | ✓ | ✓ | 47 | IMPLEMENTED | |
| CAP-019 | dylib.inventory | components | P04.4 | capabilities/dylib_inventory.py | ✓ | ✓ | ✓ | - | IMPLEMENTED | |
| CAP-020 | extension.inventory | components | P04.4 | capabilities/extension_inventory.py | ✓ | ✓ | ✓ | - | IMPLEMENTED | |
| CAP-021 | network.framework_detection | network | P04.5 | capabilities/network_framework_detection.py | ✓ | ✓ | ✓ | 52 | IMPLEMENTED | |
| CAP-022 | network.endpoint_discovery | network | P04.5 | capabilities/network_endpoint_discovery.py | ✓ | ✓ | ✓ | - | IMPLEMENTED | |
| CAP-023 | network.evidence | network | P04.5 | - | ✓ | ✗ | - | - | RESERVED | P04.5 enhancement - not yet implemented |
| CAP-024 | architecture.detection | architecture | P04.5 | capabilities/architecture_detection.py | ✓ | ✓ | ✓ | - | IMPLEMENTED | |
| CAP-025 | architecture.classification | architecture | P04.5 | - | ✓ | ✗ | - | - | RESERVED | P04.5 enhancement - not yet implemented |
| CAP-026 | callflow.reconstruct | callflow | P04.5 | capabilities/callflow_reconstruction.py | ✓ | ✓ | ✓ | - | IMPLEMENTED | |
| CAP-027 | callflow.anchor_analysis | callflow | P04.5 | - | ✓ | ✗ | - | - | RESERVED | P04.5 enhancement - not yet implemented |
| CAP-028 | crypto.detection | crypto | P04.6 | capabilities/crypto_detection.py | ✓ | ✓ | ✓ | 40 | IMPLEMENTED | Canonical name per user request |
| CAP-029 | crypto.primitive_analysis | crypto | P04.6 | - | ✓ | ✗ | - | - | RESERVED | P04.6 enhancement - not yet implemented |
| CAP-030 | anti.analysis_detection | anti_analysis | P04.6 | capabilities/anti_analysis_detection.py | ✓ | ✓ | ✓ | - | IMPLEMENTED | Canonical name per user request |
| CAP-031 | coverage.calculation | coverage | P04.7 | - | ✓ | ✗ | - | - | DEFERRED | P04.7 - implementing now |

## Summary

| Status | Count |
|--------|-------|
| IMPLEMENTED | 26 |
| RESERVED | 4 |
| DEFERRED | 1 |
| REMOVED | 0 |
| INVALID | 0 |
| **TOTAL** | **31** |

## Naming Consistency

The user request used the following terminology:
- `crypto.identify` → implemented as `crypto.detection`
- `anti_analysis.scan` → implemented as `anti.analysis_detection`

**Decision**: The canonical registry names are the implemented names:
- CAP-028: `crypto.detection` (not `crypto.identify`)
- CAP-030: `anti.analysis_detection` (not `anti_analysis.scan`)

Aliases may be added internally if backward compatibility is needed.

## Reserved/Deferred IDs

These IDs are reserved for future enhancements and should NOT be repurposed:

| CAP ID | Reserved For | Phase |
|--------|-------------|-------|
| CAP-023 | network.evidence | P04.5 |
| CAP-025 | architecture.classification | P04.5 |
| CAP-027 | callflow.anchor_analysis | P04.5 |
| CAP-029 | crypto.primitive_analysis | P04.6 |
| CAP-031 | coverage.calculation | P04.7 |

## Gaps Are Intentional

The capability IDs have gaps (e.g., 023, 025, 027, 029) because:
1. These IDs were reserved for planned but not-yet-implemented capabilities
2. Existing capabilities have stable IDs that should not be renumbered
3. Future capabilities can fill these gaps when needed

This is the intentional design, not an error.
