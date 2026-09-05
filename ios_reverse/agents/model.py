"""
Agent Models for IOS REVERSE KAISER.

Defines canonical agent roles and task structures.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Any
from datetime import datetime


class AgentRole(str, Enum):
    """Canonical agent roles."""
    PLANNER = "planner"
    ARTIFACT_ANALYST = "artifact-analyst"
    OBJC_SWIFT_ANALYST = "objc-swift-analyst"
    BINARY_ANALYST = "binary-analyst"
    NETWORK_ANALYST = "network-analyst"
    EVIDENCE_VALIDATOR = "evidence-validator"
    COVERAGE_AUDITOR = "coverage-auditor"
    REPORTER = "reporter"


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"
    STALE = "stale"


class ValidationResult(str, Enum):
    """Evidence validation result."""
    ACCEPT = "accept"
    DOWNGRADE = "downgrade"
    REJECT = "reject"
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"


class ConflictResolution(str, Enum):
    """Conflict resolution status."""
    VALIDATOR_ACCEPT_A = "validator_accept_a"
    VALIDATOR_ACCEPT_B = "validator_accept_b"
    BOTH_WEAK = "both_weak"
    UNRESOLVED = "unresolved"


class Complexity(str, Enum):
    """Workflow complexity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class Depth(str, Enum):
    """Depth profiles."""
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"
    FULL = "full"


@dataclass
class ContextPolicy:
    """Agent context policy."""
    max_context_tokens: int = 4000
    include_verified_facts: bool = True
    include_evidence_refs: bool = True
    include_artifact_refs: bool = True
    include_known_failures: bool = True
    include_expected_outputs: bool = True


@dataclass
class HandoffPolicy:
    """Agent handoff policy."""
    use_artifacts: bool = True
    require_acknowledgment: bool = False
    preserve_provenance: bool = True
    max_handoffs: int = 5


@dataclass
class RetryPolicy:
    """Task retry policy."""
    max_retries: int = 3
    retry_on_transient_failure: bool = True
    do_not_retry_on_invalid_artifact: bool = True
    backoff_multiplier: float = 2.0


@dataclass
class TerminationCondition:
    """Task termination condition."""
    condition: str
    description: str


@dataclass
class FailureSemantics:
    """Failure semantics for agent tasks."""
    transient_adapter_failure: str = "retry"  # retry, skip, block
    invalid_artifact: str = "skip"  # retry, skip, block
    missing_tool: str = "block"  # retry, skip, block
    unsupported_metadata: str = "partial"  # retry, partial, skip


@dataclass
class AgentDefinition:
    """Canonical agent definition."""
    agent_id: str
    role: AgentRole
    version: str = "1.0.0"
    description: str = ""

    # Scope
    allowed_domains: List[str] = field(default_factory=list)
    allowed_capabilities: List[str] = field(default_factory=list)
    allowed_artifacts: List[str] = field(default_factory=list)

    # I/O
    required_inputs: List[str] = field(default_factory=list)
    expected_outputs: List[str] = field(default_factory=list)

    # Constraints
    max_scope: Complexity = Complexity.LOW
    allowed_tools: List[str] = field(default_factory=list)

    # Policies
    context_policy: ContextPolicy = field(default_factory=ContextPolicy)
    handoff_policy: HandoffPolicy = field(default_factory=HandoffPolicy)
    termination_conditions: List[TerminationCondition] = field(default_factory=list)
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    failure_semantics: FailureSemantics = field(default_factory=FailureSemantics)

    def can_handle_capability(self, capability_id: str) -> bool:
        """Check if agent can handle capability."""
        if not self.allowed_capabilities:
            return False
        for allowed in self.allowed_capabilities:
            if allowed.endswith(".*"):
                domain = allowed[:-2]
                if capability_id.startswith(domain + "."):
                    return True
            elif capability_id == allowed:
                return True
        return False

    def can_handle_artifact(self, artifact_type: str) -> bool:
        """Check if agent can handle artifact type."""
        if not self.allowed_artifacts:
            return False
        if artifact_type in self.allowed_artifacts:
            return True
        if "ipa" in self.allowed_artifacts and artifact_type.endswith(".app"):
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "role": self.role.value,
            "version": self.version,
            "description": self.description,
            "allowed_domains": self.allowed_domains,
            "allowed_capabilities": self.allowed_capabilities,
            "allowed_artifacts": self.allowed_artifacts,
            "required_inputs": self.required_inputs,
            "expected_outputs": self.expected_outputs,
            "max_scope": self.max_scope.value,
            "allowed_tools": self.allowed_tools,
            "context_policy": {
                "max_context_tokens": self.context_policy.max_context_tokens,
                "include_verified_facts": self.context_policy.include_verified_facts,
                "include_evidence_refs": self.context_policy.include_evidence_refs,
                "include_artifact_refs": self.context_policy.include_artifact_refs,
                "include_known_failures": self.context_policy.include_known_failures,
                "include_expected_outputs": self.context_policy.include_expected_outputs,
            },
            "handoff_policy": {
                "use_artifacts": self.handoff_policy.use_artifacts,
                "require_acknowledgment": self.handoff_policy.require_acknowledgment,
                "preserve_provenance": self.handoff_policy.preserve_provenance,
                "max_handoffs": self.handoff_policy.max_handoffs,
            },
            "termination_conditions": [
                {"condition": tc.condition, "description": tc.description}
                for tc in self.termination_conditions
            ],
            "retry_policy": {
                "max_retries": self.retry_policy.max_retries,
                "retry_on_transient_failure": self.retry_policy.retry_on_transient_failure,
                "do_not_retry_on_invalid_artifact": self.retry_policy.do_not_retry_on_invalid_artifact,
                "backoff_multiplier": self.retry_policy.backoff_multiplier,
            },
            "failure_semantics": {
                "transient_adapter_failure": self.failure_semantics.transient_adapter_failure,
                "invalid_artifact": self.failure_semantics.invalid_artifact,
                "missing_tool": self.failure_semantics.missing_tool,
                "unsupported_metadata": self.failure_semantics.unsupported_metadata,
            },
        }


