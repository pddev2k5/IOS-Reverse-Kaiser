"""
Architecture Analysis Adapter for IOS REVERSE KAISER.

Provides application architecture detection and classification.

IMPORTANT: This represents LOGICAL architecture (ViewControllers, Services, etc.),
NOT physical (Frameworks, Dylibs from P04.4). Keep these concepts separate.
"""

from typing import Dict, Any, Optional, List, Set, Tuple
from dataclasses import dataclass

from ios_reverse.adapters.base import ToolAdapter, ToolInfo, AdapterResult
from ios_reverse.models.architecture import (
    ArchitectureRole, EvidenceLevel,
    ArchitectureComponent, ArchitectureRelationship, ArchitectureEvidence,
    ArchitectureModel, generate_architecture_id
)


class ArchitectureAnalysisAdapter(ToolAdapter):
    """
    Adapter for application architecture detection.

    IMPORTANT: This detects LOGICAL architecture roles (Service, ViewController, etc.),
    NOT physical components (Framework, Dylib from P04.4).
    """

    # Protocol names that indicate architecture roles
    PROTOCOL_ROLE_MAP = {
        'UIViewController': ArchitectureRole.VIEW_CONTROLLER,
        'UITableViewDelegate': ArchitectureRole.DELEGATE,
        'UITableViewDataSource': ArchitectureRole.DELEGATE,
        'UICollectionViewDelegate': ArchitectureRole.DELEGATE,
        'UICollectionViewDataSource': ArchitectureRole.DELEGATE,
        'NSCoding': ArchitectureRole.MODEL,
        'Codable': ArchitectureRole.MODEL,
        'Decodable': ArchitectureRole.MODEL,
        'Encodable': ArchitectureRole.MODEL,
        'NSSecureCoding': ArchitectureRole.MODEL,
        'NSObject': ArchitectureRole.UNKNOWN,
    }

    # Base class indicators
    SUPERCLASS_ROLE_MAP = {
        'UIViewController': ArchitectureRole.VIEW_CONTROLLER,
        'UIView': ArchitectureRole.UNKNOWN,
        'NSObject': ArchitectureRole.UNKNOWN,
        'NSManagedObject': ArchitectureRole.MODEL,
    }

    def __init__(self):
        super().__init__("architecture_analysis_adapter", "1.0.0")
        self._id_counter = 0

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="architecture_analysis_adapter",
            path="internal",
            version="1.0.0"
        )

    def validate_environment(self) -> Tuple[bool, Optional[str]]:
        return True, None

    def execute(self, command, cwd=None, env=None, input_data=None):
        return AdapterResult(success=True, stdout="Pure Python adapter")

    def is_available(self) -> bool:
        return True

    def detect_components(
        self,
        objc_metadata: Optional[Dict] = None,
        swift_metadata: Optional[Dict] = None,
        component_ids: Optional[List[str]] = None
    ) -> List[ArchitectureComponent]:
        """
        Detect architecture components from metadata.

        Args:
            objc_metadata: ObjC metadata from CAP-014/CAP-015
            swift_metadata: Swift metadata from CAP-016
            component_ids: Component IDs from P04.4 (optional)

        Returns:
            List of ArchitectureComponent
        """
        components = []

        # Process ObjC classes
        if objc_metadata:
            classes = objc_metadata.get('classes', [])
            for cls in classes:
                comp = self._classify_objc_class(cls, component_ids)
                if comp:
                    components.append(comp)

        # Process Swift types
        if swift_metadata:
            types = swift_metadata.get('types', [])
            for typ in types:
                comp = self._classify_swift_type(typ, component_ids)
                if comp:
                    components.append(comp)

        return components

    def _classify_objc_class(
        self,
        cls: Dict,
        component_ids: Optional[List[str]]
    ) -> Optional[ArchitectureComponent]:
        """
        Classify an ObjC class into an architecture role.
        """
        cls_name = cls.get('name', '')
        if not cls_name:
            return None

        # Determine role from name
        name_roles = self._classify_by_naming(cls_name)

        # Try to improve with structural evidence
        superclass = cls.get('superclass')
        protocols = cls.get('protocols', [])

        role = name_roles[0][0]
        role_evidence = [name_roles[0][1]]
        evidence_level = EvidenceLevel.HEURISTIC
        alternative_roles = [r[0] for r in name_roles[1:5]]  # Top alternatives

        # Check protocols for stronger evidence
        for protocol in protocols:
            if protocol in self.PROTOCOL_ROLE_MAP:
                protocol_role = self.PROTOCOL_ROLE_MAP[protocol]
                if protocol_role != ArchitectureRole.UNKNOWN:
                    role = protocol_role
                    role_evidence.append(f"Adopts protocol: {protocol}")
                    evidence_level = EvidenceLevel.STRUCTURAL
                    break

        # Check superclass for stronger evidence
        if superclass and superclass in self.SUPERCLASS_ROLE_MAP:
            super_role = self.SUPERCLASS_ROLE_MAP[superclass]
            if super_role != ArchitectureRole.UNKNOWN:
                # Only upgrade if we don't have strong evidence yet
                if evidence_level == EvidenceLevel.HEURISTIC:
                    role = super_role
                    role_evidence.append(f"Inherits: {superclass}")
                    evidence_level = EvidenceLevel.STRUCTURAL
                elif role == ArchitectureRole.UNKNOWN:
                    role = super_role
                    role_evidence.append(f"Inherits: {superclass}")
                    evidence_level = EvidenceLevel.STRUCTURAL

        # Get methods for context
        methods = []
        for method in cls.get('methods', [])[:10]:  # Limit to first 10
            selector = method.get('selector', '')
            if selector:
                methods.append(selector)

        # Get properties
        properties = [p.get('name', '') for p in cls.get('properties', [])[:10]]

        # Get references
        inbound = cls.get('referenced_by', [])
        outbound = cls.get('references', [])

        # Generate ID
        artifact_id = cls.get('artifact_id', '')
        component_id = generate_architecture_id(cls_name, artifact_id)

        return ArchitectureComponent(
            component_id=component_id,
            name=cls_name,
            role=role,
            evidence_level=evidence_level,
            role_evidence=role_evidence,
            objc_class_id=cls_name,
            component_id_p04=component_ids[0] if component_ids else None,
            artifact_id=artifact_id,
            superclass=superclass,
            protocols=protocols,
            methods=methods,
            properties=properties,
            inbound_references=inbound[:20],  # Limit
            outbound_references=outbound[:20],
            alternative_roles=[r.value for r in alternative_roles if r != ArchitectureRole.UNKNOWN],
            role_confidence_notes=[f"Classification based on {evidence_level.value} evidence"]
        )

    def _classify_swift_type(
        self,
        typ: Dict,
        component_ids: Optional[List[str]]
    ) -> Optional[ArchitectureComponent]:
        """
        Classify a Swift type into an architecture role.
        """
        type_name = typ.get('name', '')
        if not type_name:
            return None

        # Determine role from name
        name_roles = self._classify_by_naming(type_name)

        role = name_roles[0][0]
        role_evidence = [name_roles[0][1]]
        evidence_level = EvidenceLevel.HEURISTIC
        alternative_roles = [r[0] for r in name_roles[1:5]]

        # Check protocols
        protocols = typ.get('protocols', [])
        for protocol in protocols:
            if 'Delegate' in protocol:
                role = ArchitectureRole.DELEGATE
                role_evidence.append(f"Adopts: {protocol}")
                evidence_level = EvidenceLevel.STRUCTURAL
                break
            elif protocol in ['Codable', 'Decodable', 'Encodable']:
                role = ArchitectureRole.MODEL
                role_evidence.append(f"Adopts: {protocol}")
                evidence_level = EvidenceLevel.STRUCTURAL
                break

        # Get methods
        methods = []
        for method in typ.get('methods', [])[:10]:
            name = method.get('name', '')
            if name:
                methods.append(name)

        # Generate ID
        artifact_id = typ.get('artifact_id', '')
        component_id = generate_architecture_id(type_name, artifact_id)

        return ArchitectureComponent(
            component_id=component_id,
            name=type_name,
            role=role,
            evidence_level=evidence_level,
            role_evidence=role_evidence,
            swift_type_id=type_name,
            component_id_p04=component_ids[0] if component_ids else None,
            artifact_id=artifact_id,
            superclass=typ.get('superclass'),
            protocols=protocols,
            methods=methods,
            properties=typ.get('properties', [])[:10],
            alternative_roles=[r.value for r in alternative_roles if r != ArchitectureRole.UNKNOWN],
            role_confidence_notes=[f"Classification based on {evidence_level.value} evidence"]
        )

    def _classify_by_naming(self, name: str) -> List[Tuple[ArchitectureRole, str]]:
        """
        Classify component role by name heuristics.

        Returns list of (role, confidence_note) sorted by likely match.

        IMPORTANT: This is HEURISTIC only.
        """
        candidates = []
        lower_name = name.lower()

        # Strong indicators (more specific matches first)
        if lower_name.endswith('viewcontroller'):
            candidates.append((ArchitectureRole.VIEW_CONTROLLER, "Name ends with 'ViewController'"))
        if lower_name.endswith('viewmodel'):
            candidates.append((ArchitectureRole.VIEW_MODEL, "Name contains 'ViewModel'"))
        if lower_name.endswith('service'):
            candidates.append((ArchitectureRole.SERVICE, "Name ends with 'Service'"))
        if lower_name.endswith('repository'):
            candidates.append((ArchitectureRole.REPOSITORY, "Name ends with 'Repository'"))
        if lower_name.endswith('manager'):
            candidates.append((ArchitectureRole.MANAGER, "Name ends with 'Manager'"))
        if lower_name.endswith('client'):
            candidates.append((ArchitectureRole.CLIENT, "Name ends with 'Client'"))
        if lower_name.endswith('router'):
            candidates.append((ArchitectureRole.ROUTER, "Name ends with 'Router'"))
        if lower_name.endswith('coordinator'):
            candidates.append((ArchitectureRole.COORDINATOR, "Name ends with 'Coordinator'"))
        if lower_name.endswith('handler'):
            candidates.append((ArchitectureRole.HANDLER, "Name ends with 'Handler'"))
        if lower_name.endswith('provider'):
            candidates.append((ArchitectureRole.PROVIDER, "Name ends with 'Provider'"))
        if lower_name.endswith('interactor'):
            candidates.append((ArchitectureRole.INTERACTOR, "Name ends with 'Interactor'"))
        if lower_name.endswith('presenter'):
            candidates.append((ArchitectureRole.PRESENTER, "Name ends with 'Presenter'"))
        if lower_name.endswith('worker'):
            candidates.append((ArchitectureRole.WORKER, "Name ends with 'Worker'"))
        if lower_name.endswith('model') or lower_name.endswith('entity') or lower_name.endswith('dto'):
            candidates.append((ArchitectureRole.MODEL, "Name ends with 'Model', 'Entity', or 'DTO'"))

        # Weaker indicators (less specific)
        if not candidates:
            if 'service' in lower_name:
                candidates.append((ArchitectureRole.SERVICE, "Name contains 'Service'"))
            if 'manager' in lower_name:
                candidates.append((ArchitectureRole.MANAGER, "Name contains 'Manager'"))
            if 'client' in lower_name:
                candidates.append((ArchitectureRole.CLIENT, "Name contains 'Client'"))
            if 'delegate' in lower_name:
                candidates.append((ArchitectureRole.DELEGATE, "Name contains 'Delegate'"))
            if 'handler' in lower_name:
                candidates.append((ArchitectureRole.HANDLER, "Name contains 'Handler'"))
            if 'provider' in lower_name:
                candidates.append((ArchitectureRole.PROVIDER, "Name contains 'Provider'"))

        # Default
        if not candidates:
            candidates.append((ArchitectureRole.UNKNOWN, "No naming indicators"))

        return candidates

    def build_relationships(
        self,
        components: List[ArchitectureComponent],
        objc_metadata: Optional[Dict] = None,
        swift_metadata: Optional[Dict] = None
    ) -> List[ArchitectureRelationship]:
        """
        Build architecture relationships from metadata.

        Note: These are heuristic relationships based on references.
        """
        relationships = []
        seen = set()

        # Build component lookup
        by_name = {c.name: c for c in components}

        # Process ObjC references
        if objc_metadata:
            classes = objc_metadata.get('classes', [])
            for cls in classes:
                cls_name = cls.get('name', '')
                if cls_name not in by_name:
                    continue

                source_id = by_name[cls_name].component_id

                # Outbound references
                for ref in cls.get('references', [])[:20]:
                    if ref in by_name:
                        target_id = by_name[ref].component_id
                        key = f"{source_id}:{target_id}:delegates_to"
                        if key not in seen:
                            seen.add(key)
                            relationships.append(ArchitectureRelationship(
                                relationship_id=f"rel-{len(relationships)}",
                                source_id=source_id,
                                target_id=target_id,
                                relationship_type="references",
                                evidence_level=EvidenceLevel.REFERENCE,
                                evidence_sources=[f"objc:{cls_name} references {ref}"]
                            ))

        return relationships

    def build_model(
        self,
        objc_metadata: Optional[Dict] = None,
        swift_metadata: Optional[Dict] = None,
        component_ids: Optional[List[str]] = None,
        artifact_path: str = ""
    ) -> ArchitectureModel:
        """
        Build complete architecture model.
        """
        # Detect components
        components = self.detect_components(objc_metadata, swift_metadata, component_ids)

        # Build relationships
        relationships = self.build_relationships(components, objc_metadata, swift_metadata)

        # Build model
        model = ArchitectureModel(
            artifact_path=artifact_path,
            components=components,
            relationships=relationships,
        )

        # Build indexes
        model.build_indexes()

        # Compute distributions
        model.role_distribution = {}
        model.evidence_level_distribution = {}
        for comp in components:
            model.role_distribution[comp.role.value] = model.role_distribution.get(comp.role.value, 0) + 1
            model.evidence_level_distribution[comp.evidence_level.value] = model.evidence_level_distribution.get(comp.evidence_level.value, 0) + 1

        return model
