# Decisions Log

**Date**: 2026-09-04

## Naming Consistency Decision

**Issue**: User request used `crypto.identify` and `anti_analysis.scan`, but implementation used `crypto.detection` and `anti.analysis_detection`.

**Decision**: The canonical registry names are the implemented names:
- CAP-028: `crypto.detection`
- CAP-030: `anti.analysis_detection`

**Rationale**: These names are more descriptive and follow the established naming convention. The gap between user request terminology and implementation is due to natural evolution during implementation.

**Action**: No change to implementation. Document the canonical names in CAPABILITY_MATRIX.md.

---

## Gap in Capability IDs

**Issue**: Capability IDs have gaps (023, 025, 027, 029).

**Decision**: These gaps are intentional and should NOT be filled by renumbering existing capabilities.

**Rationale**:
1. Existing capabilities have stable IDs that are referenced in code/tests
2. These IDs were reserved for planned but not-yet-implemented capabilities
3. Future enhancements can fill these gaps when implemented

**Action**: Document in CAPABILITY_MATRIX.md that gaps are intentional.

---

## Evidence Strength Consistency

**Decision**: Evidence strength hierarchy is consistent across all P04.5 and P04.6 models:
- STRING_HINT < REFERENCE < STRUCTURAL < CORRELATED < VERIFIED

**Rationale**: This provides a consistent epistemic framework across all analytical capabilities.

---

## Binary Encryption ≠ Application Crypto

**Decision**: LC_ENCRYPTION_INFO/Mach-O binary encryption state is NOT evidence of application-level cryptographic behavior.

**Rationale**: Binary encryption is a protection mechanism, not an analytical finding about the app's crypto usage.

---

## Library Presence ≠ Confirmed Usage

**Decision**: Framework/library presence is tracked separately from confirmed usage.

**Rationale**: A linked framework does not mean the app actively uses it.

---

## Indicator ≠ Verified Mechanism

**Decision**: Anti-analysis indicators (jailbreak paths, debugger APIs) remain at INDICATOR/REFERENCE state until stronger evidence exists.

**Rationale**: Single heuristics should not be elevated to verified mechanisms.

---

## Report Generation Architecture

**Issue**: Is report generation a capability or a renderer service?

**Decision**: Report generation is intentionally modeled as a renderer/service outside the capability registry.

**Rationale**:
1. Renderers (JSON, Markdown) are separate from the capability layer
2. Report model is normalized and separate from renderers
3. CAP-031 coverage.calculation is a capability because it performs analysis/calculation
4. Report generation does not perform new analysis, it formats existing results

**Architecture**:
```
Capability Results → Report Model → Renderer → Output
                                     ↓
                            JSON / Markdown
```

**Action**: Document this decision. No report.generate capability is required.

---

## Coverage Auditor is a Capability

**Decision**: CAP-031 coverage.calculation IS a capability because it performs analysis.

**Rationale**: Coverage auditing involves:
1. Comparing declared policy with actual observations
2. Computing coverage rates
3. Identifying gaps
4. Building audit records

This is analytical work, not just formatting.

**Action**: Keep coverage.calculation as CAP-031.

