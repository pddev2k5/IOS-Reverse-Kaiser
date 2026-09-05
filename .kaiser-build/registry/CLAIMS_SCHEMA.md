# IOS REVERSE KAISER — Evidence & Claims Model

## Evidence Model

Evidence is the foundation of the claims model. Every analytical finding must be traceable to concrete evidence.

---

## Evidence Types

| Type | Description | Examples |
|------|-------------|----------|
| raw | Direct tool output | strings output, nm output, plist content |
| derived | Processed interpretation | extracted URLs, identified frameworks |
| inferred | LLM-generated conclusion | "likely authentication", "probably uses Firebase" |

---

## Evidence Manifest Entry

```json
{
  "id": "E-XXX-001",
  "type": "raw | derived | inferred",
  
  "case_id": "string",
  "workflow_id": "string",
  "node_id": "string",
  
  "capability_id": "string",
  "tool": "string",
  
  "file_path": "string",
  "sha256": "string",
  
  "created_at": "ISO8601",
  
  "description": "string",
  
  "references": ["array of source file paths"],
  
  "provenance": {
    "input_artifacts": ["array of input evidence IDs"],
    "processing": "string (description of transformation)"
  },
  
  "metadata": {
    "size_bytes": "number",
    "format": "string",
    "tool_version": "string"
  }
}
```

---

## Claims Model

### Claim States

| State | Description | Requirements |
|-------|-------------|-------------|
| verified | Confirmed with direct evidence | Evidence refs present, all verified |
| inferred | Reasonable conclusion | Evidence refs present, logical connection |
| suspected | Possible but unconfirmed | Evidence refs present, uncertainty noted |
| rejected | Proven false | Contradicting evidence present |
| unknown | Not yet evaluated | No evidence refs |

### Claim Definition

```json
{
  "id": "CLM-XXX-001",
  
  "claim": "string (the assertion)",
  "state": "verified | inferred | suspected | rejected | unknown",
  
  "case_id": "string",
  "workflow_id": "string",
  
  "category": "string (e.g., 'network', 'crypto', 'security')",
  
  "confidence": "number (0-100)",
  
  "evidence_refs": ["array of evidence IDs"],
  
  "reasoning": "string (how the claim was derived)",
  
  "contradicted_by": ["array of evidence IDs (if rejected)"],
  
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  
  "validated_by": "string (validator agent ID, if verified)",
  "validated_at": "ISO8601"
}
```

---

## Claim Categories

| Category | Description | Examples |
|----------|-------------|----------|
| identity | App identity findings | Bundle ID, version, executable |
| network | Network-related findings | Endpoints, frameworks, auth |
| crypto | Crypto-related findings | Algorithms, key handling |
| security | Security findings | Entitlements, pinning, protections |
| architecture | Structural findings | Frameworks, dylibs, extensions |
| metadata | Metadata findings | ObjC/Swift classes, methods |
| api | API surface findings | Exported functions, symbols |
| flow | Call flow findings | Authentication flow, data flow |

---

## Evidence → Claims Flow

```
Capability Execution
    │
    ▼
Raw Evidence Created
    │
    ├── E-001: strings_output.txt (SHA-256: abc...)
    ├── E-002: nm_output.txt (SHA-256: def...)
    └── E-003: plist_content.txt (SHA-256: ghi...)
    │
    ▼
Derived Evidence
    │
    ├── E-004: extracted_urls.json
    └── E-005: identified_frameworks.json
    │
    ▼
Claim Creation
    │
    ├── CLM-001: "App uses URLSession" (state: inferred)
    │   └── evidence_refs: [E-001, E-004]
    │
    ├── CLM-002: "App connects to api.example.com" (state: verified)
    │   └── evidence_refs: [E-001, E-004]
    │   └── validated_by: "evidence-validator"
    │
    └── CLM-003: "Uses Alamofire" (state: suspected)
        └── evidence_refs: [E-002]
        └── reasoning: "Symbols suggest Alamofire but not confirmed"
```

---

## Claim Validation Rules

### Verification Requirements

A claim can be marked **verified** only if:

1. All evidence_refs exist and are accessible
2. All raw evidence has valid SHA-256
3. Evidence-validator agent has checked the chain
4. No contradicting evidence exists
5. Explicit validation recorded

### Inference Rules

A claim can be marked **inferred** only if:

1. Evidence refs are present
2. Logical connection to evidence documented
3. Uncertainty is not excessive (confidence > 30)
4. Reasoning is documented

### Suspicion Rules

A claim can be marked **suspected** only if:

1. Some evidence exists but insufficient
2. Confidence is low (30-60)
3. Alternative explanations possible
4. Further validation recommended

### Rejection Rules

A claim can be marked **rejected** only if:

1. Contradicting evidence exists
2. Evidence refs document the contradiction
3. Reasoning explains why claim is false

---

## Evidence Integrity

### SHA-256 Verification

All raw evidence MUST have SHA-256 computed and stored:

```bash
sha256sum evidence_file.txt > evidence_file.sha256
```

Verification:
```bash
sha256sum -c evidence_file.sha256
```

### Provenance Chain

Each derived artifact must track:

1. **Input artifacts**: What was consumed
2. **Processing**: What transformation was applied
3. **Tool**: What tool performed the processing
4. **Agent**: What agent initiated the processing

---

## Report Generation

Reports must distinguish claim states:

```markdown
## Network Analysis

### Verified Findings
- App connects to `https://api.example.com/v1` (E-001, E-004)

### Inferred Findings
- App likely uses URLSession for networking (E-001, E-002)
- Probably implements certificate pinning (E-003, E-005)

### Suspected Findings
- May use Alamofire (E-006) — further validation needed
- Possibly sends analytics to `analytics.example.com` (E-007)

### Rejected Claims
- Claims of WebSocket usage were not confirmed (E-008)
```

---

## Version

| Field | Value |
|-------|-------|
| Version | 1.0 |
| Phase | P02 |
| Status | LOCKED |

---

*This document defines the evidence and claims model.*
