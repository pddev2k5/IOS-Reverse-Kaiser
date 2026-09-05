"""
Dylib Inventory Capability for IOS REVERSE KAISER.

CAP-019: dylib.inventory
"""

import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from ios_reverse.capabilities.base import (
    CapabilityExecutor, CapabilityContract, CapabilityResult,
    CapabilityStatus, ProvenanceRecord
)
from ios_reverse.models.components import (
    DylibComponent, ComponentType
)
from ios_reverse.adapters.components.dylib_adapter import DylibAdapter
from ios_reverse.adapters.components.base import ComponentTraversal, TraversalContext


class DylibInventoryContract(CapabilityContract):
    """Contract for CAP-019 dylib.inventory."""

    def __init__(self):
        super().__init__(
            id="dylib.inventory",
            version="1.0.0",
            domain="components",
            name="Dylib Inventory",
            description="Discover application-embedded dynamic libraries"
        )
        self.required_inputs = [
            {"name": "artifact_path", "type": "string", "required": True}
        ]
        self.optional_inputs = [
            {"name": "parent_id", "type": "string", "required": False},
        ]
        self.supported_input_types = ["macho", "app_bundle"]
        self.output_types = ["dylib_components", "dylib_graph"]
        self.required_adapters = []
        self.optional_adapters = ["dylib_adapter"]
        self.error_codes = {
            "E001": {"name": "ARTIFACT_NOT_FOUND", "description": "Artifact not found"},
            "E002": {"name": "DISCOVERY_FAILED", "description": "Dylib discovery failed"},
        }
        self.warning_codes = {
            "W001": {"name": "MALFORMED_DYLIB", "description": "A dylib was malformed"},
            "W002": {"name": "NO_DYLIBS", "description": "No embedded dylibs found"},
        }


class DylibInventoryCapability(CapabilityExecutor):
    """
    CAP-019: Discover application-embedded dynamic libraries.

    Distinguishes between:
    - Embedded dylib files (physically inside the application)
    - External dylib dependencies (referenced but not embedded)

    Does NOT fabricate components for unresolved dependencies.
    """

    def __init__(self):
        super().__init__()
        self._adapter = DylibAdapter()
        self._id_counter = 0

    def get_contract(self) -> CapabilityContract:
        return DylibInventoryContract()

    def _generate_id(self) -> str:
        self._id_counter += 1
        return f"dylib-inv-{self._id_counter:04d}"

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
        Execute dylib inventory.

        Args:
            inputs: Must contain artifact_path

        Returns:
            CapabilityResult with dylib components
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
        parent_id = inputs.get("parent_id")

        try:
            # Create traversal context
            context = TraversalContext(
                root_path=artifact_path,
                visited_paths=set(),
                visited_artifacts=set()
            )

            # Discover dylibs
            dylibs = self._adapter.discover_dylibs(artifact_path, context, parent_id)

            # Build result
            components = []
            warnings = []

            for dylib in dylibs:
                components.append(dylib.to_dict())

            if not dylibs:
                warnings.append("W002: No embedded dylibs found")

            metadata = {
                "artifact_path": artifact_path,
                "dylib_count": len(dylibs),
                "components": components,
                "parent_id": parent_id,
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

    def _build_provenance(
        self,
        execution_id: str,
        inputs: Dict
    ) -> ProvenanceRecord:
        """Build provenance record."""
        return ProvenanceRecord(
            capability_id="dylib.inventory",
            capability_version="1.0.0",
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            inputs=inputs,
            adapter_id="dylib_adapter",
            adapter_version="1.0.0",
            working_directory=os.getcwd(),
        )
