"""
Workflow Validator for IOS REVERSE KAISER.

Validates workflow definitions for correctness.
"""

from typing import Dict, List, Set, Tuple, Optional
from .schema import WorkflowDefinition, WorkflowNode, WorkflowEdge, WorkflowRegistry
from .registry import get_registry, get_workflow


class WorkflowValidationError(Exception):
    """Workflow validation error."""
    pass


class WorkflowValidator:
    """Validates workflow definitions."""

    # Capabilities that each workflow is allowed to reference
    WORKFLOW_SCOPE_LEAKAGE = {
        "ios.unpack": {
            "allowed": ["foundation.*", "bundle.inventory"],
            "forbidden": ["macho.*", "binary.*", "objc.*", "swift.*", "network.*", "crypto.*", "anti_analysis.*", "architecture.*", "callflow.*"],
        },
        "ios.inspect": {
            "allowed": ["foundation.*", "bundle.inventory", "macho.basic", "framework.inventory", "dylib.inventory", "extension.inventory"],
            "forbidden": ["binary.imports", "binary.exports", "binary.symbols", "objc.metadata", "swift.metadata", "network.*", "crypto.*", "anti_analysis.*"],
        },
        "ios.macho": {
            "allowed": ["foundation.*", "macho.*", "binary.*"],
            "forbidden": ["objc.*", "swift.*", "network.*", "crypto.*", "anti_analysis.*", "architecture.*", "callflow.*"],
        },
        "ios.objc": {
            "allowed": ["foundation.*", "macho.basic", "objc.*"],
            "forbidden": ["network.*", "crypto.*", "anti_analysis.*"],
        },
        "ios.swift": {
            "allowed": ["foundation.*", "macho.basic", "swift.*"],
            "forbidden": ["network.*", "crypto.*", "anti_analysis.*"],
        },
        "ios.network": {
            "allowed": ["foundation.*", "macho.basic", "binary.strings", "network.*", "architecture.*", "callflow.*", "coverage.calculation"],
            "forbidden": ["crypto.*", "anti_analysis.*"],
        },
        "ios.crypto": {
            "allowed": ["foundation.*", "macho.basic", "binary.*", "crypto.*", "coverage.calculation"],
            "forbidden": ["network.*", "anti_analysis.*"],
        },
        "ios.anti-analysis": {
            "allowed": ["foundation.*", "macho.basic", "binary.*", "anti.analysis_detection", "coverage.calculation"],
            "forbidden": ["network.*", "crypto.*"],
        },
    }

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self, workflow: WorkflowDefinition) -> Tuple[bool, List[str], List[str]]:
        """
        Validate a workflow definition.

        Returns (is_valid, errors, warnings).
        """
        self.errors = []
        self.warnings = []

        self._validate_structure(workflow)
        self._validate_dag(workflow)
        self._validate_scope(workflow)
        self._validate_conditions(workflow)

        return len(self.errors) == 0, self.errors, self.warnings

    def _validate_structure(self, workflow: WorkflowDefinition):
        """Validate basic structure."""
        if not workflow.workflow_id:
            self.errors.append("Missing workflow_id")

        if not workflow.intent:
            self.errors.append("Missing intent")

        if not workflow.entry_node:
            self.errors.append("Missing entry_node")

        if not workflow.nodes:
            self.errors.append("Workflow has no nodes")

        if not workflow.terminal_nodes:
            self.warnings.append("No terminal nodes defined")

    def _validate_dag(self, workflow: WorkflowDefinition):
        """Validate DAG structure."""
        # Build node lookup
        node_ids: Set[str] = {n.node_id for n in workflow.nodes}

        # Check entry node exists
        if workflow.entry_node and workflow.entry_node not in node_ids:
            self.errors.append(f"Entry node '{workflow.entry_node}' not found")

        # Check terminal nodes exist
        for terminal in workflow.terminal_nodes:
            if terminal not in node_ids:
                self.errors.append(f"Terminal node '{terminal}' not found")

        # Check dependencies exist
        for node in workflow.nodes:
            for dep in node.dependencies:
                if dep not in node_ids:
                    self.errors.append(f"Node '{node.node_id}' has missing dependency '{dep}'")

        # Check for cycles
        if self._has_cycle(workflow):
            self.errors.append("Workflow contains a cycle")

        # Check reachability
        reachable = self._get_reachable_nodes(workflow)
        unreachable = node_ids - reachable
        if unreachable:
            self.warnings.append(f"Unreachable nodes: {unreachable}")

    def _has_cycle(self, workflow: WorkflowDefinition) -> bool:
        """Check if workflow contains a cycle."""
        visited = set()
        rec_stack = set()

        def visit(node_id: str) -> bool:
            if node_id in rec_stack:
                return True
            if node_id in visited:
                return False

            visited.add(node_id)
            rec_stack.add(node_id)

            node = workflow.get_node(node_id)
            if node:
                for dep in node.dependencies:
                    if visit(dep):
                        return True

            rec_stack.remove(node_id)
            return False

        for node in workflow.nodes:
            if node.node_id not in visited:
                if visit(node.node_id):
                    return True

        return False

    def _get_reachable_nodes(self, workflow: WorkflowDefinition) -> Set[str]:
        """Get all nodes reachable from entry node."""
        reachable = set()
        to_visit = [workflow.entry_node] if workflow.entry_node else []

        while to_visit:
            node_id = to_visit.pop()
            if node_id in reachable:
                continue
            reachable.add(node_id)

            node = workflow.get_node(node_id)
            if node:
                for dep in node.dependencies:
                    if dep not in reachable:
                        to_visit.append(dep)

            # Also add nodes that have edges FROM this node
            for edge in workflow.edges:
                if edge.from_node == node_id and edge.to_node not in reachable:
                    to_visit.append(edge.to_node)

        return reachable

    def _validate_scope(self, workflow: WorkflowDefinition):
        """Validate capability scope doesn't leak."""
        if workflow.workflow_id not in self.WORKFLOW_SCOPE_LEAKAGE:
            return

        scope = self.WORKFLOW_SCOPE_LEAKAGE[workflow.workflow_id]
        allowed = scope["allowed"]
        forbidden = scope["forbidden"]

        # Get capabilities used in workflow
        used_caps = set()
        for node in workflow.nodes:
            if node.capability_id:
                used_caps.add(node.capability_id)

        # Check for forbidden capabilities
        for cap in used_caps:
            if self._is_forbidden(cap, forbidden):
                self.errors.append(f"Scope leakage: '{cap}' not allowed in {workflow.workflow_id}")

    def _is_forbidden(self, capability: str, forbidden_patterns: List[str]) -> bool:
        """Check if capability matches forbidden pattern."""
        for pattern in forbidden_patterns:
            if pattern.endswith(".*"):
                # Wildcard match
                domain = pattern[:-2]
                if capability.startswith(domain + "."):
                    return True
            elif capability == pattern:
                return True
        return False

    def _validate_conditions(self, workflow: WorkflowDefinition):
        """Validate workflow conditions."""
        # Check that conditions reference valid nodes
        for node in workflow.nodes:
            for cond in node.conditions:
                if cond.true_branch and not workflow.get_node(cond.true_branch):
                    self.errors.append(f"Node '{node.node_id}' condition references unknown true_branch '{cond.true_branch}'")
                if cond.false_branch and not workflow.get_node(cond.false_branch):
                    self.errors.append(f"Node '{node.node_id}' condition references unknown false_branch '{cond.false_branch}'")


