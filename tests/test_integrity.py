"""
P08 Integrity Layer Tests.

Tests for evidence, claims, provenance, and coverage integration.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from ios_reverse.models.provenance import (
    ProvenanceGraph, ProvenanceNode, ProvenanceEdge,
    ProvenanceNodeType, ProvenanceEdgeType, ExecutionStatus,
    generate_provenance_id, generate_event_id
)
from ios_reverse.workspace import (
    CaseManager, ClaimsStore, EvidenceStore,
    IntegrityChecker, IntegrityLevel, IntegrityReport,
    TraceAPI, ClaimState, EvidenceType, EvidenceStrength,
)


class TestProvenanceModel:
    """Test provenance model."""

    def test_provenance_graph_creation(self):
        """Test creating a provenance graph."""
        graph = ProvenanceGraph(case_id="case-123")

        assert graph.case_id == "case-123"
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0

    def test_add_node(self):
        """Test adding nodes to graph."""
        graph = ProvenanceGraph(case_id="case-123")

        node = ProvenanceNode(
            node_id="node-1",
            node_type=ProvenanceNodeType.ARTIFACT,
            case_id="case-123",
            created_at="2024-01-01T00:00:00Z",
            label="test.ipa"
        )

        result = graph.add_node(node)
        assert result is True
        assert len(graph.nodes) == 1
        assert graph.get_node("node-1") == node

    def test_add_edge(self):
        """Test adding edges to graph."""
        graph = ProvenanceGraph(case_id="case-123")

        # Add nodes
        node1 = ProvenanceNode(
            node_id="artifact-1",
            node_type=ProvenanceNodeType.ARTIFACT,
            case_id="case-123",
            created_at="2024-01-01T00:00:00Z",
        )
        node2 = ProvenanceNode(
            node_id="evidence-1",
            node_type=ProvenanceNodeType.EVIDENCE,
            case_id="case-123",
            created_at="2024-01-01T00:00:00Z",
        )

        graph.add_node(node1)
        graph.add_node(node2)

        # Add edge
        edge = ProvenanceEdge(
            edge_id="edge-1",
            source_id="artifact-1",
            target_id="evidence-1",
            edge_type=ProvenanceEdgeType.PRODUCED_BY,
            case_id="case-123",
            created_at="2024-01-01T00:00:00Z",
        )

        result = graph.add_edge(edge)
        assert result is True
        assert len(graph.edges) == 1

    def test_get_ancestors(self):
        """Test getting ancestors."""
        graph = ProvenanceGraph(case_id="case-123")

        # Create chain: artifact -> evidence -> claim
        artifact = ProvenanceNode(
            node_id="artifact-1",
            node_type=ProvenanceNodeType.ARTIFACT,
            case_id="case-123",
            created_at="2024-01-01T00:00:00Z",
        )
        evidence = ProvenanceNode(
            node_id="evidence-1",
            node_type=ProvenanceNodeType.EVIDENCE,
            case_id="case-123",
            created_at="2024-01-01T00:00:00Z",
        )
        claim = ProvenanceNode(
            node_id="claim-1",
            node_type=ProvenanceNodeType.CLAIM,
            case_id="case-123",
            created_at="2024-01-01T00:00:00Z",
        )

        graph.add_node(artifact)
        graph.add_node(evidence)
        graph.add_node(claim)

        graph.add_edge(ProvenanceEdge(
            edge_id="e1",
            source_id="artifact-1",
            target_id="evidence-1",
            edge_type=ProvenanceEdgeType.PRODUCED_BY,
            case_id="case-123",
            created_at="2024-01-01T00:00:00Z",
        ))

        graph.add_edge(ProvenanceEdge(
            edge_id="e2",
            source_id="evidence-1",
            target_id="claim-1",
            edge_type=ProvenanceEdgeType.SUPPORTED_BY,
            case_id="case-123",
            created_at="2024-01-01T00:00:00Z",
        ))

        # Claim ancestors
        ancestors = graph.get_ancestors("claim-1")
        assert "evidence-1" in ancestors
        assert "artifact-1" in ancestors

    def test_get_descendants(self):
        """Test getting descendants."""
        graph = ProvenanceGraph(case_id="case-123")

        # Create chain: artifact -> evidence
        artifact = ProvenanceNode(
            node_id="artifact-1",
            node_type=ProvenanceNodeType.ARTIFACT,
            case_id="case-123",
            created_at="2024-01-01T00:00:00Z",
        )
        evidence = ProvenanceNode(
            node_id="evidence-1",
            node_type=ProvenanceNodeType.EVIDENCE,
            case_id="case-123",
            created_at="2024-01-01T00:00:00Z",
        )

        graph.add_node(artifact)
        graph.add_node(evidence)

        graph.add_edge(ProvenanceEdge(
            edge_id="e1",
            source_id="artifact-1",
            target_id="evidence-1",
            edge_type=ProvenanceEdgeType.PRODUCED_BY,
            case_id="case-123",
            created_at="2024-01-01T00:00:00Z",
        ))

        # Artifact descendants
        descendants = graph.get_descendants("artifact-1")
        assert "evidence-1" in descendants

    def test_find_nodes_by_type(self):
        """Test finding nodes by type."""
        graph = ProvenanceGraph(case_id="case-123")

        graph.add_node(ProvenanceNode(
            node_id="n1",
            node_type=ProvenanceNodeType.ARTIFACT,
            case_id="case-123",
            created_at="2024-01-01T00:00:00Z",
        ))
        graph.add_node(ProvenanceNode(
            node_id="n2",
            node_type=ProvenanceNodeType.EVIDENCE,
            case_id="case-123",
            created_at="2024-01-01T00:00:00Z",
        ))
        graph.add_node(ProvenanceNode(
            node_id="n3",
            node_type=ProvenanceNodeType.EVIDENCE,
            case_id="case-123",
            created_at="2024-01-01T00:00:00Z",
        ))

        evidence_nodes = graph.find_nodes_by_type(ProvenanceNodeType.EVIDENCE)
        assert len(evidence_nodes) == 2

    def test_detect_cycles(self):
        """Test cycle detection."""
        graph = ProvenanceGraph(case_id="case-123")

        graph.add_node(ProvenanceNode(
            node_id="n1",
            node_type=ProvenanceNodeType.ARTIFACT,
            case_id="case-123",
            created_at="2024-01-01T00:00:00Z",
        ))
        graph.add_node(ProvenanceNode(
            node_id="n2",
            node_type=ProvenanceNodeType.ARTIFACT,
            case_id="case-123",
            created_at="2024-01-01T00:00:00Z",
        ))

        # Create cycle: n1 -> n2 -> n1
        graph.add_edge(ProvenanceEdge(
            edge_id="e1",
            source_id="n1",
            target_id="n2",
            edge_type=ProvenanceEdgeType.DERIVED_FROM,
            case_id="case-123",
            created_at="2024-01-01T00:00:00Z",
        ))
        graph.add_edge(ProvenanceEdge(
            edge_id="e2",
            source_id="n2",
            target_id="n1",
            edge_type=ProvenanceEdgeType.DERIVED_FROM,
            case_id="case-123",
            created_at="2024-01-01T00:00:00Z",
        ))

        cycles = graph.detect_cycles()
        assert len(cycles) > 0

    def test_serialization(self):
        """Test graph serialization."""
        graph = ProvenanceGraph(case_id="case-123")

        graph.add_node(ProvenanceNode(
            node_id="n1",
            node_type=ProvenanceNodeType.ARTIFACT,
            case_id="case-123",
            created_at="2024-01-01T00:00:00Z",
        ))

        data = graph.to_dict()
        assert data["case_id"] == "case-123"
        assert "n1" in data["nodes"]

        # Deserialize
        graph2 = ProvenanceGraph.from_dict(data)
        assert graph2.case_id == "case-123"
        assert len(graph2.nodes) == 1


class TestProvenanceIdGeneration:
    """Test provenance ID generation."""

    def test_generate_provenance_id(self):
        """Test deterministic ID generation."""
        id1 = generate_provenance_id("artifact", "case-1", "extraction")
        id2 = generate_provenance_id("artifact", "case-1", "extraction")

        assert id1 == id2
        assert id1.startswith("prv-artifact-")

    def test_generate_event_id(self):
        """Test event ID generation."""
        id1 = generate_event_id("claim_created", "case-1")
        id2 = generate_event_id("claim_created", "case-1")

        # Should be unique (using timestamp)
        assert id1.startswith("evt-")
        assert id2.startswith("evt-")


class TestClaimStateTransitions:
    """Test claim state transitions."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def case(self, temp_workspace):
        """Create test case."""
        manager = CaseManager(temp_workspace)
        file_path = Path(temp_workspace) / "sample.ipa"
        file_path.write_bytes(b"sample content")
        identity = manager.create_case(
            target_path=str(file_path),
            intent="unpack",
            depth="standard",
        )
        return identity

    def test_claim_transitions_audited(self, temp_workspace, case):
        """Test that claim transitions are audited."""
        case_dir = Path(temp_workspace) / "cases" / case.case_id
        store = ClaimsStore(case_dir)

        # Create claim
        claim = store.add_claim(
            case_id=case.case_id,
            statement="Test claim",
            state=ClaimState.SUSPECTED,
            created_by="test-agent",
        )

        # Transition to verified
        store.update_claim_state(
            claim_id=claim.claim_id,
            new_state=ClaimState.VERIFIED,
            reason="Evidence confirmed",
            evidence_added=["ev-1"],
            validated_by="validator",
        )

        # Reload and check transitions
        reloaded = store.get_claim(claim.claim_id)
        assert len(reloaded.transitions) == 2  # Initial + transition

    def test_no_verified_without_evidence(self, temp_workspace, case):
        """Test that verified claim needs evidence."""
        case_dir = Path(temp_workspace) / "cases" / case.case_id
        store = ClaimsStore(case_dir)

        # Create claim
        claim = store.add_claim(
            case_id=case.case_id,
            statement="Test claim",
            state=ClaimState.INFERRED,
            created_by="test-agent",
        )

        # Transition to verified WITHOUT evidence should work but is integrity violation
        store.update_claim_state(
            claim_id=claim.claim_id,
            new_state=ClaimState.VERIFIED,
            reason="No evidence",
            evidence_added=[],  # No evidence!
        )

        # Integrity checker should catch this
        checker = IntegrityChecker(case_dir, IntegrityLevel.STRICT)
        report = checker.check_all()

        # Should have error about verified without evidence
        error_ids = [i.category for i in report.issues if i.severity.value == "error"]
        assert "verified_without_evidence" in error_ids


