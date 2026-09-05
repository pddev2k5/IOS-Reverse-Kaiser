"""
Workflow Definitions for IOS REVERSE KAISER.

Defines all canonical workflows as declarative DAGs.
"""

from .schema import (
    WorkflowDefinition, WorkflowNode, WorkflowEdge, WorkflowCondition,
    CoveragePolicy, ToolEscalationPolicy, AgentPolicy,
    OutputArtifact, StopCondition, SuccessCondition,
    Depth, Intent, WorkflowStatus, Complexity, NodeStatus
)


def create_unpack_workflow() -> WorkflowDefinition:
    """Create the ios.unpack workflow."""
    nodes = [
        WorkflowNode(
            node_id="artifact_detect",
            capability_id="foundation.artifact_detect",
            description="Detect and validate artifact type",
            dependencies=[],
        ),
        WorkflowNode(
            node_id="ipa_validate",
            capability_id="foundation.ipa_validate",
            description="Validate IPA structure",
            dependencies=["artifact_detect"],
        ),
        WorkflowNode(
            node_id="ipa_unpack",
            capability_id="foundation.ipa_unpack",
            description="Extract IPA contents",
            dependencies=["ipa_validate"],
        ),
        WorkflowNode(
            node_id="bundle_inventory",
            capability_id="foundation.bundle_inventory",
            description="Inventory bundle contents",
            dependencies=["ipa_unpack"],
        ),
        WorkflowNode(
            node_id="manifest",
            description="Generate extraction manifest",
            dependencies=["bundle_inventory"],
        ),
    ]

    edges = [
        WorkflowEdge(from_node="artifact_detect", to_node="ipa_validate"),
        WorkflowEdge(from_node="ipa_validate", to_node="ipa_unpack"),
        WorkflowEdge(from_node="ipa_unpack", to_node="bundle_inventory"),
        WorkflowEdge(from_node="bundle_inventory", to_node="manifest"),
    ]

    return WorkflowDefinition(
        workflow_id="ios.unpack",
        intent=Intent.UNPACK.value,
        status=WorkflowStatus.IMPLEMENTED,
        accepted_artifacts=["ipa", "app"],
        default_depth=Depth.QUICK,
        supported_depths=[Depth.QUICK, Depth.STANDARD, Depth.DEEP, Depth.FULL],
        nodes=nodes,
        edges=edges,
        entry_node="artifact_detect",
        terminal_nodes=["manifest"],
        complexity=Complexity.LOW,
        stop_conditions=[
            StopCondition("all_terminal_nodes_complete", "All extraction complete"),
        ],
        success_conditions=[
            SuccessCondition("app_extracted", "App extracted to disk"),
            SuccessCondition("manifest_generated", "Bundle manifest available"),
        ],
        outputs=[
            OutputArtifact("extracted_app", "outputs/{workflow}/Payload/"),
            OutputArtifact("manifest", "outputs/{workflow}/manifest.json"),
        ],
        resume_enabled=True,
    )


def create_inspect_workflow() -> WorkflowDefinition:
    """Create the ios.inspect workflow."""
    nodes = [
        # Foundation
        WorkflowNode(
            node_id="artifact_detect",
            capability_id="foundation.artifact_detect",
            description="Detect artifact type",
            dependencies=[],
        ),
        WorkflowNode(
            node_id="ipa_validate",
            capability_id="foundation.ipa_validate",
            description="Validate IPA",
            dependencies=["artifact_detect"],
        ),
        WorkflowNode(
            node_id="ipa_unpack",
            capability_id="foundation.ipa_unpack",
            description="Extract IPA",
            dependencies=["ipa_validate"],
        ),
        WorkflowNode(
            node_id="bundle_inventory",
            capability_id="foundation.bundle_inventory",
            description="Inventory bundle",
            dependencies=["ipa_unpack"],
        ),
        WorkflowNode(
            node_id="plist_extract",
            capability_id="foundation.plist_extract",
            description="Extract Info.plist",
            dependencies=["bundle_inventory"],
        ),
        WorkflowNode(
            node_id="entitlements_extract",
            capability_id="foundation.entitlements_extract",
            description="Extract entitlements",
            dependencies=["bundle_inventory"],
        ),
        # Component inventory
        WorkflowNode(
            node_id="framework_inventory",
            capability_id="framework.inventory",
            description="Inventory frameworks",
            dependencies=["bundle_inventory"],
        ),
        WorkflowNode(
            node_id="dylib_inventory",
            capability_id="dylib.inventory",
            description="Inventory dylibs",
            dependencies=["bundle_inventory"],
        ),
        WorkflowNode(
            node_id="extension_inventory",
            capability_id="extension.inventory",
            description="Inventory extensions",
            dependencies=["bundle_inventory"],
        ),
        # Basic Mach-O
        WorkflowNode(
            node_id="macho_basic",
            capability_id="macho.basic",
            description="Basic Mach-O analysis",
            dependencies=["bundle_inventory"],
            depth_profiles={Depth.QUICK: True, Depth.STANDARD: True, Depth.DEEP: True, Depth.FULL: True},
        ),
        # Fingerprint
        WorkflowNode(
            node_id="fingerprint",
            description="Generate application fingerprint",
            dependencies=["plist_extract", "entitlements_extract", "framework_inventory", "macho_basic"],
        ),
    ]

    edges = [
        WorkflowEdge(from_node="artifact_detect", to_node="ipa_validate"),
        WorkflowEdge(from_node="ipa_validate", to_node="ipa_unpack"),
        WorkflowEdge(from_node="ipa_unpack", to_node="bundle_inventory"),
        WorkflowEdge(from_node="bundle_inventory", to_node="plist_extract"),
        WorkflowEdge(from_node="bundle_inventory", to_node="entitlements_extract"),
        WorkflowEdge(from_node="bundle_inventory", to_node="framework_inventory"),
        WorkflowEdge(from_node="bundle_inventory", to_node="dylib_inventory"),
        WorkflowEdge(from_node="bundle_inventory", to_node="extension_inventory"),
        WorkflowEdge(from_node="bundle_inventory", to_node="macho_basic"),
        WorkflowEdge(from_node="plist_extract", to_node="fingerprint"),
        WorkflowEdge(from_node="entitlements_extract", to_node="fingerprint"),
        WorkflowEdge(from_node="framework_inventory", to_node="fingerprint"),
        WorkflowEdge(from_node="macho_basic", to_node="fingerprint"),
    ]

    return WorkflowDefinition(
        workflow_id="ios.inspect",
        intent=Intent.INSPECT.value,
        status=WorkflowStatus.IMPLEMENTED,
        accepted_artifacts=["ipa", "app"],
        default_depth=Depth.STANDARD,
        supported_depths=[Depth.QUICK, Depth.STANDARD, Depth.DEEP, Depth.FULL],
        nodes=nodes,
        edges=edges,
        entry_node="artifact_detect",
        terminal_nodes=["fingerprint"],
        complexity=Complexity.MEDIUM,
        stop_conditions=[
            StopCondition("fingerprint_complete", "Fingerprint generated"),
        ],
        success_conditions=[
            SuccessCondition("bundle_identified", "Bundle info available"),
            SuccessCondition("components_inventoried", "Component inventory complete"),
        ],
        outputs=[
            OutputArtifact("fingerprint", "outputs/{workflow}/fingerprint.json"),
            OutputArtifact("bundle_manifest", "outputs/{workflow}/manifest.json"),
        ],
        resume_enabled=True,
    )


