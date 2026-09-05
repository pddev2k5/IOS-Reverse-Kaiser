# EP-08A: P08 Pre-Flight Integration Audit

**Date**: 2026-09-04
**Phase**: P08 - Evidence, Claims, Provenance + Coverage Integration
**Subphase**: EP-08A

## Summary

Pre-flight audit of existing systems from P04, P06, P07 to identify canonical models, gaps, and integration points.

## Existing Models Audit

### P04 Evidence Model

**Location**: `ios_reverse/models/coverage.py`

```python
Evidence
├── evidence_id: str
├── type: EvidenceType  # RAW, DERIVED
├── strength: EvidenceStrength  # STRING_HINT, REFERENCE, STRUCTURAL, CORRELATED, VERIFIED
├── content: Any
├── source_artifact: str
├── component: Optional[str]
├── capability_id: str
├── created_at: str
└── provenance: List[str]
```

**Assessment**: Good base, needs case_id and persistent storage integration.

### P04 Coverage Model

**Location**: `ios_reverse/models/coverage.py`

```python
CoverageTarget
├── target_id: str
├── target_type: str  # framework, class, function, etc.
├── coverage_state: CoverageState  # FULL, PARTIAL, NONE
├── evidence_refs: List[str]
├── reason: Optional[str]
└── updated_at: str
```

**Assessment**: Good, needs provenance and case integration.

### P04 Report Model

**Location**: `ios_reverse/models/report.py`

```python
ReportFinding
├── finding_id: str
├── category: str
├── severity: str
├── statement: str
├── evidence_refs: List[str]
├── claim_refs: List[str]
└── provenance: List[str]
```

**Assessment**: Good base, needs integration with P07/P08 provenance.

### P06 Evidence Validator

**Location**: `ios_reverse/agents/validator.py`

```python
EvidenceValidator
├── validate_claim(claim, evidence) -> ValidationReport
├── check_for_conflicts(claim_a, claim_b) -> ClaimConflict
└── resolve_conflict(conflict, resolution)

ValidationReport
├── result: ValidationResult  # ACCEPT, DOWNGRADE, REJECT, NEEDS_MORE_EVIDENCE
├── reason: str
└── downgrade_reason: str

ClaimConflict
├── claim_a, claim_b
├── evidence_set_a, evidence_set_b
├── resolution: ConflictResolution  # ACCEPT_A, ACCEPT_B, MERGE, UNRESOLVED
```

**Assessment**: Good validator, needs persistent storage integration.

### P07 Evidence Store

**Location**: `ios_reverse/workspace/evidence.py`

```python
EvidenceStore
├── add_evidence(...) -> EvidenceRecord
├── get_evidence(evidence_id) -> EvidenceRecord
├── list_evidence(evidence_type) -> List[EvidenceRecord]
└── validate_no_orphans() -> List[str]

EvidenceRecord
├── evidence_id: str
├── case_id: str
├── type: EvidenceType
├── strength: EvidenceStrength
├── source_artifact: str
├── capability: str
├── path: str
├── hash: str
├── created_at: str
├── component: Optional[str]
├── immutable: bool
├── parent_refs: List[str]
└── provenance: List[str]
```

**Assessment**: Good persistent store, needs provenance graph integration.

### P07 Claims Store

**Location**: `ios_reverse/workspace/evidence.py`

```python
ClaimsStore
├── add_claim(...) -> ClaimRecord
├── update_claim_state(claim_id, new_state, ...) -> bool
├── list_claims(state) -> List[ClaimRecord]
├── get_verified_claims() -> List[ClaimRecord]
└── get_claims_for_evidence(evidence_id) -> List[ClaimRecord]

ClaimRecord
├── claim_id: str
├── statement: str
├── state: ClaimState  # SUSPECTED, INFERRED, VERIFIED, REJECTED, UNKNOWN
├── evidence_refs: List[str]
├── transitions: List[Dict]  # audit trail
├── created_by: str
├── validated_by: Optional[str]
├── created_at: str
└── updated_at: str
```

**Assessment**: Good persistent store, needs validation integration and conflicts.

### P07 Artifact Store

**Location**: In manifest.json and artifacts/index.json

```python
ArtifactRecord
├── artifact_id: str
├── type: ArtifactType  # ORIGINAL, EXTRACTED, DERIVED
├── path: str
├── hash: str
├── parent_artifact: Optional[str]
├── component: Optional[str]
└── producer_capability: Optional[str]
```

**Assessment**: Good, needs full provenance tracking.

## Integration Gaps Identified

### Gap 1: No Canonical Provenance Model
- Need: `ios_reverse/models/provenance.py` - a unified provenance graph
- Will track: CASE → WORKFLOW → NODE → CAPABILITY → ADAPTER → ARTIFACT → EVIDENCE → CLAIM

### Gap 2: Evidence Validation Not Persistent
- Current: P06 validator creates in-memory ValidationReport
- Need: Persist validation events to case claim store

### Gap 3: Claim Conflicts Not Persisted
- Current: P06 validator tracks conflicts in memory
- Need: Persist conflicts to case store

### Gap 4: No Coverage-Claim Integration
- Current: Coverage tracked separately from claims
- Need: Coverage observations linked to evidence/claims

### Gap 5: No Report-Provenance Integration
- Current: Reports generated with refs, but no trace
- Need: Report findings traceable through provenance graph

### Gap 6: No Cross-Entity Queries
- Current: Stores work independently
- Need: ancestors(), descendants(), trace_claim(), trace_evidence()

## Canonical Representations (Chosen)

| Concept | Canonical Location | Notes |
|---------|-------------------|-------|
| Evidence | P07 EvidenceStore | Persistent, indexed |
| Claims | P07 ClaimsStore | Persistent, audited |
| Coverage | P04 Coverage | Extend with case_id |
| Artifacts | P07 manifest | Extend with provenance |
| Functions | P04 living docs | Extend with refs |
| Endpoints | P04 living docs | Extend with refs |
| Callflows | P04 living docs | Extend with refs |
| Conflicts | P06 + P07 | Integrate conflict store |
| Validation | P06 + P07 | Persist events |

## Migration/Adapter Strategy

1. **Evidence**: Extend P07 EvidenceRecord with provenance fields
2. **Claims**: Extend P07 ClaimRecord with conflict refs and validation events
3. **Coverage**: Create CoverageObservation in P08, linked to evidence/claims
4. **Provenance**: Create ProvenanceGraph in P08, links existing stores

## Next Steps

1. Create canonical provenance model
2. Extend existing stores with provenance references
3. Integrate validator with persistent stores
4. Create integrity checker
5. Add E2E tests
