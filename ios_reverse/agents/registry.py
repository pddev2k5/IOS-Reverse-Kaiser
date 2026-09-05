"""
Agent Registry for IOS REVERSE KAISER.

Defines all canonical agent roles.
"""

from typing import Dict, List, Optional, Set, Tuple
from .model import (
    AgentDefinition, AgentRole, AgentTask, TaskStatus,
    Complexity, ContextPolicy, HandoffPolicy, RetryPolicy,
    FailureSemantics, TerminationCondition
)


def create_planner_agent() -> AgentDefinition:
    """Create planner agent definition."""
    return AgentDefinition(
        agent_id="agent.planner",
        role=AgentRole.PLANNER,
        description="Workflow decomposition and task planning agent",
        allowed_domains=["workflow", "orchestration"],
        allowed_capabilities=[],
        allowed_artifacts=["workflow-dag", "case-state"],
        required_inputs=["workflow_dag", "current_state", "complexity", "coverage_requirements"],
        expected_outputs=["task_list", "execution_plan", "agent_assignments"],
        max_scope=Complexity.VERY_HIGH,
        allowed_tools=["workflow-engine", "task-scheduler"],
        context_policy=ContextPolicy(
            max_context_tokens=6000,
            include_verified_facts=True,
            include_evidence_refs=True,
            include_artifact_refs=True,
            include_known_failures=True,
            include_expected_outputs=True,
        ),
        handoff_policy=HandoffPolicy(
            use_artifacts=True,
            require_acknowledgment=True,
            preserve_provenance=True,
            max_handoffs=10,
        ),
        termination_conditions=[
            TerminationCondition("all_tasks_assigned", "All workflow nodes assigned"),
            TerminationCondition("blocked_tasks_identified", "Blocked tasks identified"),
            TerminationCondition("budget_exhausted", "Agent budget exhausted"),
        ],
        retry_policy=RetryPolicy(
            max_retries=2,
            retry_on_transient_failure=True,
            do_not_retry_on_invalid_artifact=True,
        ),
        failure_semantics=FailureSemantics(
            transient_adapter_failure="retry",
            invalid_artifact="skip",
            missing_tool="block",
            unsupported_metadata="partial",
        ),
    )


def create_artifact_analyst_agent() -> AgentDefinition:
    """Create artifact analyst agent definition."""
    return AgentDefinition(
        agent_id="agent.artifact-analyst",
        role=AgentRole.ARTIFACT_ANALYST,
        description="IPA/bundle/component analysis agent",
        allowed_domains=["foundation", "components"],
        allowed_capabilities=[
            "foundation.artifact_detect",
            "foundation.ipa_validate",
            "foundation.ipa_unpack",
            "foundation.bundle_inventory",
            "foundation.plist_extract",
            "foundation.entitlements_extract",
            "framework.inventory",
            "dylib.inventory",
            "extension.inventory",
        ],
        allowed_artifacts=["ipa", "app", "framework", "dylib", "appex"],
        required_inputs=["artifact_path", "artifact_type"],
        expected_outputs=["bundle_manifest", "component_inventory", "eligible_executables"],
        max_scope=Complexity.MEDIUM,
        allowed_tools=["unzip", "plist-parser"],
        context_policy=ContextPolicy(
            max_context_tokens=4000,
            include_verified_facts=True,
            include_evidence_refs=True,
            include_artifact_refs=True,
            include_known_failures=True,
            include_expected_outputs=True,
        ),
        handoff_policy=HandoffPolicy(
            use_artifacts=True,
            require_acknowledgment=False,
            preserve_provenance=True,
            max_handoffs=3,
        ),
        termination_conditions=[
            TerminationCondition("inventory_complete", "Component inventory complete"),
            TerminationCondition("eligible_set_identified", "Eligible executables identified"),
        ],
        retry_policy=RetryPolicy(
            max_retries=3,
            retry_on_transient_failure=True,
            do_not_retry_on_invalid_artifact=True,
        ),
        failure_semantics=FailureSemantics(
            transient_adapter_failure="retry",
            invalid_artifact="skip",
            missing_tool="block",
            unsupported_metadata="partial",
        ),
    )


