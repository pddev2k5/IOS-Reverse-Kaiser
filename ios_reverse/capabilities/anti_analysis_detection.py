"""
Anti-Analysis Detection Capability for IOS REVERSE KAISER.

CAP-030: anti.analysis_detection
"""

import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from ios_reverse.capabilities.base import (
    CapabilityExecutor, CapabilityContract, CapabilityResult,
    CapabilityStatus, ProvenanceRecord
)
from ios_reverse.adapters.analysis.anti_analysis_adapter import AntiAnalysisAdapter


class AntiAnalysisDetectionContract(CapabilityContract):
    """Contract for CAP-030 anti.analysis_detection."""

    def __init__(self):
        super().__init__(
            id="anti.analysis_detection",
            version="1.0.0",
            domain="anti_analysis",
            name="Anti-Analysis Detection",
            description="Detect anti-analysis mechanisms and indicators"
        )
        self.required_inputs = [
            {"name": "artifact_path", "type": "string", "required": True}
        ]
        self.optional_inputs = [
            {"name": "strings_data", "type": "string", "required": False},
            {"name": "imports", "type": "array", "required": False},
            {"name": "symbols", "type": "array", "required": False},
            {"name": "component_id", "type": "string", "required": False},
        ]
        self.output_types = ["anti_analysis_model"]
        self.error_codes = {
            "E001": {"name": "ARTIFACT_NOT_FOUND", "description": "Artifact not found"},
            "E002": {"name": "ANALYSIS_FAILED", "description": "Anti-analysis detection failed"},
        }


class AntiAnalysisDetectionCapability(CapabilityExecutor):
    """
    CAP-030: Detect anti-analysis mechanisms.

    IMPORTANT:
    - Indicator != verified mechanism
    - Debugger API import != confirmed anti-debug
    - Jailbreak path != confirmed detection
    - Does not fabricate protection effectiveness
    """

    def __init__(self):
        super().__init__()
        self._adapter = AntiAnalysisAdapter()
        self._id_counter = 0

    def get_contract(self) -> CapabilityContract:
        return AntiAnalysisDetectionContract()

    def _generate_id(self) -> str:
        self._id_counter += 1
        return f"anti-det-{self._id_counter:04d}"

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
            strings_data = inputs.get("strings_data", "")
            imports = inputs.get("imports", [])
            symbols = inputs.get("symbols", [])
            component_id = inputs.get("component_id")
            artifact_id = inputs.get("artifact_id")

            # Build model
            model = self._adapter.build_model(
                strings_data=strings_data,
                imports=imports,
                symbols=symbols,
                component_id=component_id,
                artifact_id=artifact_id,
                artifact_path=inputs["artifact_path"]
            )

            # Build result
            metadata = {
                "artifact_path": inputs["artifact_path"],
                "indicator_count": len(model.indicators),
                "reference_count": len(model.references),
                "finding_count": len(model.findings),
                "category_distribution": model.category_distribution,
                "state_distribution": model.state_distribution,
                "evidence_level_distribution": model.evidence_level_distribution,
                "indicators": [i.to_dict() for i in model.indicators[:50]],
                "references": [r.to_dict() for r in model.references[:50]],
                "findings": [f.to_dict() for f in model.findings[:20]],
            }

            status = CapabilityStatus.SUCCESS
            warnings = []

            # Empty result is valid
            if not model.findings:
                warnings.append("No anti-analysis evidence detected")

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
            capability_id="anti.analysis_detection",
            capability_version="1.0.0",
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            inputs=inputs,
            adapter_id="anti_analysis_adapter",
            adapter_version="1.0.0",
            working_directory=os.getcwd(),
        )