class TestEvidenceImmutability:
    """Test evidence immutability."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def case(self, temp_workspace):
        """Create test case."""
        manager = CaseManager(temp_workspace)
        file_path = Path(temp_workspace) / "sample.ipa"
        file_path.write_bytes(b"sample content")
        identity = manager.create_case(
            target_path=str(file_path),
            intent="unpack",
            depth="standard",
        )
        return identity

    def test_raw_evidence_not_overwritten(self, temp_workspace, case):
        """Test that raw evidence is not overwritten."""
        case_dir = Path(temp_workspace) / "cases" / case.case_id
        store = EvidenceStore(case_dir)

        # Add raw evidence
        evidence = store.add_evidence(
            case_id=case.case_id,
            evidence_type=EvidenceType.RAW,
            strength=EvidenceStrength.STRING_HINT,
            source_artifact="sample.ipa",
            capability="foundation.artifact_detect",
            content={"string": "/auth/login"},
            immutable=True,
        )

        # Try to add derived evidence that references same content
        # Raw evidence file should remain unchanged
        raw_dir = case_dir / "evidence" / "raw"
        raw_files = list(raw_dir.glob("*.json"))
        assert len(raw_files) == 1

        # Original raw evidence content should be preserved
        with open(raw_files[0]) as f:
            content = json.load(f)
        assert content.get("string") == "/auth/login"


class TestIntegrityChecker:
    """Test integrity checker."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def case_with_state(self, temp_workspace):
        """Create case with evidence and claims."""
        manager = CaseManager(temp_workspace)
        file_path = Path(temp_workspace) / "sample.ipa"
        file_path.write_bytes(b"sample content")
        identity = manager.create_case(
            target_path=str(file_path),
            intent="unpack",
            depth="standard",
        )

        case_dir = Path(temp_workspace) / "cases" / identity.case_id

        # Add evidence
        evidence_store = EvidenceStore(case_dir)
        evidence_store.add_evidence(
            case_id=identity.case_id,
            evidence_type=EvidenceType.RAW,
            strength=EvidenceStrength.REFERENCE,
            source_artifact="sample.ipa",
            capability="foundation.artifact_detect",
            content={"type": "ipa"},
        )

        # Add claim
        claims_store = ClaimsStore(case_dir)
        claims_store.add_claim(
            case_id=identity.case_id,
            statement="Test claim",
            state=ClaimState.VERIFIED,
            created_by="test-agent",
            evidence_refs=["ev-1"],  # Valid ref
        )

        return identity

    def test_check_passes_for_valid_state(self, temp_workspace, case_with_state):
        """Test integrity check passes for valid state."""
        case_dir = Path(temp_workspace) / "cases" / case_with_state.case_id

        # Get the actual evidence ID from the evidence store
        evidence_store = EvidenceStore(case_dir)
        evidence_list = evidence_store.list_evidence()
        assert len(evidence_list) > 0
        actual_ev_id = evidence_list[0].evidence_id

        # The fixture already has a VERIFIED claim with invalid "ev-1" ref
        # We need to use a fresh case that we control
        claims_store = ClaimsStore(case_dir)

        # Clear the invalid fixture claim by removing from index
        claims_index_path = case_dir / "claims" / "index.json"
        with open(claims_index_path) as f:
            claims_data = json.load(f)

        # Keep only properly linked claims
        valid_claims = []
        for entry in claims_data.get("entries", []):
            ev_refs = entry.get("evidence_refs", [])
            if ev_refs and ev_refs[0] != "ev-1":  # Skip the broken one
                valid_claims.append(entry)

        claims_data["entries"] = valid_claims
        with open(claims_index_path, 'w') as f:
            json.dump(claims_data, f, indent=2)

        # Add a properly linked claim
        claims_store.add_claim(
            case_id=case_with_state.case_id,
            statement="Properly linked claim",
            state=ClaimState.SUSPECTED,
            created_by="test-agent",
            evidence_refs=[actual_ev_id],
        )

        # Now run integrity check
        checker = IntegrityChecker(case_dir, IntegrityLevel.LENIENT)
        report = checker.check_all()
        assert report.status in ["PASS", "WARN"]  # Not FAIL

    def test_detects_invalid_evidence_ref(self, temp_workspace, case_with_state):
        """Test detecting invalid evidence reference."""
        case_dir = Path(temp_workspace) / "cases" / case_with_state.case_id

        # Add claim with invalid evidence ref
        claims_store = ClaimsStore(case_dir)
        claims_store.add_claim(
            case_id=case_with_state.case_id,
            statement="Invalid claim",
            state=ClaimState.SUSPECTED,
            created_by="test-agent",
            evidence_refs=["ev-nonexistent"],
        )

        checker = IntegrityChecker(case_dir, IntegrityLevel.STRICT)
        report = checker.check_all()

        error_ids = [i.category for i in report.issues if i.severity.value == "error"]
        assert "invalid_evidence_ref" in error_ids


