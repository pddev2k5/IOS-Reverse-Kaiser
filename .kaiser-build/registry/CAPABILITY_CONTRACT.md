# IOS REVERSE KAISER — Capability Contract Schema

## Purpose

Every capability must expose a **stable platform-level contract** that:
- Is independent of tool adapters
- Defines clear inputs, outputs, and semantics
- Has explicit failure/partial-success handling
- Preserves provenance
- Supports testing with fixtures

**Adapters are replaceable implementations; contracts are immutable.**

---

## Capability Contract Fields

### 1. Identity

```yaml
id: string           # e.g., "ipa.unpack"
version: semver      # e.g., "1.0.0"
domain: string       # e.g., "foundation"
name: string         # Human-readable name
```

### 2. Inputs

```yaml
inputs:
  required:
    - name: artifact_path
      type: path
      description: "Path to IPA file"
      constraints:
        - extension: [".ipa", ".app"]
        - exists: true
        - readable: true
    - name: output_dir
      type: path
      description: "Output directory"
      constraints:
        - exists: true
        - writable: true
        
  optional:
    - name: overwrite
      type: boolean
      default: false
      description: "Overwrite existing files"
```

### 3. Preconditions

```yaml
preconditions:
  - id: "artifact_is_ipa"
    check: "file --mime-type {artifact_path} contains 'application/octet-stream' OR name ends with .ipa"
    error: "E001: Artifact is not an IPA file"
    
  - id: "tool_unzip_available"
    check: "command_exists unzip"
    error: "E002: Required tool 'unzip' is not available"
```

### 4. Supported Artifact Types

```yaml
supported_artifacts:
  input:
    - type: ipa
      mime_types: ["application/octet-stream"]
      extensions: [".ipa"]
    - type: app_bundle
      mime_types: ["application/octet-stream"]
      extensions: [".app"]
      
  output:
    - type: extracted_payload
      description: "Unpacked Payload directory"
    - type: extraction_log
      description: "Extraction transcript"
```

### 5. Adapter Requirements

```yaml
adapters:
  required:
    - id: "unzip"
      min_version: "6.0"
      fallback: null
      
  optional:
    - id: "7z"
      min_version: "16.0"
      fallback_for: "unzip"
```

### 6. Normalized Structured Output

```yaml
output:
  schema_version: "1.0"
  
  success:
    status: "success"
    artifacts:
      - id: "extracted_payload"
        path: "{output_dir}/Payload"
        type: "directory"
        sha256: "{computed}"
        
    metadata:
      extraction_time_ms: 1234
      files_extracted: 456
      total_size_bytes: 78901234
      compression_ratio: 0.87
      
  partial_success:
    status: "partial"
    artifacts:
      - id: "partial_payload"
        path: "{output_dir}/Payload.partial"
        type: "directory"
        sha256: "{computed}"
        
    metadata:
      extraction_time_ms: 1234
      files_extracted: 400
      files_skipped: 56
      skipped_files:
        - path: "file1"
          reason: "permission denied"
          
    warnings:
      - code: "W001"
        message: "Some files were skipped"
        details:
          skipped_count: 56
          
  failure:
    status: "failure"
    error:
      code: "E001"
      message: "Artifact validation failed"
      details:
        expected_type: "ipa"
        actual_type: "zip"
```

### 7. Evidence Production

```yaml
evidence:
  produced:
    - id: "E-{seq:4d}"
      type: "raw"
      content: "stdout from unzip command"
      sha256: "{computed}"
      
    - id: "E-{seq:4d}"
      type: "derived"
      content: "extracted file manifest"
      sha256: "{computed}"
      derived_from: ["E-0001"]
      
  references:
    - evidence_id: "E-0001"
      field: "output.artifacts[0].sha256"
      role: "integrity_verification"
```

### 8. Provenance

```yaml
provenance:
  capability_id: "ipa.unpack"
  capability_version: "1.0.0"
  execution_id: "{execution_id}"
  timestamp: "{ISO8601}"
  
  inputs:
    - name: "artifact_path"
      value: "/path/to/app.ipa"
      verified: true
      
  adapter:
    id: "unzip"
    version: "6.0"
    command: ["unzip", "-q", "-o", "{artifact}", "-d", "{output}"]
    
  environment:
    os: "macos-14.0"
    working_directory: "/path/to/workspace"
    
  outputs:
    artifacts:
      - path: "{output_dir}/Payload"
        size: 78901234
        file_count: 456
```