@dataclass
class AgentTask:
    """Agent task model."""
    task_id: str
    case_id: str
    workflow_id: str
    node_id: str
    agent_role: AgentRole

    # Task specification
    objective: str
    allowed_capabilities: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)

    # Inputs/outputs
    input_artifacts: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    expected_outputs: List[str] = field(default_factory=list)

    # Execution
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    # Results
    findings: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Validation
    validation_result: Optional[ValidationResult] = None
    validation_notes: str = ""

    def mark_running(self):
        """Mark task as running."""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow().isoformat()

    def mark_done(self, findings: Dict[str, Any] = None):
        """Mark task as done."""
        self.status = TaskStatus.DONE
        self.completed_at = datetime.utcnow().isoformat()
        if findings:
            self.findings = findings

    def mark_failed(self, error: str):
        """Mark task as failed."""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow().isoformat()
        self.errors.append(error)

    def mark_blocked(self, reason: str):
        """Mark task as blocked."""
        self.status = TaskStatus.BLOCKED
        self.errors.append(f"Blocked: {reason}")

    def increment_retry(self) -> bool:
        """Increment retry count. Returns True if retry allowed."""
        self.retry_count += 1
        return self.retry_count < 3  # Default max retries

    def is_complete(self) -> bool:
        """Check if task is complete."""
        return self.status in (TaskStatus.DONE, TaskStatus.SKIPPED)

    def is_blocked(self) -> bool:
        """Check if task is blocked."""
        return self.status == TaskStatus.BLOCKED

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "case_id": self.case_id,
            "workflow_id": self.workflow_id,
            "node_id": self.node_id,
            "agent_role": self.agent_role.value,
            "objective": self.objective,
            "allowed_capabilities": self.allowed_capabilities,
            "constraints": self.constraints,
            "input_artifacts": self.input_artifacts,
            "evidence_refs": self.evidence_refs,
            "expected_outputs": self.expected_outputs,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "findings": self.findings,
            "errors": self.errors,
            "warnings": self.warnings,
            "validation_result": self.validation_result.value if self.validation_result else None,
            "validation_notes": self.validation_notes,
        }


@dataclass
class ClaimConflict:
    """Conflict between two claims."""
    conflict_id: str
    claim_a: Dict[str, Any]
    claim_b: Dict[str, Any]
    evidence_set_a: List[str]
    evidence_set_b: List[str]
    agent_source_a: str
    agent_source_b: str
    resolution: ConflictResolution = ConflictResolution.UNRESOLVED
    resolution_notes: str = ""
    resolved_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "conflict_id": self.conflict_id,
            "claim_a": self.claim_a,
            "claim_b": self.claim_b,
            "evidence_set_a": self.evidence_set_a,
            "evidence_set_b": self.evidence_set_b,
            "agent_source_a": self.agent_source_a,
            "agent_source_b": self.agent_source_b,
            "resolution": self.resolution.value,
            "resolution_notes": self.resolution_notes,
            "resolved_at": self.resolved_at,
        }


@dataclass
class AgentWorkspace:
    """Agent workspace for case."""
    workspace_path: str
    case_id: str
    agent_role: AgentRole
    tasks: List[AgentTask] = field(default_factory=list)
    findings: Dict[str, Any] = field(default_factory=dict)
    handoffs: List[Dict[str, str]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def get_pending_tasks(self) -> List[AgentTask]:
        """Get pending tasks."""
        return [t for t in self.tasks if t.status == TaskStatus.PENDING]

    def get_ready_tasks(self) -> List[AgentTask]:
        """Get ready tasks."""
        return [t for t in self.tasks if t.status == TaskStatus.READY]

    def get_completed_tasks(self) -> List[AgentTask]:
        """Get completed tasks."""
        return [t for t in self.tasks if t.is_complete()]

    def get_failed_tasks(self) -> List[AgentTask]:
        """Get failed tasks."""
        return [t for t in self.tasks if t.status == TaskStatus.FAILED]


@dataclass
class AgentSelection:
    """Agent selection decision."""
    selected_roles: List[AgentRole]
    task_assignments: List[Dict[str, str]]  # role -> task_id
    reasons: List[str]
    budget_used: int
    budget_limit: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "selected_roles": [r.value for r in self.selected_roles],
            "task_assignments": self.task_assignments,
            "reasons": self.reasons,
            "budget_used": self.budget_used,
            "budget_limit": self.budget_limit,
        }
