"""
Network Endpoint Discovery Capability for IOS REVERSE KAISER.

CAP-022: network.endpoint_discovery
"""

import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from ios_reverse.capabilities.base import (
    CapabilityExecutor, CapabilityContract, CapabilityResult,
    CapabilityStatus, ProvenanceRecord
)
from ios_reverse.adapters.analysis.network_adapter import NetworkAnalysisAdapter


class NetworkEndpointDiscoveryContract(CapabilityContract):
    """Contract for CAP-022 network.endpoint_discovery."""

    def __init__(self):
        super().__init__(
            id="network.endpoint_discovery",
            version="1.0.0",
            domain="network",
            name="Network Endpoint Discovery",
            description="Discover network endpoint candidates from evidence"
        )
        self.required_inputs = [
            {"name": "strings_data", "type": "string", "required": True}
        ]
        self.optional_inputs = [
            {"name": "objc_metadata", "type": "object", "required": False},
            {"name": "swift_metadata", "type": "object", "required": False},
            {"name": "component_ids", "type": "array", "required": False},
        ]
        self.output_types = ["endpoint_candidates", "path_candidates"]
        self.error_codes = {
            "E001": {"name": "ANALYSIS_FAILED", "description": "Endpoint discovery failed"},
        }


class NetworkEndpointDiscoveryCapability(CapabilityExecutor):
    """
    CAP-022: Discover network endpoint candidates.

    Distinguishes evidence strength:
    - STRING_HINT: Found in strings only
    - REFERENCE: Referenced by code
    - STRUCTURAL: From parsing
    - CORRELATED: Correlated with other evidence
    - VERIFIED: Confirmed by analysis

    Does NOT promote STRING_HINT to VERIFIED without evidence.
    """

    def __init__(self):
        super().__init__()
        self._adapter = NetworkAnalysisAdapter()
        self._id_counter = 0

    def get_contract(self) -> CapabilityContract:
        return NetworkEndpointDiscoveryContract()

    def _generate_id(self) -> str:
        self._id_counter += 1
        return f"net-ep-{self._id_counter:04d}"

    def validate_preconditions(self, inputs):
        # No file path validation needed - works with strings
        return True, None

    def execute(self, inputs: Dict[str, Any]) -> CapabilityResult:
        execution_id = self._generate_id()
        timestamp = datetime.utcnow()

        try:
            # Get inputs
            strings_data = inputs.get("strings_data", "")
            objc_metadata = inputs.get("objc_metadata")
            swift_metadata = inputs.get("swift_metadata")
            component_ids = inputs.get("component_ids", [])
            artifact_ids = inputs.get("artifact_ids", [])

            if not strings_data:
                return CapabilityResult(
                    status=CapabilityStatus.FAILURE,
                    execution_id=execution_id,
                    timestamp=timestamp,
                    metadata={},
                    error_code="E001",
                    error_message="strings_data is required"
                )

            # Discover endpoints
            endpoints, paths = self._adapter.discover_endpoints(
                strings_data, objc_metadata, swift_metadata,
                component_ids, artifact_ids
            )

            # Discover headers
            headers = self._adapter.discover_headers(strings_data)

            # Discover request builders
            builders = self._adapter.discover_request_builders(
                objc_metadata, swift_metadata,
                component_ids[0] if component_ids else None
            )

            # Build result
            metadata = {
                "endpoint_count": len(endpoints),
                "path_count": len(paths),
                "header_count": len(headers),
                "builder_count": len(builders),
                "endpoints": [e.to_dict() for e in endpoints],
                "paths": [p.to_dict() for p in paths],
                "headers": [h.to_dict() for h in headers],
                "builders": [b.to_dict() for b in builders],
                "evidence_distribution": {
                    "string_hint": sum(1 for e in endpoints if e.evidence_strength.value == "string_hint"),
                    "reference": sum(1 for e in endpoints if e.evidence_strength.value == "reference"),
                    "structural": sum(1 for e in endpoints if e.evidence_strength.value == "structural"),
                },
            }

            status = CapabilityStatus.SUCCESS
            warnings = []
            if not endpoints:
                warnings.append("No endpoint candidates discovered")

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
                error_code="E001",
                error_message=str(e)
            )

    def _build_provenance(self, execution_id: str, inputs: Dict) -> ProvenanceRecord:
        return ProvenanceRecord(
            capability_id="network.endpoint_discovery",
            capability_version="1.0.0",
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            inputs=inputs,
            adapter_id="network_analysis_adapter",
            adapter_version="1.0.0",
            working_directory=os.getcwd(),
        )
