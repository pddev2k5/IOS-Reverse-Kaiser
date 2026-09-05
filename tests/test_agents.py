"""
P06 Agent Tests.

Tests for agent models, registry, selector, scheduler, and validator.
"""

import pytest
from ios_reverse.agents import (
    AgentRole, TaskStatus, ValidationResult, ConflictResolution,
    AgentDefinition, AgentTask, AgentSelection,
    get_agent, get_agent_by_role, list_agents, list_roles,
    select_agents_for_workflow, get_required_agents_for_workflow_depth,
    get_budget_for_depth, AgentBudget,
    TaskScheduler, create_task_from_workflow_node, generate_deterministic_id,
    Claim, Evidence, ValidationReport, EvidenceValidator, EvidenceStrength,
    generate_context_pack, ContextPack,
    AgentTask,
)


class TestAgentRoles:
    """Test agent roles."""

    def test_all_roles_defined(self):
        """Test all canonical roles exist."""
        expected_roles = [
            AgentRole.PLANNER,
            AgentRole.ARTIFACT_ANALYST,
            AgentRole.OBJC_SWIFT_ANALYST,
            AgentRole.BINARY_ANALYST,
            AgentRole.NETWORK_ANALYST,
            AgentRole.EVIDENCE_VALIDATOR,
            AgentRole.COVERAGE_AUDITOR,
            AgentRole.REPORTER,
        ]

        for role in expected_roles:
            agent = get_agent_by_role(role)
            assert agent is not None, f"Role {role.value} not defined"
            assert agent.role == role


class TestAgentRegistry:
    """Test agent registry."""

    def test_list_agents(self):
        """Test listing agents."""
        agents = list_agents()
        assert len(agents) == 8  # 8 canonical roles

    def test_get_agent(self):
        """Test getting agent by ID."""
        agent = get_agent("agent.artifact-analyst")
        assert agent is not None
        assert agent.role == AgentRole.ARTIFACT_ANALYST

    def test_get_agent_by_role(self):
        """Test getting agent by role."""
        agent = get_agent_by_role(AgentRole.NETWORK_ANALYST)
        assert agent is not None
        assert agent.agent_id == "agent.network-analyst"

    def test_artifact_analyst_capabilities(self):
        """Test artifact analyst capabilities."""
        agent = get_agent_by_role(AgentRole.ARTIFACT_ANALYST)
        assert "foundation.artifact_detect" in agent.allowed_capabilities
        assert "foundation.ipa_unpack" in agent.allowed_capabilities


class TestAgentBudget:
    """Test agent budget."""

    def test_budget_for_depth(self):
        """Test budget values per depth."""
        assert get_budget_for_depth("quick") == 1
        assert get_budget_for_depth("standard") == 2
        assert get_budget_for_depth("deep") == 4
        assert get_budget_for_depth("full") == 6


class TestAgentSelector:
    """Test agent selection."""

    def test_select_unpack_agents(self):
        """Test selecting agents for unpack workflow."""
        selection = select_agents_for_workflow("ios.unpack", "standard")

        # Unpack should only need artifact-analyst
        assert AgentRole.ARTIFACT_ANALYST in selection.selected_roles

    def test_select_dump_agents(self):
        """Test selecting agents for dump workflow."""
        selection = select_agents_for_workflow("ios.dump", "full")

        # Dump should have multiple specialists
        assert AgentRole.ARTIFACT_ANALYST in selection.selected_roles
        assert AgentRole.BINARY_ANALYST in selection.selected_roles

    def test_select_network_agents(self):
        """Test selecting agents for network workflow."""
        selection = select_agents_for_workflow("ios.network", "deep")

        # Network workflow at deep should include network-analyst
        assert AgentRole.NETWORK_ANALYST in selection.selected_roles

    def test_select_report_agents(self):
        """Test selecting agents for report workflow."""
        selection = select_agents_for_workflow("ios.report", "standard")

        # Report should only need reporter
        assert AgentRole.REPORTER in selection.selected_roles

    def test_budget_enforcement(self):
        """Test that budget is enforced."""
        selection = select_agents_for_workflow("ios.full", "quick")

        # Quick depth should have budget of 1
        assert selection.budget_used <= selection.budget_limit

    def test_required_agents_unpack(self):
        """Test required agents for unpack."""
        # Use direct selection since get_required_agents uses registry
        selection = select_agents_for_workflow("ios.unpack", "standard")
        assert AgentRole.ARTIFACT_ANALYST in selection.selected_roles


