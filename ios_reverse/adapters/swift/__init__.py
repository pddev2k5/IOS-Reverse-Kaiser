"""
Swift metadata adapters for IOS REVERSE KAISER.

Provides adapters for Swift metadata extraction and demangling.
"""

from .swift_adapter import SwiftAdapter
from .swift_demangler import SwiftDemangler

__all__ = ["SwiftAdapter", "SwiftDemangler"]
