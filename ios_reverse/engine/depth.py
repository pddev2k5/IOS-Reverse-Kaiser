"""
Depth Resolution for IOS REVERSE KAISER.

This module handles:
- Depth normalization
- Depth validation
- Depth profiles
"""

from enum import Enum
from typing import Set, Optional
from dataclasses import dataclass


class Depth(Enum):
    """Supported depth profiles."""
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"
    FULL = "full"


# Depth aliases
DEPTH_ALIASES = {
    # quick
    "quick": Depth.QUICK,
    "q": Depth.QUICK,

    # standard
    "standard": Depth.STANDARD,
    "std": Depth.STANDARD,
    "s": Depth.STANDARD,

    # deep
    "deep": Depth.DEEP,
    "d": Depth.DEEP,

    # full
    "full": Depth.FULL,
    "f": Depth.FULL,
}


# Depth multipliers for complexity scoring
DEPTH_MULTIPLIERS = {
    Depth.QUICK: 1.0,
    Depth.STANDARD: 2.0,
    Depth.DEEP: 3.0,
    Depth.FULL: 5.0,
}


@dataclass
class DepthProfile:
    """Depth profile configuration."""
    name: Depth
    coverage: str  # minimal, normal, extended, complete
    tool_tier: int  # 1-3 (lightest to heaviest)
    includes_validation: bool
    includes_coverage_audit: bool


# Depth profile configurations
DEPTH_PROFILES = {
    Depth.QUICK: DepthProfile(
        name=Depth.QUICK,
        coverage="minimal",
        tool_tier=1,
        includes_validation=False,
        includes_coverage_audit=False
    ),
    Depth.STANDARD: DepthProfile(
        name=Depth.STANDARD,
        coverage="normal",
        tool_tier=1,
        includes_validation=True,
        includes_coverage_audit=False
    ),
    Depth.DEEP: DepthProfile(
        name=Depth.DEEP,
        coverage="extended",
        tool_tier=2,
        includes_validation=True,
        includes_coverage_audit=False
    ),
    Depth.FULL: DepthProfile(
        name=Depth.FULL,
        coverage="complete",
        tool_tier=3,
        includes_validation=True,
        includes_coverage_audit=True
    ),
}


class DepthResolver:
    """
    Resolves depth strings to canonical Depth values.

    This resolver:
    1. Normalizes input (lowercase, strip)
    2. Resolves aliases
    3. Validates against supported depths
    4. Returns canonical Depth
    """

    def __init__(self):
        self._alias_map = DEPTH_ALIASES
        self._supported = set(Depth)
        self._canonical_map = {d.value: d for d in Depth}
        self._profiles = DEPTH_PROFILES

    def resolve(self, depth_str: Optional[str]) -> Depth:
        """
        Resolve a depth string to a canonical Depth.

        Args:
            depth_str: Depth string (e.g., 'quick', 'full', 'q', 'f')

        Returns:
            Canonical Depth enum value

        Raises:
            ValueError: If depth is not supported
        """
        if depth_str is None:
            return Depth.STANDARD  # Default

        normalized = depth_str.lower().strip()

        if not normalized:
            return Depth.STANDARD  # Default

        # Check aliases first
        if normalized in self._alias_map:
            return self._alias_map[normalized]

        # Check canonical values
        if normalized in self._canonical_map:
            return self._canonical_map[normalized]

        # Not found
        supported = [d.value for d in sorted(self._supported, key=lambda x: x.value)]
        raise ValueError(
            f"Unknown depth: '{depth_str}'. "
            f"Supported depths: {', '.join(supported)}"
        )

    def get_profile(self, depth: Depth) -> DepthProfile:
        """Get depth profile for a depth value."""
        return self._profiles.get(depth, self._profiles[Depth.STANDARD])

    def get_multiplier(self, depth: Depth) -> float:
        """Get complexity multiplier for a depth."""
        return DEPTH_MULTIPLIERS.get(depth, 1.0)

    def get_supported_depths(self) -> Set[str]:
        """Get set of supported depth values."""
        return {d.value for d in self._supported}

    def is_full(self, depth: Depth) -> bool:
        """Check if depth requires full coverage audit."""
        return depth == Depth.FULL

    def is_deep(self, depth: Depth) -> bool:
        """Check if depth requires deep analysis."""
        return depth in (Depth.DEEP, Depth.FULL)
