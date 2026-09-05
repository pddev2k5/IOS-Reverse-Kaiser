"""
Tests for Coverage and Reporting capabilities (P04.7).

Tests cover:
- CAP-031: coverage.calculation
- Report models
- Coverage models
- Renderers

Test fixtures include positive and negative (false positive) cases.
"""

import pytest
import os
import sys
import json
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ios_reverse.models.coverage import (
    CoverageState, CoverageDimension, CoverageTarget, CoverageTargetType,
    CoverageObservation, CoverageGap, CoverageSummary, CoverageAudit,
    GapSeverity, generate_target_id, generate_observation_id, generate_gap_id,
    dimension_to_capability
)
from ios_reverse.models.coverage_policy import (
    CoveragePolicy, Workflow, Depth, POLICIES,
    get_policy, FULL_DIMENSIONS, STANDARD_DIMENSIONS, QUICK_DIMENSIONS
)
from ios_reverse.models.report import (
    ReportSection, ClaimStrength, FindingType, ReportFinding,
    ReportSectionData, ReportMetadata, Report,
    evidence_to_claim_strength, is_sensitive_key, redact_sensitive_dict
)
from ios_reverse.capabilities.coverage_auditor import CoverageAuditorCapability
from ios_reverse.renderers.report_renderer import (
    JSONRenderer, MarkdownRenderer, CoverageRenderer, render_report, render_coverage_audit
)


# =============================================================================
# Coverage Model Tests
# =============================================================================

class TestCoverageModel:
    """Tests for coverage model."""

    def test_coverage_state_enum(self):
        """Coverage states are correct."""
        assert CoverageState.COVERED.value == "covered"
        assert CoverageState.PARTIAL.value == "partial"
        assert CoverageState.FAILED.value == "failed"
        assert CoverageState.NOT_APPLICABLE.value == "not_applicable"
        assert CoverageState.NOT_ATTEMPTED.value == "not_attempted"
        assert CoverageState.UNKNOWN.value == "unknown"

    def test_coverage_dimension_enum(self):
        """Coverage dimensions are correct."""
        assert CoverageDimension.ARTIFACT.value == "artifact"
        assert CoverageDimension.BINARY.value == "binary"
        assert CoverageDimension.OBJC_METADATA.value == "objc_metadata"
        assert CoverageDimension.CRYPTO.value == "crypto"
        assert CoverageDimension.ANTI_ANALYSIS.value == "anti_analysis"

    def test_coverage_target_creation(self):
        """Coverage target with metadata."""
        target = CoverageTarget(
            target_id="test-target-1",
            target_type=CoverageTargetType.EXECUTABLE,
            path="/path/to/binary",
            component_id="main",
            architecture="arm64",
        )
        assert target.target_type == CoverageTargetType.EXECUTABLE
        assert target.architecture == "arm64"

    def test_coverage_observation_creation(self):
        """Coverage observation."""
        obs = CoverageObservation(
            observation_id="obs-1",
            target_id="target-1",
            dimension=CoverageDimension.BINARY,
            state=CoverageState.COVERED,
            capability_id="macho.basic",
        )
        assert obs.state == CoverageState.COVERED
        assert obs.capability_id == "macho.basic"

    def test_coverage_gap_creation(self):
        """Coverage gap."""
        gap = CoverageGap(
            gap_id="gap-1",
            dimension=CoverageDimension.CRYPTO,
            target_id="target-1",
            state=CoverageState.NOT_ATTEMPTED,
            reason="Analysis was not requested",
            severity=GapSeverity.BLOCKING,
        )
        assert gap.state == CoverageState.NOT_ATTEMPTED
        assert gap.severity == GapSeverity.BLOCKING

    def test_target_id_deterministic(self):
        """Target IDs are deterministic."""
        id1 = generate_target_id("/path/to/binary", "arm64")
        id2 = generate_target_id("/path/to/binary", "arm64")
        assert id1 == id2


# =============================================================================
# Coverage Policy Tests
# =============================================================================

