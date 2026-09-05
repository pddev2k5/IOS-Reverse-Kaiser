# Attribution

## Source Provenance

IOS REVERSE KAISER is built upon the shoulders of giants. This document acknowledges the projects and resources that influenced or contributed to this framework.

## Core Architecture

### Inspired By

The evidence-driven, layered architecture draws from:
- **Evidence accumulation patterns** from academic reverse engineering papers
- **Provenance tracking** concepts from data science workflows
- **DAG-based task orchestration** from modern build systems

### Reused Patterns

The following patterns were adapted/inspired by established practices:

| Pattern | Source | Adaptation |
|---------|--------|------------|
| DAG validation | Build system DAGs | Workflow validation |
| Immutable evidence | Git/Merkle trees | Raw evidence immutability |
| Budget-based parallelism | Task schedulers | Agent budget enforcement |

## Dependencies

### Core Python (stdlib)

No external dependencies required for core functionality. Uses Python standard library:
- `json` - Data serialization
- `pathlib` - Path handling
- `dataclasses` - Data structures
- `enum` - Enumerations
- `datetime` - Time handling
- `hashlib` - Hashing
- `zipfile` - IPA extraction
- `subprocess` - Tool execution

### Optional Dependencies

The following are optional and not required for core functionality:

| Tool | Purpose | License |
|------|---------|---------|
| ipsw | Mach-O inspection | MIT |
| IDA Pro | Disassembler | Proprietary |
| Ghidra | Disassembler | Apache 2.0 |
| radare2 | CLI reversing | LGPL 3.0 |

## Reference Materials

### Documentation

The following public documentation was referenced:
- Apple documentation on Mach-O format
- LLVM documentation on intermediate representation
- OWASP Mobile Application Security Testing Guide (MASTG)
- iOS Reverse Engineering community resources

### Research Papers

Concepts adapted from:
- Binary analysis research on provenance tracking
- Software engineering on evidence-based claims
- Formal methods on DAG validation

## Licensing

### This Project

IOS REVERSE KAISER itself is provided under:
[INSERT LICENSE - MIT, Apache 2.0, or other as appropriate]

### Third-Party Components

All third-party components maintain their original licenses:
- IDA Pro: Proprietary (Hex-Rays)
- Ghidra: Apache 2.0 (NSA)
- radare2: LGPL 3.0

## No Clones

This repository does NOT contain:
- Cloned source code from other projects
- Copied binary analysis logic
- Replicated proprietary tools

All code is original implementation or uses standard library.

## Historical Context

This framework builds upon lessons learned from:
- PE-reverse-skill (Windows reverse engineering framework)
- ios-reverse-skills (iOS reverse engineering knowledge base)
- Various open-source iOS analysis tools

## Trademark Notice

- IDA Pro is a trademark of Hex-Rays SA
- Ghidra is a trademark of the National Security Agency
- Apple, iOS are trademarks of Apple Inc.
- All other trademarks are property of their respective owners

## Contact

For questions about attribution or licensing:
[INSERT CONTACT INFORMATION]