def create_dump_workflow() -> WorkflowDefinition:
    """Create the ios.dump workflow."""
    nodes = [
        # Foundation
        WorkflowNode(
            node_id="artifact_detect",
            capability_id="foundation.artifact_detect",
            description="Detect artifact",
            dependencies=[],
        ),
        WorkflowNode(
            node_id="ipa_validate",
            capability_id="foundation.ipa_validate",
            description="Validate IPA",
            dependencies=["artifact_detect"],
        ),
        WorkflowNode(
            node_id="ipa_unpack",
            capability_id="foundation.ipa_unpack",
            description="Extract IPA",
            dependencies=["ipa_validate"],
        ),
        WorkflowNode(
            node_id="bundle_inventory",
            capability_id="foundation.bundle_inventory",
            description="Inventory bundle",
            dependencies=["ipa_unpack"],
        ),
        WorkflowNode(
            node_id="component_graph",
            description="Build component graph",
            dependencies=["bundle_inventory"],
            sub_workflow="ios.component-graph",
        ),
        # Component inventory
        WorkflowNode(
            node_id="framework_inventory",
            capability_id="framework.inventory",
            description="Inventory frameworks",
            dependencies=["bundle_inventory"],
        ),
        WorkflowNode(
            node_id="dylib_inventory",
            capability_id="dylib.inventory",
            description="Inventory dylibs",
            dependencies=["bundle_inventory"],
        ),
        WorkflowNode(
            node_id="extension_inventory",
            capability_id="extension.inventory",
            description="Inventory extensions",
            dependencies=["bundle_inventory"],
        ),
        # Mach-O analysis - depth controlled
        WorkflowNode(
            node_id="macho_basic",
            capability_id="macho.basic",
            description="Basic Mach-O",
            dependencies=["component_graph"],
            depth_profiles={Depth.QUICK: True, Depth.STANDARD: True, Depth.DEEP: True, Depth.FULL: True},
        ),
        WorkflowNode(
            node_id="macho_slices",
            capability_id="macho.slices",
            description="Architecture slices",
            dependencies=["macho_basic"],
            depth_profiles={Depth.STANDARD: True, Depth.DEEP: True, Depth.FULL: True},
        ),
        WorkflowNode(
            node_id="macho_load_commands",
            capability_id="macho.load_commands",
            description="Load commands",
            dependencies=["macho_basic"],
            depth_profiles={Depth.STANDARD: True, Depth.DEEP: True, Depth.FULL: True},
        ),
        # Binary analysis
        WorkflowNode(
            node_id="binary_imports",
            capability_id="binary.imports",
            description="Import symbols",
            dependencies=["macho_basic"],
            depth_profiles={Depth.STANDARD: True, Depth.DEEP: True, Depth.FULL: True},
        ),
        WorkflowNode(
            node_id="binary_exports",
            capability_id="binary.exports",
            description="Export symbols",
            dependencies=["macho_basic"],
            depth_profiles={Depth.STANDARD: True, Depth.DEEP: True, Depth.FULL: True},
        ),
        WorkflowNode(
            node_id="binary_symbols",
            capability_id="binary.symbols",
            description="Symbol table",
            dependencies=["macho_basic"],
            depth_profiles={Depth.STANDARD: True, Depth.DEEP: True, Depth.FULL: True},
        ),
        WorkflowNode(
            node_id="binary_strings",
            capability_id="binary.strings",
            description="String extraction",
            dependencies=["macho_basic"],
            depth_profiles={Depth.QUICK: True, Depth.STANDARD: True, Depth.DEEP: True, Depth.FULL: True},
        ),
        # Metadata
        WorkflowNode(
            node_id="objc_metadata",
            capability_id="objc.metadata",
            description="Objective-C metadata",
            dependencies=["macho_basic"],
            depth_profiles={Depth.STANDARD: True, Depth.DEEP: True, Depth.FULL: True},
        ),
        WorkflowNode(
            node_id="objc_deep_metadata",
            capability_id="objc.deep_metadata",
            description="Deep ObjC metadata",
            dependencies=["objc_metadata"],
            depth_profiles={Depth.DEEP: True, Depth.FULL: True},
        ),
        WorkflowNode(
            node_id="swift_metadata",
            capability_id="swift.metadata",
            description="Swift metadata",
            dependencies=["macho_basic"],
            depth_profiles={Depth.STANDARD: True, Depth.DEEP: True, Depth.FULL: True},
        ),
        WorkflowNode(
            node_id="swift_demangle",
            capability_id="swift.demangle",
            description="Swift demangling",
            dependencies=["swift_metadata"],
            depth_profiles={Depth.DEEP: True, Depth.FULL: True},
        ),
        # Coverage (full only)
        WorkflowNode(
            node_id="coverage_audit",
            capability_id="coverage.calculation",
            description="Coverage audit",
            dependencies=["macho_basic", "objc_metadata", "swift_metadata"],
            depth_profiles={Depth.FULL: True},
        ),
        # Dump artifacts
        WorkflowNode(
            node_id="dump_artifacts",
            description="Generate dump artifacts",
            dependencies=["macho_slices", "macho_load_commands", "binary_imports", "binary_exports", "binary_symbols", "binary_strings", "objc_metadata", "objc_deep_metadata", "swift_metadata", "swift_demangle"],
            depth_profiles={Depth.STANDARD: True, Depth.DEEP: True, Depth.FULL: True},
        ),
    ]

    edges = [
        WorkflowEdge(from_node="artifact_detect", to_node="ipa_validate"),
        WorkflowEdge(from_node="ipa_validate", to_node="ipa_unpack"),
        WorkflowEdge(from_node="ipa_unpack", to_node="bundle_inventory"),
        WorkflowEdge(from_node="bundle_inventory", to_node="component_graph"),
        WorkflowEdge(from_node="bundle_inventory", to_node="framework_inventory"),
        WorkflowEdge(from_node="bundle_inventory", to_node="dylib_inventory"),
        WorkflowEdge(from_node="bundle_inventory", to_node="extension_inventory"),
        WorkflowEdge(from_node="component_graph", to_node="macho_basic"),
        WorkflowEdge(from_node="macho_basic", to_node="macho_slices"),
        WorkflowEdge(from_node="macho_basic", to_node="macho_load_commands"),
        WorkflowEdge(from_node="macho_basic", to_node="binary_imports"),
        WorkflowEdge(from_node="macho_basic", to_node="binary_exports"),
        WorkflowEdge(from_node="macho_basic", to_node="binary_symbols"),
        WorkflowEdge(from_node="macho_basic", to_node="binary_strings"),
        WorkflowEdge(from_node="macho_basic", to_node="objc_metadata"),
        WorkflowEdge(from_node="macho_basic", to_node="swift_metadata"),
        WorkflowEdge(from_node="objc_metadata", to_node="objc_deep_metadata"),
        WorkflowEdge(from_node="swift_metadata", to_node="swift_demangle"),
        WorkflowEdge(from_node="macho_basic", to_node="coverage_audit"),
        WorkflowEdge(from_node="objc_metadata", to_node="coverage_audit"),
        WorkflowEdge(from_node="swift_metadata", to_node="coverage_audit"),
    ]

    return WorkflowDefinition(
        workflow_id="ios.dump",
        intent=Intent.DUMP.value,
        status=WorkflowStatus.IMPLEMENTED,
        accepted_artifacts=["ipa", "app"],
        default_depth=Depth.STANDARD,
        supported_depths=[Depth.QUICK, Depth.STANDARD, Depth.DEEP, Depth.FULL],
        nodes=nodes,
        edges=edges,
        entry_node="artifact_detect",
        terminal_nodes=["dump_artifacts", "coverage_audit"],
        complexity=Complexity.HIGH,
        stop_conditions=[
            StopCondition("dump_artifacts_complete", "Binary metadata dumped"),
            StopCondition("coverage_complete", "Coverage audited (full only)"),
        ],
        success_conditions=[
            SuccessCondition("components_analyzed", "All eligible binaries analyzed"),
            SuccessCondition("metadata_extracted", "Metadata available"),
        ],
        outputs=[
            OutputArtifact("binary_metadata", "outputs/{workflow}/binary/"),
            OutputArtifact("objc_metadata", "outputs/{workflow}/objc/"),
            OutputArtifact("swift_metadata", "outputs/{workflow}/swift/"),
            OutputArtifact("coverage_report", "outputs/{workflow}/coverage.json"),
        ],
        coverage_policy=CoveragePolicy(
            policy_id="dump-full",
            workflow="dump",
            depth="full",
            required_dimensions=["binary", "macho_structure", "objc_metadata", "swift_metadata"],
        ),
        resume_enabled=True,
    )