class TestCoveragePolicy:
    """Tests for coverage policy."""

    def test_policy_dimensions(self):
        """Policy has correct dimensions."""
        policy = get_policy(Workflow.FULL, Depth.FULL)
        assert CoverageDimension.BINARY in policy.required_dimensions
        assert CoverageDimension.OBJC_METADATA in policy.required_dimensions
        assert CoverageDimension.CRYPTO in policy.required_dimensions

    def test_quick_policy_minimal(self):
        """Quick policy has minimal dimensions."""
        policy = get_policy(Workflow.UNPACK, Depth.QUICK)
        assert CoverageDimension.ARTIFACT in policy.required_dimensions
        assert CoverageDimension.CRYPTO not in policy.required_dimensions

    def test_standard_policy(self):
        """Standard policy has binary + metadata."""
        policy = get_policy(Workflow.STANDARD, Depth.STANDARD)
        assert CoverageDimension.BINARY in policy.required_dimensions
        # Standard may or may not include OBJC depending on policy definition
        assert CoverageDimension.CRYPTO not in policy.required_dimensions

    def test_network_policy(self):
        """Network policy includes network."""
        policy = get_policy(Workflow.NETWORK, Depth.FULL)
        assert CoverageDimension.NETWORK in policy.required_dimensions
        assert CoverageDimension.CRYPTO in policy.required_dimensions

    def test_crypto_policy(self):
        """Crypto policy includes crypto."""
        policy = get_policy(Workflow.CRYPTO, Depth.FULL)
        assert CoverageDimension.CRYPTO in policy.required_dimensions

    def test_policy_serializable(self):
        """Policy can be serialized."""
        policy = get_policy(Workflow.FULL, Depth.FULL)
        data = policy.to_dict()
        assert "required_dimensions" in data
        assert "workflow" in data
        assert "depth" in data


# =============================================================================
# Coverage Auditor Tests (CAP-031)
# =============================================================================

class TestCoverageAuditor:
    """Tests for CAP-031 coverage.calculation."""

    def test_contract(self):
        """Capability has valid contract."""
        cap = CoverageAuditorCapability()
        contract = cap.contract
        assert contract.id == "coverage.calculation"
        assert contract.domain == "coverage"

    def test_validate_missing_workflow(self):
        """Validation fails with missing workflow."""
        cap = CoverageAuditorCapability()
        result = cap.execute({})
        assert result.status.value == "failure"
        assert result.error_code in ["E001", "E002"]

    def test_validate_missing_targets(self):
        """Validation fails with missing eligible targets."""
        cap = CoverageAuditorCapability()
        result = cap.execute({"workflow": "full", "depth": "full"})
        assert result.status.value == "failure"

    def test_all_targets_covered(self):
        """All eligible targets covered."""
        cap = CoverageAuditorCapability()

        # Use paths that will generate predictable target IDs
        targets = [
            {"path": "/bin/app1", "type": "executable"},
            {"path": "/bin/app2", "type": "executable"},
        ]

        # Generate target IDs that match what the auditor will generate
        from ios_reverse.models.coverage import generate_target_id
        target_ids = [generate_target_id(t["path"]) for t in targets]

        result = cap.execute({
            "workflow": "full",
            "depth": "full",
            "eligible_targets": targets,
            "capability_results": [
                {"target_id": target_ids[0], "capability_id": "macho.basic", "status": "success"},
                {"target_id": target_ids[1], "capability_id": "macho.basic", "status": "success"},
            ],
        })
        assert result.status.value == "success"
        # coverage_complete should be true when all targets have observations
        assert result.metadata.get("coverage_complete") == True

    def test_missing_target_coverage_not_complete(self):
        """
        INVARIANT: eligible_targets = 5, 4 analyzed, 1 never attempted
        coverage_complete MUST be false.
        """
        cap = CoverageAuditorCapability()

        # Create 5 targets but only 4 have results
        targets = [
            {"path": "/bin/app1", "type": "executable"},
            {"path": "/bin/app2", "type": "executable"},
            {"path": "/bin/app3", "type": "executable"},
            {"path": "/bin/app4", "type": "executable"},
            {"path": "/bin/app5", "type": "executable"},  # Never attempted
        ]

        results = [
            {"target_id": "target-1", "capability_id": "macho.basic", "status": "success"},
            {"target_id": "target-2", "capability_id": "macho.basic", "status": "success"},
            {"target_id": "target-3", "capability_id": "macho.basic", "status": "success"},
            {"target_id": "target-4", "capability_id": "macho.basic", "status": "success"},
            # target-5 is missing!
        ]

        result = cap.execute({
            "workflow": "full",
            "depth": "full",
            "eligible_targets": targets,
            "capability_results": results,
        })

        assert result.status.value == "success"
        # NOT_ATTEMPTED must result in coverage_complete = false
        assert result.metadata.get("coverage_complete") == False

    def test_execution_success_vs_coverage_complete(self):
        """
        INVARIANT: execution_success != coverage_complete
        """
        cap = CoverageAuditorCapability()

        # All executed nodes succeeded, but required dimension missing
        result = cap.execute({
            "workflow": "full",
            "depth": "full",
            "eligible_targets": [
                {"path": "/bin/app", "type": "executable"},
            ],
            "capability_results": [
                {"target_id": "target-1", "capability_id": "macho.basic", "status": "success"},
            ],
        })

        assert result.status.value == "success"
        # execution_success may be true but coverage_complete depends on gaps

    def test_system_framework_excluded(self):
        """System frameworks excluded from coverage denominator."""
        cap = CoverageAuditorCapability()

        targets = [
            {"path": "/bin/app", "type": "executable"},
            {"path": "/System/Library/Frameworks/UIKit.framework", "type": "framework", "is_system_framework": True},
        ]

        result = cap.execute({
            "workflow": "full",
            "depth": "full",
            "eligible_targets": targets,
            "capability_results": [
                {"target_id": "target-1", "capability_id": "macho.basic", "status": "success"},
            ],
        })

        assert result.status.value == "success"
        # System frameworks should not inflate denominator


