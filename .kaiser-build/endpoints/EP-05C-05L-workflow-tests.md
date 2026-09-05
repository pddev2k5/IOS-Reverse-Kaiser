# EP-05C-05L: Workflow Tests & Integration

**Date**: 2026-09-04
**Phase**: P05 - Workflow Maps
**Subphase**: EP-05C-05L

## Summary

Created comprehensive workflow tests and validated workflow correctness.

## Semantic Tests

### A. Unpack Narrowness ✓
```
/ios-reverse app.ipa unpack

MUST NOT select:
- network.*
- crypto.*
- anti_analysis.*
- IDA, runtime, Ghidra

Result: PASSED
```

### B. Dump Standard < Dump Full ✓
```
selected(dump standard) ⊂ selected(dump full)

Result: PASSED
```

### C. Network Standard < Network Full ✓
```
selected(network standard) ⊂ selected(network full)

Result: PASSED
```

### D. Network Standard does NOT auto-invoke Crypto ✓
```
ios.network does not include crypto.*

Result: PASSED
```

### E. Login-flow includes correct domains ✓
```
ios.login-flow includes:
- network.*
- architecture.*
- callflow.*

Result: PASSED
```

### F. Report does NOT trigger analysis ✓
```
ios.report does not include any analysis capabilities

Result: PASSED
```

### G. Full composes broad domains intentionally ✓
```
ios.full includes:
- foundation.*
- macho.*
- binary.*
- objc.*
- swift.*
- network.*
- crypto.*
- anti_analysis.*
- coverage.*

Result: PASSED
```

### H. Resume capability ✓
All workflows have `resume_enabled = True`

## Workflow Differential Testing ✓

| Workflow | Standard | Full | Is Subset |
|----------|----------|------|-----------|
| dump | ✓ | ✓ | ✓ |
| network | ✓ | ✓ | ✓ |
| macho | ✓ | ✓ | ✓ |
| objc | ✓ | ✓ | ✓ |
| swift | ✓ | ✓ | ✓ |
| crypto | ✓ | ✓ | ✓ |
| anti-analysis | ✓ | ✓ | ✓ |

## Validator Tests ✓

All workflows pass validation:
- No cycles
- No unreachable nodes
- Entry/terminal nodes valid
- Dependencies resolved
- Scope leakage prevented

## Test Summary

| Test Category | Count | Status |
|--------------|-------|--------|
| Intent Normalization | 5 | ✓ PASS |
| Registry | 3 | ✓ PASS |
| Unpack Workflow | 6 | ✓ PASS |
| Dump Workflow | 4 | ✓ PASS |
| Network Workflow | 3 | ✓ PASS |
| Report Workflow | 3 | ✓ PASS |
| Blocked Workflows | 3 | ✓ PASS |
| Validator | 4 | ✓ PASS |
| Workflow Differential | 3 | ✓ PASS |
| Schema | 5 | ✓ PASS |
| Completeness | 4 | ✓ PASS |
| Depth Profiles | 3 | ✓ PASS |
| **TOTAL** | **50** | **✓ PASS** |
