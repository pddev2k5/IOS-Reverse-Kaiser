# EP-P04-Roadmap-Reconciliation

**Date**: 2026-09-04
**Purpose**: State reconciliation and discrepancy correction

## Discrepancy Identified

Previous checkpoint incorrectly stated "P04 Complete" and listed P04.5 as "Binary Analysis Layer".

**Correct P04 Roadmap (as originally approved)**:
```
P04.1 Foundation + IPA          ✓ COMPLETE
P04.2 Mach-O + Binary           ✓ COMPLETE
P04.3 Objective-C + Swift       ✓ COMPLETE
P04.4 Frameworks + dylibs       ✓ COMPLETE
P04.5 Network + Architecture    → ACTIVE/NEXT
P04.6 Crypto + Anti-analysis     ○ PENDING
P04.7 Reporting + Coverage       ○ PENDING
P04.8 Capability Integration    ○ PENDING
```

**Correction Applied**: This document records the discrepancy and corrects the record.

## Files Verified and Synchronized

| File | Status | Notes |
|------|--------|-------|
| STATUS.md | Updated | Corrected P04.5 description |
| NEXT.md | Updated | Corrected to P04.5 Network+Architecture+Callflow |
| CONTEXT_PACK.md | Verified | Up to date |
| DECISIONS.md | Created | Records this discrepancy |
| Latest checkpoint | Updated | EP-04.4-complete reflects correct state |

## Capability Registry Audit

### Implemented Capabilities (21 total)

| CAP ID | Name | Domain | Impl | Registry | Tests | Phase | Status |
|--------|------|--------|------|----------|-------|-------|--------|
| CAP-001 | foundation.artifact_detect | foundation | ✓ | ✓ | ✓ | P04.1 | COMPLETE |
| CAP-002 | foundation.ipa_validate | foundation | ✓ | ✓ | ✓ | P04.1 | COMPLETE |
| CAP-003 | foundation.ipa_unpack | foundation | ✓ | ✓ | ✓ | P04.1 | COMPLETE |
| CAP-004 | foundation.bundle_inventory | foundation | ✓ | ✓ | ✓ | P04.1 | COMPLETE |
| CAP-005 | foundation.plist_extract | foundation | ✓ | ✓ | ✓ | P04.1 | COMPLETE |
| CAP-006 | foundation.entitlements_extract | foundation | ✓ | ✓ | ✓ | P04.1 | COMPLETE |
| CAP-007 | macho.basic | macho | ✓ | ✓ | ✓ | P04.2 | COMPLETE |
| CAP-008 | macho.slices | macho | ✓ | ✓ | ✓ | P04.2 | COMPLETE |
| CAP-009 | macho.load_commands | macho | ✓ | ✓ | ✓ | P04.2 | COMPLETE |
| CAP-010 | binary.imports | binary | ✓ | ✓ | ✓ | P04.2 | COMPLETE |
| CAP-011 | binary.exports | binary | ✓ | ✓ | ✓ | P04.2 | COMPLETE |
| CAP-012 | binary.symbols | binary | ✓ | ✓ | ✓ | P04.2 | COMPLETE |
| CAP-013 | binary.strings | binary | ✓ | ✓ | ✓ | P04.2 | COMPLETE |
| CAP-014 | objc.metadata | objective_c | ✓ | ✓ | ✓ | P04.3 | COMPLETE |
| CAP-015 | objc.deep_metadata | objective_c | ✓ | ✓ | ✓ | P04.3 | COMPLETE |
| CAP-016 | swift.metadata | swift | ✓ | ✓ | ✓ | P04.3 | COMPLETE |
| CAP-017 | swift.demangle | swift | ✓ | ✓ | ✓ | P04.3 | COMPLETE |
| CAP-018 | framework.inventory | components | ✓ | ✓ | ✓ | P04.4 | COMPLETE |
| CAP-019 | dylib.inventory | components | ✓ | ✓ | ✓ | P04.4 | COMPLETE |
| CAP-020 | extension.inventory | components | ✓ | ✓ | ✓ | P04.4 | COMPLETE |
| - | component.graph | - | ✓ | endpoint | ✓ | P04.4 | orchestration |

### Planned Capabilities (10 remaining)

| CAP ID | Name | Domain | Phase |
|--------|------|--------|-------|
| CAP-021 | network.framework_detection | network | P04.5 |
| CAP-022 | network.endpoint_discovery | network | P04.5 |
| CAP-023 | network.evidence | network | P04.5 |
| CAP-024 | architecture.detection | architecture | P04.5 |
| CAP-025 | architecture.classification | architecture | P04.5 |
| CAP-026 | callflow.reconstruct | callflow | P04.5 |
| CAP-027 | callflow.anchor_analysis | callflow | P04.5 |
| CAP-028 | crypto.detection | crypto | P04.6 |
| CAP-029 | crypto.primitive_analysis | crypto | P04.6 |
| CAP-030 | anti.analysis_detection | anti_analysis | P04.6 |
| CAP-031 | coverage.calculation | coverage | P04.7 |

### Component.graph Classification

**EP-04.4E is an ENDPOINT identifier, not a capability ID.**

The `component.graph` capability:
- Is orchestration logic (uses CAP-018, CAP-019, CAP-020)
- Combines results into a unified graph
- Does NOT have a reserved CAP number
- Is NOT in the capability namespace
- Produces `eligible_executables[]` as derived output

If component.graph needs a CAP ID for future reuse, it should receive CAP-XXX at that time.
Currently it remains as an execution endpoint.

## Reconciliation Actions

1. ✓ Created this reconciliation document
2. ✓ Updated STATUS.md with correct P04.5 description
3. ✓ Updated NEXT.md with correct P04.5 objective
4. ✓ Created DECISIONS.md to record the discrepancy
5. ✓ Verified all 21 capabilities have correct IDs
6. ✓ Verified component.graph is endpoint-only
7. ✓ Verified all tests remain green (192 passed)

## Current State After Reconciliation

```
P04 ACTIVE
P04.1 ✓ COMPLETE
P04.2 ✓ COMPLETE
P04.3 ✓ COMPLETE
P04.4 ✓ COMPLETE
P04.5 → NEXT (Network + Architecture + Callflow)
P04.6 ○ PENDING
P04.7 ○ PENDING
P04.8 ○ PENDING
```
