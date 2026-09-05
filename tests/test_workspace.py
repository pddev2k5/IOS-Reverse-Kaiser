"""
P07 Workspace Tests.

Tests for persistent case workspace and resume system.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path

from ios_reverse.workspace import (
    CaseStatus, ClaimState, EvidenceType, EvidenceStrength, ArtifactType,
    CaseIdentity, TargetInfo, WorkflowState, NodeState,
    generate_case_id, generate_evidence_id, generate_claim_id,
    compute_file_hash,
    CaseManager, CaseOperations,
    EvidenceStore, ClaimsStore,
    ResumeEngine, ResumePlan,
    ContextPackEngine, LivingDocManager,
)


class TestCaseIdentity:
    """Test case identity generation."""

    def test_generate_case_id(self):
        """Test deterministic case ID generation."""
        id1 = generate_case_id("test.ipa", "unpack", "standard")
        id2 = generate_case_id("test.ipa", "unpack", "standard")

        assert id1 == id2
        assert id1.startswith("case-")

    def test_generate_evidence_id(self):
        """Test evidence ID generation."""
        eid = generate_evidence_id("case-123", "raw")
        assert eid.startswith("ev-")

    def test_generate_claim_id(self):
        """Test claim ID generation."""
        cid = generate_claim_id("case-123", "endpoint")
        assert cid.startswith("claim-")

    def test_case_identity_to_dict(self):
        """Test case identity serialization."""
        identity = CaseIdentity(
            case_id="case-123",
            display_name="Test Case",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
            target=TargetInfo(name="test.ipa", path="/path/to/test.ipa", hash="abc123"),
            canonical_intent="unpack",
            depth="standard",
            workflow_id="ios.unpack",
        )

        data = identity.to_dict()
        assert data["case_id"] == "case-123"
        assert data["canonical_intent"] == "unpack"
        assert data["target"]["name"] == "test.ipa"

    def test_case_identity_from_dict(self):
        """Test case identity deserialization."""
        data = {
            "case_id": "case-123",
            "display_name": "Test Case",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "target": {"name": "test.ipa", "path": "/path", "hash": "abc", "size": None},
            "canonical_intent": "unpack",
            "depth": "standard",
            "workflow_id": "ios.unpack",
            "schema_version": "1.0.0",
            "status": "initializing",
        }

        identity = CaseIdentity.from_dict(data)
        assert identity.case_id == "case-123"
        assert identity.canonical_intent == "unpack"


class TestWorkflowState:
    """Test workflow state."""

    def test_workflow_state_to_dict(self):
        """Test workflow state serialization."""
        state = WorkflowState(
            workflow_id="ios.unpack",
            depth="standard",
            completed_nodes=["artifact_detect", "ipa_validate"],
            current_node="ipa_unpack",
        )

        data = state.to_dict()
        assert data["workflow_id"] == "ios.unpack"
        assert len(data["completed_nodes"]) == 2

    def test_workflow_state_from_dict(self):
        """Test workflow state deserialization."""
        data = {
            "workflow_id": "ios.unpack",
            "depth": "standard",
            "nodes": {},
            "completed_nodes": ["artifact_detect"],
            "failed_nodes": [],
            "blocked_nodes": [],
            "pending_nodes": [],
            "current_node": "ipa_unpack",
        }

        state = WorkflowState.from_dict(data)
        assert state.workflow_id == "ios.unpack"
        assert "artifact_detect" in state.completed_nodes


class TestNodeState:
    """Test node state."""

    def test_node_state_to_dict(self):
        """Test node state serialization."""
        state = NodeState(
            node_id="artifact_detect",
            status="done",
            findings={"result": "ipa"},
        )

        data = state.to_dict()
        assert data["node_id"] == "artifact_detect"
        assert data["status"] == "done"
        assert data["findings"]["result"] == "ipa"


class TestCaseManager:
    """Test case manager."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def manager(self, temp_workspace):
        """Create case manager."""
        return CaseManager(temp_workspace)

    @pytest.fixture
    def sample_file(self, temp_workspace):
        """Create sample file for testing."""
        file_path = Path(temp_workspace) / "sample.ipa"
        file_path.write_bytes(b"sample ipa content")
        return str(file_path)

    def test_create_case(self, manager, sample_file):
        """Test case creation."""
        identity = manager.create_case(
            target_path=sample_file,
            intent="unpack",
            depth="standard",
            display_name="Test Unpack"
        )

        assert identity.case_id.startswith("case-")
        assert identity.display_name == "Test Unpack"
        assert identity.canonical_intent == "unpack"
        assert identity.depth == "standard"
        assert identity.workflow_id == "ios.unpack"

    def test_load_case(self, manager, sample_file):
        """Test loading case."""
        identity = manager.create_case(
            target_path=sample_file,
            intent="unpack",
            depth="standard",
        )

        loaded = manager.load_case(identity.case_id)
        assert loaded is not None
        assert loaded.case_id == identity.case_id

    def test_list_cases(self, manager, sample_file):
        """Test listing cases."""
        identity = manager.create_case(
            target_path=sample_file,
            intent="unpack",
            depth="standard",
        )

        cases = manager.list_cases()
        assert identity.case_id in cases

    def test_case_directory_structure(self, manager, sample_file):
        """Test case creates proper directory structure."""
        identity = manager.create_case(
            target_path=sample_file,
            intent="unpack",
            depth="standard",
        )

        case_dir = Path(manager.cases_dir) / identity.case_id

        # Check directories exist
        assert (case_dir / "phases").exists()
        assert (case_dir / "endpoints").exists()
        assert (case_dir / "functions").exists()
        assert (case_dir / "callflows").exists()
        assert (case_dir / "claims").exists()
        assert (case_dir / "evidence" / "raw").exists()
        assert (case_dir / "evidence" / "derived").exists()
        assert (case_dir / "network" / "endpoints").exists()
        assert (case_dir / "artifacts" / "original").exists()
        assert (case_dir / "checkpoints").exists()
        assert (case_dir / "agents").exists()
        assert (case_dir / ".context").exists()

    def test_manifest_json(self, manager, sample_file):
        """Test manifest.json creation."""
        identity = manager.create_case(
            target_path=sample_file,
            intent="unpack",
            depth="standard",
        )

        case_dir = Path(manager.cases_dir) / identity.case_id
        manifest_path = case_dir / "manifest.json"

        assert manifest_path.exists()
        with open(manifest_path) as f:
            manifest = json.load(f)

        assert manifest["case_id"] == identity.case_id
        assert manifest["claims"]["index_path"] == "claims/index.json"
        assert manifest["evidence"]["index_path"] == "evidence/index.json"

    def test_checkpoints(self, manager, sample_file):
        """Test checkpoint creation."""
        identity = manager.create_case(
            target_path=sample_file,
            intent="unpack",
            depth="standard",
        )

        # Create checkpoint
        workflow_state = {
            "workflow_id": "ios.unpack",
            "depth": "standard",
            "nodes": {},
            "completed_nodes": ["artifact_detect"],
            "failed_nodes": [],
            "blocked_nodes": [],
            "pending_nodes": [],
        }

        checkpoint_id = manager.checkpoint_case(
            case_id=identity.case_id,
            workflow_state=workflow_state,
            evidence_refs=[],
            artifact_refs=[],
            agent_tasks=[],
            current_node="ipa_unpack",
            current_phase="intake",
        )

        assert checkpoint_id.startswith("ckpt-")

        # Load checkpoint
        checkpoint = manager.get_latest_checkpoint(identity.case_id)
        assert checkpoint is not None
        assert checkpoint["workflow_id"] == "ios.unpack"