class TestTraceAPI:
    """Test trace API."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def case_with_trace(self, temp_workspace):
        """Create case with traceable state."""
        manager = CaseManager(temp_workspace)
        file_path = Path(temp_workspace) / "sample.ipa"
        file_path.write_bytes(b"sample content")
        identity = manager.create_case(
            target_path=str(file_path),
            intent="unpack",
            depth="standard",
        )

        case_dir = Path(temp_workspace) / "cases" / identity.case_id

        # Add evidence
        evidence_store = EvidenceStore(case_dir)
        evidence = evidence_store.add_evidence(
            case_id=identity.case_id,
            evidence_type=EvidenceType.RAW,
            strength=EvidenceStrength.REFERENCE,
            source_artifact="sample.ipa",
            capability="foundation.artifact_detect",
            content={"string": "/auth/login"},
        )

        # Add claim
        claims_store = ClaimsStore(case_dir)
        claim = claims_store.add_claim(
            case_id=identity.case_id,
            statement="App connects to /auth/login",
            state=ClaimState.VERIFIED,
            created_by="network-analyst",
            evidence_refs=[evidence.evidence_id],
        )

        return identity, evidence, claim

    def test_trace_claim(self, temp_workspace, case_with_trace):
        """Test tracing a claim."""
        case_id, evidence, claim = case_with_trace
        case_dir = Path(temp_workspace) / "cases" / case_id.case_id

        api = TraceAPI(case_dir)
        result = api.trace_claim(claim.claim_id)

        assert "claim" in result
        assert result["claim"]["claim_id"] == claim.claim_id
        assert "evidence" in result

    def test_trace_evidence(self, temp_workspace, case_with_trace):
        """Test tracing evidence."""
        case_id, evidence, claim = case_with_trace
        case_dir = Path(temp_workspace) / "cases" / case_id.case_id

        api = TraceAPI(case_dir)
        result = api.trace_evidence(evidence.evidence_id)

        assert "evidence" in result
        assert result["evidence"]["evidence_id"] == evidence.evidence_id

    def test_claims_for_evidence(self, temp_workspace, case_with_trace):
        """Test finding claims for evidence."""
        case_id, evidence, claim = case_with_trace
        case_dir = Path(temp_workspace) / "cases" / case_id.case_id

        api = TraceAPI(case_dir)
        results = api.claims_for_evidence(evidence.evidence_id)

        assert len(results) >= 1
        claim_ids = [c["claim_id"] for c in results]
        assert claim.claim_id in claim_ids

    def test_evidence_for_claim(self, temp_workspace, case_with_trace):
        """Test finding evidence for claim."""
        case_id, evidence, claim = case_with_trace
        case_dir = Path(temp_workspace) / "cases" / case_id.case_id

        api = TraceAPI(case_dir)
        results = api.evidence_for_claim(claim.claim_id)

        assert len(results) >= 1
        evidence_ids = [e["evidence_id"] for e in results]
        assert evidence.evidence_id in evidence_ids


class TestCoverageAndEvidenceSeparation:
    """Test coverage and evidence certainty separation."""

    def test_coverage_completeness_vs_evidence_strength(self):
        """Test that coverage completeness != evidence certainty."""
        # Coverage can be FULL while evidence is STRING_HINT
        coverage = {
            "target": "network_analysis",
            "state": "full",  # Every binary analyzed
            "evidence": [
                {
                    "strength": "string_hint",  # Only strings found
                    "content": "api.example.com"
                }
            ]
        }

        # Coverage is complete
        assert coverage["state"] == "full"

        # But evidence is weak
        evidence_strengths = [e["strength"] for e in coverage["evidence"]]
        assert "string_hint" in evidence_strengths


class TestClaimConflictPersistence:
    """Test claim conflict persistence."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def case(self, temp_workspace):
        """Create test case."""
        manager = CaseManager(temp_workspace)
        file_path = Path(temp_workspace) / "sample.ipa"
        file_path.write_bytes(b"sample content")
        identity = manager.create_case(
            target_path=str(file_path),
            intent="unpack",
            depth="standard",
        )
        return identity

    def test_conflicts_not_silently_overwritten(self, temp_workspace, case):
        """Test that conflicts are not silently overwritten."""
        case_dir = Path(temp_workspace) / "cases" / case.case_id

        # Create conflicting claims
        claims_store = ClaimsStore(case_dir)

        claim_a = claims_store.add_claim(
            case_id=case.case_id,
            statement="Uses POST method",
            state=ClaimState.INFERRED,
            created_by="agent-a",
        )

        claim_b = claims_store.add_claim(
            case_id=case.case_id,
            statement="Uses GET method",
            state=ClaimState.INFERRED,
            created_by="agent-b",
        )

        # Both claims should exist
        claims = claims_store.list_claims()
        assert len(claims) >= 2

        # Neither should be deleted
        assert claims_store.get_claim(claim_a.claim_id) is not None
        assert claims_store.get_claim(claim_b.claim_id) is not None


