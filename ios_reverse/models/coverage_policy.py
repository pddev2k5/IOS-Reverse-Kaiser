"""
Coverage Policy for IOS REVERSE KAISER.

Provides declarative coverage policies for different workflows and depths.
"""

from dataclasses import dataclass, field
from typing import List, Set, Dict, Any
from enum import Enum

from ios_reverse.models.coverage import CoverageDimension


class Workflow(Enum):
    """Available workflows."""
    UNPACK = "unpack"
    DUMP = "dump"
    STANDARD = "standard"
    FULL = "full"
    NETWORK = "network"
    CRYPTO = "crypto"


class Depth(Enum):
    """Analysis depth profiles."""
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"
    FULL = "full"


# Standard dimension sets
BINARY_DIMENSIONS = {
    CoverageDimension.BINARY,
    CoverageDimension.ARCHITECTURE_SLICE,
    CoverageDimension.MACHO_STRUCTURE,
    CoverageDimension.LOAD_COMMANDS,
}

METADATA_DIMENSIONS = {
    CoverageDimension.IMPORTS,
    CoverageDimension.EXPORTS,
    CoverageDimension.SYMBOLS,
    CoverageDimension.STRINGS,
}

CODE_DIMENSIONS = {
    CoverageDimension.OBJC_METADATA,
    CoverageDimension.SWIFT_METADATA,
}

COMPONENT_DIMENSIONS = {
    CoverageDimension.FRAMEWORKS,
    CoverageDimension.DYLIBS,
    CoverageDimension.EXTENSIONS,
}

ANALYSIS_DIMENSIONS = {
    CoverageDimension.NETWORK,
    CoverageDimension.ARCHITECTURE,
    CoverageDimension.CALLFLOW,
    CoverageDimension.CRYPTO,
    CoverageDimension.ANTI_ANALYSIS,
}

# Quick: Only essential binary info
QUICK_DIMENSIONS = {
    CoverageDimension.ARTIFACT,
    CoverageDimension.BINARY,
}

# Standard: Binary + Metadata
STANDARD_DIMENSIONS = BINARY_DIMENSIONS | METADATA_DIMENSIONS

# Deep: Standard + Code + Components
DEEP_DIMENSIONS = STANDARD_DIMENSIONS | CODE_DIMENSIONS | COMPONENT_DIMENSIONS

# Full: Everything
FULL_DIMENSIONS = DEEP_DIMENSIONS | ANALYSIS_DIMENSIONS

# Network: Network-focused
NETWORK_DIMENSIONS = BINARY_DIMENSIONS | {CoverageDimension.NETWORK}

# Crypto: Crypto-focused
CRYPTO_DIMENSIONS = BINARY_DIMENSIONS | {CoverageDimension.CRYPTO}

# Anti-analysis
ANTI_ANALYSIS_DIMENSIONS = BINARY_DIMENSIONS | {CoverageDimension.ANTI_ANALYSIS}


@dataclass
class CoveragePolicy:
    """
    Declarative coverage policy.

    Defines what dimensions are required for a given workflow/depth combination.
    """
    workflow: Workflow
    depth: Depth
    required_dimensions: Set[CoverageDimension]
    optional_dimensions: Set[CoverageDimension] = field(default_factory=set)

    # Target set
    target_all_executables: bool = True
    target_embedded_only: bool = False

    # Failure handling
    allow_partial: bool = True
    fail_on_missing_required: bool = True

    def get_required_dimensions(self) -> List[CoverageDimension]:
        """Get sorted list of required dimensions."""
        return sorted(self.required_dimensions, key=lambda d: d.value)

    def requires_dimension(self, dimension: CoverageDimension) -> bool:
        """Check if dimension is required."""
        return dimension in self.required_dimensions

    def is_optional(self, dimension: CoverageDimension) -> bool:
        """Check if dimension is optional."""
        return dimension in self.optional_dimensions

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow": self.workflow.value,
            "depth": self.depth.value,
            "required_dimensions": [d.value for d in self.required_dimensions],
            "optional_dimensions": [d.value for d in self.optional_dimensions],
            "target_all_executables": self.target_all_executables,
            "target_embedded_only": self.target_embedded_only,
            "allow_partial": self.allow_partial,
            "fail_on_missing_required": self.fail_on_missing_required,
        }