class TestEvidenceStore:
    """Test evidence store."""

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

    def test_add_raw_evidence(self, temp_workspace, case):
        """Test adding raw evidence."""
        case_dir = Path(temp_workspace) / "cases" / case.case_id
        store = EvidenceStore(case_dir)

        evidence = store.add_evidence(
            case_id=case.case_id,
            evidence_type=EvidenceType.RAW,
            strength=EvidenceStrength.REFERENCE,
            source_artifact="sample.ipa",
            capability="foundation.artifact_detect",
            content={"type": "ipa", "size": 1234},
        )

        assert evidence.evidence_id.startswith("ev-")
        assert evidence.type == EvidenceType.RAW
        assert evidence.strength == EvidenceStrength.REFERENCE

    def test_add_derived_evidence(self, temp_workspace, case):
        """Test adding derived evidence."""
        case_dir = Path(temp_workspace) / "cases" / case.case_id
        store = EvidenceStore(case_dir)

        evidence = store.add_evidence(
            case_id=case.case_id,
            evidence_type=EvidenceType.DERIVED,
            strength=EvidenceStrength.CORRELATED,
            source_artifact="sample.ipa",
            capability="network.endpoint_discovery",
            content={"endpoints": ["https://api.example.com"]},
        )

        assert evidence.type == EvidenceType.DERIVED

    def test_list_evidence(self, temp_workspace, case):
        """Test listing evidence."""
        case_dir = Path(temp_workspace) / "cases" / case.case_id
        store = EvidenceStore(case_dir)

        store.add_evidence(
            case_id=case.case_id,
            evidence_type=EvidenceType.RAW,
            strength=EvidenceStrength.REFERENCE,
            source_artifact="sample.ipa",
            capability="foundation.artifact_detect",
            content={"type": "ipa"},
        )

        evidence_list = store.list_evidence()
        assert len(evidence_list) == 1

        raw_only = store.list_evidence(EvidenceType.RAW)
        assert len(raw_only) == 1


