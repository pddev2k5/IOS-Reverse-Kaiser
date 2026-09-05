"""
Intent Resolution for IOS REVERSE KAISER.

This module handles:
- Intent normalization
- Alias resolution
- Intent validation
"""

from enum import Enum
from typing import Set, Optional
from dataclasses import dataclass


class Intent(Enum):
    """Supported intents."""
    UNPACK = "unpack"
    INSPECT = "inspect"
    DUMP = "dump"
    DECOMPILE = "decompile"
    MACHO = "macho"
    OBJC = "objc"
    SWIFT = "swift"
    NETWORK = "network"
    LOGIN_FLOW = "login-flow"
    CRYPTO = "crypto"
    ANTI_ANALYSIS = "anti-analysis"
    IDA = "ida"
    RUNTIME = "runtime"
    REPORT = "report"
    FULL = "full"


# Intent aliases
INTENT_ALIASES = {
    # unpack
    "extract": Intent.UNPACK,

    # inspect
    "examine": Intent.INSPECT,

    # dump
    "inventory": Intent.DUMP,

    # decompile
    "disassemble": Intent.DECOMPILE,

    # macho
    "mach-o": Intent.MACHO,

    # objc
    "objective-c": Intent.OBJC,

    # swift
    "swift": Intent.SWIFT,

    # network
    "net": Intent.NETWORK,
    "http": Intent.NETWORK,

    # login-flow
    "auth": Intent.LOGIN_FLOW,
    "login": Intent.LOGIN_FLOW,

    # crypto
    "crypt": Intent.CRYPTO,
    "encryption": Intent.CRYPTO,

    # anti-analysis
    "anti-tamper": Intent.ANTI_ANALYSIS,

    # ida
    "ida-pro": Intent.IDA,

    # runtime
    "dynamic": Intent.RUNTIME,

    # report
    "report": Intent.REPORT,

    # full
    "all": Intent.FULL,
    "complete": Intent.FULL,
}


# Default depth per intent
DEFAULT_DEPTHS = {
    Intent.UNPACK: "quick",
    Intent.INSPECT: "quick",
    Intent.DUMP: "standard",
    Intent.DECOMPILE: "standard",
    Intent.MACHO: "standard",
    Intent.OBJC: "standard",
    Intent.SWIFT: "standard",
    Intent.NETWORK: "standard",
    Intent.LOGIN_FLOW: "standard",
    Intent.CRYPTO: "standard",
    Intent.ANTI_ANALYSIS: "quick",
    Intent.IDA: "deep",
    Intent.RUNTIME: "deep",
    Intent.REPORT: "standard",
    Intent.FULL: "full",
}


@dataclass
class ResolvedIntent:
    """Result of intent resolution."""
    canonical: Intent
    original: str
    depth: str
    is_alias: bool


class IntentResolver:
    """
    Resolves user input to canonical intents.

    This resolver:
    1. Normalizes input (lowercase, strip)
    2. Resolves aliases
    3. Validates against supported intents
    4. Returns canonical intent
    """

    def __init__(self):
        self._alias_map = INTENT_ALIASES
        self._supported = set(Intent)
        self._canonical_map = {i.value: i for i in Intent}

    def resolve(self, input_str: str) -> Intent:
        """
        Resolve a string to a canonical Intent.

        Args:
            input_str: User input (e.g., 'dump-full', 'extract', 'unpack')

        Returns:
            Canonical Intent enum value

        Raises:
            ValueError: If intent is not supported
        """
        normalized = input_str.lower().strip()

        # Check aliases first
        if normalized in self._alias_map:
            return self._alias_map[normalized]

        # Check canonical values
        if normalized in self._canonical_map:
            return self._canonical_map[normalized]

        # Not found
        supported = [i.value for i in sorted(self._supported, key=lambda x: x.value)]
        raise ValueError(
            f"Unknown intent: '{input_str}'. "
            f"Supported intents: {', '.join(supported)}"
        )

    def resolve_with_depth(self, input_str: str, default_depth: Optional[str] = None) -> ResolvedIntent:
        """
        Resolve intent and extract depth from input.

        Args:
            input_str: User input (e.g., 'dump-full', 'extract', 'unpack')
            default_depth: Default depth if not specified in input

        Returns:
            ResolvedIntent with canonical intent, depth, and alias info
        """
        # Extract depth suffix
        intent_str = input_str.lower().strip()
        depth = default_depth

        depth_suffixes = ["-quick", "-standard", "-deep", "-full", "-q", "-s", "-d", "-f"]
        for suffix in depth_suffixes:
            if intent_str.endswith(suffix):
                intent_str = intent_str[:-len(suffix)]
                depth = suffix[1:]  # Remove leading hyphen
                break

        # Resolve intent
        intent = self.resolve(intent_str)

        # Use default depth if not specified
        if depth is None:
            depth = DEFAULT_DEPTHS.get(intent, "standard")

        # Check if input was an alias
        is_alias = intent_str != intent.value

        return ResolvedIntent(
            canonical=intent,
            original=input_str,
            depth=depth,
            is_alias=is_alias
        )

    def get_supported_intents(self) -> Set[str]:
        """Get set of supported intent values."""
        return {i.value for i in self._supported}

    def get_default_depth(self, intent: Intent) -> str:
        """Get default depth for an intent."""
        return DEFAULT_DEPTHS.get(intent, "standard")
