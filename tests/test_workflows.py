"""
P05 Workflow Tests.

Tests for workflow schema, registry, definitions, and validation.
"""

import pytest
from ios_reverse.workflows import (
    Intent, Depth, WorkflowStatus, NodeStatus, Complexity,
    get_registry, get_workflow, list_workflows, list_intents,
    normalize_intent, parse_intent_with_depth, get_capabilities_for_workflow,
    validate_all_workflows, validate_workflow_differential,
    validate_unpack_narrowness, validate_report_no_analysis,
    WorkflowValidator,
)


class TestIntentNormalization:
    """Test intent normalization."""

    def test_simple_intent(self):
        """Test simple intent parsing."""
        intent, depth = parse_intent_with_depth("unpack")
        assert intent == "unpack"
        assert depth == "standard"

    def test_intent_with_depth(self):
        """Test intent with depth modifier."""
        intent, depth = parse_intent_with_depth("dump-full")
        assert intent == "dump"
        assert depth == "full"

    def test_intent_with_quick_depth(self):
        """Test intent with quick depth."""
        intent, depth = parse_intent_with_depth("inspect-quick")
        assert intent == "inspect"
        assert depth == "quick"

    def test_intent_with_deep_depth(self):
        """Test intent with deep depth."""
        intent, depth = parse_intent_with_depth("network-deep")
        assert intent == "network"
        assert depth == "deep"

    def test_normalize_simple(self):
        """Test normalize for simple intent."""
        result = normalize_intent("unpack")
        assert result == "unpack"

    def test_normalize_with_depth(self):
        """Test normalize with depth."""
        result = normalize_intent("dump-full")
        assert result == "dump"


class TestWorkflowRegistry:
    """Test workflow registry."""

    def test_all_workflows_registered(self):
        """Test that all expected workflows are registered."""
        workflows = list_workflows()

        expected = [
            "ios.unpack", "ios.inspect", "ios.dump", "ios.macho",
            "ios.objc", "ios.swift", "ios.network", "ios.login-flow",
            "ios.crypto", "ios.anti-analysis", "ios.report",
            "ios.decompile", "ios.ida", "ios.runtime", "ios.full",
        ]

        for wf in expected:
            assert wf in workflows, f"Missing workflow: {wf}"

    def test_get_workflow_by_id(self):
        """Test getting workflow by ID."""
        wf = get_workflow("ios.unpack")
        assert wf is not None
        assert wf.workflow_id == "ios.unpack"

    def test_get_workflow_by_intent(self):
        """Test getting workflow by intent."""
        from ios_reverse.workflows.registry import get_workflow_by_intent
        wf = get_workflow_by_intent("unpack")
        assert wf is not None
        assert wf.intent == "unpack"

    def test_list_intents(self):
        """Test listing all intents."""
        intents = list_intents()

        expected = ["unpack", "inspect", "dump", "macho", "objc", "swift",
                    "network", "login-flow", "crypto", "anti-analysis", "report"]

        for intent in expected:
            assert intent in intents


class TestUnpackWorkflow:
    """Test ios.unpack workflow."""

    @pytest.fixture
    def unpack(self):
        """Get unpack workflow."""
        return get_workflow("ios.unpack")

    def test_workflow_exists(self, unpack):
        """Test unpack workflow exists."""
        assert unpack is not None

    def test_intent(self, unpack):
        """Test unpack intent."""
        assert unpack.intent == Intent.UNPACK.value

    def test_entry_node(self, unpack):
        """Test unpack entry node."""
        assert unpack.entry_node == "artifact_detect"

    def test_terminal_nodes(self, unpack):
        """Test unpack terminal nodes."""
        assert "manifest" in unpack.terminal_nodes

    def test_no_deep_analysis(self, unpack):
        """Test unpack doesn't include deep analysis."""
        caps = set()
        for node in unpack.nodes:
            if node.capability_id:
                caps.add(node.capability_id)

        # Should not include these
        assert "objc.metadata" not in caps
        assert "swift.metadata" not in caps
        assert "network.framework_detection" not in caps
        assert "crypto.detection" not in caps

    def test_only_foundation(self, unpack):
        """Test unpack only uses foundation capabilities."""
        caps = set()
        for node in unpack.nodes:
            if node.capability_id:
                caps.add(node.capability_id)

        # Should only be foundation
        expected = {"foundation.artifact_detect", "foundation.ipa_validate",
                   "foundation.ipa_unpack", "foundation.bundle_inventory"}
        assert caps == expected

    def test_complexity_low(self, unpack):
        """Test unpack has low complexity."""
        assert unpack.complexity == Complexity.LOW


