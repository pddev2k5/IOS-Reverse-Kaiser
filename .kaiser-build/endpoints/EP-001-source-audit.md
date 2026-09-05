# EP-001 — Deep Source Audit

**ID**: EP-001  
**Title**: Deep Source Audit  
**Phase**: P01 — Deep Source Audit  
**Status**: **COMPLETE**  
**Created**: 2026-09-04  
**Updated**: 2026-09-04  

---

## Objective

Clone and deeply audit the three source repositories to understand actual implementations (not just README claims).

---

## Completed

### Repository Cloning

| Repo | Status | Commit SHA | License |
|------|--------|------------|---------|
| ios-reverse-engineering-skill | ✓ CLONED | `5d1a9ef...` | Apache 2.0 |
| ios-reverse-skills | ✓ CLONED | `cc14ebf...` | Unlicense |
| PE-reverse-skill | ✓ CLONED | `0bcf5db...` | CNF-NC ⚠️ |

### File Audit Status

| Repo | README | Scripts | Skills | Commands | Configs | Tests |
|------|--------|---------|--------|----------|---------|-------|
| ios-reverse-engineering-skill | ✓ Audited | ✓ 8 scripts | ✓ 2 skills | ✓ 2 commands | ✓ | Partial |
| ios-reverse-skills | ✓ Audited | ✓ 10+ scripts | ✓ METHODOLOGY | ✓ Multiple | ✓ | Partial |
| PE-reverse-skill | ✓ Audited | ✓ Python core | ✓ Skills | ✓ Multiple | ✓ | Partial |

### Feature Classification

| Feature | Repo1 | Repo2 | Repo3 | Selected |
|---------|-------|-------|-------|----------|
| Intent routing | Partial | Phase-based | JSON config | **Repo2 + Repo3** |
| Workflow DAG | Script pipeline | Phase sequence | JSON config | **Repo2 phases + Repo3 pattern** |
| IPA handling | IMPLEMENTED | IMPLEMENTED | N/A | **Both** |
| Mach-O analysis | IMPLEMENTED | IMPLEMENTED | N/A | **Both** |
| ObjC extraction | IMPLEMENTED | IMPLEMENTED | N/A | **Repo2 (ipsw)** |
| Swift handling | IMPLEMENTED | IMPLEMENTED | N/A | **Repo2** |
| Network analysis | IMPLEMENTED | IMPLEMENTED | N/A | **Repo2** |
| Case workspace | MISSING | MISSING | IMPLEMENTED | **Repo3 adapted** |
| Evidence manifest | MISSING | MISSING | IMPLEMENTED | **Repo3 adapted** |
| Capability registry | MISSING | MISSING | IMPLEMENTED | **Repo3 adapted** |

---

## Verified

- All 3 repos cloned successfully
- Commit SHAs recorded
- Licenses documented
- Feature classifications with concrete evidence
- Cross-repo comparisons documented
- Engineering patterns extracted from PE-reverse-skill
- CNF-NC license constraint identified and documented

---

## Artifacts Created/Modified

| Artifact | Action |
|----------|--------|
| `SOURCE_PROVENANCE.md` | Updated with full audit |
| `EP-001-source-audit.md` | Updated |
| `CP-001.json` | Created |
| `latest.json` | Updated |

---

## Tests

| Test | Status |
|------|--------|
| T01: All 3 repos cloned | **PASS** |
| T02: Commit SHAs recorded | **PASS** |
| T03: Each repo has file inventory | **PASS** |
| T04: Features classified with evidence | **PASS** |
| T05: Cross-repo comparison documented | **PASS** |
| T06: SOURCE_PROVENANCE.md updated | **PASS** |

---

## Evidence / Source References

| Source | URL | Status | License |
|--------|-----|--------|---------|
| 1 | https://github.com/Patr1ck-S/ios-reverse-engineering-skill | CLONED | Apache 2.0 |
| 2 | https://github.com/anatoly505/ios-reverse-skills | CLONED | Unlicense |
| 3 | https://github.com/DamonZS/PE-reverse-skill | CLONED | CNF-NC ⚠️ |

---

## Decisions

| ID | Decision | Rationale |
|----|----------|-----------|
| D-011 | Use Repo 2's 14-phase workflow as primary iOS workflow | Most comprehensive |
| D-012 | Use Repo 2's ipsw-based class-dump | Better than Repo 1's strings-only |
| D-013 | Adapt Repo 3's case workspace pattern for iOS | Proven structure |
| D-014 | Adapt Repo 3's evidence manifest for iOS | SHA-256 verification pattern |
| D-015 | Adapt Repo 3's capability registry pattern | Proven design |
| D-016 | PE-reverse-skill study only (CNF-NC) | Cannot incorporate code |

---

## Open Problems

| Problem | Status |
|---------|--------|
| Architecture not yet designed | PENDING (P02) |
| Capability registry schema not defined | PENDING (P02) |
| Workflow map schema not defined | PENDING (P02) |
| Agent roles not defined | PENDING (P02) |

---

## Next Actions

1. **P02: Architecture Freeze**
   - Design final architecture
   - Lock capability registry schema
   - Lock workflow map schema
   - Lock agent role definitions
   - Create architecture documents

---

## Resume From

P01 complete. Read STATUS.md → NEXT.md → CONTEXT_PACK.md → EP-001 → CP-001 → proceed to P02.

---

*Engineering stop point for P01 deep source audit.*