def validate_all_workflows() -> Dict[str, Tuple[bool, List[str], List[str]]]:
    """
    Validate all workflows in the registry.

    Returns dict mapping workflow_id to (is_valid, errors, warnings).
    """
    registry = get_registry()
    results = {}

    for workflow_id in registry.list_workflows():
        workflow = registry.get(workflow_id)
        validator = WorkflowValidator()
        is_valid, errors, warnings = validator.validate(workflow)
        results[workflow_id] = (is_valid, errors, warnings)

    return results


def validate_workflow_differential() -> Dict[str, any]:
    """
    Validate workflow differential constraints.

    Checks that:
    - dump standard ⊂ dump full
    - network standard ⊂ network full
    - etc.
    """
    results = {}

    # Define subset relationships
    relationships = [
        ("ios.dump", "ios.dump", "standard", "full"),
        ("ios.network", "ios.network", "standard", "full"),
        ("ios.macho", "ios.macho", "standard", "full"),
        ("ios.objc", "ios.objc", "standard", "full"),
        ("ios.swift", "ios.swift", "standard", "full"),
        ("ios.crypto", "ios.crypto", "standard", "full"),
        ("ios.anti-analysis", "ios.anti-analysis", "standard", "full"),
    ]

    for wf_id, _, std_depth, full_depth in relationships:
        workflow = get_workflow(wf_id)
        if not workflow:
            continue

        std_caps = set(workflow.get_capabilities_for_depth(std_depth))
        full_caps = set(workflow.get_capabilities_for_depth(full_depth))

        # Standard should be subset of full
        is_subset = std_caps.issubset(full_caps)

        results[wf_id] = {
            "standard_caps": sorted(std_caps),
            "full_caps": sorted(full_caps),
            "is_subset": is_subset,
            "missing_in_full": sorted(std_caps - full_caps),
            "extra_in_full": sorted(full_caps - std_caps),
        }

    return results


