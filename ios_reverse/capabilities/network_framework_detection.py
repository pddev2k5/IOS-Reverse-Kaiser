"""
Network Framework Detection Capability for IOS REVERSE KAISER.

CAP-021: network.framework_detection
"""

import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from ios_reverse.capabilities.base import (
    CapabilityExecutor, CapabilityContract, CapabilityResult,
    CapabilityStatus, ProvenanceRecord
)
from ios_reverse.adapters.analysis.network_adapter import NetworkAnalysisAdapter


class NetworkFrameworkDetectionContract(CapabilityContract):
    """Contract for CAP-021 network.framework_detection."""

    def __init__(self):
        super().__init__(
            id="network.framework_detection",
            version="1.0.0",
            domain="network",
            name="Network Framework Detection",
            description="Detect network framework presence and usage"
        )
        self.required_inputs = [
            {"name": "artifact_path", "type": "string", "required": True}
        ]
        self.optional_inputs = [
            {"name": "strings_data", "type": "string", "required": False},
            {"name": "objc_metadata", "type": "object", "required": False},
            {"name": "swift_metadata", "type": "object", "required": False},
            {"name": "component_id", "type": "string", "required": False},
        ]
        self.output_types = ["framework_presences"]
        self.error_codes = {
            "E001": {"name": "ARTIFACT_NOT_FOUND", "description": "Artifact not found"},
            "E002": {"name": "ANALYSIS_FAILED", "description": "Framework detection failed"},
        }


class NetworkFrameworkDetectionCapability(CapabilityExecutor):
    """
    CAP-021: Detect network framework presence and usage.

    Distinguishes:
    - Framework presence (binary includes the framework)
    - Framework usage (app actually uses the framework)

    Framework presence != confirmed usage.
    """

    def __init__(self):
        super().__init__()
        self._adapter = NetworkAnalysisAdapter()
        self._id_counter = 0

    def get_contract(self) -> CapabilityContract:
        return NetworkFrameworkDetectionContract()

    def _generate_id(self) -> str:
        self._id_counter += 1
        return f"net-fw-{self._id_counter:04d}"

    def validate_preconditions(self, inputs: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        artifact_path = inputs.get("artifact_path")
        if not artifact_path:
            return False, "artifact_path is required"
        if not os.path.exists(artifact_path):
            return False, f"Artifact not found: {artifact_path}"
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
            # Get inputs
            strings_data = inputs.get("strings_data", "")
            objc_metadata = inputs.get("objc_metadata")
            swift_metadata = inputs.get("swift_metadata")
            component_id = inputs.get("component_id")
            artifact_id = inputs.get("artifact_id")

            # Detect frameworks
            presences = self._adapter.detect_frameworks(
                strings_data, objc_metadata, swift_metadata,
                component_id, artifact_id
            )

            # Build result
            metadata = {
                "artifact_path": inputs["artifact_path"],
                "framework_count": len(presences),
                "presences": [p.to_dict() for p in presences],
                "component_id": component_id,
            }

            status = CapabilityStatus.SUCCESS
            if not presences:
                status = CapabilityStatus.PARTIAL

            return CapabilityResult(
                status=status,
                execution_id=execution_id,
                timestamp=timestamp,
                metadata=metadata,
                provenance=self._build_provenance(execution_id, inputs),
            )

        except Exception as e:
            return CapabilityResult(
                status=CapabilityStatus.FAILURE,
                execution_id=execution_id,
                timestamp=timestamp,
                metadata={},
                error_code="E002",
                error_message=str(e)
            )

    def _build_provenance(self, execution_id: str, inputs: Dict) -> ProvenanceRecord:
        return ProvenanceRecord(
            capability_id="network.framework_detection",
            capability_version="1.0.0",
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            inputs=inputs,
            adapter_id="network_analysis_adapter",
            adapter_version="1.0.0",
            working_directory=os.getcwd(),
        )
