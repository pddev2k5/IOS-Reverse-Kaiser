"""
Callflow Analysis Adapter for IOS REVERSE KAISER.

Provides call-flow reconstruction from metadata.

IMPORTANT: This reconstructs evidenced call relationships from metadata,
NOT speculative call graphs. Unresolved targets must remain explicit.
"""

from typing import Dict, Any, Optional, List, Set, Tuple
from dataclasses import dataclass

from ios_reverse.adapters.base import ToolAdapter, ToolInfo, AdapterResult
from ios_reverse.models.callflow import (
    EdgeType, EvidenceLevel, AnchorType,
    FlowAnchor, FunctionNode, CallEdge, UnresolvedTarget, CallFlow,
    generate_node_id, generate_edge_id, generate_anchor_id
)


class CallflowAnalysisAdapter(ToolAdapter):
    """
    Adapter for call-flow reconstruction.

    IMPORTANT: This is metadata-based analysis only.
    - Confirmed calls require strong evidence
    - References may not be confirmed calls
    - Unresolved targets remain explicit
    """

    # Anchor types to search for
    ANCHOR_PATTERNS = {
        AnchorType.ENDPOINT: [
            r'https?://[^\s<>"{}|\\^`\[\]]+',
            r'/api/[^\s]+',
            r'/rest/[^\s]+',
        ],
        AnchorType.SELECTOR: [],  # From ObjC metadata
        AnchorType.FUNCTION: [],  # From symbols
        AnchorType.CLASS: [],  # From ObjC/Swift metadata
    }

    # Network-related method patterns
    NETWORK_METHOD_PATTERNS = [
        'request', 'fetch', 'send', 'post', 'get', 'load', 'connect',
        'download', 'upload', 'sync', 'refresh', 'login', 'authenticate',
    ]

    def __init__(self):
        super().__init__("callflow_analysis_adapter", "1.0.0")
        self._id_counter = 0

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="callflow_analysis_adapter",
            path="internal",
            version="1.0.0"
        )

    def validate_environment(self) -> Tuple[bool, Optional[str]]:
        return True, None

    def execute(self, command, cwd=None, env=None, input_data=None):
        return AdapterResult(success=True, stdout="Pure Python adapter")

    def is_available(self) -> bool:
        return True

    def create_anchors(
        self,
        strings_data: str = "",
        objc_metadata: Optional[Dict] = None,
        swift_metadata: Optional[Dict] = None,
        network_endpoints: Optional[List[Dict]] = None,
        component_id: Optional[str] = None,
        artifact_id: Optional[str] = None
    ) -> List[FlowAnchor]:
        """
        Create anchors from various sources.

        Anchors are starting points for callflow analysis.
        """
        anchors = []
        seen = set()

        # From strings (URLs, paths)
        import re
        for pattern in self.ANCHOR_PATTERNS[AnchorType.ENDPOINT]:
            for match in re.finditer(pattern, strings_data):
                value = match.group(0)
                anchor_id = generate_anchor_id(AnchorType.ENDPOINT.value, value)
                if anchor_id in seen:
                    continue
                seen.add(anchor_id)

                anchors.append(FlowAnchor(
                    anchor_id=anchor_id,
                    anchor_type=AnchorType.ENDPOINT,
                    value=value,
                    component_id=component_id,
                    artifact_id=artifact_id,
                    offset=match.start(),
                    evidence_strength=EvidenceLevel.REFERENCE
                ))

        # From ObjC classes/methods
        if objc_metadata:
            # Classes
            for cls in objc_metadata.get('classes', [])[:100]:
                cls_name = cls.get('name', '')
                anchor_id = generate_anchor_id(AnchorType.CLASS.value, cls_name)
                if anchor_id not in seen:
                    seen.add(anchor_id)
                    anchors.append(FlowAnchor(
                        anchor_id=anchor_id,
                        anchor_type=AnchorType.CLASS,
                        value=cls_name,
                        component_id=component_id,
                        artifact_id=artifact_id,
                        evidence_strength=EvidenceLevel.REFERENCE
                    ))

                # Network-related methods
                for method in cls.get('methods', []):
                    selector = method.get('selector', '')
                    if any(p in selector.lower() for p in self.NETWORK_METHOD_PATTERNS):
                        anchor_id = generate_anchor_id(AnchorType.SELECTOR.value, selector)
                        if anchor_id not in seen:
                            seen.add(anchor_id)
                            anchors.append(FlowAnchor(
                                anchor_id=anchor_id,
                                anchor_type=AnchorType.SELECTOR,
                                value=selector,
                                component_id=component_id,
                                artifact_id=artifact_id,
                                evidence_strength=EvidenceLevel.REFERENCE
                            ))

        # From network endpoints
        if network_endpoints:
            for ep in network_endpoints:
                value = ep.get('full_url', ep.get('host', ''))
                if value:
                    anchor_id = generate_anchor_id(AnchorType.ENDPOINT.value, value)
                    if anchor_id not in seen:
                        seen.add(anchor_id)
                        anchors.append(FlowAnchor(
                            anchor_id=anchor_id,
                            anchor_type=AnchorType.ENDPOINT,
                            value=value,
                            component_id=component_id,
                            artifact_id=artifact_id,
                            evidence_strength=EvidenceLevel.REFERENCE
                        ))

        return anchors

    def create_nodes(
        self,
        objc_metadata: Optional[Dict] = None,
        swift_metadata: Optional[Dict] = None,
        symbols: Optional[List[Dict]] = None,
        component_id: Optional[str] = None,
        artifact_id: Optional[str] = None
    ) -> List[FunctionNode]:
        """
        Create function/method nodes from metadata.
        """
        nodes = []
        seen = set()

        # From ObjC methods
        if objc_metadata:
            for cls in objc_metadata.get('classes', []):
                cls_name = cls.get('name', '')
                for method in cls.get('methods', []):
                    selector = method.get('selector', '')
                    if not selector:
                        continue

                    # Generate node ID
                    address = method.get('address')
                    node_id = generate_node_id(selector, artifact_id or '', address)

                    if node_id in seen:
                        continue
                    seen.add(node_id)

                    # Determine method type
                    is_class_method = selector.startswith('+')
                    is_init = selector.startswith('-') and ('init' in selector or 'initWith' in selector)

                    nodes.append(FunctionNode(
                        node_id=node_id,
                        name=selector,
                        is_method=True,
                        is_init=is_init,
                        is_class_method=is_class_method,
                        component_id=component_id,
                        artifact_id=artifact_id,
                        address=address,
                        selector=selector,
                        evidence_level=EvidenceLevel.REFERENCE
                    ))

        # From Swift functions
        if swift_metadata:
            for typ in swift_metadata.get('types', []):
                type_name = typ.get('name', '')
                for method in typ.get('methods', []):
                    name = method.get('name', '')
                    if not name:
                        continue

                    node_id = generate_node_id(name, artifact_id or '', None)
                    if node_id in seen:
                        continue
                    seen.add(node_id)

                    nodes.append(FunctionNode(
                        node_id=node_id,
                        name=name,
                        demangled_name=name,
                        is_method=True,
                        component_id=component_id,
                        artifact_id=artifact_id,
                        swift_type=type_name,
                        evidence_level=EvidenceLevel.REFERENCE
                    ))

        # From symbols
        if symbols:
            for sym in symbols[:200]:  # Limit
                name = sym.get('name', '')
                if not name or name.startswith('_'):
                    continue

                node_id = generate_node_id(name, artifact_id or '', sym.get('address'))
                if node_id in seen:
                    continue
                seen.add(node_id)

                nodes.append(FunctionNode(
                    node_id=node_id,
                    name=name,
                    component_id=component_id,
                    artifact_id=artifact_id,
                    address=sym.get('address'),
                    evidence_level=EvidenceLevel.REFERENCE
                ))

        return nodes

    def reconstruct_edges(
        self,
        nodes: List[FunctionNode],
        objc_metadata: Optional[Dict] = None,
        swift_metadata: Optional[Dict] = None,
        anchors: Optional[List[FlowAnchor]] = None
    ) -> Tuple[List[CallEdge], List[UnresolvedTarget]]:
        """
        Reconstruct call edges from metadata.

        Returns:
            Tuple of (edges, unresolved_targets)
        """
        edges = []
        unresolved = []
        seen = set()

        # Build node lookup by name
        node_by_name = {}
        for node in nodes:
            name = node.selector or node.name
            if name not in node_by_name:
                node_by_name[name] = []
            node_by_name[name].append(node)

        # Build anchor lookup
        anchor_by_value = {}
        if anchors:
            for anchor in anchors:
                if anchor.value not in anchor_by_value:
                    anchor_by_value[anchor.value] = []
                anchor_by_value[anchor.value].append(anchor)

        # Process ObjC metadata for references
        if objc_metadata:
            for cls in objc_metadata.get('classes', []):
                cls_name = cls.get('name', '')

                # Get source node(s)
                source_nodes = node_by_name.get(cls_name, [])

                # Outbound references from this class
                for ref in cls.get('references', [])[:50]:
                    # Check if target exists
                    target_nodes = node_by_name.get(ref, [])

                    if not target_nodes:
                        # Unresolved target
                        for src in source_nodes[:1]:  # Only one unresolved per source
                            key = f"{src.node_id}:{ref}"
                            if key not in seen:
                                seen.add(key)
                                unresolved.append(UnresolvedTarget(
                                    unresolved_id=f"unres-{len(unresolved)}",
                                    name=ref,
                                    source_id=src.node_id,
                                    reason="no_symbol",
                                    evidence_level=EvidenceLevel.WEAK,
                                    evidence_sources=[f"objc:{cls_name} references {ref}"]
                                ))
                    else:
                        # Create edges to found targets
                        for src in source_nodes[:1]:  # Primary source
                            for tgt in target_nodes[:3]:  # Limit targets
                                edge_id = generate_edge_id(src.node_id, tgt.node_id, None)
                                if edge_id not in seen:
                                    seen.add(edge_id)

                                    # Determine edge type
                                    if ref in anchor_by_value:
                                        edge_type = EdgeType.CONFIRMED_CALL
                                        evidence = EvidenceLevel.STRUCTURAL
                                    else:
                                        edge_type = EdgeType.REFERENCE
                                        evidence = EvidenceLevel.REFERENCE

                                    edges.append(CallEdge(
                                        edge_id=edge_id,
                                        source_id=src.node_id,
                                        target_id=tgt.node_id,
                                        edge_type=edge_type,
                                        evidence_level=evidence,
                                        evidence_sources=[f"objc:{cls_name} references {ref}"]
                                    ))

        return edges, unresolved

    def link_anchors_to_nodes(
        self,
        anchors: List[FlowAnchor],
        nodes: List[FunctionNode]
    ) -> List[FlowAnchor]:
        """
        Link anchors to nodes that reference them.

        Updates anchors in place to track referencing nodes.
        """
        # Build node lookup by name/selector
        node_names = {}
        for node in nodes:
            name = node.selector or node.name
            if name not in node_names:
                node_names[name] = []
            node_names[name].append(node)

        # Build selector/function lookup for anchor values
        for anchor in anchors:
            if anchor.anchor_type == AnchorType.ENDPOINT:
                # Look for methods that reference this URL
                for node_name, node_list in node_names.items():
                    if anchor.value in node_name or node_name in anchor.value:
                        for node in node_list[:1]:
                            anchor.referencing_nodes.append(node.node_id)
                            node.anchors.append(anchor.anchor_id)
            elif anchor.anchor_type in (AnchorType.SELECTOR, AnchorType.FUNCTION):
                # Direct method reference
                if anchor.value in node_names:
                    for node in node_names[anchor.value][:1]:
                        anchor.referencing_nodes.append(node.node_id)
                        node.anchors.append(anchor.anchor_id)

        return anchors

    def build_model(
        self,
        strings_data: str = "",
        objc_metadata: Optional[Dict] = None,
        swift_metadata: Optional[Dict] = None,
        symbols: Optional[List[Dict]] = None,
        network_endpoints: Optional[List[Dict]] = None,
        component_id: Optional[str] = None,
        artifact_id: Optional[str] = None,
        artifact_path: str = ""
    ) -> CallFlow:
        """
        Build complete callflow model.
        """
        # Create anchors
        anchors = self.create_anchors(
            strings_data, objc_metadata, swift_metadata,
            network_endpoints, component_id, artifact_id
        )

        # Create nodes
        nodes = self.create_nodes(
            objc_metadata, swift_metadata, symbols,
            component_id, artifact_id
        )

        # Link anchors to nodes
        anchors = self.link_anchors_to_nodes(anchors, nodes)

        # Reconstruct edges
        edges, unresolved = self.reconstruct_edges(
            nodes, objc_metadata, swift_metadata, anchors
        )

        # Build model
        model = CallFlow(
            artifact_path=artifact_path,
            anchors=anchors,
            nodes=nodes,
            edges=edges,
            unresolved=unresolved,
        )

        # Build indexes
        model.build_indexes()

        # Compute statistics
        model.compute_statistics()

        return model