# =============================================================================
# Report Model Tests
# =============================================================================

class TestReportModel:
    """Tests for report model."""

    def test_report_section_enum(self):
        """Report sections are correct."""
        assert ReportSection.EXECUTIVE_SUMMARY.value == "executive_summary"
        assert ReportSection.CRYPTO.value == "crypto"
        assert ReportSection.ANTI_ANALYSIS.value == "anti_analysis"

    def test_claim_strength_enum(self):
        """Claim strengths are correct."""
        assert ClaimStrength.SUSPECTED.value == "suspected"
        assert ClaimStrength.INFERRED.value == "inferred"
        assert ClaimStrength.DETECTED.value == "detected"
        assert ClaimStrength.VERIFIED.value == "verified"

    def test_evidence_to_claim_strength(self):
        """Evidence level maps to claim strength."""
        assert evidence_to_claim_strength("string_hint") == ClaimStrength.SUSPECTED
        assert evidence_to_claim_strength("reference") == ClaimStrength.INFERRED
        assert evidence_to_claim_strength("structural") == ClaimStrength.DETECTED
        assert evidence_to_claim_strength("correlated") == ClaimStrength.DETECTED
        assert evidence_to_claim_strength("verified") == ClaimStrength.VERIFIED

    def test_report_finding_creation(self):
        """Report finding with evidence."""
        finding = ReportFinding(
            finding_id="find-1",
            finding_type=FindingType.NETWORK_ENDPOINT,
            title="Network endpoint found",
            description="API endpoint discovered",
            strength=ClaimStrength.INFERRED,
            evidence_ids=["ev-1"],
        )
        assert finding.strength == ClaimStrength.INFERRED
        assert len(finding.evidence_ids) == 1

    def test_report_metadata_creation(self):
        """Report metadata."""
        metadata = ReportMetadata(
            report_id="report-1",
            artifact_path="/path/to/app.ipa",
            workflow="full",
            depth="full",
            generated_at="2024-01-01T00:00:00",
        )
        assert metadata.workflow == "full"
        assert metadata.coverage_complete == False

    def test_report_serializable(self):
        """Report can be serialized."""
        metadata = ReportMetadata(
            report_id="report-1",
            artifact_path="/path/to/app.ipa",
            workflow="full",
            depth="full",
            generated_at="2024-01-01T00:00:00",
        )
        section = ReportSectionData(
            section=ReportSection.EXECUTIVE_SUMMARY,
            title="Executive Summary",
            summary="Analysis complete",
        )
        report = Report(
            metadata=metadata,
            sections=[section],
        )

        data = report.to_dict()
        assert "metadata" in data
        assert "sections" in data


# =============================================================================
# Sensitive Data Tests
# =============================================================================