def create_objc_swift_analyst_agent() -> AgentDefinition:
    """Create ObjC/Swift analyst agent definition."""
    return AgentDefinition(
        agent_id="agent.objc-swift-analyst",
        role=AgentRole.OBJC_SWIFT_ANALYST,
        description="Objective-C and Swift metadata analysis agent",
        allowed_domains=["objective_c", "swift"],
        allowed_capabilities=[
            "objc.metadata",
            "objc.deep_metadata",
            "swift.metadata",
            "swift.demangle",
        ],
        allowed_artifacts=["executable", "framework", "dylib"],
        required_inputs=["binary_path", "component_id"],
        expected_outputs=["objc_metadata", "swift_metadata", "class_relationships", "type_hierarchy"],
        max_scope=Complexity.HIGH,
        allowed_tools=["macho-parser", "objc-metadata-extractor", "swift-demangler"],
        context_policy=ContextPolicy(
            max_context_tokens=5000,
            include_verified_facts=True,
            include_evidence_refs=True,
            include_artifact_refs=True,
            include_known_failures=True,
            include_expected_outputs=True,
        ),
        handoff_policy=HandoffPolicy(
            use_artifacts=True,
            require_acknowledgment=False,
            preserve_provenance=True,
            max_handoffs=4,
        ),
        termination_conditions=[
            TerminationCondition("metadata_extracted", "Language metadata extracted"),
            TerminationCondition("relationships_identified", "Class/type relationships identified"),
        ],
        retry_policy=RetryPolicy(
            max_retries=3,
            retry_on_transient_failure=True,
            do_not_retry_on_invalid_artifact=True,
        ),
        failure_semantics=FailureSemantics(
            transient_adapter_failure="retry",
            invalid_artifact="skip",
            missing_tool="partial",
            unsupported_metadata="partial",
        ),
    )


def create_binary_analyst_agent() -> AgentDefinition:
    """Create binary analyst agent definition."""
    return AgentDefinition(
        agent_id="agent.binary-analyst",
        role=AgentRole.BINARY_ANALYST,
        description="Mach-O and binary analysis agent",
        allowed_domains=["macho", "binary"],
        allowed_capabilities=[
            "macho.basic",
            "macho.slices",
            "macho.load_commands",
            "binary.imports",
            "binary.exports",
            "binary.symbols",
            "binary.strings",
        ],
        allowed_artifacts=["executable", "framework", "dylib", "macho"],
        required_inputs=["binary_path"],
        expected_outputs=["macho_header", "imports", "exports", "symbols", "strings"],
        max_scope=Complexity.HIGH,
        allowed_tools=["macho-parser", "strings-extractor", "objdump"],
        context_policy=ContextPolicy(
            max_context_tokens=5000,
            include_verified_facts=True,
            include_evidence_refs=True,
            include_artifact_refs=True,
            include_known_failures=True,
            include_expected_outputs=True,
        ),
        handoff_policy=HandoffPolicy(
            use_artifacts=True,
            require_acknowledgment=False,
            preserve_provenance=True,
            max_handoffs=4,
        ),
        termination_conditions=[
            TerminationCondition("macho_analyzed", "Mach-O structure analyzed"),
            TerminationCondition("symbols_extracted", "Symbol table extracted"),
            TerminationCondition("strings_extracted", "Strings extracted"),
        ],
        retry_policy=RetryPolicy(
            max_retries=3,
            retry_on_transient_failure=True,
            do_not_retry_on_invalid_artifact=True,
        ),
        failure_semantics=FailureSemantics(
            transient_adapter_failure="retry",
            invalid_artifact="skip",
            missing_tool="partial",
            unsupported_metadata="partial",
        ),
    )


def create_network_analyst_agent() -> AgentDefinition:
    """Create network analyst agent definition."""
    return AgentDefinition(
        agent_id="agent.network-analyst",
        role=AgentRole.NETWORK_ANALYST,
        description="Network framework and endpoint analysis agent",
        allowed_domains=["network"],
        allowed_capabilities=[
            "network.framework_detection",
            "network.endpoint_discovery",
            "architecture.detection",
        ],
        allowed_artifacts=["executable", "framework", "strings"],
        required_inputs=["binary_path", "strings_data"],
        expected_outputs=["framework_presence", "endpoint_candidates", "network_correlations"],
        max_scope=Complexity.HIGH,
        allowed_tools=["strings-extractor", "regex-engine"],
        context_policy=ContextPolicy(
            max_context_tokens=5000,
            include_verified_facts=True,
            include_evidence_refs=True,
            include_artifact_refs=True,
            include_known_failures=True,
            include_expected_outputs=True,
        ),
        handoff_policy=HandoffPolicy(
            use_artifacts=True,
            require_acknowledgment=True,
            preserve_provenance=True,
            max_handoffs=4,
        ),
        termination_conditions=[
            TerminationCondition("frameworks_identified", "Network frameworks identified"),
            TerminationCondition("endpoints_discovered", "Endpoint candidates discovered"),
            TerminationCondition("gaps_recorded", "Unresolved gaps recorded"),
        ],
        retry_policy=RetryPolicy(
            max_retries=3,
            retry_on_transient_failure=True,
            do_not_retry_on_invalid_artifact=True,
        ),
        failure_semantics=FailureSemantics(
            transient_adapter_failure="retry",
            invalid_artifact="skip",
            missing_tool="partial",
            unsupported_metadata="partial",
        ),
    )


