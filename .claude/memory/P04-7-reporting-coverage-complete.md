---
name: p04-7-reporting-coverage-complete
description: P04.7 Reporting + Coverage completed
metadata:
  type: project
---

# P04.7 Complete: Reporting + Coverage

## Summary
Completed P04.7 with coverage auditing and reporting capabilities.

## What Was Built

### Models (4)
- `ios_reverse/models/coverage.py` - Coverage model with CoverageState, CoverageDimension, CoverageAudit
- `ios_reverse/models/coverage_policy.py` - Declarative coverage policies
- `ios_reverse/models/report.py` - Report model with ReportSection, ClaimStrength
- `ios_reverse/renderers/report_renderer.py` - JSON and Markdown renderers

### Capabilities (1)
- CAP-031: `coverage.calculation` - Coverage auditing capability

## Key Design Decisions

### Coverage
1. **NOT_ATTEMPTED ≠ FAILED** - Semantically different
2. **execution_success ≠ coverage_complete** - Separate concerns
3. **False 100% prevented** - 10 eligible, 8 analyzed = 80%, not 100%
4. **Explicit denominator** - Always track eligible target count

### Reporting
1. **Model separate from renderer** - Normalized model, multiple renderers
2. **Claim strength preserved** - STRING_HINT → SUSPECTED, not promoted
3. **Sensitive data handling** - Conservative redaction
4. **Partial analysis generates reports** - Even failed workflows produce reports

## Test Results
- **330 passed, 2 skipped** - All tests pass
- P04.7 specific: 46 tests

## Why This Matters
- Measurable coverage semantics
- Declarative coverage policies
- Human + machine readable reports
- Evidence strength preserved

## How to Apply
```python
from ios_reverse.capabilities import CoverageAuditorCapability
from ios_reverse.renderers import render_report, render_coverage_audit
```

## Links
- [[p04-6-crypto-anti-analysis-complete]] - P04.6 layer
- [[p04-5-network-architecture-callflow-complete]] - P04.5 layer
