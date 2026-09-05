"""
Agents module for IOS REVERSE KAISER.

Provides adaptive multi-agent orchestration.
"""

from .model import (
    AgentRole,
    TaskStatus,
    ValidationResult,
    ConflictResolution,
    Complexity,
    Depth,
    ContextPolicy,
    HandoffPolicy,
    RetryPolicy,
    TerminationCondition,
    FailureSemantics,
    AgentDefinition,
    AgentTask,
    ClaimConflict,
    AgentWorkspace,
    AgentSelection,
)

from .registry import (
    AgentRegistry,
    get_registry,
    get_agent,
    get_agent_by_role,
    list_agents,
    list_roles,
)

from .selector import (
    AgentBudget,
    get_budget_for_depth,
    select_agents_for_workflow,
    validate_agent_selection,
    get_required_agents_for_workflow_depth,
)

from .scheduler import (
    TaskSchedule,
    DependencyGraph,
    TaskScheduler,
    create_task_from_workflow_node,
    generate_deterministic_id,
)

from .validator import (
    EvidenceStrength,
    Claim,
    Evidence,
    ValidationReport,
    EvidenceValidator,
    validate_claim,
    validate_findings,
)

from .context import (
    ContextPack,
    generate_context_pack,
    save_context_pack,
    load_context_pack,
    generate_agent_workspace,
    write_agent_status,
    write_handoff,
)

__all__ = [
    # Model
    "AgentRole",
    "TaskStatus",
    "ValidationResult",
    "ConflictResolution",
    "Complexity",
    "Depth",
    "ContextPolicy",
    "HandoffPolicy",
    "RetryPolicy",
    "TerminationCondition",
    "FailureSemantics",
    "AgentDefinition",
    "AgentTask",
    "ClaimConflict",
    "AgentWorkspace",
    "AgentSelection",

    # Registry
    "AgentRegistry",
    "get_registry",
    "get_agent",
    "get_agent_by_role",
    "list_agents",
    "list_roles",

    # Selector
    "AgentBudget",
    "get_budget_for_depth",
    "select_agents_for_workflow",
    "validate_agent_selection",
    "get_required_agents_for_workflow_depth",

    # Scheduler
    "TaskSchedule",
    "DependencyGraph",
    "TaskScheduler",
    "create_task_from_workflow_node",
    "generate_deterministic_id",

    # Validator
    "EvidenceStrength",
    "Claim",
    "Evidence",
    "ValidationReport",
    "EvidenceValidator",
    "validate_claim",
    "validate_findings",

    # Context
    "ContextPack",
    "generate_context_pack",
    "save_context_pack",
    "load_context_pack",
    "generate_agent_workspace",
    "write_agent_status",
    "write_handoff",
]
