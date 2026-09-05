# P04 — iOS Capability Layer

**Phase**: P04  
**Status**: **ACTIVE (P04.1)**  
**Duration**: 2026-09-04  
**Phase Version**: 1.0  

---

## OVERVIEW

P04 implements all 31 capabilities with tool adapters. Split into 8 resumable subphases for granular progress tracking and recovery.

---

## SUBPHASES

| Subphase | Domain | Capabilities | Status |
|----------|--------|-------------|--------|
| P04.1 | Foundation + IPA | 6 | **COMPLETE** |
| P04.2 | Mach-O + Binary | 7 | PENDING |
| P04.3 | Objective-C + Swift | 4 | PENDING |
| P04.4 | Frameworks + dylibs + extensions | 3 | PENDING |
| P04.5 | Network + architecture + callflow | 5 | PENDING |
| P04.6 | Crypto + anti-analysis | 2 | PENDING |
| P04.7 | Reporting + coverage primitives | 3 | PENDING |
| P04.8 | Integration gate | 1 | PENDING |

---

## CAPABILITIES BY SUBPHASE

### P04.1: Foundation + IPA (6 capabilities)

| ID | Capability | Adapters Required |
|----|------------|-------------------|
| CAP-001 | foundation.artifact_detect | file |
| CAP-002 | ipa.validate | unzip |
| CAP-003 | ipa.unpack | unzip |
| CAP-004 | bundle.inventory | find |
| CAP-005 | plist.extract | plutil |
| CAP-006 | entitlements.extract | codesign, plutil |

### P04.2: Mach-O + Binary (7 capabilities)

| ID | Capability | Adapters Required |
|----|------------|-------------------|
| CAP-010 | macho.basic | file |
| CAP-011 | macho.slices | lipo |
| CAP-012 | macho.load_commands | otool |
| CAP-020 | binary.imports | nm, otool |
| CAP-021 | binary.exports | nm |
| CAP-022 | binary.symbols | nm |
| CAP-023 | binary.strings | strings |

### P04.3: Objective-C + Swift (4 capabilities)

| ID | Capability | Adapters Required |
|----|------------|-------------------|
| CAP-030 | objc.metadata | ipsw, nm |
| CAP-031 | objc.deep_metadata | ipsw, nm, strings |
| CAP-032 | swift.metadata | ipsw, nm |
| CAP-034 | swift.demangle | swift-demangle |

### P04.4: Frameworks + dylibs + extensions (3 capabilities)

| ID | Capability | Adapters Required |
|----|------------|-------------------|
| CAP-040 | framework.inventory | find |
| CAP-041 | dylib.inventory | find |
| CAP-042 | extension.inventory | find |

### P04.5: Network + architecture + callflow (5 capabilities)

| ID | Capability | Adapters Required |
|----|------------|-------------------|
| CAP-050 | architecture.discovery | lipo, file |
| CAP-060 | network.discovery | strings |
| CAP-061 | network.framework_detect | strings, otool |
| CAP-062 | network.endpoint_extract | strings, ipsw |
| CAP-070 | callflow.reconstruct | ipsw, Ghidra |

### P04.6: Crypto + anti-analysis (2 capabilities)

| ID | Capability | Adapters Required |
|----|------------|-------------------|
| CAP-080 | crypto.identify | strings, nm |
| CAP-090 | anti_analysis.scan | strings |

### P04.7: Reporting + coverage primitives (3 capabilities)

| ID | Capability | Adapters Required |
|----|------------|-------------------|
| CAP-100 | runtime.abstract | Frida |
| CAP-110 | report.generate | — |
| CAP-111 | coverage.audit | — |

### P04.8: Integration gate (1 capability)

| ID | Capability | Adapters Required |
|----|------------|-------------------|
| CAP-112 | evidence.validate | — |

---

## SUBPHASE GATES

Each subphase must pass these gates before proceeding:

### Gate 1: Schema Compliance
- [ ] All capabilities in subphase have valid contracts
- [ ] IDs follow `{domain}.{operation}` pattern
- [ ] Versions are valid semver

### Gate 2: Implementation
- [ ] All capabilities have implementations
- [ ] Or explicitly documented as `DEFERRED` with reason
- [ ] Adapters are implemented for required tools

### Gate 3: Output Normalization
- [ ] Success output matches schema
- [ ] Failure output has error code
- [ ] Partial success output has warnings

### Gate 4: Provenance
- [ ] Execution ID present
- [ ] Inputs recorded
- [ ] Adapter ID recorded
- [ ] Outputs with paths recorded

### Gate 5: Testing
- [ ] Unit tests for success path
- [ ] Unit tests for each error code
- [ ] Fixture-based tests (not just mocks)
- [ ] Integration tests where applicable

---

## CONTRACT VALIDATION

Every capability contract is validated against:

```python
def validate_capability_contract(capability: Capability) -> List[ValidationError]:
    errors = []
    
    # 1. Schema compliance
    errors += validate_identity(capability)
    errors += validate_inputs(capability)
    errors += validate_preconditions(capability)
    errors += validate_artifacts(capability)
    errors += validate_adapters(capability)
    
    # 2. Output normalization
    errors += validate_output_schema(capability)
    errors += validate_success_output(capability)
    errors += validate_failure_output(capability)
    errors += validate_partial_success_output(capability)
    
    # 3. Provenance
    errors += validate_provenance_fields(capability)
    
    # 4. Error handling
    errors += validate_errors(capability)
    errors += validate_warnings(capability)
    errors += validate_stop_conditions(capability)
    errors += validate_fallback_behavior(capability)
    
    # 5. Testing
    errors += validate_tests(capability)
    
    return errors
```

---

## TEST REQUIREMENTS

### Unit Tests
Each capability MUST have:
- Test for success path
- Test for each error code
- Test for partial success (if applicable)
- Test for fallback behavior (if applicable)

### Fixture Tests
At least one test per subphase MUST use:
- Real fixture file (not mock)
- Verified expected output
- Provenance verification

### Integration Tests
Each subphase MUST have:
- End-to-end capability pipeline test
- Provenance chain verification
- Output normalization verification

---

## RESUMPTION

Each subphase creates:
- Endpoint document (e.g., `EP-04.1.md`)
- Checkpoint (e.g., `CP-04.1.json`)
- Test results

To resume:
1. Read latest endpoint
2. Read latest checkpoint
3. Continue from next incomplete subphase

---

## QUALITY GATE

P04 does NOT complete until:

- [ ] All 31 capabilities have implementations OR documented DEFERRED status
- [ ] All capabilities satisfy capability schema
- [ ] All capabilities emit normalized outputs
- [ ] All capabilities preserve provenance
- [ ] All capabilities have failure/partial-success semantics
- [ ] All tests pass
- [ ] Integration gate passes

---

## NEXT: P04.1

See `phases/P04.1-FOUNDATION-IPA.md` for subphase work.

---

*P04 started. See subphases for granular progress.*