def create_evidence_validator_agent() -> AgentDefinition:
    """Create evidence validator agent definition."""
    return AgentDefinition(
        agent_id="agent.evidence-validator",
        role=AgentRole.EVIDENCE_VALIDATOR,
        description="Evidence and claim validation agent",
        allowed_domains=["validation"],
        allowed_capabilities=[],
        allowed_artifacts=["claim", "evidence"],
        required_inputs=["candidate_claims", "evidence_refs"],
        expected_outputs=["validation_results", "downgrades", "rejections", "conflicts"],
        max_scope=Complexity.HIGH,
        allowed_tools=["evidence-checker", "claim-validator"],
        context_policy=ContextPolicy(
            max_context_tokens=4000,
            include_verified_facts=True,
            include_evidence_refs=True,
            include_artifact_refs=True,
            include_known_failures=True,
            include_expected_outputs=True,
        ),
        handoff_policy=HandoffPolicy(
            use_artifacts=True,
            require_acknowledgment=True,
            preserve_provenance=True,
            max_handoffs=5,
        ),
        termination_conditions=[
            TerminationCondition("all_claims_validated", "All candidate claims validated"),
            TerminationCondition("conflicts_resolved", "Conflicts identified and resolved"),
        ],
        retry_policy=RetryPolicy(
            max_retries=2,
            retry_on_transient_failure=True,
            do_not_retry_on_invalid_artifact=True,
        ),
        failure_semantics=FailureSemantics(
            transient_adapter_failure="retry",
            invalid_artifact="skip",
            missing_tool="partial",
            unsupported_metadata="partial",
        ),
    )


def create_coverage_auditor_agent() -> AgentDefinition:
    """Create coverage auditor agent definition."""
    return AgentDefinition(
        agent_id="agent.coverage-auditor",
        role=AgentRole.COVERAGE_AUDITOR,
        description="Coverage policy compliance auditor",
        allowed_domains=["coverage"],
        allowed_capabilities=["coverage.calculation"],
        allowed_artifacts=["case-state", "analysis-results"],
        required_inputs=["workflow", "depth", "eligible_targets", "capability_results"],
        expected_outputs=["coverage_audit", "gaps", "missing_dimensions"],
        max_scope=Complexity.MEDIUM,
        allowed_tools=["coverage-calculator"],
        context_policy=ContextPolicy(
            max_context_tokens=4000,
            include_verified_facts=True,
            include_evidence_refs=True,
            include_artifact_refs=True,
            include_known_failures=True,
            include_expected_outputs=True,
        ),
        handoff_policy=HandoffPolicy(
            use_artifacts=True,
            require_acknowledgment=False,
            preserve_provenance=True,
            max_handoffs=2,
        ),
        termination_conditions=[
            TerminationCondition("coverage_audited", "Coverage audit complete"),
            TerminationCondition("gaps_identified", "Coverage gaps identified"),
        ],
        retry_policy=RetryPolicy(
            max_retries=2,
            retry_on_transient_failure=True,
            do_not_retry_on_invalid_artifact=True,
        ),
        failure_semantics=FailureSemantics(
            transient_adapter_failure="retry",
            invalid_artifact="skip",
            missing_tool="partial",
            unsupported_metadata="partial",
        ),
    )