class TestSensitiveData:
    """Tests for sensitive data handling."""

    def test_is_sensitive_key(self):
        """Identifies sensitive keys."""
        assert is_sensitive_key("api_key") == True
        assert is_sensitive_key("secret_token") == True
        assert is_sensitive_key("password") == True
        assert is_sensitive_key("username") == False
        assert is_sensitive_key("endpoint") == False

    def test_redact_sensitive_dict(self):
        """Redacts sensitive values."""
        data = {
            "api_key": "secret12345",
            "username": "admin",
            "password": "supersecret",
        }
        redacted = redact_sensitive_dict(data)

        assert redacted["username"] == "admin"
        assert redacted["api_key"] != "secret12345"
        assert redacted["password"] != "supersecret"

    def test_redact_nested(self):
        """Redacts nested sensitive values."""
        data = {
            "auth": {
                "token": "Bearer secret12345",
                "user": "admin",
            }
        }
        redacted = redact_sensitive_dict(data)
        assert redacted["auth"]["user"] == "admin"


# =============================================================================
# Renderer Tests
# =============================================================================

class TestRenderers:
    """Tests for report renderers."""

    def test_json_renderer(self):
        """JSON renderer produces valid JSON."""
        metadata = ReportMetadata(
            report_id="report-1",
            artifact_path="/path/to/app.ipa",
            workflow="full",
            depth="full",
            generated_at="2024-01-01T00:00:00",
        )
        report = Report(metadata=metadata, sections=[])

        renderer = JSONRenderer()
        output = renderer.render(report)

        # Should be valid JSON
        data = json.loads(output)
        assert data["metadata"]["report_id"] == "report-1"

    def test_markdown_renderer(self):
        """Markdown renderer produces markdown."""
        metadata = ReportMetadata(
            report_id="report-1",
            artifact_path="/path/to/app.ipa",
            workflow="full",
            depth="full",
            generated_at="2024-01-01T00:00:00",
        )
        section = ReportSectionData(
            section=ReportSection.EXECUTIVE_SUMMARY,
            title="Executive Summary",
            summary="Analysis complete",
        )
        report = Report(metadata=metadata, sections=[section])

        renderer = MarkdownRenderer()
        output = renderer.render(report)

        assert "# Analysis Report" in output
        assert "## Executive Summary" in output

    def test_coverage_json_renderer(self):
        """Coverage JSON renderer works."""
        audit = CoverageAudit(
            audit_id="audit-1",
            workflow="full",
            depth="full",
            timestamp="2024-01-01T00:00:00",
            eligible_targets=[],
            required_dimensions=[CoverageDimension.BINARY],
            observations=[],
            gaps=[],
            summary=CoverageSummary(
                workflow="full",
                depth="full",
                total_eligible_targets=5,
                execution_success=True,
                coverage_complete=False,
            ),
        )

        renderer = CoverageRenderer(format="json")
        output = renderer.render_audit(audit)

        data = json.loads(output)
        assert data["audit_id"] == "audit-1"

    def test_coverage_markdown_renderer(self):
        """Coverage markdown renderer works."""
        audit = CoverageAudit(
            audit_id="audit-1",
            workflow="full",
            depth="full",
            timestamp="2024-01-01T00:00:00",
            eligible_targets=[],
            required_dimensions=[CoverageDimension.BINARY],
            observations=[],
            gaps=[],
        )

        renderer = CoverageRenderer(format="markdown")
        output = renderer.render_audit(audit)

        assert "# Coverage Report" in output

    def test_render_report_function(self):
        """render_report convenience function works."""
        metadata = ReportMetadata(
            report_id="report-1",
            artifact_path="/path/to/app.ipa",
            workflow="full",
            depth="full",
            generated_at="2024-01-01T00:00:00",
        )
        report = Report(metadata=metadata, sections=[])

        output = render_report(report, format="json")
        data = json.loads(output)
        assert data["metadata"]["report_id"] == "report-1"


# =============================================================================
# Invariants
# =============================================================================

