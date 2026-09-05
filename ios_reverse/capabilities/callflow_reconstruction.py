"""
Callflow Reconstruction Capability for IOS REVERSE KAISER.

CAP-026: callflow.reconstruct
"""

import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from ios_reverse.capabilities.base import (
    CapabilityExecutor, CapabilityContract, CapabilityResult,
    CapabilityStatus, ProvenanceRecord
)
from ios_reverse.adapters.analysis.callflow_adapter import CallflowAnalysisAdapter


class CallflowReconstructContract(CapabilityContract):
    """Contract for CAP-026 callflow.reconstruct."""

    def __init__(self):
        super().__init__(
            id="callflow.reconstruct",
            version="1.0.0",
            domain="callflow",
            name="Callflow Reconstruction",
            description="Reconstruct call flow from metadata"
        )
        self.required_inputs = [
            {"name": "objc_metadata", "type": "object", "required": False},
            {"name": "swift_metadata", "type": "object", "required": False},
        ]
        self.optional_inputs = [
            {"name": "strings_data", "type": "string", "required": False},
            {"name": "symbols", "type": "array", "required": False},
            {"name": "network_endpoints", "type": "array", "required": False},
            {"name": "component_id", "type": "string", "required": False},
            {"name": "artifact_id", "type": "string", "required": False},
        ]
        self.output_types = ["callflow_model"]
        self.error_codes = {
            "E001": {"name": "ANALYSIS_FAILED", "description": "Callflow reconstruction failed"},
        }


class CallflowReconstructCapability(CapabilityExecutor):
    """
    CAP-026: Reconstruct call flow from metadata.

    Anchor-driven reconstruction:
    1. Create anchors from endpoints, selectors, functions
    2. Create nodes from methods/functions
    3. Link anchors to nodes
    4. Reconstruct edges with evidence

    IMPORTANT:
    - Confirmed calls require strong evidence
    - References are not confirmed calls
    - Unresolved targets remain explicit
    """

    def __init__(self):
        super().__init__()
        self._adapter = CallflowAnalysisAdapter()
        self._id_counter = 0

    def get_contract(self) -> CapabilityContract:
        return CallflowReconstructContract()

    def _generate_id(self) -> str:
        self._id_counter += 1
        return f"cf-rec-{self._id_counter:04d}"

    def validate_preconditions(self, inputs):
        # Works with metadata inputs
        return True, None

    def execute(self, inputs: Dict[str, Any]) -> CapabilityResult:
        execution_id = self._generate_id()
        timestamp = datetime.utcnow()

        try:
            strings_data = inputs.get("strings_data", "")
            objc_metadata = inputs.get("objc_metadata")
            swift_metadata = inputs.get("swift_metadata")
            symbols = inputs.get("symbols", [])
            network_endpoints = inputs.get("network_endpoints", [])
            component_id = inputs.get("component_id")
            artifact_id = inputs.get("artifact_id")
            artifact_path = inputs.get("artifact_path", "")

            # Build model
            model = self._adapter.build_model(
                strings_data=strings_data,
                objc_metadata=objc_metadata,
                swift_metadata=swift_metadata,
                symbols=symbols,
                network_endpoints=network_endpoints,
                component_id=component_id,
                artifact_id=artifact_id,
                artifact_path=artifact_path
            )

            # Build result
            metadata = {
                "artifact_path": artifact_path,
                "anchor_count": len(model.anchors),
                "node_count": len(model.nodes),
                "edge_count": len(model.edges),
                "unresolved_count": len(model.unresolved),
                "confirmed_call_count": model.confirmed_call_count,
                "reference_count": model.reference_count,
                "anchors": [a.to_dict() for a in model.anchors[:50]],  # Limit
                "nodes": [n.to_dict() for n in model.nodes[:100]],  # Limit
                "edges": [e.to_dict() for e in model.edges[:100]],  # Limit
                "unresolved": [u.to_dict() for u in model.unresolved[:50]],  # Limit
            }

            status = CapabilityStatus.SUCCESS
            if len(model.unresolved) > len(model.edges):
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
            capability_id="callflow.reconstruct",
            capability_version="1.0.0",
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            inputs=inputs,
            adapter_id="callflow_analysis_adapter",
            adapter_version="1.0.0",
            working_directory=os.getcwd(),
        )
