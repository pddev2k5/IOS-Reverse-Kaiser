"""
Tests for IOS REVERSE KAISER core engine.
"""

import pytest
from ios_reverse.cli.parser import CommandParser, ParsedCommand, CommandError
from ios_reverse.engine.intent import Intent, IntentResolver
from ios_reverse.engine.depth import Depth, DepthResolver
from ios_reverse.engine.complexity import ComplexityScorer, ComplexityFactors, OrchestrationTier
from ios_reverse.engine.state import StateMachine, NodeState, StateTransitionError
from ios_reverse.engine.workflow import Workflow, WorkflowNode, WorkflowRegistry


class TestCommandParser:
    """Tests for command parser."""

    def setup_method(self):
        self.parser = CommandParser()

    def test_parse_basic(self):
        """Test basic command parsing."""
        result = self.parser.parse("app.ipa unpack")
        assert result.target == "app.ipa"
        assert result.intent == "unpack"
        assert result.depth == "quick"  # default for unpack

    def test_parse_with_depth_suffix(self):
        """Test parsing with depth suffix."""
        result = self.parser.parse("app.ipa dump-full")
        assert result.target == "app.ipa"
        assert result.intent == "dump"
        assert result.depth == "full"

    def test_parse_with_depth_option(self):
        """Test parsing with --depth option."""
        result = self.parser.parse("app.ipa dump --depth deep")
        assert result.target == "app.ipa"
        assert result.intent == "dump"
        assert result.depth == "deep"

    def test_parse_with_alias(self):
        """Test parsing with intent alias."""
        result = self.parser.parse("app.ipa extract")
        assert result.intent == "unpack"

    def test_parse_with_alias_full(self):
        """Test parsing with full alias."""
        result = self.parser.parse("app.ipa inventory-full")
        assert result.intent == "dump"
        assert result.depth == "full"

    def test_parse_invalid_intent(self):
        """Test parsing with invalid intent."""
        with pytest.raises(CommandError):
            self.parser.parse("app.ipa invalid_intent")

    def test_parse_invalid_depth(self):
        """Test parsing with invalid depth."""
        with pytest.raises(CommandError):
            self.parser.parse("app.ipa dump-invalid")

    def test_parse_with_output(self):
        """Test parsing with output directory."""
        result = self.parser.parse("app.ipa dump -o output")
        assert result.target == "app.ipa"
        assert result.intent == "dump"
        assert result.output_dir == "output"

    def test_parse_minimal_args(self):
        """Test parsing with minimal arguments."""
        with pytest.raises(CommandError):
            self.parser.parse("app.ipa")


class TestIntentResolver:
    """Tests for intent resolver."""

    def setup_method(self):
        self.resolver = IntentResolver()

    def test_resolve_canonical(self):
        """Test resolving canonical intent."""
        assert self.resolver.resolve("unpack") == Intent.UNPACK
        assert self.resolver.resolve("dump") == Intent.DUMP
        assert self.resolver.resolve("network") == Intent.NETWORK

    def test_resolve_alias(self):
        """Test resolving alias."""
        assert self.resolver.resolve("extract") == Intent.UNPACK
        assert self.resolver.resolve("inventory") == Intent.DUMP
        assert self.resolver.resolve("auth") == Intent.LOGIN_FLOW

    def test_resolve_invalid(self):
        """Test resolving invalid intent."""
        with pytest.raises(ValueError):
            self.resolver.resolve("invalid")

    def test_resolve_with_depth(self):
        """Test resolving with depth."""
        result = self.resolver.resolve_with_depth("dump-full")
        assert result.canonical == Intent.DUMP
        assert result.depth == "full"

    def test_get_supported_intents(self):
        """Test getting supported intents."""
        intents = self.resolver.get_supported_intents()
        assert "unpack" in intents
        assert "dump" in intents
        assert "network" in intents


