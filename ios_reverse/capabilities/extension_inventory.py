"""
Extension Inventory Capability for IOS REVERSE KAISER.

CAP-020: extension.inventory
"""

import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from ios_reverse.capabilities.base import (
    CapabilityExecutor, CapabilityContract, CapabilityResult,
    CapabilityStatus, ProvenanceRecord
)
from ios_reverse.models.components import ExtensionComponent
from ios_reverse.adapters.components.extension_adapter import ExtensionAdapter
from ios_reverse.adapters.components.base import ComponentTraversal, TraversalContext


class ExtensionInventoryContract(CapabilityContract):
    """Contract for CAP-020 extension.inventory."""

    def __init__(self):
        super().__init__(
            id="extension.inventory",
            version="1.0.0",
            domain="components",
            name="Extension Inventory",
            description="Discover application extensions"
        )
        self.required_inputs = [
            {"name": "artifact_path", "type": "string", "required": True}
        ]
        self.optional_inputs = [
            {"name": "parent_id", "type": "string", "required": False},
        ]
        self.supported_input_types = ["macho", "app_bundle"]
        self.output_types = ["extension_components", "extension_graph"]
        self.required_adapters = []
        self.optional_adapters = ["extension_adapter"]
        self.error_codes = {
            "E001": {"name": "ARTIFACT_NOT_FOUND", "description": "Artifact not found"},
            "E002": {"name": "DISCOVERY_FAILED", "description": "Extension discovery failed"},
        }
        self.warning_codes = {
            "W001": {"name": "MALFORMED_EXTENSION", "description": "An extension bundle was malformed"},
            "W002": {"name": "NO_EXTENSIONS", "description": "No extensions found"},
        }


class ExtensionInventoryCapability(CapabilityExecutor):
    """
    CAP-020: Discover application extensions.

    Handles various extension types:
    - Widgets
    - Share extensions
    - Notification extensions
    - Intents
    - Keyboard extensions
    - Other extension points

    Extension metadata is inspected structurally from Info.plist.
    """

    def __init__(self):
        super().__init__()
        self._adapter = ExtensionAdapter()
        self._id_counter = 0

    def get_contract(self) -> CapabilityContract:
        return ExtensionInventoryContract()

    def _generate_id(self) -> str:
        self._id_counter += 1
        return f"ext-inv-{self._id_counter:04d}"

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
        Execute extension inventory.

        Args:
            inputs: Must contain artifact_path

        Returns:
            CapabilityResult with extension components
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

            # Discover extensions
            extensions = self._adapter.discover_extensions(artifact_path, context, parent_id)

            # Build result
            components = []
            warnings = []

            for ext in extensions:
                components.append(ext.to_dict())

            if not extensions:
                warnings.append("W002: No extensions found")

            metadata = {
                "artifact_path": artifact_path,
                "extension_count": len(extensions),
                "components": components,
                "extension_points": self._summarize_extension_points(extensions),
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

    def _summarize_extension_points(
        self,
        extensions: List[ExtensionComponent]
    ) -> Dict[str, int]:
        """Summarize extension types by extension point."""
        summary = {}
        for ext in extensions:
            point = ext.extension_point or "unknown"
            summary[point] = summary.get(point, 0) + 1
        return summary

    def _build_provenance(
        self,
        execution_id: str,
        inputs: Dict
    ) -> ProvenanceRecord:
        """Build provenance record."""
        return ProvenanceRecord(
            capability_id="extension.inventory",
            capability_version="1.0.0",
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            inputs=inputs,
            adapter_id="extension_adapter",
            adapter_version="1.0.0",
            working_directory=os.getcwd(),
        )
