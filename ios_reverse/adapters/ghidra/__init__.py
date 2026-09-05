"""
Ghidra Headless Adapter for IOS REVERSE KAISER.
"""

from ios_reverse.adapters.ghidra.contract import (
    GhidraHeadlessAdapter,
    GhidraFunction,
    GhidraXref,
    GhidraDecompileResult,
)

__all__ = [
    "GhidraHeadlessAdapter",
    "GhidraFunction",
    "GhidraXref",
    "GhidraDecompileResult",
]
