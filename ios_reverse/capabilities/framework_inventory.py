"""
Framework Inventory Capability for IOS REVERSE KAISER.

CAP-018: framework.inventory
"""

import os
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from ios_reverse.capabilities.base import (
    CapabilityExecutor, CapabilityContract, CapabilityResult,
    CapabilityStatus, EvidenceRecord, ProvenanceRecord
)
from ios_reverse.models.components import (
    ComponentType, Classification, OwnershipHint,
    FrameworkComponent, AppComponent, ComponentGraph,
    generate_component_id
)
from ios_reverse.adapters.components.framework_adapter import FrameworkAdapter
from ios_reverse.adapters.components.base import ComponentTraversal, TraversalContext


class FrameworkInventoryContract(CapabilityContract):
    """Contract for CAP-018 framework.inventory."""

    def __init__(self):
        super().__init__(
            id="framework.inventory",
            version="1.0.0",
            domain="components",
            name="Framework Inventory",
            description="Discover and normalize embedded frameworks"
        )
        self.required_inputs = [
            {"name": "artifact_path", "type": "string", "required": True}
        ]
        self.optional_inputs = [
            {"name": "parent_app_id", "type": "string", "required": False},
            {"name": "compute_hashes", "type": "boolean", "default": True},
        ]
        self.supported_input_types = ["macho", "app_bundle"]
        self.output_types = ["framework_components", "framework_graph"]
        self.required_adapters = []
        self.optional_adapters = ["framework_adapter"]
        self.error_codes = {
            "E001": {"name": "ARTIFACT_NOT_FOUND", "description": "Artifact not found"},
            "E002": {"name": "DISCOVERY_FAILED", "description": "Framework discovery failed"},
        }
        self.warning_codes = {
            "W001": {"name": "MALFORMED_FRAMEWORK", "description": "A framework bundle was malformed"},
            "W002": {"name": "NO_FRAMEWORKS", "description": "No embedded frameworks found"},
        }


class FrameworkInventoryCapability(CapabilityExecutor):
    """
    CAP-018: Discover and normalize embedded frameworks.

    Distinguishes between:
    - Embedded frameworks (physically inside the application)
    - System/external dependencies (referenced but not embedded)

    Does NOT create fake UIKit/Foundation components.
    """

    def __init__(self):
        super().__init__()
        self._adapter = FrameworkAdapter()
        self._id_counter = 0

    def get_contract(self) -> CapabilityContract:
        return FrameworkInventoryContract()

    def _generate_id(self) -> str:
        self._id_counter += 1
        return f"fw-inv-{self._id_counter:04d}"

    def validate_preconditions(
        self,
        inputs: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Validate preconditions."""
        artifact_path = inputs.get("artifact_path")
        if not artifact_path:
            return False, "artifact_path is required"
        if not os.path.exists(artifact_path):
            return False, f"Artifact not found: {artifact_path}"
        return True, None

    def execute(self, inputs: Dict[str, Any]) -> CapabilityResult:
        """
        Execute framework inventory.

        Args:
            inputs: Must contain artifact_path

        Returns:
            CapabilityResult with framework components
        """
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

        artifact_path = inputs["artifact_path"]
        parent_app_id = inputs.get("parent_app_id")

        try:
            # Create traversal context
            context = TraversalContext(
                root_path=artifact_path,
                visited_paths=set(),
                visited_artifacts=set()
            )

            # Discover frameworks
            frameworks = self._adapter.discover_frameworks(artifact_path, context)

            # Build result
            components = []
            warnings = []

            for fw in frameworks:
                components.append(fw.to_dict())
                if fw.classification == Classification.UNKNOWN:
                    warnings.append(f"W001: Malformed framework: {fw.name}")

            if not frameworks:
                warnings.append("W002: No embedded frameworks found")

            metadata = {
                "artifact_path": artifact_path,
                "framework_count": len(frameworks),
                "components": components,
                "classifications": self._summarize_classifications(frameworks),
                "parent_app_id": parent_app_id,
            }

            status = CapabilityStatus.SUCCESS
            if warnings:
                status = CapabilityStatus.PARTIAL

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

    def _summarize_classifications(
        self,
        frameworks: List[FrameworkComponent]
    ) -> Dict[str, int]:
        """Summarize framework classifications."""
        summary = {
            "embedded": 0,
            "system_external": 0,
            "unknown": 0
        }
        for fw in frameworks:
            summary[fw.classification.value] += 1
        return summary

    def _build_provenance(
        self,
        execution_id: str,
        inputs: Dict
    ) -> ProvenanceRecord:
        """Build provenance record."""
        return ProvenanceRecord(
            capability_id="framework.inventory",
            capability_version="1.0.0",
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            inputs=inputs,
            adapter_id="framework_adapter",
            adapter_version="1.0.0",
            working_directory=os.getcwd(),
        )
