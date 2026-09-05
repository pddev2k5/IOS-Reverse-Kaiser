# Workflows

## Overview

IOS REVERSE KAISER provides 15 canonical workflows, each defined as a directed acyclic graph (DAG) of capabilities.

## Workflow Status Legend

| Status | Meaning |
|--------|---------|
| ✓ IMPLEMENTED | Fully functional |
| ⊘ BLOCKED | Requires unavailable tool |
| ◐ PARTIAL | Limited functionality |

## Canonical Workflows

### 1. ios.unpack

**Purpose**: Extract and validate IPA contents

**Status**: ✓ IMPLEMENTED

**Default Depth**: quick

**Supported Depth**: quick, standard, deep, full

```
artifact_detect
       ↓
ipa_validate
       ↓
ipa_unpack
       ↓
bundle_inventory
       ↓
     STOP
```

**Capabilities**:
- `foundation.artifact_detect`
- `bundle.validate`
- `bundle.unpack`
- `bundle.inventory`

**Coverage Policy**: All executable targets in IPA

---

### 2. ios.inspect

**Purpose**: Basic bundle inventory and metadata

**Status**: ✓ IMPLEMENTED

**Default Depth**: standard

**Supported Depth**: quick, standard

```
artifact_detect
       ↓
ipa_validate
       ↓
bundle_inventory
       ↓
macho_basic
       ↓
     STOP
```

**Capabilities**:
- `foundation.artifact_detect`
- `bundle.validate`
- `bundle.inventory`
- `macho.basic`

**Coverage Policy**: All executables

---

### 3. ios.dump

**Purpose**: Standard binary analysis dump

**Status**: ✓ IMPLEMENTED

**Default Depth**: standard

**Supported Depth**: quick, standard, deep, full

```
unpack_bundle
       ↓
macho_analysis
       ↓
binary_strings
       ↓
framework_inventory
       ↓
  [optional]
symbol_extraction
       ↓
     STOP
```

**Capabilities**:
- `bundle.unpack`
- `macho.analysis`
- `binary.strings`
- `framework.inventory`
- `binary.symbols` (optional)

**Coverage Policy**: All eligible executables

---

### 4. ios.macho

**Purpose**: Deep Mach-O binary analysis

**Status**: ✓ IMPLEMENTED

**Default Depth**: standard

**Supported Depth**: standard, deep, full

```
unpack_bundle
       ↓
macho_header
       ↓
macho_load_commands
       ↓
macho_segments
       ↓
macho_symbols
       ↓
     STOP
```

**Capabilities**:
- `macho.header`
- `macho.load_commands`
- `macho.segments`
- `macho.symbols`

**Coverage Policy**: All Mach-O binaries

---

### 5. ios.objc

**Purpose**: Objective-C metadata extraction

**Status**: ✓ IMPLEMENTED

**Default Depth**: standard

**Supported Depth**: standard, deep, full

```
unpack_bundle
       ↓
macho_basic
       ↓
objc_class_list
       ↓
objc_method_list
       ↓
objc_selector
       ↓
     STOP
```

**Capabilities**:
- `bundle.unpack`
- `macho.basic`
- `objc.class_list`
- `objc.method_list`
- `objc.selector`

**Coverage Policy**: All ObjC binaries

---

### 6. ios.swift

**Purpose**: Swift metadata extraction

**Status**: ✓ IMPLEMENTED

**Default Depth**: standard

**Supported Depth**: standard, deep, full

```
unpack_bundle
       ↓
macho_basic
       ↓
swift_type_refs
       ↓
swift_metadata
       ↓
swift_demangle
       ↓
     STOP
```

**Capabilities**:
- `bundle.unpack`
- `macho.basic`
- `swift.type_refs`
- `swift.metadata`
- `swift.demangle`

**Coverage Policy**: All Swift binaries

---

### 7. ios.network

**Purpose**: Network endpoint analysis

**Status**: ✓ IMPLEMENTED

**Default Depth**: standard

**Supported Depth**: quick, standard, deep, full

```
unpack_bundle
       ↓
network_endpoints
       ↓
url_schemes
       ↓
tls_config
       ↓
network_architecture
       ↓
     STOP
```

**Capabilities**:
- `bundle.unpack`
- `network.endpoints`
- `network.url_schemes`
- `network.tls_config`
- `network.architecture`

**Coverage Policy**: All executables

---

### 8. ios.login-flow

**Purpose**: Authentication callflow analysis

**Status**: ✓ IMPLEMENTED

**Default Depth**: standard

**Supported Depth**: standard, deep, full

```
unpack_bundle
       ↓
network_endpoints
       ↓
callflow_auth
       ↓
objc_metadata
       ↓
swift_metadata
       ↓
     STOP
```

**Capabilities**:
- `bundle.unpack`
- `network.endpoints`
- `callflow.auth`
- `objc.metadata`
- `swift.metadata`

**Coverage Policy**: Authentication-related components

---

### 9. ios.crypto