# Predefined policies
POLICIES: Dict[str, CoveragePolicy] = {
    # Unpack: Minimal extraction
    "unpack.quick": CoveragePolicy(
        workflow=Workflow.UNPACK,
        depth=Depth.QUICK,
        required_dimensions=QUICK_DIMENSIONS,
        allow_partial=True,
        fail_on_missing_required=False,
    ),
    "unpack.standard": CoveragePolicy(
        workflow=Workflow.UNPACK,
        depth=Depth.STANDARD,
        required_dimensions=QUICK_DIMENSIONS | BINARY_DIMENSIONS,
        allow_partial=True,
        fail_on_missing_required=False,
    ),

    # Dump: Standard binary analysis
    "dump.quick": CoveragePolicy(
        workflow=Workflow.DUMP,
        depth=Depth.QUICK,
        required_dimensions=BINARY_DIMENSIONS,
        allow_partial=True,
        fail_on_missing_required=False,
    ),
    "dump.standard": CoveragePolicy(
        workflow=Workflow.DUMP,
        depth=Depth.STANDARD,
        required_dimensions=STANDARD_DIMENSIONS,
        allow_partial=True,
        fail_on_missing_required=True,
    ),
    "dump.full": CoveragePolicy(
        workflow=Workflow.DUMP,
        depth=Depth.FULL,
        required_dimensions=DEEP_DIMENSIONS,
        allow_partial=False,
        fail_on_missing_required=True,
    ),

    # Standard: Default analysis
    "standard.quick": CoveragePolicy(
        workflow=Workflow.STANDARD,
        depth=Depth.QUICK,
        required_dimensions=BINARY_DIMENSIONS,
        allow_partial=True,
        fail_on_missing_required=False,
    ),
    "standard.standard": CoveragePolicy(
        workflow=Workflow.STANDARD,
        depth=Depth.STANDARD,
        required_dimensions=STANDARD_DIMENSIONS,
        allow_partial=True,
        fail_on_missing_required=True,
    ),
    "standard.deep": CoveragePolicy(
        workflow=Workflow.STANDARD,
        depth=Depth.DEEP,
        required_dimensions=DEEP_DIMENSIONS,
        allow_partial=False,
        fail_on_missing_required=True,
    ),
    "standard.full": CoveragePolicy(
        workflow=Workflow.STANDARD,
        depth=Depth.FULL,
        required_dimensions=FULL_DIMENSIONS,
        allow_partial=False,
        fail_on_missing_required=True,
    ),

    # Full: Maximum coverage
    "full.full": CoveragePolicy(
        workflow=Workflow.FULL,
        depth=Depth.FULL,
        required_dimensions=FULL_DIMENSIONS,
        allow_partial=False,
        fail_on_missing_required=True,
    ),

    # Network: Network-focused
    "network.standard": CoveragePolicy(
        workflow=Workflow.NETWORK,
        depth=Depth.STANDARD,
        required_dimensions=NETWORK_DIMENSIONS,
        allow_partial=True,
        fail_on_missing_required=True,
    ),
    "network.full": CoveragePolicy(
        workflow=Workflow.NETWORK,
        depth=Depth.FULL,
        required_dimensions=NETWORK_DIMENSIONS | ANALYSIS_DIMENSIONS,
        allow_partial=False,
        fail_on_missing_required=True,
    ),

    # Crypto: Crypto-focused
    "crypto.standard": CoveragePolicy(
        workflow=Workflow.CRYPTO,
        depth=Depth.STANDARD,
        required_dimensions=CRYPTO_DIMENSIONS,
        allow_partial=True,
        fail_on_missing_required=True,
    ),
    "crypto.full": CoveragePolicy(
        workflow=Workflow.CRYPTO,
        depth=Depth.FULL,
        required_dimensions=CRYPTO_DIMENSIONS | ANALYSIS_DIMENSIONS,
        allow_partial=False,
        fail_on_missing_required=True,
    ),
}


def get_policy(workflow: Workflow, depth: Depth) -> CoveragePolicy:
    """Get coverage policy for workflow/depth combination."""
    key = f"{workflow.value}.{depth.value}"
    return POLICIES.get(key, CoveragePolicy(
        workflow=workflow,
        depth=depth,
        required_dimensions=set(),
    ))


def get_all_policies() -> Dict[str, CoveragePolicy]:
    """Get all available policies."""
    return POLICIES.copy()