def create_macho_workflow() -> WorkflowDefinition:
    """Create the ios.macho workflow."""
    nodes = [
        WorkflowNode(
            node_id="artifact_detect",
            capability_id="foundation.artifact_detect",
            description="Detect artifact",
            dependencies=[],
        ),
        WorkflowNode(
            node_id="ipa_unpack",
            capability_id="foundation.ipa_unpack",
            description="Extract if needed",
            dependencies=["artifact_detect"],
            optional=True,
        ),
        WorkflowNode(
            node_id="macho_basic",
            capability_id="macho.basic",
            description="Basic Mach-O analysis",
            dependencies=["artifact_detect"],
        ),
        WorkflowNode(
            node_id="macho_slices",
            capability_id="macho.slices",
            description="Architecture slices",
            dependencies=["macho_basic"],
            depth_profiles={Depth.STANDARD: True, Depth.DEEP: True, Depth.FULL: True},
        ),
        WorkflowNode(
            node_id="macho_load_commands",
            capability_id="macho.load_commands",
            description="Load commands",
            dependencies=["macho_basic"],
            depth_profiles={Depth.STANDARD: True, Depth.DEEP: True, Depth.FULL: True},
        ),
        WorkflowNode(
            node_id="binary_imports",
            capability_id="binary.imports",
            description="Import symbols",
            dependencies=["macho_basic"],
            depth_profiles={Depth.DEEP: True, Depth.FULL: True},
        ),
        WorkflowNode(
            node_id="binary_exports",
            capability_id="binary.exports",
            description="Export symbols",
            dependencies=["macho_basic"],
            depth_profiles={Depth.DEEP: True, Depth.FULL: True},
        ),
        WorkflowNode(
            node_id="binary_symbols",
            capability_id="binary.symbols",
            description="Symbol table",
            dependencies=["macho_basic"],
            depth_profiles={Depth.DEEP: True, Depth.FULL: True},
        ),
    ]

    edges = [
        WorkflowEdge(from_node="artifact_detect", to_node="ipa_unpack"),
        WorkflowEdge(from_node="artifact_detect", to_node="macho_basic"),
        WorkflowEdge(from_node="macho_basic", to_node="macho_slices"),
        WorkflowEdge(from_node="macho_basic", to_node="macho_load_commands"),
        WorkflowEdge(from_node="macho_basic", to_node="binary_imports"),
        WorkflowEdge(from_node="macho_basic", to_node="binary_exports"),
        WorkflowEdge(from_node="macho_basic", to_node="binary_symbols"),
    ]

    return WorkflowDefinition(
        workflow_id="ios.macho",
        intent=Intent.MACHO.value,
        status=WorkflowStatus.IMPLEMENTED,
        accepted_artifacts=["ipa", "app", "framework", "dylib", "macho"],
        default_depth=Depth.STANDARD,
        supported_depths=[Depth.QUICK, Depth.STANDARD, Depth.DEEP, Depth.FULL],
        nodes=nodes,
        edges=edges,
        entry_node="artifact_detect",
        terminal_nodes=["binary_symbols"],
        complexity=Complexity.MEDIUM,
        stop_conditions=[
            StopCondition("macho_analysis_complete", "Mach-O analysis complete"),
        ],
        success_conditions=[
            SuccessCondition("architecture_identified", "Architecture detected"),
            SuccessCondition("structure_analyzed", "Mach-O structure analyzed"),
        ],
        outputs=[
            OutputArtifact("macho_report", "outputs/{workflow}/macho.json"),
        ],
        resume_enabled=True,
    )


def create_objc_workflow() -> WorkflowDefinition:
    """Create the ios.objc workflow."""
    nodes = [
        WorkflowNode(
            node_id="artifact_detect",
            capability_id="foundation.artifact_detect",
            description="Detect artifact",
            dependencies=[],
        ),
        WorkflowNode(
            node_id="macho_basic",
            capability_id="macho.basic",
            description="Mach-O prerequisite",
            dependencies=["artifact_detect"],
        ),
        WorkflowNode(
            node_id="objc_metadata",
            capability_id="objc.metadata",
            description="Objective-C metadata",
            dependencies=["macho_basic"],
            depth_profiles={Depth.QUICK: True, Depth.STANDARD: True, Depth.DEEP: True, Depth.FULL: True},
        ),
        WorkflowNode(
            node_id="objc_deep_metadata",
            capability_id="objc.deep_metadata",
            description="Deep ObjC metadata",
            dependencies=["objc_metadata"],
            depth_profiles={Depth.STANDARD: True, Depth.DEEP: True, Depth.FULL: True},
        ),
    ]

    edges = [
        WorkflowEdge(from_node="artifact_detect", to_node="macho_basic"),
        WorkflowEdge(from_node="macho_basic", to_node="objc_metadata"),
        WorkflowEdge(from_node="objc_metadata", to_node="objc_deep_metadata"),
    ]

    return WorkflowDefinition(
        workflow_id="ios.objc",
        intent=Intent.OBJC.value,
        status=WorkflowStatus.IMPLEMENTED,
        accepted_artifacts=["ipa", "app", "framework", "macho"],
        default_depth=Depth.STANDARD,
        supported_depths=[Depth.QUICK, Depth.STANDARD, Depth.DEEP, Depth.FULL],
        nodes=nodes,
        edges=edges,
        entry_node="artifact_detect",
        terminal_nodes=["objc_deep_metadata"],
        complexity=Complexity.MEDIUM,
        stop_conditions=[
            StopCondition("objc_analysis_complete", "ObjC analysis complete"),
        ],
        success_conditions=[
            SuccessCondition("classes_identified", "ObjC classes found"),
        ],
        outputs=[
            OutputArtifact("objc_report", "outputs/{workflow}/objc.json"),
        ],
        resume_enabled=True,
    )