**Purpose**: Cryptographic primitive detection

**Status**: ✓ IMPLEMENTED

**Default Depth**: standard

**Supported Depth**: deep, full

```
unpack_bundle
       ↓
crypto_primitives
       ↓
crypto_key_mgmt
       ↓
crypto_algo
       ↓
     STOP
```

**Capabilities**:
- `bundle.unpack`
- `crypto.primitives`
- `crypto.key_management`
- `crypto.algorithm`

**Coverage Policy**: All executables

---

### 10. ios.anti-analysis

**Purpose**: Anti-analysis protection detection

**Status**: ✓ IMPLEMENTED

**Default Depth**: standard

**Supported Depth**: deep, full

```
unpack_bundle
       ↓
anti_debug
       ↓
anti_tamper
       ↓
anti_emulator
       ↓
     STOP
```

**Capabilities**:
- `bundle.unpack`
- `anti_analysis.debug`
- `anti_analysis.tamper`
- `anti_analysis.emulator`

**Coverage Policy**: All executables

---

### 11. ios.decompile

**Purpose**: Decompiled pseudocode generation

**Status**: ⊘ BLOCKED

**Reason**: Requires commercial decompiler (IDA Pro, Ghidra)

**Required Tools**: IDA Pro + ida-pro-mcp, or Ghidra

---

### 12. ios.ida

**Purpose**: IDA Pro interactive analysis

**Status**: ⊘ BLOCKED

**Reason**: Requires IDA Pro + MCP server

**Required Tools**: IDA Pro, ida-pro-mcp server

---

### 13. ios.runtime

**Purpose**: Runtime instrumentation

**Status**: ⊘ BLOCKED

**Reason**: Requires runtime provider (jailbreak + Frida)

**Required Tools**: Jailbroken device or simulator, Frida

---

### 14. ios.report

**Purpose**: Generate analysis report

**Status**: ✓ IMPLEMENTED

**Default Depth**: standard

```
load_results
       ↓
generate_json
       ↓
generate_markdown
       ↓
     STOP
```

**Capabilities**:
- `report.load_results`
- `report.generate_json`
- `report.generate_markdown`

---

### 15. ios.full

**Purpose**: Comprehensive analysis (all capabilities)

**Status**: ✓ IMPLEMENTED

**Default Depth**: full

```
unpack_bundle
       ↓
macho_full
       ↓
objc_full
       ↓
swift_full
       ↓
network_full
       ↓
crypto_full
       ↓
anti_analysis_full
       ↓
     STOP
```

**Capabilities**: All implemented capabilities

**Coverage Policy**: Maximum declared coverage

---

## Depth Profiles

| Depth | Agent Budget | Unpack | Inspect | Dump | Network | Report |
|-------|--------------|--------|---------|------|---------|--------|
| quick | 1 | ✓ | - | - | - | - |
| standard | 2 | ✓ | ✓ | ✓ | ✓ | ✓ |
| deep | 4 | ✓ | - | ✓ | ✓ | ✓ |
| full | 6 | ✓ | ✓ | ✓ | ✓ | ✓ |

## Scope Leakage Rules

### ios.unpack

**Allowed**: `foundation.*`, `bundle.inventory`

**Forbidden**: `macho.*`, `binary.*`, `objc.*`, `swift.*`, `network.*`, `crypto.*`, `anti_analysis.*`

### ios.network

**Allowed**: `foundation.*`, `bundle.inventory`, `macho.basic`, `binary.strings`, `network.*`, `architecture.*`, `callflow.*`, `coverage.*`

**Forbidden**: `crypto.*`, `anti_analysis.*`

### ios.crypto

**Allowed**: `foundation.*`, `bundle.inventory`, `macho.basic`, `binary.*`, `crypto.*`, `coverage.*`

**Forbidden**: `network.*`, `anti_analysis.*`

## Workflow Selection

```
User Command
     ↓
Intent Resolved (unpack, network, crypto, etc.)
     ↓
Depth Resolved (quick, standard, deep, full)
     ↓
Workflow DAG Selected
     ↓
Scope Validated (no leakage)
     ↓
Agent Budget Allocated
     ↓
Execution
```

## Workflow Status Summary

| Workflow | Status | Depth |
|----------|--------|-------|
| ios.unpack | ✓ | quick-full |
| ios.inspect | ✓ | quick-standard |
| ios.dump | ✓ | quick-full |
| ios.macho | ✓ | standard-full |
| ios.objc | ✓ | standard-full |
| ios.swift | ✓ | standard-full |
| ios.network | ✓ | quick-full |
| ios.login-flow | ✓ | standard-full |
| ios.crypto | ✓ | deep-full |
| ios.anti-analysis | ✓ | deep-full |
| ios.decompile | ⊘ BLOCKED | - |
| ios.ida | ⊘ BLOCKED | - |
| ios.runtime | ⊘ BLOCKED | - |
| ios.report | ✓ | standard |
| ios.full | ✓ | full |