def validate_unpack_narrowness() -> Tuple[bool, List[str]]:
    """
    Validate that ios.unpack does NOT include unrelated analysis capabilities.

    Returns (is_valid, errors).
    """
    errors = []
    workflow = get_workflow("ios.unpack")

    if not workflow:
        errors.append("ios.unpack workflow not found")
        return False, errors

    # Get all capability IDs used
    caps = set()
    for node in workflow.nodes:
        if node.capability_id:
            caps.add(node.capability_id)

    # These should NOT be in unpack
    forbidden = [
        "binary.imports", "binary.exports", "binary.symbols",
        "objc.metadata", "objc.deep_metadata",
        "swift.metadata", "swift.demangle",
        "network.framework_detection", "network.endpoint_discovery",
        "crypto.detection", "anti.analysis_detection",
        "architecture.detection", "callflow.reconstruct",
    ]

    for cap in caps:
        if cap in forbidden:
            errors.append(f"ios.unpack includes forbidden capability: {cap}")

    # Check scope leakage rules
    validator = WorkflowValidator()
    is_valid, errs, _ = validator.validate(workflow)
    errors.extend(errs)

    return len(errors) == 0, errors


def validate_report_no_analysis() -> Tuple[bool, List[str]]:
    """
    Validate that ios.report does NOT trigger analysis.

    Returns (is_valid, errors).
    """
    errors = []
    workflow = get_workflow("ios.report")

    if not workflow:
        errors.append("ios.report workflow not found")
        return False, errors

    # Report should only load and render, not analyze
    caps = set()
    for node in workflow.nodes:
        if node.capability_id:
            caps.add(node.capability_id)

    # These should NOT be in report
    forbidden_analysis = [
        "macho.basic", "macho.slices", "macho.load_commands",
        "binary.imports", "binary.exports", "binary.symbols", "binary.strings",
        "objc.metadata", "objc.deep_metadata",
        "swift.metadata", "swift.demangle",
        "network.framework_detection", "network.endpoint_discovery",
        "crypto.detection", "anti.analysis_detection",
        "architecture.detection", "callflow.reconstruct",
    ]

    for cap in caps:
        if cap in forbidden_analysis:
            errors.append(f"ios.report includes analysis capability: {cap}")

    return len(errors) == 0, errors
