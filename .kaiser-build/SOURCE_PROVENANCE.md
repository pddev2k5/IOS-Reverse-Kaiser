# IOS REVERSE KAISER — SOURCE PROVENANCE

## Research Sources

All source repositories cloned into `_research/sources/` for immutable reference.

---

## Source 1: ios-reverse-engineering-skill

| Field | Value |
|-------|-------|
| URL | https://github.com/Patr1ck-S/ios-reverse-engineering-skill |
| Status | **CLONED** |
| Commit SHA | `5d1a9ef7d34160a2bdc2233272ef446355de9b0d` |
| License | Apache 2.0 |
| Attribution Required | Yes (Apache 2.0 header) |
| Directory | `_research/sources/ios-reverse-engineering-skill/` |

### Relevant Files

| Category | Files |
|----------|-------|
| README | README.md, README_EN.md |
| Skills | `plugins/ios-reverse-engineering/skills/ios-reverse-engineering/SKILL.md` |
| Scripts | `scripts/ios_unpack.sh`, `scripts/ios_fingerprint.sh`, `scripts/ios_macho_analyze.sh`, `scripts/ios_class_scan.sh`, `scripts/ios_api_scan.py`, `scripts/ios_report.py` |
| References | `references/api-extraction-patterns.md`, `references/ios-analysis-checklist.md`, `references/macho-notes.md` |
| Commands | `commands/ida-ios-analyze.md`, `commands/ios-decompile.md` |
| Config | `.claude-plugin/plugin.json`, `.mcp.json` |

### Feature Provenance

| Feature | Status | Evidence |
|---------|--------|----------|
| IPA unpacking | **IMPLEMENTED** | `scripts/ios_unpack.sh` — handles IPA, .app, .framework, .dylib, .dSYM |
| Info.plist extraction | **IMPLEMENTED** | `scripts/ios_fingerprint.sh` — uses plutil |
| Entitlements extraction | **IMPLEMENTED** | `scripts/ios_fingerprint.sh` — uses codesign |
| Framework/dylib inventory | **IMPLEMENTED** | `scripts/ios_fingerprint.sh` — find commands |
| Mach-O analysis | **IMPLEMENTED** | `scripts/ios_macho_analyze.sh` — architecture, load commands, linked libs, symbols, strings |
| ObjC metadata | **IMPLEMENTED** | `scripts/ios_class_scan.sh` — class, selector extraction |
| Swift metadata | **IMPLEMENTEDED** | `scripts/ios_class_scan.sh` — Swift symbol extraction |
| Network/API discovery | **IMPLEMENTED** | `scripts/ios_api_scan.py` — URLs, domains, REST, GraphQL, WebSocket |
| Report generation | **IMPLEMENTED** | `scripts/ios_report.py` — structured markdown report |
| IDA Pro integration | **IMPLEMENTED** | Optional MCP, `bin/ida-pro-mcp-check`, commands |

### Architecture Patterns Extracted

1. **Script pipeline**: Ordered script execution for analysis workflow
2. **Output directory convention**: `ios_analysis_out/` with subdirectories
3. **Environment file persistence**: `paths.env` for state between scripts
4. **Skill metadata format**: YAML frontmatter with allowed-tools
5. **Command routing**: Slash command definitions in .md files
6. **Safety boundaries**: Explicit security rules in SKILL.md

---

## Source 2: ios-reverse-skills

| Field | Value |
|-------|-------|
| URL | https://github.com/anatoly505/ios-reverse-skills |
| Status | **CLONED** |
| Commit SHA | `cc14ebf3548471ee1bc8aacc73926ce429349b4f` |
| License | Unlicense (public domain) |
| Attribution Required | Not required (public domain) |
| Directory | `_research/sources/ios-reverse-skills/` |

### Relevant Files

| Category | Files |
|----------|-------|
| README | README.md, NOTICE.md |
| Methodology | `skill/METHODOLOGY.md` (14-phase workflow) |
| Scripts | `skill/scripts/check-deps.sh`, `skill/scripts/extract-ipa.sh`, `skill/scripts/find-api-calls.sh`, `skill/scripts/deep-secret-scan.sh`, `skill/scripts/reversing-analyze.sh`, `skill/scripts/detect-sdks.sh`, `skill/scripts/detect-protections.sh`, `skill/scripts/frida-toolbox.sh`, `skill/scripts/audit-vulnerabilities.sh` |
| Ghidra Scripts | `skill/scripts/ghidra/*.java` (7 scripts) |
| References | 20+ reference documents in `skill/references/` |
| Agent Adapters | `agents/claude-code/`, `agents/cursor/`, `agents/qwen-coder/`, etc. |

### Feature Provenance

