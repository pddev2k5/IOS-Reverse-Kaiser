"""
Coverage Auditor Capability for IOS REVERSE KAISER.

CAP-031: coverage.calculation
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Set

from ios_reverse.capabilities.base import (
    CapabilityExecutor, CapabilityContract, CapabilityResult,
    CapabilityStatus, ProvenanceRecord
)
from ios_reverse.models.coverage import (
    CoverageState, CoverageDimension, CoverageTarget, CoverageTargetType,
    CoverageObservation, CoverageGap, CoverageSummary, CoverageAudit,
    CoverageGap as GapModel, GapSeverity,
    generate_target_id, generate_observation_id, generate_gap_id,
    dimension_to_capability
)
from ios_reverse.models.coverage_policy import CoveragePolicy, Workflow, Depth


class CoverageAuditorContract(CapabilityContract):
    """Contract for CAP-031 coverage.calculation."""

    def __init__(self):
        super().__init__(
            id="coverage.calculation",
            version="1.0.0",
            domain="coverage",
            name="Coverage Calculation",
            description="Calculate and audit analysis coverage"
        )
        self.required_inputs = [
            {"name": "workflow", "type": "string", "required": True},
            {"name": "depth", "type": "string", "required": True},
            {"Name": "eligible_targets", "type": "array", "required": True},
        ]
        self.optional_inputs = [
            {"name": "capability_results", "type": "array", "required": False},
            {"name": "observations", "type": "array", "required": False},
            {"name": "policy", "type": "object", "required": False},
        ]
        self.output_types = ["coverage_audit"]
        self.error_codes = {
            "E001": {"name": "INVALID_WORKFLOW", "description": "Invalid workflow"},
            "E002": {"name": "INVALID_DEPTH", "description": "Invalid depth"},
            "E003": {"name": "AUDIT_FAILED", "description": "Coverage audit failed"},
        }


class CoverageAuditorCapability(CapabilityExecutor):
    """
    CAP-031: Calculate and audit analysis coverage.

    Key principles:
    - Coverage percentages are meaningless without explicit denominators
    - NOT_ATTEMPTED != FAILED
    - execution_success != coverage_complete
    - No false 100% coverage
    """

    def __init__(self):
        super().__init__()
        self._id_counter = 0

    def get_contract(self) -> CapabilityContract:
        return CoverageAuditorContract()

    def _generate_id(self) -> str:
        self._id_counter += 1
        return f"cov-audit-{self._id_counter:04d}"

    def validate_preconditions(self, inputs: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        workflow = inputs.get("workflow")
        depth = inputs.get("depth")
        eligible_targets = inputs.get("eligible_targets", [])

        if not workflow:
            return False, "workflow is required"
        if not depth:
            return False, "depth is required"
        if not eligible_targets:
            return False, "eligible_targets is required"

        return True, None

    def execute(self, inputs: Dict[str, Any]) -> CapabilityResult:
        execution_id = self._generate_id()
        timestamp = datetime.utcnow()

        valid, error = self.validate_preconditions(inputs)
        if not valid:
            return CapabilityResult(
                status=CapabilityStatus.FAILURE,
                execution_id=execution_id,
                timestamp=timestamp,
                metadata={},
                error_code="E001",
                error_message=error
            )

        try:
            workflow = inputs["workflow"]
            depth = inputs["depth"]
            eligible_targets = inputs.get("eligible_targets", [])
            capability_results = inputs.get("capability_results", [])
            observations = inputs.get("observations", [])
            policy_override = inputs.get("policy")

            # Determine policy
            if policy_override:
                policy = CoveragePolicy(
                    workflow=Workflow(policy_override.get("workflow", workflow)),
                    depth=Depth(policy_override.get("depth", depth)),
                    required_dimensions=set(),
                )
            else:
                try:
                    policy = CoveragePolicy(
                        workflow=Workflow(workflow),
                        depth=Depth(depth),
                        required_dimensions=set(),
                    )
                except ValueError:
                    return CapabilityResult(
                        status=CapabilityStatus.FAILURE,
                        execution_id=execution_id,
                        timestamp=timestamp,
                        metadata={},
                        error_code="E001",
                        error_message=f"Invalid workflow: {workflow}"
                    )

            # Build audit
            audit = self._build_audit(
                workflow=workflow,
                depth=depth,
                eligible_targets=eligible_targets,
                capability_results=capability_results,
                observations=observations,
                policy=policy,
                execution_id=execution_id,
            )

            # Build result
            metadata = {
                "audit_id": audit.audit_id,
                "workflow": workflow,
                "depth": depth,
                "total_eligible_targets": len(audit.eligible_targets),
                "total_dimensions": len(audit.required_dimensions),
                "observation_count": len(audit.observations),
                "gap_count": len(audit.gaps),
                "blocking_gap_count": len(audit.get_blocking_gaps()),
                "execution_success": audit.summary.execution_success,
                "coverage_complete": audit.summary.coverage_complete,
                "target_coverage_rate": audit.summary.target_coverage_rate,
                "dimension_coverage_rate": audit.summary.dimension_coverage_rate,
                "successful_coverage_rate": audit.summary.successful_coverage_rate,
            }

            status = CapabilityStatus.SUCCESS
            warnings = []

            if not audit.summary.coverage_complete:
                warnings.append("Coverage incomplete - see gaps for details")

            if audit.summary.targets_not_attempted > 0:
                warnings.append(f"{audit.summary.targets_not_attempted} eligible targets were not attempted")

            return CapabilityResult(
                status=status,
                execution_id=execution_id,
                timestamp=timestamp,
                metadata=metadata,
                provenance=self._build_provenance(execution_id, inputs),
                warnings=warnings
            )

        except Exception as e:
            return CapabilityResult(
                status=CapabilityStatus.FAILURE,
                execution_id=execution_id,
                timestamp=timestamp,
                metadata={},
                error_code="E003",
                error_message=str(e)
            )

    def _build_audit(
        self,
        workflow: str,
        depth: str,
        eligible_targets: List[Dict],
        capability_results: List[Dict],
        observations: List[Dict],
        policy: CoveragePolicy,
        execution_id: str,
    ) -> CoverageAudit:
        """Build coverage audit from inputs."""

        # Parse eligible targets
        targets = []
        for target_data in eligible_targets:
            try:
                target = CoverageTarget(
                    target_id=generate_target_id(
                        target_data.get("path", ""),
                        target_data.get("architecture")
                    ),
                    target_type=CoverageTargetType(target_data.get("type", "executable")),
                    path=target_data.get("path", ""),
                    component_id=target_data.get("component_id"),
                    artifact_id=target_data.get("artifact_id"),
                    architecture=target_data.get("architecture"),
                    is_system_framework=target_data.get("is_system_framework", False),
                )
                targets.append(target)
            except (ValueError, KeyError):
                continue

        # Parse required dimensions from policy
        required_dimensions = list(policy.required_dimensions)

        # Parse observations
        parsed_observations = []
        for obs_data in observations:
            try:
                obs = CoverageObservation(
                    observation_id=obs_data.get("observation_id", generate_observation_id(
                        obs_data.get("target_id", ""),
                        CoverageDimension(obs_data.get("dimension", "binary"))
                    )),
                    target_id=obs_data.get("target_id", ""),
                    dimension=CoverageDimension(obs_data.get("dimension", "binary")),
                    state=CoverageState(obs_data.get("state", "unknown")),
                    evidence_count=obs_data.get("evidence_count", 0),
                    result_count=obs_data.get("result_count", 0),
                    error_message=obs_data.get("error_message"),
                    capability_id=obs_data.get("capability_id"),
                    capability_version=obs_data.get("capability_version"),
                    execution_id=obs_data.get("execution_id"),
                    timestamp=obs_data.get("timestamp"),
                )
                parsed_observations.append(obs)
            except (ValueError, KeyError):
                continue

        # Parse capability results into observations
        for result in capability_results:
            target_id = result.get("target_id", "unknown")
            capability_id = result.get("capability_id", "")

            # Map capability to dimensions
            cap_dims = self._capability_to_dimensions(capability_id)

            for dim in cap_dims:
                obs_id = generate_observation_id(target_id, dim)
                status_val = result.get("status", "unknown")
                state = self._status_to_state(status_val)

                obs = CoverageObservation(
                    observation_id=obs_id,
                    target_id=target_id,
                    dimension=dim,
                    state=state,
                    evidence_count=result.get("evidence_count", 0),
                    result_count=result.get("result_count", 0),
                    error_message=result.get("error_message"),
                    capability_id=capability_id,
                    capability_version=result.get("capability_version"),
                    execution_id=result.get("execution_id"),
                    timestamp=result.get("timestamp"),
                )
                parsed_observations.append(obs)

        # Build summary
        summary = self._build_summary(
            workflow=workflow,
            depth=depth,
            targets=targets,
            observations=parsed_observations,
            required_dimensions=required_dimensions,
        )

        # Identify gaps
        gaps = self._identify_gaps(
            targets=targets,
            observations=parsed_observations,
            required_dimensions=required_dimensions,
            summary=summary,
        )

        # Build audit
        audit = CoverageAudit(
            audit_id=f"audit-{execution_id}",
            workflow=workflow,
            depth=depth,
            timestamp=datetime.utcnow().isoformat(),
            eligible_targets=targets,
            required_dimensions=required_dimensions,
            observations=parsed_observations,
            gaps=gaps,
            summary=summary,
        )
        audit.build_indexes()

        return audit

    def _capability_to_dimensions(self, capability_id: str) -> List[CoverageDimension]:
        """Map capability ID to coverage dimensions."""
        mapping = {
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
            "network.framework_detection": [CoverageDimension.NETWORK],
            "architecture.detection": [CoverageDimension.ARCHITECTURE],
            "callflow.reconstruct": [CoverageDimension.CALLFLOW],
            "crypto.detection": [CoverageDimension.CRYPTO],
            "anti.analysis_detection": [CoverageDimension.ANTI_ANALYSIS],
        }
        return mapping.get(capability_id, [])

    def _status_to_state(self, status: str) -> CoverageState:
        """Map capability status to coverage state."""
        mapping = {
            "success": CoverageState.COVERED,
            "partial": CoverageState.PARTIAL,
            "failure": CoverageState.FAILED,
        }
        return mapping.get(status, CoverageState.UNKNOWN)

    def _build_summary(
        self,
        workflow: str,
        depth: str,
        targets: List[CoverageTarget],
        observations: List[CoverageObservation],
        required_dimensions: List[CoverageDimension],
    ) -> CoverageSummary:
        """Build coverage summary."""

        # Filter out system frameworks
        non_system_targets = [t for t in targets if not t.is_system_framework]

        summary = CoverageSummary(
            workflow=workflow,
            depth=depth,
            total_eligible_targets=len(targets),
            eligible_non_system_targets=len(non_system_targets),
            total_dimensions=len(required_dimensions),
        )

        # Index observations by target
        obs_by_target = {}
        for obs in observations:
            if obs.target_id not in obs_by_target:
                obs_by_target[obs.target_id] = []
            obs_by_target[obs.target_id].append(obs)

        # Count target states
        for target in targets:
            target_obs = obs_by_target.get(target.target_id, [])

            if not target_obs:
                summary.targets_not_attempted += 1
            else:
                # Determine overall state for this target
                states = [obs.state for obs in target_obs]
                if any(s == CoverageState.FAILED for s in states):
                    summary.targets_failed += 1
                elif any(s == CoverageState.PARTIAL for s in states):
                    summary.targets_partial += 1
                elif all(s == CoverageState.COVERED for s in states):
                    summary.targets_covered += 1
                elif any(s == CoverageState.NOT_APPLICABLE for s in states):
                    summary.targets_not_applicable += 1
                else:
                    summary.targets_unknown += 1

        # Build dimension summaries
        obs_by_dim = {}
        for obs in observations:
            dim_key = obs.dimension.value
            if dim_key not in obs_by_dim:
                obs_by_dim[dim_key] = []
            obs_by_dim[dim_key].append(obs)

        for dim in required_dimensions:
            dim_obs = obs_by_dim.get(dim.value, [])
            dim_summary = CoverageDimensionSummary(
                dimension=dim,
                total_targets=len(targets),
            )
            for obs in dim_obs:
                if obs.state == CoverageState.COVERED:
                    dim_summary.covered += 1
                elif obs.state == CoverageState.PARTIAL:
                    dim_summary.partial += 1
                elif obs.state == CoverageState.FAILED:
                    dim_summary.failed += 1
                elif obs.state == CoverageState.NOT_APPLICABLE:
                    dim_summary.not_applicable += 1
                elif obs.state == CoverageState.NOT_ATTEMPTED:
                    dim_summary.not_attempted += 1
                else:
                    dim_summary.unknown += 1

            summary.dimension_summaries[dim.value] = dim_summary

        # Compute rates
        summary.compute_rates()

        # Determine execution success and coverage complete
        summary.execution_success = summary.targets_failed == 0
        summary.coverage_complete = (
            summary.targets_not_attempted == 0 and
            summary.targets_failed == 0 and
            summary.targets_unknown == 0
        )

        return summary

    def _identify_gaps(
        self,
        targets: List[CoverageTarget],
        observations: List[CoverageObservation],
        required_dimensions: List[CoverageDimension],
        summary: CoverageSummary,
    ) -> List[CoverageGap]:
        """Identify coverage gaps."""
        gaps = []

        # Index observations
        obs_by_target = {}
        obs_by_dim = {}
        for obs in observations:
            # By target
            if obs.target_id not in obs_by_target:
                obs_by_target[obs.target_id] = []
            obs_by_target[obs.target_id].append(obs)

            # By dimension
            dim_key = obs.dimension.value
            if dim_key not in obs_by_dim:
                obs_by_dim[dim_key] = []
            obs_by_dim[dim_key].append(obs)

        # Identify missing targets
        observed_targets = set(obs_by_target.keys())
        all_targets = {t.target_id for t in targets}

        for target in targets:
            if target.target_id not in observed_targets:
                # Target was never attempted
                gap = CoverageGap(
                    gap_id=generate_gap_id(
                        CoverageDimension.BINARY,  # Use BINARY as default
                        target.target_id,
                        CoverageState.NOT_ATTEMPTED
                    ),
                    dimension=CoverageDimension.BINARY,
                    target_id=target.target_id,
                    state=CoverageState.NOT_ATTEMPTED,
                    reason="Target was eligible but never attempted",
                    severity=GapSeverity.BLOCKING if target.target_type == CoverageTargetType.EXECUTABLE else GapSeverity.WARNING,
                    is_blocking=target.target_type == CoverageTargetType.EXECUTABLE,
                    possible_action=f"Retry analysis for {target.path}",
                )
                gaps.append(gap)

        # Identify missing dimensions per target
        for target in targets:
            target_obs = obs_by_target.get(target.target_id, [])
            observed_dims = {obs.dimension for obs in target_obs}

            for dim in required_dimensions:
                if dim not in observed_dims:
                    # Dimension was not attempted for this target
                    gap = CoverageGap(
                        gap_id=generate_gap_id(dim, target.target_id, CoverageState.NOT_ATTEMPTED),
                        dimension=dim,
                        target_id=target.target_id,
                        state=CoverageState.NOT_ATTEMPTED,
                        reason=f"Dimension {dim.value} was not attempted for this target",
                        severity=GapSeverity.NON_BLOCKING,
                        capability_id=dimension_to_capability(dim),
                    )
                    gaps.append(gap)

        # Identify failed targets/dimensions
        for obs in observations:
            if obs.state == CoverageState.FAILED:
                gap = CoverageGap(
                    gap_id=generate_gap_id(obs.dimension, obs.target_id, CoverageState.FAILED),
                    dimension=obs.dimension,
                    target_id=obs.target_id,
                    state=CoverageState.FAILED,
                    reason=obs.error_message or "Analysis failed",
                    severity=GapSeverity.BLOCKING,
                    is_blocking=True,
                    capability_id=obs.capability_id,
                    possible_action=f"Retry capability {obs.capability_id}",
                    evidence_ids=[obs.observation_id],
                )
                gaps.append(gap)

        return gaps

    def _build_provenance(self, execution_id: str, inputs: Dict) -> ProvenanceRecord:
        """Build provenance record."""
        return ProvenanceRecord(
            capability_id="coverage.calculation",
            capability_version="1.0.0",
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            inputs=inputs,
            adapter_id="internal",
            adapter_version="1.0.0",
            working_directory="",
        )