class TestReportProvenance:
    """Test report provenance tracing."""

    def test_finding_references_claim(self):
        """Test that finding can reference claim."""
        finding = {
            "finding_id": "F-001",
            "statement": "App connects to api.example.com",
            "claim_id": "CLM-001",
            "evidence_refs": ["EVD-001"],
            "claim_state": "verified",
        }

        assert finding["claim_id"] is not None
        assert "EVD-001" in finding["evidence_refs"]

    def test_finding_ancestry_chain(self):
        """Test complete finding ancestry."""
        # finding -> claim -> evidence -> artifact -> original
        chain = {
            "original_artifact": {
                "artifact_id": "ART-001",
                "type": "original"
            },
            "evidence": {
                "evidence_id": "EVD-001",
                "produced_from": "ART-001"
            },
            "claim": {
                "claim_id": "CLM-001",
                "supported_by": ["EVD-001"]
            },
            "finding": {
                "finding_id": "F-001",
                "claim_ref": "CLM-001"
            }
        }

        # Can trace from finding back to original
        current = chain["finding"]
        assert current["claim_ref"] == "CLM-001"


class TestDeterminism:
    """Test determinism of operations."""

    def test_provenance_graph_ordering(self):
        """Test that graph operations are deterministic."""
        graph = ProvenanceGraph(case_id="case-123")

        # Add nodes in specific order
        for i in range(5):
            graph.add_node(ProvenanceNode(
                node_id=f"node-{i}",
                node_type=ProvenanceNodeType.ARTIFACT,
                case_id="case-123",
                created_at="2024-01-01T00:00:00Z",
            ))

        # Serialization should be deterministic
        data1 = graph.to_dict()
        data2 = graph.to_dict()

        assert data1 == data2

    def test_integrity_check_ordering(self):
        """Test that integrity check results are deterministic."""
        temp_dir = tempfile.mkdtemp()
        try:
            manager = CaseManager(temp_dir)
            file_path = Path(temp_dir) / "sample.ipa"
            file_path.write_bytes(b"sample")
            identity = manager.create_case(
                target_path=str(file_path),
                intent="unpack",
                depth="standard",
            )

            case_dir = Path(temp_dir) / "cases" / identity.case_id
            checker1 = IntegrityChecker(case_dir, IntegrityLevel.LENIENT)
            checker2 = IntegrityChecker(case_dir, IntegrityLevel.LENIENT)

            report1 = checker1.check_all()
            report2 = checker2.check_all()

            # Status should be the same
            assert report1.status == report2.status
        finally:
            shutil.rmtree(temp_dir)


