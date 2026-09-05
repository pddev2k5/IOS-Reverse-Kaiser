# IOS REVERSE KAISER — MASTER PLAN

## Project Definition

**Name**: IOS REVERSE KAISER  
**Type**: Production-quality iOS reverse-engineering skill/framework  
**Platform**: iOS ONLY (Windows PE support explicitly excluded)  
**User-Facing Interface**: Single `/ios-reverse` command family

---

## Mission Statement

Build a modular, resumable, evidence-driven iOS reverse-engineering framework by deeply researching and selectively integrating concepts from three source repositories, with zero Windows PE user-facing capabilities.

---

## Source Repositories

| # | Repository | Focus |
|---|------------|-------|
| 1 | https://github.com/Patr1ck-S/ios-reverse-engineering-skill | iOS RE fundamentals |
| 2 | https://github.com/anatoly505/ios-reverse-skills | iOS reverse skills |
| 3 | https://github.com/DamonZS/PE-reverse-skill | Platform-neutral engineering patterns |

---

## Phase Plan

| Phase | Name | Objective |
|-------|------|-----------|
| P00 | Bootstrap | Persistent build memory, project structure |
| P01 | Deep Source Audit | Clone repos, audit actual implementations |
| P02 | Architecture Freeze | Design finalized, documents locked |
| P03 | Core Execution Engine | Workflow DAG executor, state machine |
| P04 | iOS Capability Layer | 30+ atomic iOS-specific capabilities |
| P05 | Workflow Maps | Declarative YAML/JSON workflows per intent |
| P06 | Adaptive Multi-Agent | Agent roles, orchestration tiers |
| P07 | Persistent Workspaces | Case management, resume system |
| P08 | Evidence & Provenance | Claims, evidence, coverage auditing |
| P09 | Tool Adapters | IDA, Ghidra, ipsw, runtime, etc. |
| P10 | Testing & Reliability | Full test suite with semantic tests |
| P11 | Documentation | User guides, API docs, release notes |
| P12 | Git Finalization | Commit, push, release |

---

## Key Architectural Principles

1. **Filesystem is Source of Truth** — Never rely on conversation memory
2. **One Slash Command** — `/ios-reverse` with intent+depth routing
3. **Declarative Workflows** — YAML/JSON DAGs, not monoliths
4. **Narrow Execution** — Requests must NOT auto-expand scope
5. **Persistent State** — Checkpoints, endpoints, case workspaces
6. **Evidence-Driven** — Machine-readable claims with provenance
7. **Adaptive Agents** — Single → multi based on complexity
8. **Coverage Auditing** — Full/deep modes require measurable completion

---

## Intent Model

| Intent | Description | Depth Profile |
|--------|-------------|---------------|
| unpack | Extract IPA contents | quick/standard |
| inspect | Surface-level examination | quick/standard |
| dump | Comprehensive extraction | standard/full |
| decompile | Binary decompilation | standard/full |
| macho | Mach-O binary analysis | quick/standard/deep/full |
| objc | Objective-C metadata | quick/standard/deep |
| swift | Swift metadata/demangling | quick/standard/deep |
| network | Network analysis | quick/standard/full |
| login-flow | Authentication flow | standard/deep |
| crypto | Crypto identification | quick/standard/deep |
| anti-analysis | Anti-RE detection | quick/standard |
| ida | IDA-specific analysis | deep/full |
| runtime | Runtime instrumentation | deep/full |
| report | Generate findings report | standard/full |
| full | Complete coverage | full |

---

## Capability Count Target

Minimum 30 atomic capabilities across domains:
- Foundation (artifact detection, validation, unpacking)
- Bundle analysis (Info.plist, entitlements, inventory)
- Mach-O analysis (basic, slices, load commands)
- Binary analysis (imports, exports, symbols, strings)
- Metadata (ObjC, Swift)
- Network (discovery, framework, endpoints)
- Crypto identification
- Anti-analysis detection
- Coverage auditing
- Report generation

---

## Quality Gates

- Every phase requires: ENTRY → WORK → TEST → EVIDENCE → QUALITY_GATE → ENDPOINT → CHECKPOINT → NEXT
- Phases marked ACTIVE until quality gate passes
- Semantic routing tests must pass before P10 completion
- Resume tests must pass before P12

---

## Success Criteria

See `.kaiser-build/DECISIONS.md` for complete definition of done.

---

## Version

| Field | Value |
|-------|-------|
| Major | 0 |
| Minor | 0 |
| Patch | 1 |
| Status | P00 BOOTSTRAP |

---

*This document is the source of truth for project scope, phases, and success criteria.*