def create_swift_workflow() -> WorkflowDefinition:
    """Create the ios.swift workflow."""
    nodes = [
        WorkflowNode(
            node_id="artifact_detect",
            capability_id="foundation.artifact_detect",
            description="Detect artifact",
            dependencies=[],
        ),
        WorkflowNode(
            node_id="macho_basic",
            capability_id="macho.basic",
            description="Mach-O prerequisite",
            dependencies=["artifact_detect"],
        ),
        WorkflowNode(
            node_id="swift_metadata",
            capability_id="swift.metadata",
            description="Swift metadata",
            dependencies=["macho_basic"],
            depth_profiles={Depth.QUICK: True, Depth.STANDARD: True, Depth.DEEP: True, Depth.FULL: True},
        ),
        WorkflowNode(
            node_id="swift_demangle",
            capability_id="swift.demangle",
            description="Swift demangling",
            dependencies=["swift_metadata"],
            depth_profiles={Depth.STANDARD: True, Depth.DEEP: True, Depth.FULL: True},
        ),
    ]

    edges = [
        WorkflowEdge(from_node="artifact_detect", to_node="macho_basic"),
        WorkflowEdge(from_node="macho_basic", to_node="swift_metadata"),
        WorkflowEdge(from_node="swift_metadata", to_node="swift_demangle"),
    ]

    return WorkflowDefinition(
        workflow_id="ios.swift",
        intent=Intent.SWIFT.value,
        status=WorkflowStatus.IMPLEMENTED,
        accepted_artifacts=["ipa", "app", "framework", "macho"],
        default_depth=Depth.STANDARD,
        supported_depths=[Depth.QUICK, Depth.STANDARD, Depth.DEEP, Depth.FULL],
        nodes=nodes,
        edges=edges,
        entry_node="artifact_detect",
        terminal_nodes=["swift_demangle"],
        complexity=Complexity.MEDIUM,
        stop_conditions=[
            StopCondition("swift_analysis_complete", "Swift analysis complete"),
        ],
        success_conditions=[
            SuccessCondition("swift_modules_identified", "Swift modules found"),
        ],
        outputs=[
            OutputArtifact("swift_report", "outputs/{workflow}/swift.json"),
        ],
        resume_enabled=True,
    )


def create_network_workflow() -> WorkflowDefinition:
    """Create the ios.network workflow."""
    nodes = [
        # Foundation
        WorkflowNode(
            node_id="artifact_detect",
            capability_id="foundation.artifact_detect",
            description="Detect artifact",
            dependencies=[],
        ),
        WorkflowNode(
            node_id="dump_standard",
            description="Standard dump prerequisites",
            dependencies=["artifact_detect"],
            sub_workflow="ios.dump",
            depth_profiles={Depth.STANDARD: True, Depth.DEEP: True, Depth.FULL: True},
        ),
        # Network analysis
        WorkflowNode(
            node_id="network_framework_detection",
            capability_id="network.framework_detection",
            description="Network framework detection",
            dependencies=["dump_standard"],
            depth_profiles={Depth.QUICK: True, Depth.STANDARD: True, Depth.DEEP: True, Depth.FULL: True},
        ),
        WorkflowNode(
            node_id="network_endpoint_discovery",
            capability_id="network.endpoint_discovery",
            description="Endpoint discovery",
            dependencies=["dump_standard"],
            depth_profiles={Depth.QUICK: True, Depth.STANDARD: True, Depth.DEEP: True, Depth.FULL: True},
        ),
        WorkflowNode(
            node_id="architecture_detection",
            capability_id="architecture.detection",
            description="Architecture pattern detection",
            dependencies=["dump_standard"],
            depth_profiles={Depth.DEEP: True, Depth.FULL: True},
        ),
        WorkflowNode(
            node_id="callflow_reconstruct",
            capability_id="callflow.reconstruct",
            description="Callflow reconstruction",
            dependencies=["dump_standard"],
            depth_profiles={Depth.DEEP: True, Depth.FULL: True},
        ),
        # Coverage
        WorkflowNode(
            node_id="coverage_audit",
            capability_id="coverage.calculation",
            description="Coverage audit",
            dependencies=["network_framework_detection", "network_endpoint_discovery"],
            depth_profiles={Depth.FULL: True},
        ),
        # Network dossier
        WorkflowNode(
            node_id="network_dossier",
            description="Generate network dossier",
            dependencies=["network_framework_detection", "network_endpoint_discovery", "architecture_detection", "callflow_reconstruct"],
        ),
    ]

    edges = [
        WorkflowEdge(from_node="artifact_detect", to_node="dump_standard"),
        WorkflowEdge(from_node="dump_standard", to_node="network_framework_detection"),
        WorkflowEdge(from_node="dump_standard", to_node="network_endpoint_discovery"),
        WorkflowEdge(from_node="dump_standard", to_node="architecture_detection"),
        WorkflowEdge(from_node="dump_standard", to_node="callflow_reconstruct"),
        WorkflowEdge(from_node="network_framework_detection", to_node="coverage_audit"),
        WorkflowEdge(from_node="network_endpoint_discovery", to_node="coverage_audit"),
        WorkflowEdge(from_node="network_framework_detection", to_node="network_dossier"),
        WorkflowEdge(from_node="network_endpoint_discovery", to_node="network_dossier"),
        WorkflowEdge(from_node="architecture_detection", to_node="network_dossier"),
        WorkflowEdge(from_node="callflow_reconstruct", to_node="network_dossier"),
    ]

    return WorkflowDefinition(
        workflow_id="ios.network",
        intent=Intent.NETWORK.value,
        status=WorkflowStatus.IMPLEMENTED,
        accepted_artifacts=["ipa", "app"],
        default_depth=Depth.STANDARD,
        supported_depths=[Depth.QUICK, Depth.STANDARD, Depth.DEEP, Depth.FULL],
        nodes=nodes,
        edges=edges,
        entry_node="artifact_detect",
        terminal_nodes=["network_dossier", "coverage_audit"],
        complexity=Complexity.HIGH,
        agent_policy=AgentPolicy(
            allowed_agents=["artifact-analyst", "network-analyst", "evidence-validator"],
            required_agents=["network-analyst"],
        ),
        stop_conditions=[
            StopCondition("endpoints_discovered", "Network endpoints analyzed"),
            StopCondition("coverage_complete", "Coverage audited (full only)"),
        ],
        success_conditions=[
            SuccessCondition("framework_presence_identified", "Network frameworks identified"),
            SuccessCondition("endpoint_candidates_found", "Endpoint candidates discovered"),
        ],
        outputs=[
            OutputArtifact("network_report", "outputs/{workflow}/network.json"),
            OutputArtifact("endpoints", "outputs/{workflow}/endpoints/"),
            OutputArtifact("coverage_report", "outputs/{workflow}/coverage.json"),
        ],
        coverage_policy=CoveragePolicy(
            policy_id="network-full",
            workflow="network",
            depth="full",
            required_dimensions=["network", "architecture", "callflow"],
        ),
        resume_enabled=True,
    )