### 9. Warnings and Errors

```yaml
errors:
  E001:
    code: "E001"
    name: "INVALID_ARTIFACT"
    message: "Artifact is not a valid IPA file"
    severity: "error"
    recoverable: false
    
  E002:
    code: "E002"
    name: "TOOL_UNAVAILABLE"
    message: "Required tool '{tool}' is not available"
    severity: "error"
    recoverable: true
    fallback: "try alternative tool"
    
warnings:
  W001:
    code: "W001"
    name: "SKIPPED_FILES"
    message: "{count} files were skipped during extraction"
    severity: "warning"
    recoverable: true
    
  W002:
    code: "W002"
    name: "PERMISSION_DENIED"
    message: "Cannot read file '{path}'"
    severity: "warning"
    recoverable: true
```

### 10. Partial-Success Semantics

```yaml
partial_success:
  definition: "Extraction completed but some files were skipped"
  
  conditions:
    trigger_on:
      - "permission_denied on non-critical file"
      - "symlink loop detected"
      - "path too long"
      
    do_not_trigger_on:
      - "main executable missing"
      - "Info.plist missing"
      - "corrupt archive"
      
  recovery:
    can_continue: true
    outputs_partial: true
    coverage_note: "Analysis can proceed with reduced coverage"
    
  test_expectations:
    status: "partial"
    artifacts_produced: true
    warnings_present: true
    error_absent: true
```

### 11. Fallback Behavior

```yaml
fallback:
  strategy: "escalate"
  
  levels:
    - adapter: "unzip"
      condition: "primary"
      
    - adapter: "7z"
      condition: "unzip unavailable"
      test: "command_exists 7z"
      
    - adapter: "python_zipfile"
      condition: "no archive tools available"
      test: "python import zipfile"
      
    - adapter: null
      condition: "no fallback available"
      result: "FAILURE with E002"
```

### 12. Stop Conditions

```yaml
stop_conditions:
  immediate:
    - "main executable missing after extraction"
    - "archive is corrupt"
    - "output directory is not writable"
    
  retry:
    - condition: "network timeout during extraction"
      max_retries: 3
      backoff_ms: 1000
      
  abort_workflow:
    - condition: "E001 (invalid artifact)"
    - condition: "E002 (tool unavailable, no fallback)"
```

### 13. Tests

```yaml
tests:
  unit:
    - id: "test_valid_ipa"
      fixture: "fixtures/valid_app.ipa"
      expected:
        status: "success"
        files_extracted: ">0"
        
    - id: "test_corrupt_ipa"
      fixture: "fixtures/corrupt_app.ipa"
      expected:
        status: "failure"
        error_code: "E001"
        
    - id: "test_unzip_fallback"
      fixture: "fixtures/valid_app.ipa"
      mocks:
        tool_unzip: false
      expected:
        status: "success"
        adapter_used: "7z"
        
  integration:
    - id: "test_extraction_pipeline"
      requires: ["ipa.unpack", "bundle.inventory"]
      fixtures:
        - "fixtures/valid_app.ipa"
      assertions:
        - "extracted files match inventory"
        - "provenance chain complete"
```

---

## Capability Contract Validation

Every capability MUST pass these validation gates:

### Gate 1: Schema Compliance
```yaml
- id: unique and follows pattern "{domain}.{operation}"
- version: valid semver
- all required fields present
- types match schema
```

### Gate 2: Output Normalization
```yaml
- output schema_version matches contract version
- success output has required fields
- failure output has error with code and message
- partial_success output has warnings array
```

### Gate 3: Provenance Preservation
```yaml
- execution_id present
- timestamp present
- inputs recorded
- adapter_id recorded
- outputs recorded with paths
```

### Gate 4: Error Handling
```yaml
- all errors have code, name, message, severity
- recoverable errors have fallback defined
- stop conditions are explicit
```

### Gate 5: Test Coverage
```yaml
- unit tests for success path
- unit tests for each error code
- unit tests for partial_success
- fixture-based tests (not just mocks)
```

---

## Version

| Field | Value |
|-------|-------|
| Version | 1.0 |
| Phase | P04 |
| Status | LOCKED |

---

*This document defines the capability contract schema.*
