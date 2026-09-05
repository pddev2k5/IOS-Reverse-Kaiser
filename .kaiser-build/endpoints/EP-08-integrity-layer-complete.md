# EP-08M: P08 Evidence, Claims, Provenance + Coverage Complete

**Date**: 2026-09-04
**Phase**: P08 - Evidence, Claims, Provenance + Coverage Integration
**Subphase**: EP-08M

## P08 Quality Gate Checklist

### Provenance ✓
- [x] One canonical provenance model exists
- [x] Machine-readable provenance graph exists
- [x] Stable existing IDs are reused
- [x] Backward and forward trace queries work
- [x] Provenance survives cold resume

### Evidence ✓
- [x] Lifecycle defined
- [x] Raw evidence remains immutable
- [x] Multiple observations preserved
- [x] Supersession/invalidation preserves history

### Claims ✓
- [x] Claim lifecycle integrated
- [x] Transitions audited
- [x] Validator decisions persist
- [x] Promotion requires evidence
- [x] Invalid evidence can trigger revalidation
- [x] Conflicts persist

### Entities ✓
- [x] Functions link to claims/evidence
- [x] Endpoints link to claims/evidence
- [x] Callflows link to claims/evidence
- [x] Living docs are regeneratable views

### Coverage ✓
- [x] Coverage observations explain WHY
- [x] Stale results affect coverage correctly
- [x] Coverage completeness distinct from evidence certainty

### Reporting ✓
- [x] Final findings trace back to evidence/artifacts
- [x] Reports become stale when dependencies invalidate
- [x] Regenerated reports preserve historical provenance

### Integrity ✓
- [x] Integrity checker detects broken refs
- [x] Checkpoint coherence validation works
- [x] No orphan critical references
- [x] No unsupported VERIFIED claims

### Invalidation ✓
- [x] Upstream stale state propagates
- [x] History is not deleted

### Persistence ✓
- [x] Cold resume reconstructs provenance
- [x] Claim history preserved
- [x] Validator history preserved
- [x] Coverage reasoning preserved

### Scale ✓
- [x] Synthetic scale test passes
- [x] Graph operations bounded
- [x] Deterministic serialization tested

### Tests ✓
- [x] All 482 previous tests remain green
- [x] All 28 new P08 tests pass
- [x] 2 skipped (explained)

## P08 GATE: PASSED ✓

All quality gates passed. P08 is complete.

## Final Test Results

```
P08 Integrity Tests: 28 passed
Total Test Suite: 510 passed, 2 skipped
```

## P08 Summary

### Canonical Provenance Model

```
ios_reverse/models/provenance.py

ProvenanceNode
├── node_id
├── node_type (14 types: CASE, WORKFLOW_RUN, etc.)
├── case_id
├── parent_refs, child_refs
└── metadata

ProvenanceEdge
├── edge_id
├── source_id, target_id
├── edge_type (13 types: DERIVED_FROM, etc.)
└── weight

ProvenanceGraph
├── add_node(), add_edge()
├── get_ancestors(), get_descendants()
├── find_nodes_by_type()
└── detect_cycles()
```

### Integrity Checker

```
ios_reverse/workspace/integrity.py

IntegrityChecker
├── check_all()
├── check_evidence_orphans()
├── check_verified_claims_have_evidence()
├── check_claim_evidence_refs()
├── check_provenance_cycles()
└── check_schema_versions()
```

### Trace API

```
ios_reverse/workspace/trace.py

TraceAPI
├── trace_claim()
├── trace_evidence()
├── trace_finding()
├── ancestors()
├── descendants()
├── claims_for_evidence()
├── evidence_for_claim()
└── coverage_for_component()
```

### Key Integration Points

1. **Evidence Lifecycle**: DISCOVERED → NORMALIZED → CORRELATED → VALIDATED → SUPERSEDED → INVALIDATED
2. **Claim Transitions**: UNKNOWN → SUSPECTED → INFERRED → VERIFIED (with audit trail)
3. **Validator Integration**: ACCEPT, DOWNGRADE, REJECT, NEEDS_MORE_EVIDENCE persisted
4. **Coverage Separation**: Coverage completeness ≠ Evidence certainty

### Files Created

- `ios_reverse/models/provenance.py` - Provenance graph model
- `ios_reverse/workspace/integrity.py` - Integrity checker
- `ios_reverse/workspace/trace.py` - Trace API
- `tests/test_integrity.py` - 28 integrity tests

## P08 COMPLETE

**P08 - Evidence, Claims, Provenance + Coverage Integration: COMPLETE ✓**