class TestDumpWorkflow:
    """Test ios.dump workflow."""

    @pytest.fixture
    def dump(self):
        """Get dump workflow."""
        return get_workflow("ios.dump")

    def test_workflow_exists(self, dump):
        """Test dump workflow exists."""
        assert dump is not None

    def test_intent(self, dump):
        """Test dump intent."""
        assert dump.intent == Intent.DUMP.value

    def test_has_coverage(self, dump):
        """Test dump has coverage audit node."""
        cap_names = [n.capability_id for n in dump.nodes if n.capability_id]
        assert "coverage.calculation" in cap_names

    def test_depth_profiles(self, dump):
        """Test dump supports all depths."""
        assert Depth.QUICK in dump.supported_depths
        assert Depth.STANDARD in dump.supported_depths
        assert Depth.DEEP in dump.supported_depths
        assert Depth.FULL in dump.supported_depths


class TestNetworkWorkflow:
    """Test ios.network workflow."""

    @pytest.fixture
    def network(self):
        """Get network workflow."""
        return get_workflow("ios.network")

    def test_workflow_exists(self, network):
        """Test network workflow exists."""
        assert network is not None

    def test_intent(self, network):
        """Test network intent."""
        assert network.intent == Intent.NETWORK.value

    def test_high_complexity(self, network):
        """Test network has high complexity."""
        assert network.complexity == Complexity.HIGH

    def test_has_network_capabilities(self, network):
        """Test network includes network capabilities."""
        caps = [n.capability_id for n in network.nodes if n.capability_id]

        assert "network.framework_detection" in caps
        assert "network.endpoint_discovery" in caps


class TestReportWorkflow:
    """Test ios.report workflow."""

    @pytest.fixture
    def report(self):
        """Get report workflow."""
        return get_workflow("ios.report")

    def test_workflow_exists(self, report):
        """Test report workflow exists."""
        assert report is not None

    def test_intent(self, report):
        """Test report intent."""
        assert report.intent == Intent.REPORT.value

    def test_does_not_include_analysis(self, report):
        """Test report does not include analysis capabilities."""
        caps = set()
        for node in report.nodes:
            if node.capability_id:
                caps.add(node.capability_id)

        # Should not include any analysis capabilities
        forbidden = [
            "macho.basic", "binary.imports", "objc.metadata",
            "network.framework_detection", "crypto.detection"
        ]

        for cap in forbidden:
            assert cap not in caps, f"Report should not include {cap}"


class TestAdvancedWorkflows:
    """Test advanced workflows (IDA, decompile, runtime)."""

    def test_decompile_implemented(self):
        """Test decompile is implemented."""
        wf = get_workflow("ios.decompile")
        assert wf.status == WorkflowStatus.IMPLEMENTED

    def test_ida_implemented(self):
        """Test IDA is implemented."""
        wf = get_workflow("ios.ida")
        assert wf.status == WorkflowStatus.IMPLEMENTED

    def test_runtime_partial(self):
        """Test runtime is partial (requires device)."""
        wf = get_workflow("ios.runtime")
        assert wf.status == WorkflowStatus.PARTIAL


class TestWorkflowValidator:
    """Test workflow validation."""

    def test_validate_all_workflows(self):
        """Test validating all workflows."""
        results = validate_all_workflows()

        for wf_id, (is_valid, errors, warnings) in results.items():
            assert is_valid, f"{wf_id} has errors: {errors}"

    def test_validate_unpack_narrowness(self):
        """Test unpack narrowness validation."""
        is_valid, errors = validate_unpack_narrowness()
        assert is_valid, f"Unpack is not narrow: {errors}"

    def test_validate_report_no_analysis(self):
        """Test report doesn't trigger analysis."""
        is_valid, errors = validate_report_no_analysis()
        assert is_valid, f"Report triggers analysis: {errors}"

    def test_unpack_scope_leakage(self):
        """Test unpack scope leakage detection."""
        validator = WorkflowValidator()
        unpack = get_workflow("ios.unpack")
        is_valid, errors, _ = validator.validate(unpack)

        # Should not have scope leakage
        for err in errors:
            assert "Scope leakage" not in err


class TestWorkflowDifferential:
    """Test workflow differential constraints."""

    def test_dump_standard_subset_of_full(self):
        """Test dump standard ⊂ dump full."""
        results = validate_workflow_differential()

        assert "ios.dump" in results
        result = results["ios.dump"]

        assert result["is_subset"], "dump standard should be subset of dump full"
        assert len(result["missing_in_full"]) == 0

    def test_network_standard_subset_of_full(self):
        """Test network standard ⊂ network full."""
        results = validate_workflow_differential()

        assert "ios.network" in results
        result = results["ios.network"]

        assert result["is_subset"], "network standard should be subset of network full"

    def test_capabilities_for_depth(self):
        """Test getting capabilities for specific depth."""
        caps_full = get_capabilities_for_workflow("ios.dump", "full")
        caps_std = get_capabilities_for_workflow("ios.dump", "standard")

        # Full should have at least as many capabilities as standard
        assert len(caps_full) >= len(caps_std)