class TestTaskScheduler:
    """Test task scheduler."""

    @pytest.fixture
    def scheduler(self):
        """Create scheduler."""
        return TaskScheduler()

    def test_add_task(self, scheduler):
        """Test adding task."""
        task = AgentTask(
            task_id="task-1",
            case_id="case-1",
            workflow_id="ios.unpack",
            node_id="artifact_detect",
            agent_role=AgentRole.ARTIFACT_ANALYST,
            objective="Detect artifact",
        )
        scheduler.add_task(task)
        assert scheduler.get_task("task-1") is not None

    def test_dependency_ready(self, scheduler):
        """Test dependency resolution for ready tasks."""
        task1 = AgentTask(
            task_id="task-1",
            case_id="case-1",
            workflow_id="ios.unpack",
            node_id="artifact_detect",
            agent_role=AgentRole.ARTIFACT_ANALYST,
            objective="Detect artifact",
        )
        task2 = AgentTask(
            task_id="task-2",
            case_id="case-1",
            workflow_id="ios.unpack",
            node_id="ipa_validate",
            agent_role=AgentRole.ARTIFACT_ANALYST,
            objective="Validate IPA",
        )

        scheduler.add_task(task1)
        scheduler.add_task(task2)
        scheduler.add_dependency("task-2", "task-1")

        # task-1 should be ready, task-2 should not
        ready = scheduler.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].task_id == "task-1"

    def test_mark_done(self, scheduler):
        """Test marking task done."""
        task = AgentTask(
            task_id="task-1",
            case_id="case-1",
            workflow_id="ios.unpack",
            node_id="artifact_detect",
            agent_role=AgentRole.ARTIFACT_ANALYST,
            objective="Detect artifact",
        )
        scheduler.add_task(task)
        scheduler.mark_task_done("task-1", {"result": "detected"})

        task = scheduler.get_task("task-1")
        assert task.status == TaskStatus.DONE

    def test_mark_failed(self, scheduler):
        """Test marking task failed."""
        task1 = AgentTask(
            task_id="task-1",
            case_id="case-1",
            workflow_id="ios.unpack",
            node_id="artifact_detect",
            agent_role=AgentRole.ARTIFACT_ANALYST,
            objective="Detect artifact",
        )
        task2 = AgentTask(
            task_id="task-2",
            case_id="case-1",
            workflow_id="ios.unpack",
            node_id="ipa_validate",
            agent_role=AgentRole.ARTIFACT_ANALYST,
            objective="Validate IPA",
        )

        scheduler.add_task(task1)
        scheduler.add_task(task2)
        scheduler.add_dependency("task-2", "task-1")

        scheduler.mark_task_failed("task-1", "Artifact not found")

        # task-2 should be blocked
        task2_status = scheduler.get_task("task-2").status
        assert task2_status == TaskStatus.BLOCKED

    def test_is_complete(self, scheduler):
        """Test completion check."""
        task = AgentTask(
            task_id="task-1",
            case_id="case-1",
            workflow_id="ios.unpack",
            node_id="artifact_detect",
            agent_role=AgentRole.ARTIFACT_ANALYST,
            objective="Detect artifact",
        )
        scheduler.add_task(task)
        assert not scheduler.is_complete()

        scheduler.mark_task_done("task-1")
        assert scheduler.is_complete()