def create_login_flow_workflow() -> WorkflowDefinition:
    """Create the ios.login-flow workflow."""
    nodes = [
        # Foundation
        WorkflowNode(
            node_id="artifact_detect",
            capability_id="foundation.artifact_detect",
            description="Detect artifact",
            dependencies=[],
        ),
        WorkflowNode(
            node_id="network_analysis",
            description="Network analysis prerequisites",
            dependencies=["artifact_detect"],
            sub_workflow="ios.network",
        ),
        # Login anchors
        WorkflowNode(
            node_id="login_anchors",
            description="Discover login/auth anchors",
            dependencies=["network_analysis"],
        ),
        WorkflowNode(
            node_id="auth_services",
            description="Identify auth services",
            dependencies=["login_anchors"],
        ),
        # Correlation
        WorkflowNode(
            node_id="architecture_correlation",
            capability_id="architecture.detection",
            description="Architecture correlation",
            dependencies=["network_analysis"],
        ),
        WorkflowNode(
            node_id="callflow_reconstruction",
            capability_id="callflow.reconstruct",
            description="Callflow reconstruction",
            dependencies=["network_analysis"],
        ),
        # Request builders
        WorkflowNode(
            node_id="request_builder_candidates",
            description="Identify request builder candidates",
            dependencies=["auth_services", "callflow_reconstruction"],
        ),
        # Gaps
        WorkflowNode(
            node_id="unresolved_gaps",
            description="Record unresolved gaps",
            dependencies=["request_builder_candidates"],
        ),
        # Login flow dossier
        WorkflowNode(
            node_id="login_flow_dossier",
            description="Generate login flow dossier",
            dependencies=["login_anchors", "auth_services", "architecture_correlation", "callflow_reconstruction", "request_builder_candidates", "unresolved_gaps"],
        ),
    ]

    edges = [
        WorkflowEdge(from_node="artifact_detect", to_node="network_analysis"),
        WorkflowEdge(from_node="network_analysis", to_node="login_anchors"),
        WorkflowEdge(from_node="network_analysis", to_node="architecture_correlation"),
        WorkflowEdge(from_node="network_analysis", to_node="callflow_reconstruction"),
        WorkflowEdge(from_node="login_anchors", to_node="auth_services"),
        WorkflowEdge(from_node="auth_services", to_node="request_builder_candidates"),
        WorkflowEdge(from_node="callflow_reconstruction", to_node="request_builder_candidates"),
        WorkflowEdge(from_node="request_builder_candidates", to_node="unresolved_gaps"),
        WorkflowEdge(from_node="unresolved_gaps", to_node="login_flow_dossier"),
        WorkflowEdge(from_node="login_anchors", to_node="login_flow_dossier"),
        WorkflowEdge(from_node="auth_services", to_node="login_flow_dossier"),
        WorkflowEdge(from_node="architecture_correlation", to_node="login_flow_dossier"),
        WorkflowEdge(from_node="callflow_reconstruction", to_node="login_flow_dossier"),
    ]

    return WorkflowDefinition(
        workflow_id="ios.login-flow",
        intent=Intent.LOGIN_FLOW.value,
        status=WorkflowStatus.IMPLEMENTED,
        accepted_artifacts=["ipa", "app"],
        default_depth=Depth.DEEP,
        supported_depths=[Depth.STANDARD, Depth.DEEP, Depth.FULL],
        nodes=nodes,
        edges=edges,
        entry_node="artifact_detect",
        terminal_nodes=["login_flow_dossier"],
        complexity=Complexity.HIGH,
        agent_policy=AgentPolicy(
            allowed_agents=["planner", "network-analyst", "objc-swift-analyst", "binary-analyst", "evidence-validator"],
            required_agents=["network-analyst", "evidence-validator"],
        ),
        stop_conditions=[
            StopCondition("login_anchors_processed", "All login anchors analyzed"),
            StopCondition("gaps_recorded", "Unresolved gaps documented"),
        ],
        success_conditions=[
            SuccessCondition("login_endpoints_identified", "Login endpoints discovered"),
            SuccessCondition("auth_flow_traced", "Auth flow candidates identified"),
        ],
        outputs=[
            OutputArtifact("login_flow_report", "outputs/{workflow}/login-flow.md"),
            OutputArtifact("callflows", "outputs/{workflow}/callflows/"),
            OutputArtifact("endpoints", "outputs/{workflow}/endpoints/"),
        ],
        resume_enabled=True,
    )


def create_crypto_workflow() -> WorkflowDefinition:
    """Create the ios.crypto workflow."""
    nodes = [
        WorkflowNode(
            node_id="artifact_detect",
            capability_id="foundation.artifact_detect",
            description="Detect artifact",
            dependencies=[],
        ),
        WorkflowNode(
            node_id="dump_standard",
            description="Standard dump prerequisites",
            dependencies=["artifact_detect"],
            sub_workflow="ios.dump",
            depth_profiles={Depth.STANDARD: True, Depth.DEEP: True, Depth.FULL: True},
        ),
        WorkflowNode(
            node_id="crypto_detection",
            capability_id="crypto.detection",
            description="Crypto detection",
            dependencies=["dump_standard"],
            depth_profiles={Depth.QUICK: True, Depth.STANDARD: True, Depth.DEEP: True, Depth.FULL: True},
        ),
        WorkflowNode(
            node_id="coverage_audit",
            capability_id="coverage.calculation",
            description="Coverage audit",
            dependencies=["crypto_detection"],
            depth_profiles={Depth.FULL: True},
        ),
        WorkflowNode(
            node_id="crypto_dossier",
            description="Generate crypto dossier",
            dependencies=["crypto_detection"],
        ),
    ]

    edges = [
        WorkflowEdge(from_node="artifact_detect", to_node="dump_standard"),
        WorkflowEdge(from_node="dump_standard", to_node="crypto_detection"),
        WorkflowEdge(from_node="crypto_detection", to_node="coverage_audit"),
        WorkflowEdge(from_node="crypto_detection", to_node="crypto_dossier"),
    ]

    return WorkflowDefinition(
        workflow_id="ios.crypto",
        intent=Intent.CRYPTO.value,
        status=WorkflowStatus.IMPLEMENTED,
        accepted_artifacts=["ipa", "app"],
        default_depth=Depth.STANDARD,
        supported_depths=[Depth.QUICK, Depth.STANDARD, Depth.DEEP, Depth.FULL],
        nodes=nodes,
        edges=edges,
        entry_node="artifact_detect",
        terminal_nodes=["crypto_dossier", "coverage_audit"],
        complexity=Complexity.MEDIUM,
        stop_conditions=[
            StopCondition("crypto_analysis_complete", "Crypto analysis complete"),
        ],
        success_conditions=[
            SuccessCondition("crypto_primitives_identified", "Crypto candidates found"),
        ],
        outputs=[
            OutputArtifact("crypto_report", "outputs/{workflow}/crypto.json"),
            OutputArtifact("coverage_report", "outputs/{workflow}/coverage.json"),
        ],
        coverage_policy=CoveragePolicy(
            policy_id="crypto-full",
            workflow="crypto",
            depth="full",
            required_dimensions=["crypto"],
        ),
        resume_enabled=True,
    )