class TestClaimsStore:
    """Test claims store."""

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

    def test_add_claim(self, temp_workspace, case):
        """Test adding claim."""
        case_dir = Path(temp_workspace) / "cases" / case.case_id
        store = ClaimsStore(case_dir)

        claim = store.add_claim(
            case_id=case.case_id,
            statement="App connects to https://api.example.com",
            state=ClaimState.SUSPECTED,
            created_by="network-analyst",
        )

        assert claim.claim_id.startswith("claim-")
        assert claim.statement == "App connects to https://api.example.com"
        assert claim.state == ClaimState.SUSPECTED

    def test_update_claim_state(self, temp_workspace, case):
        """Test updating claim state."""
        case_dir = Path(temp_workspace) / "cases" / case.case_id
        store = ClaimsStore(case_dir)

        claim = store.add_claim(
            case_id=case.case_id,
            statement="App uses encryption",
            state=ClaimState.INFERRED,
            created_by="binary-analyst",
        )

        # Update to verified
        updated = store.update_claim_state(
            claim_id=claim.claim_id,
            new_state=ClaimState.VERIFIED,
            reason="Confirmed via import analysis",
            evidence_added=["ev-123"],
            validated_by="evidence-validator",
        )

        assert updated is True

        # Reload and check
        reloaded = store.get_claim(claim.claim_id)
        assert reloaded.state == ClaimState.VERIFIED
        assert len(reloaded.transitions) == 2

    def test_get_verified_claims(self, temp_workspace, case):
        """Test getting verified claims."""
        case_dir = Path(temp_workspace) / "cases" / case.case_id
        store = ClaimsStore(case_dir)

        store.add_claim(
            case_id=case.case_id,
            statement="Claim 1",
            state=ClaimState.VERIFIED,
            created_by="agent",
        )
        store.add_claim(
            case_id=case.case_id,
            statement="Claim 2",
            state=ClaimState.SUSPECTED,
            created_by="agent",
        )

        verified = store.get_verified_claims()
        assert len(verified) == 1
        assert verified[0].statement == "Claim 1"


class TestResumeEngine:
    """Test resume engine."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def completed_case(self, temp_workspace):
        """Create case with checkpoint."""
        manager = CaseManager(temp_workspace)
        file_path = Path(temp_workspace) / "sample.ipa"
        file_path.write_bytes(b"sample content")
        identity = manager.create_case(
            target_path=str(file_path),
            intent="unpack",
            depth="standard",
        )

        # Create checkpoint
        workflow_state = {
            "workflow_id": "ios.unpack",
            "depth": "standard",
            "nodes": {
                "artifact_detect": {"node_id": "artifact_detect", "status": "done"},
                "ipa_validate": {"node_id": "ipa_validate", "status": "done"},
                "ipa_unpack": {"node_id": "ipa_unpack", "status": "pending"},
            },
            "completed_nodes": ["artifact_detect", "ipa_validate"],
            "failed_nodes": [],
            "blocked_nodes": [],
            "pending_nodes": ["ipa_unpack", "bundle_inventory", "manifest"],
            "current_node": "ipa_unpack",
        }

        manager.checkpoint_case(
            case_id=identity.case_id,
            workflow_state=workflow_state,
            evidence_refs=["ev-1"],
            artifact_refs=["art-1"],
            agent_tasks=[],
            current_node="ipa_unpack",
            current_phase="intake",
        )

        return identity.case_id

    def test_create_resume_plan(self, temp_workspace, completed_case):
        """Test creating resume plan."""
        engine = ResumeEngine(temp_workspace)
        plan = engine.create_resume_plan(completed_case)

        assert plan is not None
        assert plan.case_id == completed_case
        assert plan.workflow_id == "ios.unpack"
        assert "artifact_detect" in plan.valid_completed_nodes
        assert "ipa_unpack" in plan.next_ready_nodes

    def test_get_next_ready_nodes(self, temp_workspace, completed_case):
        """Test getting next ready nodes."""
        engine = ResumeEngine(temp_workspace)
        plan = engine.create_resume_plan(completed_case)

        assert "ipa_unpack" in plan.next_ready_nodes


class TestContextPack:
    """Test context pack generation."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def case_with_checkpoint(self, temp_workspace):
        """Create case with checkpoint."""
        from ios_reverse.workspace.model import Checkpoint, WorkflowState, NodeState

        manager = CaseManager(temp_workspace)
        file_path = Path(temp_workspace) / "sample.ipa"
        file_path.write_bytes(b"sample content")
        identity = manager.create_case(
            target_path=str(file_path),
            intent="unpack",
            depth="standard",
        )

        # Create checkpoint
        workflow_state = {
            "workflow_id": "ios.unpack",
            "depth": "standard",
            "nodes": {
                "artifact_detect": {"node_id": "artifact_detect", "status": "done"},
            },
            "completed_nodes": ["artifact_detect"],
            "failed_nodes": [],
            "blocked_nodes": [],
            "pending_nodes": ["ipa_validate"],
            "current_node": "ipa_validate",
        }

        manager.checkpoint_case(
            case_id=identity.case_id,
            workflow_state=workflow_state,
            evidence_refs=[],
            artifact_refs=[],
            agent_tasks=[],
            current_node="ipa_validate",
            current_phase="intake",
        )

        checkpoint_data = manager.get_latest_checkpoint(identity.case_id)
        checkpoint = Checkpoint.from_dict(checkpoint_data)

        return identity.case_id, checkpoint

    def test_generate_context_pack(self, temp_workspace, case_with_checkpoint):
        """Test generating context pack."""
        case_id, checkpoint = case_with_checkpoint
        engine = ContextPackEngine(temp_workspace)

        content = engine.generate_context_pack(case_id, checkpoint)

        assert "# Agent Context Pack" in content
        assert case_id in content
        assert "ios.unpack" in content
        assert "## Case Objective" in content
        assert "## Next Action" in content

    def test_save_context_pack(self, temp_workspace, case_with_checkpoint):
        """Test saving context pack."""
        case_id, checkpoint = case_with_checkpoint
        engine = ContextPackEngine(temp_workspace)

        path = engine.save_context_pack(case_id, checkpoint)

        assert Path(path).exists()

        # Load and verify
        loaded = engine.load_context_pack(case_id)
        assert loaded is not None
        assert "# Agent Context Pack" in loaded


