"""
Objective-C Metadata Capabilities for IOS REVERSE KAISER.

CAP-014: objc.metadata - Basic Objective-C metadata extraction
CAP-015: objc.deep_metadata - Extended Objective-C correlation
"""

import hashlib
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import field

from ios_reverse.capabilities.base import (
    CapabilityExecutor, CapabilityContract, CapabilityResult,
    CapabilityStatus, EvidenceRecord, ProvenanceRecord
)
from ios_reverse.models.objc import (
    ObjCModel, EvidenceStrength
)
from ios_reverse.adapters.objc.objc_adapter import ObjCAdapter


# =============================================================================
# CAP-014: objc.metadata
# =============================================================================

class ObjCMetadataContract(CapabilityContract):
    """Contract for CAP-014 objc.metadata."""

    def __init__(self):
        super().__init__(
            id="objc.metadata",
            version="1.0.0",
            domain="objective_c",
            name="ObjC Metadata",
            description="Extract Objective-C runtime metadata"
        )
        self.required_inputs = [
            {"name": "artifact_path", "type": "string", "required": True}
        ]
        self.optional_inputs = [
            {"name": "extract_methods", "type": "boolean", "default": True},
            {"name": "extract_properties", "type": "boolean", "default": True},
            {"name": "extract_selectors", "type": "boolean", "default": True},
            {"name": "min_evidence_strength", "type": "string", "default": "string_hint"},
            {"name": "sections", "type": "object", "required": False},
            {"name": "symbols", "type": "array", "required": False},
        ]
        self.supported_input_types = ["macho"]
        self.output_types = ["objc_classes", "objc_protocols", "objc_categories", "objc_methods"]
        self.required_adapters = []
        self.optional_adapters = ["objc_adapter"]
        self.error_codes = {
            "E001": {"name": "ARTIFACT_NOT_FOUND", "description": "Binary not found"},
            "E002": {"name": "EXTRACTION_FAILED", "description": "Metadata extraction failed"},
            "E003": {"name": "NO_OBJC_METADATA", "description": "No Objective-C metadata found"},
        }
        self.warning_codes = {
            "W001": {"name": "PARTIAL_EXTRACTION", "description": "Some metadata could not be extracted"},
            "W002": {"name": "WEAK_EVIDENCE", "description": "Metadata from weak evidence sources"},
        }


