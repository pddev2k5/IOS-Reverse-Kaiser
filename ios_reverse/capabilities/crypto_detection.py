"""
Crypto Detection Capability for IOS REVERSE KAISER.

CAP-028: crypto.detection
"""

import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from ios_reverse.capabilities.base import (
    CapabilityExecutor, CapabilityContract, CapabilityResult,
    CapabilityStatus, ProvenanceRecord
)
from ios_reverse.adapters.analysis.crypto_adapter import CryptoAnalysisAdapter


class CryptoDetectionContract(CapabilityContract):
    """Contract for CAP-028 crypto.detection."""

    def __init__(self):
        super().__init__(
            id="crypto.detection",
            version="1.0.0",
            domain="crypto",
            name="Crypto Detection",
            description="Detect cryptographic operations and library presence"
        )
        self.required_inputs = [
            {"name": "artifact_path", "type": "string", "required": True}
        ]
        self.optional_inputs = [
            {"name": "imports", "type": "array", "required": False},
            {"name": "symbols", "type": "array", "required": False},
            {"name": "strings_data", "type": "string", "required": False},
            {"name": "objc_metadata", "type": "object", "required": False},
            {"name": "component_id", "type": "string", "required": False},
        ]
        self.output_types = ["crypto_model"]
        self.error_codes = {
            "E001": {"name": "ARTIFACT_NOT_FOUND", "description": "Artifact not found"},
            "E002": {"name": "ANALYSIS_FAILED", "description": "Crypto detection failed"},
        }


class CryptoDetectionCapability(CapabilityExecutor):
    """
    CAP-028: Detect cryptographic operations and library presence.

    IMPORTANT:
    - Library presence != confirmed usage
    - String "AES" alone is STRING_HINT
    - Does not fabricate parameters or key material
    """

    def __init__(self):
        super().__init__()
        self._adapter = CryptoAnalysisAdapter()
        self._id_counter = 0

    def get_contract(self) -> CapabilityContract:
        return CryptoDetectionContract()

    def _generate_id(self) -> str:
        self._id_counter += 1
        return f"crypto-det-{self._id_counter:04d}"

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
            imports = inputs.get("imports", [])
            symbols = inputs.get("symbols", [])
            strings_data = inputs.get("strings_data", "")
            objc_metadata = inputs.get("objc_metadata")
            component_id = inputs.get("component_id")
            artifact_id = inputs.get("artifact_id")

            # Build model
            model = self._adapter.build_model(
                imports=imports,
                symbols=symbols,
                strings_data=strings_data,
                objc_metadata=objc_metadata,
                component_id=component_id,
                artifact_id=artifact_id,
                artifact_path=inputs["artifact_path"]
            )

            # Build result
            metadata = {
                "artifact_path": inputs["artifact_path"],
                "library_presence_count": len(model.library_presences),
                "operation_count": len(model.operations),
                "primitive_distribution": model.primitive_distribution,
                "algorithm_distribution": model.algorithm_distribution,
                "evidence_level_distribution": model.evidence_level_distribution,
                "library_presences": [r.to_dict() for r in model.library_presences[:20]],
                "operations": [o.to_dict() for o in model.operations[:50]],
            }

            status = CapabilityStatus.SUCCESS
            warnings = []

            # Empty result is valid
            if not model.operations and not model.library_presences:
                warnings.append("No crypto evidence detected")

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
                error_code="E002",
                error_message=str(e)
            )

    def _build_provenance(self, execution_id: str, inputs: Dict) -> ProvenanceRecord:
        return ProvenanceRecord(
            capability_id="crypto.detection",
            capability_version="1.0.0",
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            inputs=inputs,
            adapter_id="crypto_analysis_adapter",
            adapter_version="1.0.0",
            working_directory=os.getcwd(),
        )