def create_reporter_agent() -> AgentDefinition:
    """Create reporter agent definition."""
    return AgentDefinition(
        agent_id="agent.reporter",
        role=AgentRole.REPORTER,
        description="Report generation agent",
        allowed_domains=["reporting"],
        allowed_capabilities=[],
        allowed_artifacts=["analysis-results", "coverage-audit", "claims", "evidence"],
        required_inputs=["case_id", "output_format"],
        expected_outputs=["json_report", "markdown_report"],
        max_scope=Complexity.LOW,
        allowed_tools=["json-renderer", "markdown-renderer"],
        context_policy=ContextPolicy(
            max_context_tokens=5000,
            include_verified_facts=True,
            include_evidence_refs=True,
            include_artifact_refs=True,
            include_known_failures=True,
            include_expected_outputs=True,
        ),
        handoff_policy=HandoffPolicy(
            use_artifacts=True,
            require_acknowledgment=False,
            preserve_provenance=True,
            max_handoffs=2,
        ),
        termination_conditions=[
            TerminationCondition("report_generated", "Report generated"),
        ],
        retry_policy=RetryPolicy(
            max_retries=2,
            retry_on_transient_failure=True,
            do_not_retry_on_invalid_artifact=True,
        ),
        failure_semantics=FailureSemantics(
            transient_adapter_failure="retry",
            invalid_artifact="skip",
            missing_tool="block",
            unsupported_metadata="partial",
        ),
    )


def create_all_agents() -> Dict[str, AgentDefinition]:
    """Create all agent definitions."""
    return {
        "agent.planner": create_planner_agent(),
        "agent.artifact-analyst": create_artifact_analyst_agent(),
        "agent.objc-swift-analyst": create_objc_swift_analyst_agent(),
        "agent.binary-analyst": create_binary_analyst_agent(),
        "agent.network-analyst": create_network_analyst_agent(),
        "agent.evidence-validator": create_evidence_validator_agent(),
        "agent.coverage-auditor": create_coverage_auditor_agent(),
        "agent.reporter": create_reporter_agent(),
    }


class AgentRegistry:
    """Registry of all agent definitions."""

    def __init__(self):
        self._agents: Dict[str, AgentDefinition] = {}
        self._roles: Dict[AgentRole, AgentDefinition] = {}
        for agent_id, agent in create_all_agents().items():
            self.register(agent)

    def register(self, agent: AgentDefinition):
        """Register an agent."""
        self._agents[agent.agent_id] = agent
        self._roles[agent.role] = agent

    def get(self, agent_id: str) -> Optional[AgentDefinition]:
        """Get agent by ID."""
        return self._agents.get(agent_id)

    def get_by_role(self, role: AgentRole) -> Optional[AgentDefinition]:
        """Get agent by role."""
        return self._roles.get(role)

    def list_agents(self) -> List[str]:
        """List all agent IDs."""
        return sorted(self._agents.keys())

    def list_roles(self) -> List[AgentRole]:
        """List all roles."""
        return sorted(self._roles.keys(), key=lambda r: r.value)

    def validate_agent(self, agent_id: str) -> Tuple[bool, List[str]]:
        """Validate agent definition."""
        agent = self.get(agent_id)
        if not agent:
            return False, [f"Agent {agent_id} not found"]

        errors = []
        if not agent.agent_id:
            errors.append("Missing agent_id")
        if not agent.role:
            errors.append("Missing role")
        if not agent.description:
            errors.append("Missing description")

        return len(errors) == 0, errors

    def get_allowed_agents(self, workflow_allowed: List[str]) -> List[AgentRole]:
        """Get list of allowed agents from workflow allowed list."""
        role_map = {
            "planner": AgentRole.PLANNER,
            "artifact-analyst": AgentRole.ARTIFACT_ANALYST,
            "objc-swift-analyst": AgentRole.OBJC_SWIFT_ANALYST,
            "binary-analyst": AgentRole.BINARY_ANALYST,
            "network-analyst": AgentRole.NETWORK_ANALYST,
            "evidence-validator": AgentRole.EVIDENCE_VALIDATOR,
            "coverage-auditor": AgentRole.COVERAGE_AUDITOR,
            "reporter": AgentRole.REPORTER,
        }

        result = []
        for allowed in workflow_allowed:
            if allowed in role_map:
                result.append(role_map[allowed])

        return result


# Global registry
_registry: AgentRegistry = None


def get_registry() -> AgentRegistry:
    """Get or create the agent registry."""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry


def get_agent(agent_id: str) -> Optional[AgentDefinition]:
    """Get agent by ID."""
    return get_registry().get(agent_id)


def get_agent_by_role(role: AgentRole) -> Optional[AgentDefinition]:
    """Get agent by role."""
    return get_registry().get_by_role(role)


def list_agents() -> List[str]:
    """List all agent IDs."""
    return get_registry().list_agents()


def list_roles() -> List[AgentRole]:
    """List all roles."""
    return get_registry().list_roles()
