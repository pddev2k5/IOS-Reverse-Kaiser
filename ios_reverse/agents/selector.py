"""
Agent Selector for IOS REVERSE KAISER.

Selects appropriate agents based on workflow, depth, and complexity.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .model import (
    AgentRole, AgentSelection, TaskStatus,
    Complexity, Depth, AgentTask
)
from .registry import get_registry, get_agent_by_role
from ios_reverse.workflows import get_workflow


@dataclass
class AgentBudget:
    """Agent budget configuration."""
    quick: int = 1
    standard: int = 2
    deep: int = 4
    full: int = 6


# Default budget
DEFAULT_BUDGET = AgentBudget()


def get_budget_for_depth(depth: str) -> int:
    """Get agent budget for depth."""
    budget_map = {
        Depth.QUICK.value: DEFAULT_BUDGET.quick,
        Depth.STANDARD.value: DEFAULT_BUDGET.standard,
        Depth.DEEP.value: DEFAULT_BUDGET.deep,
        Depth.FULL.value: DEFAULT_BUDGET.full,
    }
    return budget_map.get(depth, DEFAULT_BUDGET.standard)


def select_agents_for_workflow(
    workflow_id: str,
    depth: str,
    ready_nodes: List[str] = None,
    coverage_required: bool = False
) -> AgentSelection:
    """
    Select agents for workflow execution.

    Args:
        workflow_id: Workflow to select agents for
        depth: Depth profile
        ready_nodes: Ready nodes in workflow
        coverage_required: Whether coverage audit is required

    Returns:
        AgentSelection with selected roles and assignments
    """
    if ready_nodes is None:
        ready_nodes = []

    workflow = get_workflow(workflow_id)
    if not workflow:
        return AgentSelection(
            selected_roles=[],
            task_assignments=[],
            reasons=[f"Unknown workflow: {workflow_id}"],
            budget_used=0,
            budget_limit=0
        )

    # Get allowed agents from workflow
    registry = get_registry()

    # Check if workflow has agent policy
    if workflow.agent_policy and workflow.agent_policy.allowed_agents:
        allowed_from_workflow = workflow.agent_policy.allowed_agents
    else:
        # Fall back to default based on workflow intent
        allowed_from_workflow = _get_default_allowed_agents(workflow_id)

    allowed_roles = registry.get_allowed_agents(allowed_from_workflow)

    # If no allowed roles from registry, use defaults
    if not allowed_roles:
        allowed_roles = _get_default_roles_for_workflow(workflow_id)

    # Get budget
    budget = get_budget_for_depth(depth)

    # Determine required agents based on workflow and depth
    selected_roles = _determine_required_roles(
        workflow_id, depth, ready_nodes, allowed_roles, coverage_required
    )

    # Limit by budget
    if len(selected_roles) > budget:
        selected_roles = selected_roles[:budget]

    # Create task assignments
    task_assignments = _create_task_assignments(selected_roles, ready_nodes)

    # Generate reasons
    reasons = _generate_selection_reasons(
        workflow_id, depth, selected_roles, allowed_roles, coverage_required
    )

    return AgentSelection(
        selected_roles=selected_roles,
        task_assignments=task_assignments,
        reasons=reasons,
        budget_used=len(selected_roles),
        budget_limit=budget
    )


def _get_default_allowed_agents(workflow_id: str) -> List[str]:
    """Get default allowed agents based on workflow."""
    defaults = {
        "ios.unpack": ["artifact-analyst"],
        "ios.inspect": ["artifact-analyst"],
        "ios.dump": ["artifact-analyst", "binary-analyst", "objc-swift-analyst", "coverage-auditor"],
        "ios.macho": ["binary-analyst"],
        "ios.objc": ["objc-swift-analyst"],
        "ios.swift": ["objc-swift-analyst"],
        "ios.network": ["network-analyst", "artifact-analyst", "evidence-validator", "coverage-auditor"],
        "ios.login-flow": ["planner", "network-analyst", "objc-swift-analyst", "binary-analyst", "evidence-validator"],
        "ios.crypto": ["binary-analyst", "coverage-auditor"],
        "ios.anti-analysis": ["binary-analyst", "coverage-auditor"],
        "ios.report": ["reporter"],
        "ios.decompile": ["binary-analyst"],
        "ios.ida": ["binary-analyst"],
        "ios.runtime": ["binary-analyst"],
        "ios.full": ["planner", "artifact-analyst", "objc-swift-analyst", "binary-analyst", "network-analyst", "evidence-validator", "coverage-auditor", "reporter"],
    }
    return defaults.get(workflow_id, ["artifact-analyst"])


def _get_default_roles_for_workflow(workflow_id: str) -> List[AgentRole]:
    """Get default roles based on workflow."""
    defaults = {
        "ios.unpack": [AgentRole.ARTIFACT_ANALYST],
        "ios.inspect": [AgentRole.ARTIFACT_ANALYST],
        "ios.dump": [AgentRole.ARTIFACT_ANALYST, AgentRole.BINARY_ANALYST, AgentRole.OBJC_SWIFT_ANALYST, AgentRole.COVERAGE_AUDITOR],
        "ios.macho": [AgentRole.BINARY_ANALYST],
        "ios.objc": [AgentRole.OBJC_SWIFT_ANALYST],
        "ios.swift": [AgentRole.OBJC_SWIFT_ANALYST],
        "ios.network": [AgentRole.NETWORK_ANALYST, AgentRole.ARTIFACT_ANALYST, AgentRole.EVIDENCE_VALIDATOR, AgentRole.COVERAGE_AUDITOR],
        "ios.login-flow": [AgentRole.PLANNER, AgentRole.NETWORK_ANALYST, AgentRole.OBJC_SWIFT_ANALYST, AgentRole.BINARY_ANALYST, AgentRole.EVIDENCE_VALIDATOR],
        "ios.crypto": [AgentRole.BINARY_ANALYST, AgentRole.COVERAGE_AUDITOR],
        "ios.anti-analysis": [AgentRole.BINARY_ANALYST, AgentRole.COVERAGE_AUDITOR],
        "ios.report": [AgentRole.REPORTER],
        "ios.decompile": [AgentRole.BINARY_ANALYST],
        "ios.ida": [AgentRole.BINARY_ANALYST],
        "ios.runtime": [AgentRole.BINARY_ANALYST],
        "ios.full": [AgentRole.PLANNER, AgentRole.ARTIFACT_ANALYST, AgentRole.OBJC_SWIFT_ANALYST, AgentRole.BINARY_ANALYST, AgentRole.NETWORK_ANALYST, AgentRole.EVIDENCE_VALIDATOR, AgentRole.COVERAGE_AUDITOR, AgentRole.REPORTER],
    }
    return defaults.get(workflow_id, [AgentRole.ARTIFACT_ANALYST])


def _determine_required_roles(
    workflow_id: str,
    depth: str,
    ready_nodes: List[str],
    allowed_roles: List[AgentRole],
    coverage_required: bool
) -> List[AgentRole]:
    """Determine required roles based on workflow and nodes."""
    roles = []

    # Always add artifact-analyst for workflows that need foundation
    if AgentRole.ARTIFACT_ANALYST in allowed_roles:
        foundation_workflows = [
            "ios.unpack", "ios.inspect", "ios.dump",
            "ios.macho", "ios.network", "ios.login-flow",
            "ios.crypto", "ios.anti-analysis", "ios.full"
        ]
        if workflow_id in foundation_workflows:
            roles.append(AgentRole.ARTIFACT_ANALYST)

    # Add planner for complex workflows at deep/full depth
    if AgentRole.PLANNER in allowed_roles:
        complex_workflows = ["ios.network", "ios.login-flow", "ios.full"]
        if workflow_id in complex_workflows and depth in [Depth.DEEP.value, Depth.FULL.value]:
            roles.append(AgentRole.PLANNER)

    # Add binary analyst for dump/macho workflows
    if AgentRole.BINARY_ANALYST in allowed_roles:
        binary_workflows = ["ios.dump", "ios.macho", "ios.crypto", "ios.anti-analysis", "ios.full"]
        if workflow_id in binary_workflows:
            roles.append(AgentRole.BINARY_ANALYST)

    # Add ObjC/Swift analyst for dump/network workflows
    if AgentRole.OBJC_SWIFT_ANALYST in allowed_roles:
        metadata_workflows = ["ios.dump", "ios.objc", "ios.swift", "ios.network", "ios.login-flow", "ios.full"]
        if workflow_id in metadata_workflows:
            roles.append(AgentRole.OBJC_SWIFT_ANALYST)

    # Add network analyst for network/login-flow
    if AgentRole.NETWORK_ANALYST in allowed_roles:
        network_workflows = ["ios.network", "ios.login-flow"]
        if workflow_id in network_workflows:
            roles.append(AgentRole.NETWORK_ANALYST)

    # Add evidence validator for complex workflows
    if AgentRole.EVIDENCE_VALIDATOR in allowed_roles:
        if depth in [Depth.DEEP.value, Depth.FULL.value]:
            roles.append(AgentRole.EVIDENCE_VALIDATOR)

    # Add coverage auditor if required or full depth
    if AgentRole.COVERAGE_AUDITOR in allowed_roles:
        if coverage_required or depth == Depth.FULL.value:
            if workflow_id in ["ios.dump", "ios.network", "ios.crypto", "ios.anti-analysis", "ios.full"]:
                roles.append(AgentRole.COVERAGE_AUDITOR)

    # Add reporter for report workflow
    if AgentRole.REPORTER in allowed_roles:
        if workflow_id == "ios.report":
            roles.append(AgentRole.REPORTER)

    # Deduplicate while preserving order
    seen = set()
    unique_roles = []
    for role in roles:
        if role not in seen:
            seen.add(role)
            unique_roles.append(role)

    return unique_roles


def _create_task_assignments(
    roles: List[AgentRole],
    ready_nodes: List[str]
) -> List[Dict[str, str]]:
    """Create task assignments for roles."""
    assignments = []
    for i, role in enumerate(roles):
        task_id = f"task-{role.value}-{i}"
        assignments.append({
            "role": role.value,
            "task_id": task_id,
            "assigned": "true"
        })
    return assignments


def _generate_selection_reasons(
    workflow_id: str,
    depth: str,
    selected: List[AgentRole],
    allowed: List[AgentRole],
    coverage_required: bool
) -> List[str]:
    """Generate human-readable reasons for selection."""
    reasons = []

    for role in selected:
        if role == AgentRole.ARTIFACT_ANALYST:
            reasons.append(f"Selected {role.value} because workflow {workflow_id} requires foundation analysis")
        elif role == AgentRole.PLANNER:
            reasons.append(f"Selected {role.value} because depth={depth} and workflow is complex")
        elif role == AgentRole.BINARY_ANALYST:
            reasons.append(f"Selected {role.value} because workflow {workflow_id} requires binary analysis")
        elif role == AgentRole.OBJC_SWIFT_ANALYST:
            reasons.append(f"Selected {role.value} because workflow {workflow_id} requires language metadata")
        elif role == AgentRole.NETWORK_ANALYST:
            reasons.append(f"Selected {role.value} because workflow {workflow_id} requires network analysis")
        elif role == AgentRole.EVIDENCE_VALIDATOR:
            reasons.append(f"Selected {role.value} because depth={depth} requires validation")
        elif role == AgentRole.COVERAGE_AUDITOR:
            reasons.append(f"Selected {role.value} because coverage_required={coverage_required} or depth=full")
        elif role == AgentRole.REPORTER:
            reasons.append(f"Selected {role.value} because workflow is ios.report")

    # Add any allowed but not selected
    for role in allowed:
        if role not in selected:
            reasons.append(f"Skipped {role.value} - not required for workflow={workflow_id} depth={depth}")

    return reasons


def validate_agent_selection(selection: AgentSelection, workflow_id: str) -> Tuple[bool, List[str]]:
    """
    Validate agent selection against workflow policy.

    Returns (is_valid, errors).
    """
    errors = []
    workflow = get_workflow(workflow_id)

    if not workflow:
        return False, [f"Unknown workflow: {workflow_id}"]

    if not workflow.agent_policy:
        return True, []  # No policy defined, any selection is valid

    allowed = workflow.agent_policy.allowed_agents
    registry = get_registry()

    for role in selection.selected_roles:
        if role.value not in allowed:
            errors.append(f"Agent role {role.value} not allowed in workflow {workflow_id}")

    return len(errors) == 0, errors


def get_required_agents_for_workflow_depth(
    workflow_id: str,
    depth: str
) -> List[AgentRole]:
    """
    Get the required agent roles for a workflow at given depth.

    This returns the full set of agents that SHOULD be selected,
    without budget constraints.
    """
    workflow = get_workflow(workflow_id)
    if not workflow:
        return []

    registry = get_registry()
    allowed_roles = registry.get_allowed_agents(
        workflow.agent_policy.allowed_agents if workflow.agent_policy else []
    )

    return _determine_required_roles(
        workflow_id, depth, [], allowed_roles, depth == Depth.FULL.value
    )
