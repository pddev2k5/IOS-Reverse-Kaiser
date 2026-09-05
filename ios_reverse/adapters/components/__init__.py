"""
Component inventory adapters for IOS REVERSE KAISER.

Provides adapters for framework, dylib, and extension discovery.
"""

from .framework_adapter import FrameworkAdapter
from .dylib_adapter import DylibAdapter
from .extension_adapter import ExtensionAdapter

__all__ = ["FrameworkAdapter", "DylibAdapter", "ExtensionAdapter"]