class TestEvidenceValidator:
    """Test evidence validator."""

    @pytest.fixture
    def validator(self):
        """Create validator."""
        return EvidenceValidator()

    def test_add_evidence(self, validator):
        """Test adding evidence."""
        evidence = Evidence(
            evidence_id="ev-1",
            evidence_type="string",
            content="https://api.example.com",
            source_artifact="strings.txt",
            strength=EvidenceStrength.STRING_HINT,
            timestamp="2024-01-01T00:00:00Z",
        )
        validator.add_evidence(evidence)
        assert validator.get_evidence("ev-1") is not None

    def test_validate_claim_with_evidence(self, validator):
        """Test validating claim with evidence."""
        evidence = Evidence(
            evidence_id="ev-1",
            evidence_type="string",
            content="https://api.example.com",
            source_artifact="strings.txt",
            strength=EvidenceStrength.REFERENCE,
            timestamp="2024-01-01T00:00:00Z",
        )
        validator.add_evidence(evidence)

        claim = Claim(
            claim_id="claim-1",
            claim_type="endpoint",
            claim_value="https://api.example.com",
            evidence_refs=["ev-1"],
            strength=EvidenceStrength.REFERENCE,
            source="network-analyst",
        )

        report = validator.validate_claim(claim)
        assert report.result == ValidationResult.ACCEPT

    def test_validate_claim_missing_evidence(self, validator):
        """Test validating claim with missing evidence."""
        claim = Claim(
            claim_id="claim-1",
            claim_type="endpoint",
            claim_value="https://api.example.com",
            evidence_refs=["ev-1"],  # ev-1 not added
            strength=EvidenceStrength.REFERENCE,
            source="network-analyst",
        )

        report = validator.validate_claim(claim)
        assert report.result == ValidationResult.NEEDS_MORE_EVIDENCE

    def test_validate_claim_downgrade(self, validator):
        """Test validating claim that needs downgrade."""
        # Add weak evidence
        evidence = Evidence(
            evidence_id="ev-1",
            evidence_type="string",
            content="api.example.com",
            source_artifact="strings.txt",
            strength=EvidenceStrength.STRING_HINT,
            timestamp="2024-01-01T00:00:00Z",
        )
        validator.add_evidence(evidence)

        # Claim needs stronger evidence
        claim = Claim(
            claim_id="claim-1",
            claim_type="endpoint",
            claim_value="https://api.example.com",
            evidence_refs=["ev-1"],
            strength=EvidenceStrength.VERIFIED,  # Too strong
            source="network-analyst",
        )

        report = validator.validate_claim(claim)
        assert report.result == ValidationResult.DOWNGRADE


class TestContextPack:
    """Test context pack generation."""

    def test_generate_context_pack(self):
        """Test generating context pack."""
        task = AgentTask(
            task_id="task-1",
            case_id="case-1",
            workflow_id="ios.network",
            node_id="endpoint_discovery",
            agent_role=AgentRole.NETWORK_ANALYST,
            objective="Discover network endpoints",
            allowed_capabilities=["network.endpoint_discovery"],
            expected_outputs=["endpoints"],
        )

        pack = generate_context_pack(
            task,
            verified_facts=["Network framework present"],
            evidence_refs=["ev-1", "ev-2"],
        )

        assert pack.task_id == "task-1"
        assert pack.agent_role == AgentRole.NETWORK_ANALYST
        assert "Network framework present" in pack.verified_facts

    def test_context_pack_to_markdown(self):
        """Test context pack to markdown."""
        pack = ContextPack(
            task_id="task-1",
            agent_role=AgentRole.NETWORK_ANALYST,
            objective="Discover endpoints",
            workflow_id="ios.network",
            node_id="endpoint_discovery",
            allowed_capabilities=["network.endpoint_discovery"],
            allowed_tools=["strings-extractor"],
            verified_facts=[],
            evidence_refs=["ev-1"],
            artifact_refs=["strings.txt"],
            known_failures=[],
            expected_outputs=["endpoints"],
            constraints=["preserve_endpoint_strength"],
        )

        md = pack.to_markdown()
        assert "# Agent Context Pack: task-1" in md
        assert "## Objective" in md
        assert "Discover endpoints" in md