class TestLivingDocs:
    """Test living document management."""

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
        return identity.case_id

    def test_create_function_doc(self, temp_workspace, case):
        """Test creating function document."""
        manager = LivingDocManager(temp_workspace)

        path = manager.create_function_doc(
            case_id=case,
            function_id="func-001",
            function_name="login",
            component="AuthService",
            address="0x1000",
        )

        assert Path(path).exists()
        content = Path(path).read_text()
        assert "Function: login" in content
        assert "AuthService" in content

    def test_create_endpoint_doc(self, temp_workspace, case):
        """Test creating endpoint document."""
        manager = LivingDocManager(temp_workspace)

        path = manager.create_endpoint_doc(
            case_id=case,
            endpoint_id="ep-001",
            method="POST",
            path="/api/login",
        )

        assert Path(path).exists()
        content = Path(path).read_text()
        assert "POST /api/login" in content

    def test_create_callflow_doc(self, temp_workspace, case):
        """Test creating callflow document."""
        manager = LivingDocManager(temp_workspace)

        path = manager.create_callflow_doc(
            case_id=case,
            callflow_id="cf-001",
            callflow_name="login-flow",
        )

        assert Path(path).exists()
        content = Path(path).read_text()
        assert "Callflow: login-flow" in content


class TestCaseOperations:
    """Test case operations."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_create_operation(self, temp_workspace):
        """Test create operation."""
        ops = CaseOperations(temp_workspace)
        file_path = Path(temp_workspace) / "sample.ipa"
        file_path.write_bytes(b"sample")

        identity = ops.create(
            target_path=str(file_path),
            intent="unpack",
            depth="standard",
            display_name="Test Case"
        )

        assert identity.display_name == "Test Case"

    def test_list_operation(self, temp_workspace):
        """Test list operation."""
        ops = CaseOperations(temp_workspace)
        file_path = Path(temp_workspace) / "sample.ipa"
        file_path.write_bytes(b"sample")

        identity = ops.create(
            target_path=str(file_path),
            intent="unpack",
            depth="standard",
        )

        cases = ops.list()
        assert identity.case_id in cases

    def test_resume_operation(self, temp_workspace):
        """Test resume operation."""
        ops = CaseOperations(temp_workspace)
        file_path = Path(temp_workspace) / "sample.ipa"
        file_path.write_bytes(b"sample")

        identity = ops.create(
            target_path=str(file_path),
            intent="unpack",
            depth="standard",
        )

        # Create a checkpoint first
        workflow_state = {
            "workflow_id": "ios.unpack",
            "depth": "standard",
            "nodes": {},
            "completed_nodes": ["artifact_detect"],
            "failed_nodes": [],
            "blocked_nodes": [],
            "pending_nodes": [],
        }
        ops.checkpoint(
            case_id=identity.case_id,
            workflow_state=workflow_state,
            evidence_refs=[],
            artifact_refs=[],
            agent_tasks=[],
        )

        result = ops.resume(identity.case_id)
        assert result is not None
        assert result["case"].case_id == identity.case_id