def create_anti_analysis_workflow() -> WorkflowDefinition:
    """Create the ios.anti-analysis workflow."""
    nodes = [
        WorkflowNode(
            node_id="artifact_detect",
            capability_id="foundation.artifact_detect",
            description="Detect artifact",
            dependencies=[],
        ),
        WorkflowNode(
            node_id="dump_standard",
            description="Standard dump prerequisites",
            dependencies=["artifact_detect"],
            sub_workflow="ios.dump",
            depth_profiles={Depth.STANDARD: True, Depth.DEEP: True, Depth.FULL: True},
        ),
        WorkflowNode(
            node_id="anti_analysis_detection",
            capability_id="anti.analysis_detection",
            description="Anti-analysis detection",
            dependencies=["dump_standard"],
            depth_profiles={Depth.QUICK: True, Depth.STANDARD: True, Depth.DEEP: True, Depth.FULL: True},
        ),
        WorkflowNode(
            node_id="coverage_audit",
            capability_id="coverage.calculation",
            description="Coverage audit",
            dependencies=["anti_analysis_detection"],
            depth_profiles={Depth.FULL: True},
        ),
        WorkflowNode(
            node_id="anti_analysis_dossier",
            description="Generate anti-analysis dossier",
            dependencies=["anti_analysis_detection"],
        ),
    ]

    edges = [
        WorkflowEdge(from_node="artifact_detect", to_node="dump_standard"),
        WorkflowEdge(from_node="dump_standard", to_node="anti_analysis_detection"),
        WorkflowEdge(from_node="anti_analysis_detection", to_node="coverage_audit"),
        WorkflowEdge(from_node="anti_analysis_detection", to_node="anti_analysis_dossier"),
    ]

    return WorkflowDefinition(
        workflow_id="ios.anti-analysis",
        intent=Intent.ANTI_ANALYSIS.value,
        status=WorkflowStatus.IMPLEMENTED,
        accepted_artifacts=["ipa", "app"],
        default_depth=Depth.STANDARD,
        supported_depths=[Depth.QUICK, Depth.STANDARD, Depth.DEEP, Depth.FULL],
        nodes=nodes,
        edges=edges,
        entry_node="artifact_detect",
        terminal_nodes=["anti_analysis_dossier", "coverage_audit"],
        complexity=Complexity.MEDIUM,
        stop_conditions=[
            StopCondition("anti_analysis_complete", "Anti-analysis analysis complete"),
        ],
        success_conditions=[
            SuccessCondition("indicators_identified", "Anti-analysis indicators found"),
        ],
        outputs=[
            OutputArtifact("anti_analysis_report", "outputs/{workflow}/anti-analysis.json"),
            OutputArtifact("coverage_report", "outputs/{workflow}/coverage.json"),
        ],
        coverage_policy=CoveragePolicy(
            policy_id="anti-analysis-full",
            workflow="anti-analysis",
            depth="full",
            required_dimensions=["anti_analysis"],
        ),
        resume_enabled=True,
    )


def create_report_workflow() -> WorkflowDefinition:
    """Create the ios.report workflow."""
    nodes = [
        WorkflowNode(
            node_id="load_results",
            description="Load analysis results",
            dependencies=[],
        ),
        WorkflowNode(
            node_id="generate_json_report",
            description="Generate JSON report",
            dependencies=["load_results"],
        ),
        WorkflowNode(
            node_id="generate_markdown_report",
            description="Generate Markdown report",
            dependencies=["load_results"],
        ),
    ]

    edges = [
        WorkflowEdge(from_node="load_results", to_node="generate_json_report"),
        WorkflowEdge(from_node="load_results", to_node="generate_markdown_report"),
    ]

    return WorkflowDefinition(
        workflow_id="ios.report",
        intent=Intent.REPORT.value,
        status=WorkflowStatus.IMPLEMENTED,
        accepted_artifacts=["case"],
        default_depth=Depth.STANDARD,
        supported_depths=[Depth.QUICK, Depth.STANDARD, Depth.DEEP, Depth.FULL],
        nodes=nodes,
        edges=edges,
        entry_node="load_results",
        terminal_nodes=["generate_json_report", "generate_markdown_report"],
        complexity=Complexity.LOW,
        stop_conditions=[
            StopCondition("reports_generated", "Reports available"),
        ],
        success_conditions=[
            SuccessCondition("json_report_available", "JSON report generated"),
            SuccessCondition("markdown_report_available", "Markdown report generated"),
        ],
        outputs=[
            OutputArtifact("json_report", "outputs/{workflow}/report.json"),
            OutputArtifact("markdown_report", "outputs/{workflow}/report.md"),
        ],
        resume_enabled=True,
    )