class TestDepthResolver:
    """Tests for depth resolver."""

    def setup_method(self):
        self.resolver = DepthResolver()

    def test_resolve_canonical(self):
        """Test resolving canonical depth."""
        assert self.resolver.resolve("quick") == Depth.QUICK
        assert self.resolver.resolve("standard") == Depth.STANDARD
        assert self.resolver.resolve("deep") == Depth.DEEP
        assert self.resolver.resolve("full") == Depth.FULL

    def test_resolve_alias(self):
        """Test resolving depth alias."""
        assert self.resolver.resolve("q") == Depth.QUICK
        assert self.resolver.resolve("s") == Depth.STANDARD
        assert self.resolver.resolve("d") == Depth.DEEP
        assert self.resolver.resolve("f") == Depth.FULL

    def test_resolve_none(self):
        """Test resolving None (default)."""
        assert self.resolver.resolve(None) == Depth.STANDARD
        assert self.resolver.resolve("") == Depth.STANDARD

    def test_get_multiplier(self):
        """Test getting depth multiplier."""
        assert self.resolver.get_multiplier(Depth.QUICK) == 1.0
        assert self.resolver.get_multiplier(Depth.STANDARD) == 2.0
        assert self.resolver.get_multiplier(Depth.DEEP) == 3.0
        assert self.resolver.get_multiplier(Depth.FULL) == 5.0

    def test_is_full(self):
        """Test is_full check."""
        assert self.resolver.is_full(Depth.FULL)
        assert not self.resolver.is_full(Depth.DEEP)


class TestComplexityScorer:
    """Tests for complexity scorer."""

    def setup_method(self):
        self.scorer = ComplexityScorer()

    def test_simple_workflow(self):
        """Test scoring simple workflow."""
        factors = ComplexityFactors(
            artifact_count=1,
            depth_multiplier=1.0,
            domains=["foundation"],
        )
        score = self.scorer.calculate(factors)
        assert score.tier == OrchestrationTier.SIMPLE
        assert "executor" in score.agents

    def test_moderate_workflow(self):
        """Test scoring moderate workflow."""
        factors = ComplexityFactors(
            artifact_count=2,
            depth_multiplier=2.0,
            domains=["foundation", "macho"],
        )
        score = self.scorer.calculate(factors)
        assert score.tier in {OrchestrationTier.MODERATE, OrchestrationTier.COMPLEX}

    def test_complex_workflow(self):
        """Test scoring complex workflow."""
        factors = ComplexityFactors(
            artifact_count=3,
            depth_multiplier=3.0,
            domains=["foundation", "macho", "binary", "network"],
            binary_count=2,
            decompilation_needed=True,
            xref_analysis=True,
        )
        score = self.scorer.calculate(factors)
        assert score.tier in {OrchestrationTier.COMPLEX, OrchestrationTier.FULL}


class TestStateMachine:
    """Tests for state machine."""

    def setup_method(self):
        self.sm = StateMachine()

    def test_add_node(self):
        """Test adding a node."""
        self.sm.add_node("node1")
        assert self.sm.get_state("node1") == NodeState.PENDING

    def test_valid_transition(self):
        """Test valid state transition."""
        self.sm.add_node("node1")
        self.sm.mark_ready("node1")
        assert self.sm.get_state("node1") == NodeState.READY

    def test_invalid_transition(self):
        """Test invalid state transition."""
        self.sm.add_node("node1")
        with pytest.raises(StateTransitionError):
            self.sm.mark_done("node1")  # Can't go PENDING -> DONE

    def test_full_flow(self):
        """Test full state flow."""
        self.sm.add_node("node1")
        self.sm.mark_ready("node1")
        self.sm.mark_running("node1")
        self.sm.mark_done("node1")
        assert self.sm.get_state("node1") == NodeState.DONE

    def test_skip_flow(self):
        """Test skip flow."""
        self.sm.add_node("node1")
        self.sm.mark_ready("node1")
        self.sm.mark_skipped("node1")
        assert self.sm.get_state("node1") == NodeState.SKIPPED

    def test_failure_flow(self):
        """Test failure flow."""
        self.sm.add_node("node1")
        self.sm.mark_ready("node1")
        self.sm.mark_running("node1")
        self.sm.mark_failed("node1", "test error")
        assert self.sm.get_state("node1") == NodeState.FAILED
        assert self.sm.get_status("node1").error == "test error"

    def test_get_summary(self):
        """Test getting summary."""
        self.sm.add_node("node1")
        self.sm.add_node("node2")
        self.sm.mark_ready("node1")
        self.sm.mark_running("node1")
        summary = self.sm.get_summary()
        assert summary["total"] == 2
        assert summary["pending"] == 1
        assert summary["ready"] == 0
        assert summary["running"] == 1