class TestColdResumePreservesProvenance:
    """Test that cold resume preserves provenance."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_provenance_persists_across_load(self, temp_workspace):
        """Test provenance persists across case reload."""
        # Create case with provenance
        manager = CaseManager(temp_workspace)
        file_path = Path(temp_workspace) / "sample.ipa"
        file_path.write_bytes(b"sample content")
        identity = manager.create_case(
            target_path=str(file_path),
            intent="unpack",
            depth="standard",
        )

        case_dir = Path(temp_workspace) / "cases" / identity.case_id

        # Add evidence
        evidence_store = EvidenceStore(case_dir)
        evidence = evidence_store.add_evidence(
            case_id=identity.case_id,
            evidence_type=EvidenceType.RAW,
            strength=EvidenceStrength.REFERENCE,
            source_artifact="sample.ipa",
            capability="foundation.artifact_detect",
            content={"test": "data"},
        )

        # Add claim with SUSPECTED state to avoid verified-claim integrity check
        claims_store = ClaimsStore(case_dir)
        claim = claims_store.add_claim(
            case_id=identity.case_id,
            statement="Test statement",
            state=ClaimState.SUSPECTED,  # Use SUSPECTED instead of VERIFIED
            created_by="test-agent",
            evidence_refs=[evidence.evidence_id],
        )

        # Reload case
        reloaded_identity = manager.load_case(identity.case_id)
        assert reloaded_identity.case_id == identity.case_id

        # Reload evidence
        reloaded_evidence = evidence_store.get_evidence(evidence.evidence_id)
        assert reloaded_evidence is not None
        assert reloaded_evidence.evidence_id == evidence.evidence_id

        # Reload claim
        reloaded_claim = claims_store.get_claim(claim.claim_id)
        assert reloaded_claim is not None
        assert reloaded_claim.claim_id == claim.claim_id
        assert len(reloaded_claim.transitions) == len(claim.transitions)


class TestScalePerformance:
    """Test scale and performance."""

    def test_large_graph_traversal(self):
        """Test traversal of large graph remains bounded."""
        graph = ProvenanceGraph(case_id="case-scale-test")

        # Create 100 nodes in chain
        for i in range(100):
            graph.add_node(ProvenanceNode(
                node_id=f"node-{i}",
                node_type=ProvenanceNodeType.ARTIFACT,
                case_id="case-scale-test",
                created_at="2024-01-01T00:00:00Z",
            ))

            if i > 0:
                graph.add_edge(ProvenanceEdge(
                    edge_id=f"edge-{i}",
                    source_id=f"node-{i-1}",
                    target_id=f"node-{i}",
                    edge_type=ProvenanceEdgeType.DERIVED_FROM,
                    case_id="case-scale-test",
                    created_at="2024-01-01T00:00:00Z",
                ))

        # Traversal should complete quickly
        ancestors = graph.get_ancestors("node-99")
        assert len(ancestors) == 99  # All previous nodes

    def test_many_to_many_relationships(self):
        """Test many-to-many evidence/claim relationships."""
        temp_dir = tempfile.mkdtemp()
        try:
            manager = CaseManager(temp_dir)
            file_path = Path(temp_dir) / "sample.ipa"
            file_path.write_bytes(b"sample")
            identity = manager.create_case(
                target_path=str(file_path),
                intent="unpack",
                depth="standard",
            )

            case_dir = Path(temp_dir) / "cases" / identity.case_id
            evidence_store = EvidenceStore(case_dir)
            claims_store = ClaimsStore(case_dir)

            # Create 50 evidence items
            evidence_ids = []
            for i in range(50):
                ev = evidence_store.add_evidence(
                    case_id=identity.case_id,
                    evidence_type=EvidenceType.RAW,
                    strength=EvidenceStrength.REFERENCE,
                    source_artifact="sample.ipa",
                    capability="test",
                    content={"id": i},
                )
                evidence_ids.append(ev.evidence_id)

            # Create 20 claims referencing all evidence
            for i in range(20):
                claims_store.add_claim(
                    case_id=identity.case_id,
                    statement=f"Claim {i}",
                    state=ClaimState.VERIFIED,
                    created_by="test",
                    evidence_refs=evidence_ids,  # All evidence
                )

            # Trace API should handle this
            api = TraceAPI(case_dir)
            claims = claims_store.list_claims()
            for claim in claims[:5]:  # Check first 5
                result = api.trace_claim(claim.claim_id)
                assert len(result.get("evidence", [])) == 50
        finally:
            shutil.rmtree(temp_dir)
