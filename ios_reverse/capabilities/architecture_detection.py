"""
Architecture Detection Capability for IOS REVERSE KAISER.

CAP-024: architecture.detection
"""

import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from ios_reverse.capabilities.base import (
    CapabilityExecutor, CapabilityContract, CapabilityResult,
    CapabilityStatus, ProvenanceRecord
)
from ios_reverse.adapters.analysis.architecture_adapter import ArchitectureAnalysisAdapter


class ArchitectureDetectionContract(CapabilityContract):
    """Contract for CAP-024 architecture.detection."""

    def __init__(self):
        super().__init__(
            id="architecture.detection",
            version="1.0.0",
            domain="architecture",
            name="Architecture Detection",
            description="Detect application architecture components"
        )
        self.required_inputs = [
            {"name": "objc_metadata", "type": "object", "required": False},
            {"name": "swift_metadata", "type": "object", "required": False},
        ]
        self.optional_inputs = [
            {"name": "component_ids", "type": "array", "required": False},
        ]
        self.output_types = ["architecture_components"]
        self.error_codes = {
            "E001": {"name": "ANALYSIS_FAILED", "description": "Architecture detection failed"},
        }


class ArchitectureDetectionCapability(CapabilityExecutor):
    """
    CAP-024: Detect application architecture components.

    IMPORTANT: This detects LOGICAL architecture roles (Service, ViewController, etc.),
    NOT physical components (Framework, Dylib from P04.4).
    """

    def __init__(self):
        super().__init__()
        self._adapter = ArchitectureAnalysisAdapter()
        self._id_counter = 0

    def get_contract(self) -> CapabilityContract:
        return ArchitectureDetectionContract()

    def _generate_id(self) -> str:
        self._id_counter += 1
        return f"arch-det-{self._id_counter:04d}"

    def validate_preconditions(self, inputs):
        # Needs metadata inputs
        if not inputs.get("objc_metadata") and not inputs.get("swift_metadata"):
            return False, "objc_metadata or swift_metadata required"
        return True, None

    def execute(self, inputs: Dict[str, Any]) -> CapabilityResult:
        execution_id = self._generate_id()
        timestamp = datetime.utcnow()

        try:
            objc_metadata = inputs.get("objc_metadata")
            swift_metadata = inputs.get("swift_metadata")
            component_ids = inputs.get("component_ids")

            if not objc_metadata and not swift_metadata:
                return CapabilityResult(
                    status=CapabilityStatus.FAILURE,
                    execution_id=execution_id,
                    timestamp=timestamp,
                    metadata={},
                    error_code="E001",
                    error_message="objc_metadata or swift_metadata required"
                )

            # Build model
            model = self._adapter.build_model(
                objc_metadata, swift_metadata, component_ids
            )

            # Build result
            metadata = {
                "component_count": len(model.components),
                "components": [c.to_dict() for c in model.components],
                "role_distribution": model.role_distribution,
                "evidence_level_distribution": model.evidence_level_distribution,
            }

            status = CapabilityStatus.SUCCESS
            if not model.components:
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
                error_code="E001",
                error_message=str(e)
            )

    def _build_provenance(self, execution_id: str, inputs: Dict) -> ProvenanceRecord:
        return ProvenanceRecord(
            capability_id="architecture.detection",
            capability_version="1.0.0",
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            inputs=inputs,
            adapter_id="architecture_analysis_adapter",
            adapter_version="1.0.0",
            working_directory=os.getcwd(),
        )