class TestWorkflow:
    """Tests for workflow."""

    def test_from_dict(self):
        """Test loading workflow from dict."""
        data = {
            "id": "test-workflow",
            "version": "1.0.0",
            "name": "Test",
            "description": "Test workflow",
            "intent": "unpack",
            "nodes": [
                {
                    "id": "node1",
                    "name": "Node 1",
                    "capability": "ipa.validate",
                },
                {
                    "id": "node2",
                    "name": "Node 2",
                    "capability": "ipa.unpack",
                    "depends_on": ["node1"],
                },
            ],
            "edges": [
                {"from": "node1", "to": "node2"}
            ],
        }
        workflow = Workflow.from_dict(data)
        assert workflow.id == "test-workflow"
        assert len(workflow.nodes) == 2

    def test_topological_sort(self):
        """Test topological sort."""
        data = {
            "id": "test",
            "version": "1.0.0",
            "intent": "unpack",
            "nodes": [
                {"id": "n1", "name": "N1", "capability": "cap1"},
                {"id": "n2", "name": "N2", "capability": "cap2", "depends_on": ["n1"]},
                {"id": "n3", "name": "N3", "capability": "cap3", "depends_on": ["n1"]},
                {"id": "n4", "name": "N4", "capability": "cap4", "depends_on": ["n2", "n3"]},
            ],
        }
        workflow = Workflow.from_dict(data)
        order = workflow.topological_sort()
        # n1 must come before n2 and n3
        # n2 and n3 must come before n4
        assert order.index("n1") < order.index("n2")
        assert order.index("n1") < order.index("n3")
        assert order.index("n2") < order.index("n4")
        assert order.index("n3") < order.index("n4")

    def test_validate_cycle(self):
        """Test cycle detection."""
        data = {
            "id": "test",
            "version": "1.0.0",
            "intent": "unpack",
            "nodes": [
                {"id": "n1", "name": "N1", "capability": "cap1", "depends_on": ["n2"]},
                {"id": "n2", "name": "N2", "capability": "cap2", "depends_on": ["n1"]},
            ],
        }
        workflow = Workflow.from_dict(data)
        errors = workflow.validate()
        assert len(errors) > 0  # Should detect cycle


class TestWorkflowRegistry:
    """Tests for workflow registry."""

    def setup_method(self):
        self.registry = WorkflowRegistry()

    def test_register(self):
        """Test registering workflow."""
        data = {
            "id": "test",
            "version": "1.0.0",
            "intent": "unpack",
            "nodes": [
                {"id": "n1", "name": "N1", "capability": "cap1"},
            ],
        }
        workflow = Workflow.from_dict(data)
        self.registry.register(workflow)
        assert self.registry.get("test") is not None

    def test_get_for_intent(self):
        """Test getting workflows for intent."""
        data = {
            "id": "test",
            "version": "1.0.0",
            "intent": "unpack",
            "nodes": [],
        }
        workflow = Workflow.from_dict(data)
        self.registry.register(workflow)
        workflows = self.registry.get_for_intent("unpack")
        assert len(workflows) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