def create_full_workflow() -> WorkflowDefinition:
    """Create the ios.full workflow."""
    nodes = [
        # Foundation
        WorkflowNode(
            node_id="artifact_detect",
            capability_id="foundation.artifact_detect",
            description="Detect artifact",
            dependencies=[],
        ),
        WorkflowNode(
            node_id="ipa_validate",
            capability_id="foundation.ipa_validate",
            description="Validate IPA",
            dependencies=["artifact_detect"],
        ),
        WorkflowNode(
            node_id="ipa_unpack",
            capability_id="foundation.ipa_unpack",
            description="Extract IPA",
            dependencies=["ipa_validate"],
        ),
        WorkflowNode(
            node_id="bundle_inventory",
            capability_id="foundation.bundle_inventory",
            description="Inventory bundle",
            dependencies=["ipa_unpack"],
        ),
        WorkflowNode(
            node_id="plist_extract",
            capability_id="foundation.plist_extract",
            description="Extract Info.plist",
            dependencies=["bundle_inventory"],
        ),
        WorkflowNode(
            node_id="entitlements_extract",
            capability_id="foundation.entitlements_extract",
            description="Extract entitlements",
            dependencies=["bundle_inventory"],
        ),
        # Component inventory
        WorkflowNode(
            node_id="component_graph",
            description="Build component graph",
            dependencies=["bundle_inventory"],
            sub_workflow="ios.component-graph",
        ),
        WorkflowNode(
            node_id="framework_inventory",
            capability_id="framework.inventory",
            description="Inventory frameworks",
            dependencies=["bundle_inventory"],
        ),
        WorkflowNode(
            node_id="dylib_inventory",
            capability_id="dylib.inventory",
            description="Inventory dylibs",
            dependencies=["bundle_inventory"],
        ),
        WorkflowNode(
            node_id="extension_inventory",
            capability_id="extension.inventory",
            description="Inventory extensions",
            dependencies=["bundle_inventory"],
        ),
        # Mach-O/Binary
        WorkflowNode(
            node_id="macho_basic",
            capability_id="macho.basic",
            description="Basic Mach-O",
            dependencies=["component_graph"],
        ),
        WorkflowNode(
            node_id="macho_slices",
            capability_id="macho.slices",
            description="Architecture slices",
            dependencies=["macho_basic"],
        ),
        WorkflowNode(
            node_id="macho_load_commands",
            capability_id="macho.load_commands",
            description="Load commands",
            dependencies=["macho_basic"],
        ),
        WorkflowNode(
            node_id="binary_imports",
            capability_id="binary.imports",
            description="Import symbols",
            dependencies=["macho_basic"],
        ),
        WorkflowNode(
            node_id="binary_exports",
            capability_id="binary.exports",
            description="Export symbols",
            dependencies=["macho_basic"],
        ),
        WorkflowNode(
            node_id="binary_symbols",
            capability_id="binary.symbols",
            description="Symbol table",
            dependencies=["macho_basic"],
        ),
        WorkflowNode(
            node_id="binary_strings",
            capability_id="binary.strings",
            description="String extraction",
            dependencies=["macho_basic"],
        ),
        # Metadata
        WorkflowNode(
            node_id="objc_metadata",
            capability_id="objc.metadata",
            description="Objective-C metadata",
            dependencies=["macho_basic"],
        ),
        WorkflowNode(
            node_id="objc_deep_metadata",
            capability_id="objc.deep_metadata",
            description="Deep ObjC metadata",
            dependencies=["objc_metadata"],
        ),
        WorkflowNode(
            node_id="swift_metadata",
            capability_id="swift.metadata",
            description="Swift metadata",
            dependencies=["macho_basic"],
        ),
        WorkflowNode(
            node_id="swift_demangle",
            capability_id="swift.demangle",
            description="Swift demangling",
            dependencies=["swift_metadata"],
        ),
        # Network
        WorkflowNode(
            node_id="network_framework_detection",
            capability_id="network.framework_detection",
            description="Network framework detection",
            dependencies=["binary_strings"],
        ),
        WorkflowNode(
            node_id="network_endpoint_discovery",
            capability_id="network.endpoint_discovery",
            description="Endpoint discovery",
            dependencies=["network_framework_detection"],
        ),
        WorkflowNode(
            node_id="architecture_detection",
            capability_id="architecture.detection",
            description="Architecture pattern detection",
            dependencies=["binary_strings"],
        ),
        WorkflowNode(
            node_id="callflow_reconstruct",
            capability_id="callflow.reconstruct",
            description="Callflow reconstruction",
            dependencies=["binary_strings"],
        ),
        # Crypto/Anti-analysis
        WorkflowNode(
            node_id="crypto_detection",
            capability_id="crypto.detection",
            description="Crypto detection",
            dependencies=["binary_strings"],
        ),
        WorkflowNode(
            node_id="anti_analysis_detection",
            capability_id="anti.analysis_detection",
            description="Anti-analysis detection",
            dependencies=["binary_strings"],
        ),
        # Coverage
        WorkflowNode(
            node_id="coverage_audit",
            capability_id="coverage.calculation",
            description="Coverage audit",
            dependencies=["macho_basic", "objc_metadata", "swift_metadata", "network_endpoint_discovery", "crypto_detection", "anti_analysis_detection"],
        ),
        # Report
        WorkflowNode(
            node_id="generate_report",
            description="Generate integrated report",
            dependencies=["bundle_inventory", "plist_extract", "entitlements_extract", "component_graph", "framework_inventory", "dylib_inventory", "extension_inventory", "macho_basic", "objc_metadata", "swift_metadata", "network_endpoint_discovery", "crypto_detection", "anti_analysis_detection", "coverage_audit"],
        ),
    ]

    edges = [
        WorkflowEdge(from_node="artifact_detect", to_node="ipa_validate"),
        WorkflowEdge(from_node="ipa_validate", to_node="ipa_unpack"),
        WorkflowEdge(from_node="ipa_unpack", to_node="bundle_inventory"),
        WorkflowEdge(from_node="bundle_inventory", to_node="plist_extract"),
        WorkflowEdge(from_node="bundle_inventory", to_node="entitlements_extract"),
        WorkflowEdge(from_node="bundle_inventory", to_node="component_graph"),
        WorkflowEdge(from_node="bundle_inventory", to_node="framework_inventory"),
        WorkflowEdge(from_node="bundle_inventory", to_node="dylib_inventory"),
        WorkflowEdge(from_node="bundle_inventory", to_node="extension_inventory"),
        WorkflowEdge(from_node="component_graph", to_node="macho_basic"),
        WorkflowEdge(from_node="macho_basic", to_node="macho_slices"),
        WorkflowEdge(from_node="macho_basic", to_node="macho_load_commands"),
        WorkflowEdge(from_node="macho_basic", to_node="binary_imports"),
        WorkflowEdge(from_node="macho_basic", to_node="binary_exports"),
        WorkflowEdge(from_node="macho_basic", to_node="binary_symbols"),
        WorkflowEdge(from_node="macho_basic", to_node="binary_strings"),
        WorkflowEdge(from_node="macho_basic", to_node="objc_metadata"),
        WorkflowEdge(from_node="macho_basic", to_node="swift_metadata"),
        WorkflowEdge(from_node="objc_metadata", to_node="objc_deep_metadata"),
        WorkflowEdge(from_node="swift_metadata", to_node="swift_demangle"),
        WorkflowEdge(from_node="binary_strings", to_node="network_framework_detection"),
        WorkflowEdge(from_node="binary_strings", to_node="architecture_detection"),
        WorkflowEdge(from_node="binary_strings", to_node="callflow_reconstruct"),
        WorkflowEdge(from_node="binary_strings", to_node="crypto_detection"),
        WorkflowEdge(from_node="binary_strings", to_node="anti_analysis_detection"),
        WorkflowEdge(from_node="network_framework_detection", to_node="network_endpoint_discovery"),
        WorkflowEdge(from_node="macho_basic", to_node="coverage_audit"),
        WorkflowEdge(from_node="objc_metadata", to_node="coverage_audit"),
        WorkflowEdge(from_node="swift_metadata", to_node="coverage_audit"),
        WorkflowEdge(from_node="network_endpoint_discovery", to_node="coverage_audit"),
        WorkflowEdge(from_node="crypto_detection", to_node="coverage_audit"),
        WorkflowEdge(from_node="anti_analysis_detection", to_node="coverage_audit"),
        WorkflowEdge(from_node="coverage_audit", to_node="generate_report"),
    ]

    return WorkflowDefinition(
        workflow_id="ios.full",
        intent=Intent.FULL.value,
        status=WorkflowStatus.IMPLEMENTED,
        accepted_artifacts=["ipa", "app"],
        default_depth=Depth.FULL,
        supported_depths=[Depth.STANDARD, Depth.DEEP, Depth.FULL],
        nodes=nodes,
        edges=edges,
        entry_node="artifact_detect",
        terminal_nodes=["generate_report"],
        complexity=Complexity.VERY_HIGH,
        agent_policy=AgentPolicy(
            allowed_agents=["planner", "artifact-analyst", "binary-analyst", "objc-swift-analyst", "network-analyst", "evidence-validator", "coverage-auditor"],
            required_agents=["artifact-analyst"],
        ),
        stop_conditions=[
            StopCondition("all_domains_analyzed", "All analysis domains complete"),
            StopCondition("coverage_audited", "Coverage audit complete"),
        ],
        success_conditions=[
            SuccessCondition("all_components_analyzed", "Complete analysis"),
        ],
        outputs=[
            OutputArtifact("full_report", "outputs/{workflow}/report.md"),
            OutputArtifact("json_report", "outputs/{workflow}/report.json"),
            OutputArtifact("coverage_report", "outputs/{workflow}/coverage.json"),
        ],
        coverage_policy=CoveragePolicy(
            policy_id="full",
            workflow="full",
            depth="full",
            required_dimensions=["binary", "macho_structure", "objc_metadata", "swift_metadata", "network", "crypto", "anti_analysis"],
        ),
        resume_enabled=True,
    )