| Feature | Status | Evidence |
|---------|--------|----------|
| 14-phase workflow | **IMPLEMENTED** | `skill/METHODOLOGY.md` — comprehensive phase definitions |
| Initial probe/triage | **IMPLEMENTED** | `scripts/initial-probe.sh` — five-pass triage |
| Encryption detection | **IMPLEMENTED** | `scripts/check-encryption.sh` — cryptid check |
| Decryption helper | **IMPLEMENTED** | `scripts/decrypt-helper.sh` — bagbak, frida-ios-dump, Clutch |
| IPA extraction | **IMPLEMENTED** | `scripts/extract-ipa.sh` — ipsw class-dump integration |
| Call flow tracing | **IMPLEMENTED** | Methodology Phase 4 + `references/call-flow-analysis.md` |
| API endpoint discovery | **IMPLEMENTED** | `scripts/find-api-calls.sh` — URLSession, Alamofire, GraphQL, WebSocket |
| Security audit | **IMPLEMENTED** | `scripts/find-api-calls.sh --security` — ATS, cert pinning, crypto |
| Cloud credential scan | **IMPLEMENTED** | `scripts/deep-secret-scan.sh` — Firebase, AWS, GCP, Azure, Stripe |
| Deep binary reversing | **IMPLEMENTED** | `scripts/reversing-analyze.sh` — radare2/rizin/Ghidra |
| SDK fingerprinting | **IMPLEMENTED** | `scripts/detect-sdks.sh` — CVE cross-reference |
| Protection detection | **IMPLEMENTED** | `scripts/detect-protections.sh` — 0-20 score |
| Dynamic instrumentation | **IMPLEMENTED** | `scripts/frida-toolbox.sh` — Frida script bundle |
| Vulnerability audit | **IMPLEMENTED** | `scripts/audit-vulnerabilities.sh` — OWASP MASTG mapping |
| Binary patching | **IMPLEMENTED** | `references/binary-patching.md` — AArch64/armv7 |
| Multi-agent adapters | **IMPLEMENTED** | `agents/` — Claude Code, Cursor, Qwen Coder, etc. |

### Architecture Patterns Extracted

1. **Phase-based workflow**: Sequential phases with clear entry/exit criteria
2. **Dependency management**: `check-deps.sh` + `install-dep.sh`
3. **Agent-agnostic methodology**: Model-agnostic `METHODOLOGY.md` + per-agent adapters
4. **Comprehensive reference docs**: 20+ detailed reference guides
5. **Structured reporting**: Markdown templates with OWASP MASTG mapping
6. **Tool integration**: ipsw, radare2/rizin, Ghidra, Frida, class-dump

---

## Source 3: PE-reverse-skill

| Field | Value |
|-------|-------|
| URL | https://github.com/DamonZS/PE-reverse-skill |
| Status | **CLONED** |
| Commit SHA | `0bcf5db8d0e2cd47d8d4f7d9cd86c40f619a2cd4` |
| License | CNF-NC (Non-Commercial Only) — **CANNOT INCORPORATE INTO DERIVATIVE WORKS** |
| Attribution Required | Yes (preserve license and copyright notice) |
| Directory | `_research/sources/PE-reverse-skill/` |

### Relevant Files

| Category | Files |
|----------|-------|
| Context | CONTEXT.md, AGENTS.md |
| Python Core | `reverse_analyzer/core/`, `reverse_analyzer/runtime/`, `reverse_analyzer/evidence/` |
| Skills | `reverse-skills/skills/` |
| Instructions | `reverse_analyzer/instructions/` |
| Go Server | `cmd/reverse-analyzer-server/`, `cmd/reverse-analyzer-runner/` |

### Engineering Pattern Provenance

| Pattern | Status | Evidence | iOS Adaptation |
|---------|--------|----------|-----------------|
| Case workspace | **IMPLEMENTED** | `reverse-skills/skills/scripts/case-init.py` — case.json, notes.md, evidence/ | **SELECTED** — Adopt for case workspace structure |
| Evidence manifest | **IMPLEMENTED** | `reverse_analyzer/evidence/manifest.py` — SHA-256, provenance | **SELECTED** — Adopt for evidence tracking |
| Capability/Provider model | **IMPLEMENTED** | `reverse_analyzer/core/` + providers | **SELECTED** — Adapt for iOS capabilities |
| Routing configuration | **IMPLEMENTED** | `reverse-skills/skills/config/routing.json` | **SELECTED** — Adapt for intent routing |
| Orchestration (Experiment/Flow/Task) | **IMPLEMENTED** | `reverse_analyzer/runtime/`, Go orchestration | **SELECTED** — Adapt for workflow DAG |
| Tool manifest | **IMPLEMENTED** | `reverse-skills/skills/config/tool-manifest.json` | **SELECTED** — Adapt for tool adapters |
| Multi-platform adapters | **IMPLEMENTED** | `reverse_analyzer/instructions/platforms/` | Reference only |
| Evidence SHA-256 | **IMPLEMENTED** | `atomic_write`/`sha256_*` utilities | **SELECTED** — Adopt for evidence integrity |
| Workspace isolation | **IMPLEMENTED** | Docker/Podman runner with no-new-privileges | Reference only |