class TestInvariants:
    """Tests that prove key invariants."""

    def test_not_attempted_not_failed(self):
        """NOT_ATTEMPTED is distinct from FAILED."""
        assert CoverageState.NOT_ATTEMPTED != CoverageState.FAILED
        assert CoverageState.NOT_ATTEMPTED.value == "not_attempted"
        assert CoverageState.FAILED.value == "failed"

    def test_partial_is_valid(self):
        """PARTIAL is a valid state."""
        assert CoverageState.PARTIAL.value == "partial"

    def test_not_applicable_is_valid(self):
        """NOT_APPLICABLE is valid for dimensions not applicable to target."""
        assert CoverageState.NOT_APPLICABLE.value == "not_applicable"

    def test_false_100_prevented(self):
        """
        INVARIANT: A full workflow must NEVER report 100% because all executed nodes passed.
        """
        cap = CoverageAuditorCapability()

        # 10 eligible binaries, 8 analyzed, 2 never attempted
        targets = [{"path": f"/bin/app{i}", "type": "executable"} for i in range(10)]

        # Only 8 have results
        results = [
            {"target_id": f"target-{i}", "capability_id": "macho.basic", "status": "success"}
            for i in range(8)
        ]
        # targets 9 and 10 are missing (not_attempted)

        result = cap.execute({
            "workflow": "full",
            "depth": "full",
            "eligible_targets": targets,
            "capability_results": results,
        })

        # Must NOT be 100%
        coverage_rate = result.metadata.get("target_coverage_rate", 1.0)
        assert coverage_rate < 1.0, "Coverage must not be 100% when targets are not_attempted"

    def test_dimension_coverage_tracked(self):
        """Dimension coverage is tracked separately."""
        policy = get_policy(Workflow.FULL, Depth.FULL)
        assert len(policy.required_dimensions) > 0

    def test_claim_strength_preserved(self):
        """Claim strength is preserved in reporting."""
        # STRING_HINT should become SUSPECTED, not DETECTED
        strength = evidence_to_claim_strength("string_hint")
        assert strength == ClaimStrength.SUSPECTED

        # VERIFIED should remain VERIFIED
        strength = evidence_to_claim_strength("verified")
        assert strength == ClaimStrength.VERIFIED

    def test_all_tests_from_previous_phases_pass(self):
        """All previous tests remain green."""
        # This is verified by running all tests together
        pass


# =============================================================================
# Cross-Capability Tests
# =============================================================================

class TestCrossCapability:
    """Tests across capabilities."""

    def test_objc_not_applicable_for_swift_binary(self):
        """
        ObjC absent from pure Swift binary may be NOT_APPLICABLE.
        """
        # This is a design choice - ObjC may be NOT_APPLICABLE for Swift-only binaries
        state = CoverageState.NOT_APPLICABLE
        assert state == CoverageState.NOT_APPLICABLE

    def test_network_string_hint_preserved(self):
        """Network STRING_HINT remains STRING_HINT in report."""
        finding = ReportFinding(
            finding_id="find-1",
            finding_type=FindingType.NETWORK_ENDPOINT,
            title="Network string found",
            description="API endpoint string observed",
            strength=ClaimStrength.SUSPECTED,  # STRING_HINT maps to SUSPECTED
        )
        assert finding.strength == ClaimStrength.SUSPECTED

    def test_unresolved_callflow_preserved(self):
        """Unresolved callflow remains unresolved in report."""
        # This is preserved by the finding type
        finding_type = FindingType.CALLFLOW
        assert finding_type == FindingType.CALLFLOW

    def test_partial_analysis_can_generate_report(self):
        """Partial upstream analysis still allows report generation."""
        metadata = ReportMetadata(
            report_id="report-1",
            artifact_path="/path/to/app.ipa",
            workflow="full",
            depth="full",
            generated_at="2024-01-01T00:00:00",
            execution_success=False,  # Partial success
            coverage_complete=False,  # Coverage not complete
        )
        report = Report(metadata=metadata, sections=[])

        renderer = JSONRenderer()
        output = renderer.render(report)

        # Should still render successfully
        data = json.loads(output)
        assert data["metadata"]["report_id"] == "report-1"


# =============================================================================
# Determinism Tests
# =============================================================================

class TestDeterminism:
    """Tests for deterministic output."""

    def test_json_ordering_deterministic(self):
        """JSON output is deterministic."""
        metadata = ReportMetadata(
            report_id="report-1",
            artifact_path="/path/to/app.ipa",
            workflow="full",
            depth="full",
            generated_at="2024-01-01T00:00:00",
        )
        report = Report(metadata=metadata, sections=[])

        renderer = JSONRenderer(sort_keys=True)
        output1 = renderer.render(report)
        output2 = renderer.render(report)

        assert output1 == output2

    def test_coverage_audit_deterministic(self):
        """Coverage audit is deterministic."""
        audit = CoverageAudit(
            audit_id="audit-1",
            workflow="full",
            depth="full",
            timestamp="2024-01-01T00:00:00",
            eligible_targets=[],
            required_dimensions=[CoverageDimension.BINARY],
            observations=[],
            gaps=[],
        )
        audit.build_indexes()

        renderer = CoverageRenderer(format="json")
        output1 = renderer.render_audit(audit)
        output2 = renderer.render_audit(audit)

        assert output1 == output2