def create_decompile_workflow() -> WorkflowDefinition:
    """Create the ios.decompile workflow."""
    nodes = [
        WorkflowNode(
            node_id="artifact_detect",
            capability_id="foundation.artifact_detect",
            description="Detect artifact",
            dependencies=[],
        ),
        WorkflowNode(
            node_id="macho_analysis",
            description="Mach-O analysis",
            dependencies=["artifact_detect"],
            sub_workflow="ios.macho",
        ),
        WorkflowNode(
            node_id="language_detection",
            description="Detect languages/runtimes",
            dependencies=["macho_analysis"],
        ),
        WorkflowNode(
            node_id="decompiler_analysis",
            capability_id="decompiler.analyze",
            description="Decompile with available provider (IDA/Ghidra/rizin)",
            dependencies=["language_detection"],
            depth_profiles={Depth.DEEP: True, Depth.FULL: True},
        ),
        WorkflowNode(
            node_id="xref_analysis",
            capability_id="decompiler.xref_analysis",
            description="Cross-reference analysis",
            dependencies=["decompiler_analysis"],
            depth_profiles={Depth.FULL: True},
        ),
    ]

    edges = [
        WorkflowEdge(from_node="artifact_detect", to_node="macho_analysis"),
        WorkflowEdge(from_node="macho_analysis", to_node="language_detection"),
        WorkflowEdge(from_node="language_detection", to_node="decompiler_analysis"),
        WorkflowEdge(from_node="decompiler_analysis", to_node="xref_analysis"),
    ]

    return WorkflowDefinition(
        workflow_id="ios.decompile",
        intent=Intent.DECOMPILE.value,
        status=WorkflowStatus.IMPLEMENTED,
        accepted_artifacts=["ipa", "app", "framework", "macho"],
        default_depth=Depth.DEEP,
        supported_depths=[Depth.DEEP, Depth.FULL],
        nodes=nodes,
        edges=edges,
        entry_node="artifact_detect",
        terminal_nodes=["decompiler_analysis", "xref_analysis"],
        complexity=Complexity.HIGH,
        stop_conditions=[
            StopCondition("decompilation_complete", "Decompilation analysis complete"),
        ],
        success_conditions=[
            SuccessCondition("functions_decompiled", "Functions decompiled"),
            SuccessCondition("xrefs_analyzed", "Cross-references analyzed"),
        ],
        outputs=[
            OutputArtifact("decompiled_functions", "outputs/{workflow}/functions/"),
            OutputArtifact("xrefs", "outputs/{workflow}/xrefs/"),
            OutputArtifact("language_report", "outputs/{workflow}/languages.json"),
        ],
        resume_enabled=True,
    )


def create_ida_workflow() -> WorkflowDefinition:
    """Create the ios.ida workflow."""
    nodes = [
        WorkflowNode(
            node_id="artifact_detect",
            capability_id="foundation.artifact_detect",
            description="Detect artifact",
            dependencies=[],
        ),
        WorkflowNode(
            node_id="tool_check",
            description="Check IDA availability",
            dependencies=["artifact_detect"],
        ),
        WorkflowNode(
            node_id="target_verification",
            capability_id="ida.target_verification",
            description="Verify target binary",
            dependencies=["tool_check"],
        ),
        WorkflowNode(
            node_id="ida_analysis",
            capability_id="ida.analysis",
            description="IDA analysis (functions, imports, exports, strings, xrefs)",
            dependencies=["target_verification"],
        ),
        WorkflowNode(
            node_id="evidence_export",
            description="Export IDA evidence",
            dependencies=["ida_analysis"],
        ),
    ]

    edges = [
        WorkflowEdge(from_node="artifact_detect", to_node="tool_check"),
        WorkflowEdge(from_node="tool_check", to_node="target_verification"),
        WorkflowEdge(from_node="target_verification", to_node="ida_analysis"),
        WorkflowEdge(from_node="ida_analysis", to_node="evidence_export"),
    ]

    return WorkflowDefinition(
        workflow_id="ios.ida",
        intent=Intent.IDA.value,
        status=WorkflowStatus.IMPLEMENTED,
        accepted_artifacts=["ipa", "app", "framework", "macho", "idb"],
        default_depth=Depth.DEEP,
        supported_depths=[Depth.DEEP, Depth.FULL],
        nodes=nodes,
        edges=edges,
        entry_node="artifact_detect",
        terminal_nodes=["evidence_export"],
        complexity=Complexity.HIGH,
        stop_conditions=[
            StopCondition("ida_analysis_complete", "IDA analysis complete"),
        ],
        success_conditions=[
            SuccessCondition("functions_listed", "Functions enumerated"),
            SuccessCondition("xrefs_analyzed", "Cross-references analyzed"),
        ],
        outputs=[
            OutputArtifact("ida_report", "outputs/{workflow}/ida-report.json"),
            OutputArtifact("functions", "outputs/{workflow}/functions/"),
            OutputArtifact("xrefs", "outputs/{workflow}/xrefs/"),
        ],
        resume_enabled=True,
    )


def create_runtime_workflow() -> WorkflowDefinition:
    """Create the ios.runtime workflow."""
    nodes = [
        WorkflowNode(
            node_id="artifact_detect",
            capability_id="foundation.artifact_detect",
            description="Detect artifact",
            dependencies=[],
        ),
        WorkflowNode(
            node_id="runtime_session",
            capability_id="runtime.session",
            description="Manage runtime session",
            dependencies=["artifact_detect"],
        ),
        WorkflowNode(
            node_id="runtime_analysis",
            capability_id="runtime.analysis",
            description="Runtime analysis (Frida/LLDB)",
            dependencies=["runtime_session"],
        ),
    ]

    edges = [
        WorkflowEdge(from_node="artifact_detect", to_node="runtime_session"),
        WorkflowEdge(from_node="runtime_session", to_node="runtime_analysis"),
    ]

    return WorkflowDefinition(
        workflow_id="ios.runtime",
        intent=Intent.RUNTIME.value,
        status=WorkflowStatus.PARTIAL,
        accepted_artifacts=["ipa", "app"],
        default_depth=Depth.FULL,
        supported_depths=[Depth.FULL],
        nodes=nodes,
        edges=edges,
        entry_node="artifact_detect",
        terminal_nodes=["runtime_analysis"],
        complexity=Complexity.VERY_HIGH,
        stop_conditions=[
            StopCondition("runtime_analysis_complete", "Runtime analysis complete"),
        ],
        success_conditions=[
            SuccessCondition("session_established", "Runtime session established"),
            SuccessCondition("observations_captured", "Runtime observations captured"),
        ],
        outputs=[
            OutputArtifact("runtime_report", "outputs/{workflow}/runtime-report.json"),
            OutputArtifact("observations", "outputs/{workflow}/observations/"),
        ],
        resume_enabled=True,
    )


def create_all_workflows() -> dict:
    """Create and return all workflow definitions."""
    return {
        "ios.unpack": create_unpack_workflow(),
        "ios.inspect": create_inspect_workflow(),
        "ios.dump": create_dump_workflow(),
        "ios.macho": create_macho_workflow(),
        "ios.objc": create_objc_workflow(),
        "ios.swift": create_swift_workflow(),
        "ios.network": create_network_workflow(),
        "ios.login-flow": create_login_flow_workflow(),
        "ios.crypto": create_crypto_workflow(),
        "ios.anti-analysis": create_anti_analysis_workflow(),
        "ios.report": create_report_workflow(),
        "ios.decompile": create_decompile_workflow(),
        "ios.ida": create_ida_workflow(),
        "ios.runtime": create_runtime_workflow(),
        "ios.full": create_full_workflow(),
    }