class ObjCMetadataCapability(CapabilityExecutor):
    """
    CAP-014: Extract and normalize Objective-C runtime metadata.

    Extracts:
    - Classes (with superclass relationships)
    - Protocols
    - Categories
    - Selectors
    - Methods (instance and class)
    - Properties
    - Instance variables

    Evidence is preserved with strength indicators.
    """

    def __init__(self):
        super().__init__()
        self._adapter = ObjCAdapter()
        self._id_counter = 0

    def get_contract(self) -> CapabilityContract:
        return ObjCMetadataContract()

    def _generate_id(self) -> str:
        """Generate unique ID for this execution."""
        self._id_counter += 1
        return f"objc-meta-{self._id_counter:04d}"

    def validate_preconditions(self, inputs: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate inputs before execution."""
        artifact_path = inputs.get("artifact_path")

        if not artifact_path:
            return False, "artifact_path is required"

        if not os.path.exists(artifact_path):
            return False, f"Artifact not found: {artifact_path}"

        return True, None

    def execute(self, inputs: Dict[str, Any]) -> CapabilityResult:
        """
        Execute Objective-C metadata extraction.

        Args:
            inputs: Must contain artifact_path

        Returns:
            CapabilityResult with ObjC metadata
        """
        execution_id = self._generate_id()
        timestamp = datetime.utcnow()

        # Validate preconditions
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

        try:
            # Extract metadata
            sections = inputs.get("sections")
            symbols = inputs.get("symbols")

            result = self._adapter.extract_metadata(
                artifact_path=artifact_path,
                sections=sections,
                symbols=symbols,
                compute_hashes=True
            )

            if not result.success:
                return CapabilityResult(
                    status=CapabilityStatus.FAILURE,
                    execution_id=execution_id,
                    timestamp=timestamp,
                    metadata={},
                    error_code="E002",
                    error_message=result.error or "Extraction failed"
                )

            # Extract model from result
            model_dict = result.metadata.get("model", {})
            model = self._dict_to_model(artifact_path, model_dict)

            # Check if we found any ObjC
            if not model.has_objc:
                return CapabilityResult(
                    status=CapabilityStatus.SUCCESS,
                    execution_id=execution_id,
                    timestamp=timestamp,
                    metadata={
                        "artifact_path": artifact_path,
                        "artifact_hash": model.artifact_hash,
                        "has_objc": False,
                        "class_count": 0,
                        "protocol_count": 0,
                        "category_count": 0,
                        "method_count": 0,
                    },
                    provenance=self._build_provenance(execution_id, inputs)
                )

            # Build evidence records
            evidence = self._build_evidence(model, execution_id, timestamp, artifact_path)

            # Build metadata output
            metadata = {
                "artifact_path": artifact_path,
                "artifact_hash": model.artifact_hash,
                "file_size": model.file_size,
                "has_objc": model.has_objc,
                "class_count": len(model.classes),
                "protocol_count": len(model.protocols),
                "category_count": len(model.categories),
                "method_count": len(model.methods),
                "selector_count": len(model.selectors),
                "property_count": len(model.properties),
                "ivar_count": len(model.ivars),
                "evidence_distribution": model.evidence_strength_distribution,
                "sections_found": model.sections_found,
                # Include detailed entity lists
                "classes": [c.to_dict() for c in model.classes[:50]],
                "protocols": [p.to_dict() for p in model.protocols[:50]],
                "categories": [cat.to_dict() for cat in model.categories[:50]],
                "methods": [m.to_dict() for m in model.methods[:100]],
                "selectors": [s.to_dict() for s in model.selectors[:100]],
            }

            # Add warnings if needed
            warnings = []
            if model.warnings:
                warnings = [f"W001: {w}" for w in model.warnings]

            status = CapabilityStatus.SUCCESS
            if len(warnings) > 0:
                status = CapabilityStatus.PARTIAL

            return CapabilityResult(
                status=status,
                execution_id=execution_id,
                timestamp=timestamp,
                metadata=metadata,
                evidence=evidence,
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

    def _dict_to_model(self, artifact_path: str, model_dict: Dict) -> ObjCModel:
        """Convert dictionary back to model for processing."""
        model = ObjCModel(
            artifact_path=model_dict.get("artifact_path", artifact_path),
            artifact_hash=model_dict.get("artifact_hash", ""),
            file_size=model_dict.get("file_size", 0),
            has_objc=model_dict.get("has_objc", False),
            sections_found=model_dict.get("sections_found", []),
            warnings=model_dict.get("warnings", []),
        )

        # Reconstruct classes
        for c in model_dict.get("classes", []):
            from ios_reverse.models.objc import ObjCClass, AddressType
            cls = ObjCClass(
                id=c.get("id", ""),
                name=c.get("name", ""),
                is_meta=c.get("is_meta", False),
                evidence=EvidenceStrength(c.get("evidence", "string_hint")),
                source_artifact=artifact_path,
            )
            model.classes.append(cls)

        # Reconstruct protocols
        for p in model_dict.get("protocols", []):
            from ios_reverse.models.objc import ObjCProtocol
            proto = ObjCProtocol(
                id=p.get("id", ""),
                name=p.get("name", ""),
                evidence=EvidenceStrength(p.get("evidence", "string_hint")),
                source_artifact=artifact_path,
            )
            model.protocols.append(proto)

        # Reconstruct categories
        for cat in model_dict.get("categories", []):
            from ios_reverse.models.objc import ObjCCategory
            category = ObjCCategory(
                id=cat.get("id", ""),
                name=cat.get("name", ""),
                target_class=cat.get("target_class", ""),
                evidence=EvidenceStrength(cat.get("evidence", "string_hint")),
                source_artifact=artifact_path,
            )
            model.categories.append(category)

        # Reconstruct methods
        for m in model_dict.get("methods", []):
            from ios_reverse.models.objc import ObjCMethod
            method = ObjCMethod(
                id=m.get("id", ""),
                name=m.get("name", ""),
                selector=m.get("selector", ""),
                is_class_method=m.get("is_class_method", False),
                evidence=EvidenceStrength(m.get("evidence", "string_hint")),
                source_artifact=artifact_path,
            )
            model.methods.append(method)

        # Reconstruct selectors
        for s in model_dict.get("selectors", []):
            from ios_reverse.models.objc import ObjCSelector
            selector = ObjCSelector(
                id=s.get("id", ""),
                name=s.get("name", ""),
                evidence=EvidenceStrength(s.get("evidence", "string_hint")),
                source_artifact=artifact_path,
            )
            model.selectors.append(selector)

        model.build_indexes()
        return model

    def _build_evidence(
        self,
        model: ObjCModel,
        execution_id: str,
        timestamp: datetime,
        artifact_path: str
    ) -> List[EvidenceRecord]:
        """Build evidence records for the extraction."""
        evidence = []

        # Create evidence for classes
        for cls in model.classes[:20]:  # Limit evidence records
            ev = EvidenceRecord(
                id=f"ev-{uuid.uuid4().hex[:8]}",
                type="derived",
                capability_id="objc.metadata",
                execution_id=execution_id,
                timestamp=timestamp,
                file_path=artifact_path,
                size=model.file_size if model.file_size else None,
                derived_from=["objc_adapter"],
                references={"class_name": cls.name}
            )
            evidence.append(ev)

        return evidence

    def _build_provenance(self, execution_id: str, inputs: Dict) -> ProvenanceRecord:
        """Build provenance record."""
        return ProvenanceRecord(
            capability_id="objc.metadata",
            capability_version="1.0.0",
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            inputs=inputs,
            adapter_id="objc_adapter",
            adapter_version="1.0.0",
            working_directory=os.getcwd(),
        )


# =============================================================================
# CAP-015: objc.deep_metadata
# =============================================================================

class ObjCDeepMetadataContract(CapabilityContract):
    """Contract for CAP-015 objc.deep_metadata."""

    def __init__(self):
        super().__init__(
            id="objc.deep_metadata",
            version="1.0.0",
            domain="objective_c",
            name="ObjC Deep Metadata",
            description="Extended Objective-C correlation and relationships"
        )
        self.required_inputs = [
            {"name": "artifact_path", "type": "string", "required": True}
        ]
        self.optional_inputs = [
            {"name": "base_metadata", "type": "object", "required": False},
            {"name": "build_call_graph", "type": "boolean", "default": False},
            {"name": "resolve_selectors", "type": "boolean", "default": True},
        ]
        self.supported_input_types = ["macho"]
        self.output_types = ["objc_references", "objc_correlations", "unresolved_targets"]
        self.required_adapters = []
        self.optional_adapters = ["objc_adapter"]
        self.error_codes = {
            "E001": {"name": "ARTIFACT_NOT_FOUND", "description": "Binary not found"},
            "E002": {"name": "CORRELATION_FAILED", "description": "Correlation analysis failed"},
        }
        self.warning_codes = {
            "W001": {"name": "NO_BASE_METADATA", "description": "No base ObjC metadata provided"},
            "W002": {"name": "UNRESOLVED_CORRELATIONS", "description": "Some correlations could not be resolved"},
        }


class ObjCDeepMetadataCapability(CapabilityExecutor):
    """
    CAP-015: Extended Objective-C correlation and relationships.

    Builds on objc.metadata to create:
    - Class hierarchy (superclass chains)
    - Protocol adoption relationships
    - Category -> class relationships
    - Selector references
    - Method -> IMP relationships

    IMPORTANT: Does NOT claim call relationships that aren't evidenced.
    """

    def __init__(self):
        super().__init__()
        self._base_capability = ObjCMetadataCapability()
        self._id_counter = 0

    def get_contract(self) -> CapabilityContract:
        return ObjCDeepMetadataContract()

    def _generate_id(self) -> str:
        """Generate unique ID for this execution."""
        self._id_counter += 1
        return f"objc-deep-{self._id_counter:04d}"

    def validate_preconditions(self, inputs: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate inputs before execution."""
        artifact_path = inputs.get("artifact_path")

        if not artifact_path:
            return False, "artifact_path is required"

        if not os.path.exists(artifact_path):
            return False, f"Artifact not found: {artifact_path}"

        return True, None

    def execute(self, inputs: Dict[str, Any]) -> CapabilityResult:
        """
        Execute extended Objective-C correlation.

        Args:
            inputs: artifact_path and optional base_metadata

        Returns:
            CapabilityResult with relationships and correlations
        """
        execution_id = self._generate_id()
        timestamp = datetime.utcnow()

        # Validate preconditions
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

        try:
            # Get or use base metadata
            base_metadata = inputs.get("base_metadata")
            if base_metadata is None:
                # Run base extraction
                base_result = self._base_capability.execute({"artifact_path": artifact_path})
                if base_result.status == CapabilityStatus.FAILURE:
                    return base_result
                base_metadata = base_result.metadata

            # Build relationships
            references = self._build_references(base_metadata, artifact_path)

            # Build correlations
            correlations = self._build_correlations(base_metadata, artifact_path)

            # Check for unresolved targets
            unresolved = self._find_unresolved(base_metadata)

            # Determine status
            status = CapabilityStatus.SUCCESS
            warnings = []

            if len(unresolved) > 0:
                warnings.append(f"W002: {len(unresolved)} unresolved correlations")

            if len(references) == 0:
                warnings.append("W001: No relationships could be established")

            metadata = {
                "artifact_path": artifact_path,
                "has_objc": base_metadata.get("has_objc", False),
                "class_count": base_metadata.get("class_count", 0),
                "reference_count": len(references),
                "correlation_count": len(correlations),
                "unresolved_count": len(unresolved),
                "references": references[:100],
                "correlations": correlations[:50],
                "unresolved": unresolved[:20],
            }

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

    def _build_references(self, base_metadata: Dict, artifact_path: str) -> List[Dict]:
        """Build metadata relationship references."""
        references = []

        classes = base_metadata.get("classes", [])
        protocols = base_metadata.get("protocols", [])
        categories = base_metadata.get("categories", [])
        methods = base_metadata.get("methods", [])

        # Build class name to id map
        class_map = {c.get("name"): c.get("id") for c in classes}

        # Class -> superclass references
        for cls in classes:
            superclass = cls.get("superclass")
            if superclass and superclass in class_map:
                references.append({
                    "type": "class_to_superclass",
                    "source_id": cls.get("id"),
                    "source_name": cls.get("name"),
                    "target_id": class_map.get(superclass),
                    "target_name": superclass,
                    "evidence": "structural",
                })

        # Class -> protocol references
        for cls in classes:
            for proto in cls.get("protocols", []):
                proto_id = next((p.get("id") for p in protocols if p.get("name") == proto), None)
                if proto_id:
                    references.append({
                        "type": "class_to_protocol",
                        "source_id": cls.get("id"),
                        "source_name": cls.get("name"),
                        "target_id": proto_id,
                        "target_name": proto,
                        "evidence": "structural",
                    })

        # Category -> target class references
        for cat in categories:
            target = cat.get("target_class")
            if target and target in class_map:
                references.append({
                    "type": "category_to_class",
                    "source_id": cat.get("id"),
                    "source_name": cat.get("name"),
                    "target_id": class_map.get(target),
                    "target_name": target,
                    "evidence": "structural",
                })

        return references

    def _build_correlations(self, base_metadata: Dict, artifact_path: str) -> List[Dict]:
        """Build unresolved correlation targets."""
        correlations = []

        # NOTE: Do NOT fabricate call relationships
        # Only create correlation hints from metadata

        methods = base_metadata.get("methods", [])

        for method in methods:
            imp_addr = method.get("imp_address")
            if imp_addr:
                correlations.append({
                    "type": "method_to_address",
                    "method_id": method.get("id"),
                    "method_name": method.get("name"),
                    "selector": method.get("selector"),
                    "address": imp_addr,
                    "note": "IMP address from method structure",
                })

        return correlations

    def _find_unresolved(self, base_metadata: Dict) -> List[Dict]:
        """Find unresolved correlation targets."""
        unresolved = []

        # Look for class references that couldn't be resolved
        classes = base_metadata.get("classes", [])
        protocols = base_metadata.get("protocols", [])

        known_names = {c.get("name") for c in classes}
        known_names.update({p.get("name") for p in protocols})

        for cls in classes:
            superclass = cls.get("superclass")
            if superclass and superclass not in known_names:
                unresolved.append({
                    "type": "unresolved_superclass",
                    "class_id": cls.get("id"),
                    "class_name": cls.get("name"),
                    "missing_name": superclass,
                    "note": "Superclass not found in metadata",
                })

        return unresolved

    def _build_provenance(self, execution_id: str, inputs: Dict) -> ProvenanceRecord:
        """Build provenance record."""
        return ProvenanceRecord(
            capability_id="objc.deep_metadata",
            capability_version="1.0.0",
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            inputs=inputs,
            working_directory=os.getcwd(),
        )