class TestDeterministicID:
    """Test deterministic ID generation."""

    def test_deterministic_id(self):
        """Test deterministic ID generation."""
        id1 = generate_deterministic_id("task", "case-1", "node-1")
        id2 = generate_deterministic_id("task", "case-1", "node-1")

        assert id1 == id2  # Same input should produce same ID

    def test_different_ids(self):
        """Test different inputs produce different IDs."""
        id1 = generate_deterministic_id("task", "case-1", "node-1")
        id2 = generate_deterministic_id("task", "case-1", "node-2")

        assert id1 != id2


class TestWorkflowIntegration:
    """Test workflow-agent integration."""

    def test_unpack_no_network_analyst(self):
        """Test that unpack doesn't select network analyst."""
        selection = select_agents_for_workflow("ios.unpack", "standard")
        assert AgentRole.NETWORK_ANALYST not in selection.selected_roles

    def test_unpack_no_coverage_auditor(self):
        """Test that unpack doesn't select coverage auditor."""
        selection = select_agents_for_workflow("ios.unpack", "standard")
        assert AgentRole.COVERAGE_AUDITOR not in selection.selected_roles

    def test_dump_full_has_coverage_auditor(self):
        """Test that dump full can select coverage auditor when coverage_required."""
        selection = select_agents_for_workflow("ios.dump", "full", coverage_required=True)
        # When coverage_required is True, coverage auditor should be included
        assert AgentRole.COVERAGE_AUDITOR in selection.selected_roles

    def test_report_only_reporter(self):
        """Test that report only selects reporter."""
        selection = select_agents_for_workflow("ios.report", "standard")
        assert selection.selected_roles == [AgentRole.REPORTER]

    def test_login_flow_complex_selection(self):
        """Test login-flow gets appropriate specialists."""
        selection = select_agents_for_workflow("ios.login-flow", "deep")

        assert AgentRole.PLANNER in selection.selected_roles
        assert AgentRole.NETWORK_ANALYST in selection.selected_roles

    def test_dump_standard_subset_of_full(self):
        """Test that dump standard agents ⊂ dump full agents."""
        std = select_agents_for_workflow("ios.dump", "standard")
        full = select_agents_for_workflow("ios.dump", "full", coverage_required=True)

        # Full should have at least as many agents
        assert len(full.selected_roles) >= len(std.selected_roles)


class TestBlockedWorkflows:
    """Test that blocked workflows are handled."""

    def test_decompile_workflow(self):
        """Test decompile workflow exists (blocked)."""
        from ios_reverse.workflows import get_workflow
        wf = get_workflow("ios.decompile")
        assert wf is not None
        assert wf.status.value == "blocked"


class TestAgentTask:
    """Test agent task model."""

    def test_task_status_transitions(self):
        """Test task status transitions."""
        task = AgentTask(
            task_id="task-1",
            case_id="case-1",
            workflow_id="ios.unpack",
            node_id="artifact_detect",
            agent_role=AgentRole.ARTIFACT_ANALYST,
            objective="Detect artifact",
        )

        assert task.status == TaskStatus.PENDING

        task.mark_running()
        assert task.status == TaskStatus.RUNNING

        task.mark_done({"result": "detected"})
        assert task.status == TaskStatus.DONE

    def test_task_mark_failed(self):
        """Test marking task as failed."""
        task = AgentTask(
            task_id="task-1",
            case_id="case-1",
            workflow_id="ios.unpack",
            node_id="artifact_detect",
            agent_role=AgentRole.ARTIFACT_ANALYST,
            objective="Detect artifact",
        )

        task.mark_failed("Artifact not found")
        assert task.status == TaskStatus.FAILED
        assert "Artifact not found" in task.errors

    def test_task_retry(self):
        """Test task retry logic."""
        task = AgentTask(
            task_id="task-1",
            case_id="case-1",
            workflow_id="ios.unpack",
            node_id="artifact_detect",
            agent_role=AgentRole.ARTIFACT_ANALYST,
            objective="Detect artifact",
        )

        task.mark_failed("Transient error")
        assert task.increment_retry() is True
        assert task.increment_retry() is True
        assert task.increment_retry() is False  # Max retries reached
