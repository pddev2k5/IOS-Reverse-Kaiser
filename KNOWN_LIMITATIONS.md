# Known Limitations

This document lists known limitations of IOS REVERSE KAISER. These are documented truthfully and are not hidden or marketed as features.

## Filesystem Reliability (PARTIAL)

**Status**: PARTIAL

**Classification**: Environmental + Platform

**Reason**: The case workspace handles failures gracefully but cannot simulate certain failure conditions in unit tests:

1. **Atomic Write Limitations**
   - Cannot simulate disk-full conditions
   - Cannot simulate permission errors deterministically
   - Cannot simulate filesystem unmount

2. **Platform-Specific Lock Behavior**
   - `fcntl` advisory locks only work on Unix/Linux/macOS
   - Windows has no portable equivalent
   - Lock is simulated on Windows (best effort)

**Mitigation**: Code uses try/except, provides fallbacks, detects corruption, and recovers properly.

**P12 Verification**: Verify checkpoint integrity on Windows.

---

## Live Tool Integration (BLOCKED)

**Status**: BLOCKED - Requires commercial tools or specific environment

### IDA Pro Integration

| Aspect | Status |
|--------|--------|
| Adapter Contract | ✓ Defined |
| MCP Server | ✗ Not implemented |
| Session Management | ✗ Not implemented |
| Live Testing | ✗ Requires IDA license |

### Ghidra Integration

| Aspect | Status |
|--------|--------|
| Adapter Contract | ✓ Defined |
| Headless Server | ✗ Not configured |
| Live Testing | ✗ Requires Ghidra installation |

### Runtime Instrumentation

| Aspect | Status |
|--------|--------|
| Provider Abstraction | ✓ Defined |
| Frida Integration | ✗ Not implemented |
| Jailbreak Device | ✗ Not available |
| Live Testing | ✗ Requires jailbroken device |

---

## Platform Limitations

### Windows

| Feature | Status | Notes |
|---------|--------|-------|
| Core analysis | ✓ Works | Python-based |
| IPA extraction | ✓ Works | Python zipfile |
| Mach-O parsing | ✓ Works | Pure Python |
| Objective-C metadata | ✓ Works | Static only |
| Swift metadata | ✓ Works | Static only |
| Network analysis | ✓ Works | Static only |
| macOS tools | ✗ N/A | otool, plutil, codesign |
| File locking | ◐ Best effort | No fcntl |

### Linux

| Feature | Status | Notes |
|---------|--------|-------|
| Core analysis | ✓ Works | Python-based |
| IPA extraction | ✓ Works | Python zipfile |
| Mach-O parsing | ✓ Works | Pure Python |
| Objective-C metadata | ✓ Works | Static only |
| Swift metadata | ✓ Works | Static only |
| Network analysis | ✓ Works | Static only |
| macOS tools | ✗ N/A | otool, plutil, codesign |

### macOS

| Feature | Status | Notes |
|---------|--------|-------|
| Core analysis | ✓ Works | Python-based |
| IPA extraction | ✓ Works | Python zipfile |
| Mach-O parsing | ✓ Works | Pure Python + otool |
| Objective-C metadata | ✓ Works | Static + runtime |
| Swift metadata | ✓ Works | Static + runtime |
| Network analysis | ✓ Works | Static only |
| macOS tools | ✓ Works | otool, plutil, codesign |
| File locking | ✓ Works | fcntl available |

---

## Binary Limitations

### Encrypted Binaries

| Issue | Impact | Workaround |
|-------|--------|------------|
| FairPlay DRM | Cannot analyze | Use decrypted IPA |
| App Store encryption | Cannot analyze | Use decrypted IPA |
| Custom encryption | Cannot analyze | Manual decryption |

### Stripped Binaries

| Issue | Impact | Workaround |
|-------|--------|------------|
| Stripped symbols | Limited ObjC/Swift | Use class-dump |
| No debug info | Limited analysis | Use IDA/Ghidra |
| Obfuscated code | Limited static analysis | Runtime analysis |

### Swift ABI Changes

| Issue | Impact | Workaround |
|-------|--------|------------|
| New Swift versions | Incomplete metadata | Use newer tools |
| Swift 6 changes | Partial support | Manual analysis |

---

## Workflow Limitations

### Decompile Workflow

| Status | BLOCKED |
|--------|---------|
| Requires | IDA Pro or Ghidra |
| Alternative | Use `ios.macho` for assembly |

### IDA Workflow

| Status | BLOCKED |
|--------|---------|
| Requires | IDA Pro + MCP server |
| Alternative | Use `ios.dump` or `ios.macho` |

### Runtime Workflow

| Status | BLOCKED |
|--------|---------|
| Requires | Jailbroken device + Frida |
| Alternative | Static analysis only |

---

## Analysis Limitations

### Static Analysis Bounds

Static analysis cannot determine:
- Actual runtime behavior
- Dynamic code loading
- Runtime-generated code
- Obfuscated control flow
- Encrypted data at runtime
- User interaction effects

### Network Analysis Bounds

Static network analysis cannot determine:
- Actual network traffic (without proxy)
- Server responses
- Dynamic endpoints
- CDN resolution
- Load balancer behavior

### Coverage Limitations

- Coverage percentage reflects static analysis only
- Cannot detect dynamically loaded code
- Cannot analyze encrypted/decrypted runtime
- False 100% prevention is implemented but not perfect

---

## Test Limitations

### Live Tool Tests

Live tool integration tests are skipped when:
- Tool not installed
- License not available
- Platform not supported

These tests have explicit skip reasons and do not masquerade as passes.

### Performance Tests

Performance tests use broad smoke thresholds, not strict benchmarks:
- No machine-specific timing requirements
- No microbenchmarking
- No memory profiling

### Cross-Platform Tests

Tests run primarily on Windows:
- Platform-specific tests may be skipped on other platforms
- File locking tests limited by platform capabilities

---

## Scope Limitations

### What This Is NOT

IOS REVERSE KAISER is NOT:
- A Windows PE reverse toolkit (use PE-reverse-skill)
- An Android reverse toolkit
- An automatic decompiler
- A replacement for IDA Pro or Ghidra
- A tool that reconstructs perfect source code
- A runtime debugger without jailbreak

### Out of Scope

- Binary modification/patching
- App Store submission tools
- Code signing tools
- Device management
- Enterprise MDM integration

---

## Deferred Features

| Feature | Reason | Target |
|---------|--------|--------|
| IDA MCP integration | Requires MCP server | P14+ |
| Ghidra headless | Requires server setup | P14+ |
| Runtime provider | Requires jailbreak | P15+ |
| Frida integration | Requires device | P15+ |
| Cloud analysis | Requires infrastructure | Future |

---

## Summary

| Category | Status |
|----------|--------|
| Core Analysis | ✓ Complete |
| Workflows | ✓ Complete |
| Evidence/Claims | ✓ Complete |
| Tool Adapters | ✓ Contract ready |
| Live Tool Integration | ⊘ Deferred |
| Runtime Analysis | ⊘ Deferred |
| Cross-Platform File Locks | ◐ Partial |
| Decompilation | ⊘ Blocked |

This system provides valuable static analysis without commercial tools. Full decompilation and runtime analysis require additional tooling.
