"""
Coverage Model for IOS REVERSE KAISER.

Provides normalized models for analysis coverage tracking and auditing.

IMPORTANT:
- Coverage percentages are meaningless without explicit denominators
- NOT_ATTEMPTED != FAILED
- execution_success != coverage_complete
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, Set


class CoverageState(Enum):
    """Coverage states for targets/dimensions."""
    COVERED = "covered"               # Successfully analyzed
    PARTIAL = "partial"              # Partially analyzed
    FAILED = "failed"                # Attempted but unsuccessful
    NOT_APPLICABLE = "not_applicable"  # Not applicable for this target
    NOT_ATTEMPTED = "not_attempted"   # Eligible but not attempted
    UNKNOWN = "unknown"              # Unknown state


class CoverageDimension(Enum):
    """Coverage dimensions corresponding to capabilities."""
    ARTIFACT = "artifact"
    BINARY = "binary"
    ARCHITECTURE_SLICE = "architecture_slice"
    MACHO_STRUCTURE = "macho_structure"
    LOAD_COMMANDS = "load_commands"
    IMPORTS = "imports"
    EXPORTS = "exports"
    SYMBOLS = "symbols"
    STRINGS = "strings"
    OBJC_METADATA = "objc_metadata"
    SWIFT_METADATA = "swift_metadata"
    FRAMEWORKS = "frameworks"
    DYLIBS = "dylibs"
    EXTENSIONS = "extensions"
    NETWORK = "network"
    ARCHITECTURE = "architecture"
    CALLFLOW = "callflow"
    CRYPTO = "crypto"
    ANTI_ANALYSIS = "anti_analysis"


class CoverageTargetType(Enum):
    """Types of coverage targets."""
    EXECUTABLE = "executable"
    FRAMEWORK = "framework"
    DYLIB = "dylib"
    EXTENSION = "extension"
    BUNDLE = "bundle"
    ARTIFACT = "artifact"


class GapSeverity(Enum):
    """Severity of coverage gaps."""
    BLOCKING = "blocking"           # Prevents full coverage
    NON_BLOCKING = "non_blocking"   # Does not prevent workflow completion
    WARNING = "warning"             # Informational only


@dataclass
class CoverageTarget:
    """A target eligible for coverage tracking."""
    target_id: str
    target_type: CoverageTargetType
    path: str
    component_id: Optional[str] = None
    artifact_id: Optional[str] = None
    architecture: Optional[str] = None  # e.g., "arm64", "armv7"
    is_system_framework: bool = False  # Exclude from coverage denominator

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_id": self.target_id,
            "target_type": self.target_type.value,
            "path": self.path,
            "component_id": self.component_id,
            "artifact_id": self.artifact_id,
            "architecture": self.architecture,
            "is_system_framework": self.is_system_framework,
        }


@dataclass
class CoverageObservation:
    """An observation about coverage for a target/dimension."""
    observation_id: str
    target_id: str
    dimension: CoverageDimension
    state: CoverageState

    # Details
    evidence_count: int = 0
    result_count: int = 0
    error_message: Optional[str] = None

    # Provenance
    capability_id: Optional[str] = None
    capability_version: Optional[str] = None
    execution_id: Optional[str] = None
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "target_id": self.target_id,
            "dimension": self.dimension.value,
            "state": self.state.value,
            "evidence_count": self.evidence_count,
            "result_count": self.result_count,
            "error_message": self.error_message,
            "capability_id": self.capability_id,
            "execution_id": self.execution_id,
            "timestamp": self.timestamp,
        }


@dataclass
class CoverageGap:
    """A gap in coverage."""
    gap_id: str
    dimension: CoverageDimension
    target_id: str
    state: CoverageState
    reason: str

    # Classification
    severity: GapSeverity = GapSeverity.NON_BLOCKING
    is_blocking: bool = False

    # Resolution
    capability_id: Optional[str] = None
    possible_action: Optional[str] = None

    # Provenance
    evidence_ids: List[str] = field(default_factory=list)
    provenance: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gap_id": self.gap_id,
            "dimension": self.dimension.value,
            "target_id": self.target_id,
            "state": self.state.value,
            "reason": self.reason,
            "severity": self.severity.value,
            "is_blocking": self.is_blocking,
            "capability_id": self.capability_id,
            "possible_action": self.possible_action,
            "evidence_count": len(self.evidence_ids),
            "provenance": self.provenance,
        }


@dataclass
class CoverageDimensionSummary:
    """Summary of coverage for a dimension."""
    dimension: CoverageDimension
    total_targets: int = 0
    covered: int = 0
    partial: int = 0
    failed: int = 0
    not_applicable: int = 0
    not_attempted: int = 0
    unknown: int = 0

    @property
    def coverage_rate(self) -> float:
        """Coverage rate as a fraction of applicable targets."""
        applicable = self.total_targets - self.not_applicable - self.not_attempted
        if applicable == 0:
            return 1.0
        return self.covered / applicable if applicable > 0 else 0.0

    @property
    def coverage_percentage(self) -> str:
        """Coverage rate as percentage string."""
        return f"{self.coverage_rate * 100:.1f}%"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension.value,
            "total_targets": self.total_targets,
            "covered": self.covered,
            "partial": self.partial,
            "failed": self.failed,
            "not_applicable": self.not_applicable,
            "not_attempted": self.not_attempted,
            "unknown": self.unknown,
            "coverage_rate": self.coverage_rate,
            "coverage_percentage": self.coverage_percentage,
        }


@dataclass
class CoverageSummary:
    """Complete coverage summary."""
    workflow: str
    depth: str

    # Counts
    total_eligible_targets: int = 0
    eligible_non_system_targets: int = 0
    total_dimensions: int = 0

    # Target coverage
    targets_covered: int = 0
    targets_partial: int = 0
    targets_failed: int = 0
    targets_not_applicable: int = 0
    targets_not_attempted: int = 0
    targets_unknown: int = 0

    # Dimension summaries
    dimension_summaries: Dict[str, CoverageDimensionSummary] = field(default_factory=dict)

    # Computed metrics
    target_coverage_rate: float = 0.0
    dimension_coverage_rate: float = 0.0
    successful_coverage_rate: float = 0.0

    # Overall determination
    execution_success: bool = False
    coverage_complete: bool = False

    def compute_rates(self):
        """Compute coverage rates."""
        # Target coverage: percentage of ALL eligible targets that were covered
        # NOT_ATTEMPTED is NOT subtracted from denominator - they count as uncovered
        eligible = self.total_eligible_targets - self.targets_not_applicable
        if eligible > 0:
            self.target_coverage_rate = self.targets_covered / eligible
        else:
            self.target_coverage_rate = 1.0

        # Dimension coverage
        if self.total_dimensions > 0:
            fully_covered_dims = sum(1 for s in self.dimension_summaries.values()
                                    if s.unknown == 0 and s.failed == 0 and s.not_attempted == 0)
            self.dimension_coverage_rate = fully_covered_dims / self.total_dimensions

        # Successful coverage (what was attempted and succeeded)
        attempted = self.targets_covered + self.targets_partial + self.targets_failed
        if attempted > 0:
            self.successful_coverage_rate = self.targets_covered / attempted

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow": self.workflow,
            "depth": self.depth,
            "total_eligible_targets": self.total_eligible_targets,
            "eligible_non_system_targets": self.eligible_non_system_targets,
            "total_dimensions": self.total_dimensions,
            "targets_covered": self.targets_covered,
            "targets_partial": self.targets_partial,
            "targets_failed": self.targets_failed,
            "targets_not_applicable": self.targets_not_applicable,
            "targets_not_attempted": self.targets_not_attempted,
            "targets_unknown": self.targets_unknown,
            "target_coverage_rate": self.target_coverage_rate,
            "dimension_coverage_rate": self.dimension_coverage_rate,
            "successful_coverage_rate": self.successful_coverage_rate,
            "execution_success": self.execution_success,
            "coverage_complete": self.coverage_complete,
            "dimension_summaries": {k: v.to_dict() for k, v in self.dimension_summaries.items()},
        }


@dataclass
class CoverageAudit:
    """
    Complete coverage audit.

    Captures the full picture of what was and was not analyzed.
    """
    audit_id: str
    workflow: str
    depth: str
    timestamp: str

    # Eligible scope
    eligible_targets: List[CoverageTarget] = field(default_factory=list)
    required_dimensions: List[CoverageDimension] = field(default_factory=list)

    # Observations
    observations: List[CoverageObservation] = field(default_factory=list)

    # Gaps
    gaps: List[CoverageGap] = field(default_factory=list)

    # Summary
    summary: Optional[CoverageSummary] = None

    # Indexes
    _obs_by_target: Dict[str, List[CoverageObservation]] = field(default_factory=dict, repr=False)
    _obs_by_dimension: Dict[str, List[CoverageObservation]] = field(default_factory=dict, repr=False)
    _gap_by_id: Dict[str, CoverageGap] = field(default_factory=dict, repr=False)

    def build_indexes(self):
        """Build lookup indexes."""
        self._obs_by_target = {}
        self._obs_by_dimension = {}

        for obs in self.observations:
            # By target
            if obs.target_id not in self._obs_by_target:
                self._obs_by_target[obs.target_id] = []
            self._obs_by_target[obs.target_id].append(obs)

            # By dimension
            dim_key = obs.dimension.value
            if dim_key not in self._obs_by_dimension:
                self._obs_by_dimension[dim_key] = []
            self._obs_by_dimension[dim_key].append(obs)

        # Gap index
        self._gap_by_id = {g.gap_id: g for g in self.gaps}

    def get_observations_for_target(self, target_id: str) -> List[CoverageObservation]:
        """Get all observations for a target."""
        return self._obs_by_target.get(target_id, [])

    def get_observations_for_dimension(self, dimension: CoverageDimension) -> List[CoverageObservation]:
        """Get all observations for a dimension."""
        return self._obs_by_dimension.get(dimension.value, [])

    def get_gap(self, gap_id: str) -> Optional[CoverageGap]:
        """Get gap by ID."""
        return self._gap_by_id.get(gap_id)

    def get_blocking_gaps(self) -> List[CoverageGap]:
        """Get all blocking gaps."""
        return [g for g in self.gaps if g.is_blocking]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "workflow": self.workflow,
            "depth": self.depth,
            "timestamp": self.timestamp,
            "eligible_target_count": len(self.eligible_targets),
            "required_dimension_count": len(self.required_dimensions),
            "observation_count": len(self.observations),
            "gap_count": len(self.gaps),
            "blocking_gap_count": len(self.get_blocking_gaps()),
            "summary": self.summary.to_dict() if self.summary else None,
        }


# Helper functions

def generate_target_id(path: str, arch: Optional[str] = None) -> str:
    """Generate deterministic target ID."""
    import hashlib
    content = f"{path}:{arch}" if arch else path
    hash_val = hashlib.sha256(content.encode()).hexdigest()[:16]
    return f"target-{hash_val}"


def generate_observation_id(target_id: str, dimension: CoverageDimension) -> str:
    """Generate deterministic observation ID."""
    import hashlib
    content = f"{target_id}:{dimension.value}"
    hash_val = hashlib.sha256(content.encode()).hexdigest()[:16]
    return f"obs-{hash_val}"


def generate_gap_id(dimension: CoverageDimension, target_id: str, state: CoverageState) -> str:
    """Generate deterministic gap ID."""
    import hashlib
    content = f"{dimension.value}:{target_id}:{state.value}"
    hash_val = hashlib.sha256(content.encode()).hexdigest()[:16]
    return f"gap-{hash_val}"


def dimension_to_capability(dimension: CoverageDimension) -> Optional[str]:
    """Map coverage dimension to capability ID."""
    mapping = {
        CoverageDimension.ARTIFACT: "foundation.artifact_detect",
        CoverageDimension.BINARY: "macho.basic",
        CoverageDimension.ARCHITECTURE_SLICE: "macho.slices",
        CoverageDimension.MACHO_STRUCTURE: "macho.load_commands",
        CoverageDimension.LOAD_COMMANDS: "macho.load_commands",
        CoverageDimension.IMPORTS: "binary.imports",
        CoverageDimension.EXPORTS: "binary.exports",
        CoverageDimension.SYMBOLS: "binary.symbols",
        CoverageDimension.STRINGS: "binary.strings",
        CoverageDimension.OBJC_METADATA: "objc.metadata",
        CoverageDimension.SWIFT_METADATA: "swift.metadata",
        CoverageDimension.FRAMEWORKS: "framework.inventory",
        CoverageDimension.DYLIBS: "dylib.inventory",
        CoverageDimension.EXTENSIONS: "extension.inventory",
        CoverageDimension.NETWORK: "network.endpoint_discovery",
        CoverageDimension.ARCHITECTURE: "architecture.detection",
        CoverageDimension.CALLFLOW: "callflow.reconstruct",
        CoverageDimension.CRYPTO: "crypto.detection",
        CoverageDimension.ANTI_ANALYSIS: "anti.analysis_detection",
    }
    return mapping.get(dimension)


def capability_to_dimensions(capability_id: str) -> List[CoverageDimension]:
    """Map capability to coverage dimensions."""
    reverse_mapping = {
        "foundation.artifact_detect": [CoverageDimension.ARTIFACT],
        "macho.basic": [CoverageDimension.BINARY],
        "macho.slices": [CoverageDimension.ARCHITECTURE_SLICE],
        "macho.load_commands": [CoverageDimension.MACHO_STRUCTURE, CoverageDimension.LOAD_COMMANDS],
        "binary.imports": [CoverageDimension.IMPORTS],
        "binary.exports": [CoverageDimension.EXPORTS],
        "binary.symbols": [CoverageDimension.SYMBOLS],
        "binary.strings": [CoverageDimension.STRINGS],
        "objc.metadata": [CoverageDimension.OBJC_METADATA],
        "swift.metadata": [CoverageDimension.SWIFT_METADATA],
        "framework.inventory": [CoverageDimension.FRAMEWORKS],
        "dylib.inventory": [CoverageDimension.DYLIBS],
        "extension.inventory": [CoverageDimension.EXTENSIONS],
        "network.endpoint_discovery": [CoverageDimension.NETWORK],
        "architecture.detection": [CoverageDimension.ARCHITECTURE],
        "callflow.reconstruct": [CoverageDimension.CALLFLOW],
        "crypto.detection": [CoverageDimension.CRYPTO],
        "anti.analysis_detection": [CoverageDimension.ANTI_ANALYSIS],
    }
    return reverse_mapping.get(capability_id, [])