### CRITICAL LICENSE WARNING

**PE-reverse-skill uses CNF-NC (Custom Non-Commercial) license.**

The license explicitly prohibits:
- Commercial use of the project or any parts
- Modifying the source code (including AI modifications)
- Redistributing the project or derivatives

**DECISION**: Study for platform-neutral engineering patterns ONLY. Do NOT copy code or derivative works. Extract architectural concepts and re-implement for iOS context.

### Architecture Concepts to Extract

1. **Case structure**: `case.json`, `notes.md`, `evidence/`, `reports/` — adapt for iOS case workspace
2. **Evidence manifest**: SHA-256 verification, provenance tracking — adopt pattern
3. **Routing configuration**: JSON-based workflow selection — adapt for intent routing
4. **Capability/Provider separation**: Provider lifecycle pattern — adapt for iOS capabilities
5. **Orchestration hierarchy**: Experiment > Flow > Task > Subtask — adapt for workflow DAG
6. **Tool manifest**: Tool contracts with dependencies — adapt for tool adapters
7. **Platform adapters**: Abstract deployment layer — reference for multi-agent

---

## Cross-Repository Feature Comparison

| Feature | Repo1 | Repo2 | Repo3 | Selected |
|---------|-------|-------|-------|----------|
| Intent routing | Basic | Phase-based | JSON config | **Repo2 + Repo3** |
| IPA handling | ✓ | ✓ | N/A | **Both good** |
| Mach-O analysis | ✓ | ✓ | N/A | **Both good** |
| ObjC extraction | ✓ | ✓ | N/A | **Repo2 better** (ipsw class-dump) |
| Swift handling | ✓ | ✓ | N/A | **Repo2 better** (ipsw + demangler) |
| Network analysis | ✓ | ✓ | N/A | **Repo2 better** (more comprehensive) |
| Security audit | Partial | ✓ | N/A | **Repo2 better** |
| Cloud secrets | ✗ | ✓ | N/A | **Repo2 only** |
| SDK detection | ✗ | ✓ | N/A | **Repo2 only** |
| Protection score | ✗ | ✓ | N/A | **Repo2 only** |
| Dynamic instr. | ✗ | ✓ | N/A | **Repo2 only** |
| Workflow DAG | Script pipeline | Phase sequence | JSON config | **Repo3 pattern + Repo2 phases** |
| Case workspace | ✗ | ✗ | ✓ | **Repo3 adapted** |
| Evidence manifest | ✗ | ✗ | ✓ | **Repo3 adapted** |
| Capability registry | ✗ | ✗ | ✓ | **Repo3 adapted** |
| Agent adapters | ✗ | ✓ | ✓ | **Both adapted** |

---

## Final Source Selection

| Concept | Source | Rationale |
|---------|--------|-----------|
| iOS analysis scripts | Repo 1 + Repo 2 | Both have solid implementations; Repo 2 is more comprehensive |
| 14-phase workflow | Repo 2 | Most mature iOS reverse workflow |
| IPA/Mach-O handling | Repo 1 + Repo 2 | Combine strongest elements |
| Network analysis | Repo 2 | More comprehensive patterns |
| Security audit patterns | Repo 2 | ATS, cert pinning, crypto detection |
| Cloud credential scan | Repo 2 | Firebase, AWS, GCP, Azure, Stripe |
| Case workspace structure | Repo 3 concept | Re-implement for iOS |
| Evidence manifest | Repo 3 pattern | Re-implement for iOS |
| Intent routing | Repo 2 + Repo 3 | Phase-based + JSON config |
| Workflow DAG | Repo 3 pattern | Re-implement for iOS |
| Capability registry | Repo 3 pattern | Re-implement for iOS |
| Tool adapters | Repo 3 pattern | Re-implement for iOS |

---

## Audit Classification Summary

| Repository | Features | Score | License |
|------------|----------|-------|---------|
| ios-reverse-engineering-skill | 12/12 implemented | **HIGH** | Apache 2.0 ✓ |
| ios-reverse-skills | 15/15 implemented | **HIGH** | Unlicense ✓✓ |
| PE-reverse-skill | 8 patterns studied | **HIGH** | CNF-NC ⚠️ (study only) |

---

*This document is the immutable record of source material provenance. Updated after P01 audit.*