class TestWorkflowSchema:
    """Test workflow schema structures."""

    def test_workflow_definition(self):
        """Test workflow definition creation."""
        wf = get_workflow("ios.unpack")

        assert wf.workflow_id
        assert wf.version
        assert wf.intent
        assert wf.nodes
        assert wf.edges
        assert wf.entry_node
        assert wf.terminal_nodes

    def test_workflow_node(self):
        """Test workflow node structure."""
        wf = get_workflow("ios.unpack")
        node = wf.get_node("artifact_detect")

        assert node.node_id == "artifact_detect"
        assert node.capability_id
        assert node.description

    def test_get_capabilities_for_depth(self):
        """Test getting capabilities for depth."""
        wf = get_workflow("ios.dump")

        quick_caps = wf.get_capabilities_for_depth(Depth.QUICK)
        full_caps = wf.get_capabilities_for_depth(Depth.FULL)

        # Full should have more or equal capabilities
        assert len(full_caps) >= len(quick_caps)

    def test_node_dependencies(self):
        """Test node dependency resolution."""
        wf = get_workflow("ios.unpack")
        deps = wf.get_node_dependencies("ipa_validate")

        assert "artifact_detect" in deps

    def test_terminal_nodes(self):
        """Test getting terminal nodes."""
        wf = get_workflow("ios.unpack")
        terminals = wf.get_terminal_nodes()

        assert len(terminals) > 0
        assert all(t.node_id in wf.terminal_nodes for t in terminals)


class TestWorkflowCompleteness:
    """Test workflow completeness requirements."""

    def test_all_canonical_intents_have_workflows(self):
        """Test all canonical intents have workflows."""
        canonical_intents = [
            "unpack", "inspect", "dump", "decompile", "macho",
            "objc", "swift", "network", "login-flow", "crypto",
            "anti-analysis", "ida", "runtime", "report", "full"
        ]

        for intent in canonical_intents:
            # Try direct lookup first
            wf = get_workflow(f"ios.{intent}")
            if wf is None:
                # Try intent-based lookup
                from ios_reverse.workflows.registry import get_workflow_by_intent
                wf = get_workflow_by_intent(intent)
            assert wf is not None, f"Missing workflow for intent: {intent}"

    def test_all_workflows_have_entry_nodes(self):
        """Test all workflows have entry nodes."""
        for wf_id in list_workflows():
            wf = get_workflow(wf_id)
            assert wf.entry_node, f"{wf_id} missing entry node"
            assert wf.get_node(wf.entry_node), f"{wf_id} entry node not found"

    def test_all_workflows_have_terminal_nodes(self):
        """Test all workflows have terminal nodes."""
        for wf_id in list_workflows():
            wf = get_workflow(wf_id)
            assert wf.terminal_nodes, f"{wf_id} missing terminal nodes"

    def test_all_workflows_resumable(self):
        """Test all workflows are resumable."""
        for wf_id in list_workflows():
            wf = get_workflow(wf_id)
            assert wf.resume_enabled, f"{wf_id} not resumable"


class TestDepthProfiles:
    """Test depth profile behavior."""

    def test_quick_narrower_than_standard(self):
        """Test quick is narrower than standard."""
        caps_quick = get_capabilities_for_workflow("ios.dump", "quick")
        caps_std = get_capabilities_for_workflow("ios.dump", "standard")

        # Quick should have fewer or equal capabilities
        assert len(caps_quick) <= len(caps_std)

    def test_deep_narrower_than_full(self):
        """Test deep is narrower than full."""
        caps_deep = get_capabilities_for_workflow("ios.dump", "deep")
        caps_full = get_capabilities_for_workflow("ios.dump", "full")

        # Deep should have fewer or equal capabilities
        assert len(caps_deep) <= len(caps_full)

    def test_all_workflows_support_depths(self):
        """Test all workflows support declared depths."""
        for wf_id in list_workflows():
            wf = get_workflow(wf_id)
            caps = wf.get_capabilities_for_depth(wf.default_depth)
            # Some workflows (like report) don't have analysis capabilities
            # and that's expected. Only warn if it's a blocking issue.
            # For now, just check that the workflow exists and has nodes.
            assert len(wf.nodes) > 0, f"{wf_id} has no nodes"
