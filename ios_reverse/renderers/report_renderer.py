"""
Report Renderer for IOS REVERSE KAISER.

Provides renderers for different output formats.
"""

import json
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

from ios_reverse.models.report import (
    Report, ReportSection, ReportFinding, ReportSectionData,
    ReportMetadata, ClaimStrength, FindingType
)
from ios_reverse.models.coverage import CoverageAudit, CoverageGap, CoverageSummary


class ReportRenderer(ABC):
    """Base class for report renderers."""

    @abstractmethod
    def render(self, report: Report) -> str:
        """Render report to string."""
        pass

    def _safe_value(self, value: Any) -> Any:
        """Safely handle values that might not serialize."""
        if hasattr(value, 'to_dict'):
            return value.to_dict()
        if hasattr(value, 'value'):
            return value.value
        return value


class JSONRenderer(ReportRenderer):
    """JSON report renderer."""

    def __init__(self, indent: int = 2, sort_keys: bool = True):
        self.indent = indent
        self.sort_keys = sort_keys

    def render(self, report: Report) -> str:
        """Render report to JSON string."""
        data = self._report_to_dict(report)
        return json.dumps(data, indent=self.indent, sort_keys=self.sort_keys, default=str)

    def _report_to_dict(self, report: Report) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "metadata": self._metadata_to_dict(report.metadata),
            "sections": [self._section_to_dict(s) for s in report.sections],
            "evidence_ids": report.evidence_ids,
            "artifact_ids": report.artifact_ids,
            "errors": report.errors,
            "warnings": report.warnings,
            "unresolved_findings": [self._finding_to_dict(f) for f in report.unresolved_findings],
        }

    def _metadata_to_dict(self, metadata: ReportMetadata) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "report_id": metadata.report_id,
            "artifact_path": metadata.artifact_path,
            "workflow": metadata.workflow,
            "depth": metadata.depth,
            "generated_at": metadata.generated_at,
            "analysis_version": metadata.analysis_version,
            "analysis_duration_seconds": metadata.analysis_duration_seconds,
            "coverage_audit_id": metadata.coverage_audit_id,
            "execution_success": metadata.execution_success,
            "coverage_complete": metadata.coverage_complete,
        }

    def _section_to_dict(self, section: ReportSectionData) -> Dict[str, Any]:
        """Convert section to dictionary."""
        return {
            "section": section.section.value,
            "title": section.title,
            "summary": section.summary,
            "findings": [self._finding_to_dict(f) for f in section.findings],
            "statistics": section.statistics,
            "artifact_references": section.artifact_references,
            "errors": section.errors,
            "warnings": section.warnings,
        }

    def _finding_to_dict(self, finding: ReportFinding) -> Dict[str, Any]:
        """Convert finding to dictionary."""
        return {
            "finding_id": finding.finding_id,
            "finding_type": finding.finding_type.value,
            "title": finding.title,
            "description": finding.description,
            "strength": finding.strength.value,
            "evidence_ids": finding.evidence_ids,
            "artifact_ids": finding.artifact_ids,
            "component_id": finding.component_id,
            "category": finding.category,
            "tags": finding.tags,
        }


class MarkdownRenderer(ReportRenderer):
    """Markdown report renderer."""

    def __init__(self, include_toc: bool = True):
        self.include_toc = include_toc

    def render(self, report: Report) -> str:
        """Render report to Markdown string."""
        lines = []

        # Title
        lines.append(f"# Analysis Report: {report.metadata.artifact_path}")
        lines.append("")

        # Metadata
        lines.append("## Metadata")
        lines.append("")
        lines.append(f"- **Report ID**: {report.metadata.report_id}")
        lines.append(f"- **Workflow**: {report.metadata.workflow}")
        lines.append(f"- **Depth**: {report.metadata.depth}")
        lines.append(f"- **Generated**: {report.metadata.generated_at}")
        lines.append(f"- **Execution Success**: {'Yes' if report.metadata.execution_success else 'No'}")
        lines.append(f"- **Coverage Complete**: {'Yes' if report.metadata.coverage_complete else 'No'}")
        lines.append("")

        # Table of contents
        if self.include_toc and report.sections:
            lines.append("## Table of Contents")
            lines.append("")
            for section in report.sections:
                anchor = section.section.value.replace("_", "-")
                lines.append(f"- [{section.title}](#{anchor})")
            lines.append("")

        # Sections
        for section in report.sections:
            if not section.findings and not section.summary:
                continue  # Skip empty sections

            lines.append(f"## {section.title}")
            lines.append("")

            if section.summary:
                lines.append(section.summary)
                lines.append("")

            if section.statistics:
                lines.append("### Statistics")
                lines.append("")
                for key, value in section.statistics.items():
                    lines.append(f"- **{self._format_key(key)}**: {value}")
                lines.append("")

            if section.findings:
                lines.append(f"### Findings ({len(section.findings)})")
                lines.append("")
                for finding in section.findings[:20]:  # Limit to 20 in main report
                    lines.append(self._render_finding(finding))
                if len(section.findings) > 20:
                    lines.append(f"*... and {len(section.findings) - 20} more findings*")
                lines.append("")

            if section.errors:
                lines.append("### Errors")
                lines.append("")
                for error in section.errors:
                    lines.append(f"- {error}")
                lines.append("")

            if section.warnings:
                lines.append("### Warnings")
                lines.append("")
                for warning in section.warnings:
                    lines.append(f"- {warning}")
                lines.append("")

        # Unresolved findings
        if report.unresolved_findings:
            lines.append("## Unresolved Findings")
            lines.append("")
            for finding in report.unresolved_findings[:10]:
                lines.append(self._render_finding(finding))
            if len(report.unresolved_findings) > 10:
                lines.append(f"*... and {len(report.unresolved_findings) - 10} more*")
            lines.append("")

        # Errors and warnings
        if report.errors:
            lines.append("## Errors")
            lines.append("")
            for error in report.errors:
                lines.append(f"- {error}")
            lines.append("")

        if report.warnings:
            lines.append("## Warnings")
            lines.append("")
            for warning in report.warnings:
                lines.append(f"- {warning}")
            lines.append("")

        return "\n".join(lines)

    def _render_finding(self, finding: ReportFinding) -> str:
        """Render a single finding."""
        lines = []
        lines.append(f"### {finding.title}")
        lines.append("")
        lines.append(f"**Type**: {finding.finding_type.value.replace('_', ' ').title()}")
        lines.append(f"**Strength**: {self._strength_to_text(finding.strength)}")
        if finding.component_id:
            lines.append(f"**Component**: {finding.component_id}")
        lines.append("")
        lines.append(finding.description)
        lines.append("")
        if finding.evidence_ids:
            lines.append(f"*Evidence IDs: {', '.join(finding.evidence_ids[:5])}*")
        return "\n".join(lines)

    def _strength_to_text(self, strength: ClaimStrength) -> str:
        """Convert strength to human-readable text."""
        mapping = {
            ClaimStrength.SUSPECTED: "Suspected (low confidence)",
            ClaimStrength.INFERRED: "Inferred (medium confidence)",
            ClaimStrength.DETECTED: "Detected (higher confidence)",
            ClaimStrength.VERIFIED: "Verified (high confidence)",
            ClaimStrength.UNKNOWN: "Unknown",
        }
        return mapping.get(strength, "Unknown")

    def _format_key(self, key: str) -> str:
        """Format dictionary key for display."""
        return key.replace("_", " ").replace("-", " ").title()


class CoverageRenderer:
    """Renderer for coverage reports."""

    def __init__(self, format: str = "markdown"):
        self.format = format

    def render_audit(self, audit: CoverageAudit) -> str:
        """Render coverage audit."""
        if self.format == "json":
            return self._render_audit_json(audit)
        else:
            return self._render_audit_markdown(audit)

    def _render_audit_json(self, audit: CoverageAudit) -> str:
        """Render coverage audit as JSON."""
        import json
        data = {
            "audit_id": audit.audit_id,
            "workflow": audit.workflow,
            "depth": audit.depth,
            "timestamp": audit.timestamp,
            "summary": self._summary_to_dict(audit.summary) if audit.summary else None,
            "eligible_targets": len(audit.eligible_targets),
            "required_dimensions": [d.value for d in audit.required_dimensions],
            "observation_count": len(audit.observations),
            "gap_count": len(audit.gaps),
            "blocking_gap_count": len(audit.get_blocking_gaps()),
            "gaps": [self._gap_to_dict(g) for g in audit.gaps],
        }
        return json.dumps(data, indent=2, default=str)

    def _render_audit_markdown(self, audit: CoverageAudit) -> str:
        """Render coverage audit as Markdown."""
        lines = []
        lines.append("# Coverage Report")
        lines.append("")
        lines.append(f"**Workflow**: {audit.workflow}")
        lines.append(f"**Depth**: {audit.depth}")
        lines.append(f"**Timestamp**: {audit.timestamp}")
        lines.append("")

        if audit.summary:
            lines.append("## Summary")
            lines.append("")
            summary = audit.summary
            lines.append(f"- **Eligible Targets**: {summary.total_eligible_targets}")
            lines.append(f"- **Non-system Targets**: {summary.eligible_non_system_targets}")
            lines.append(f"- **Required Dimensions**: {summary.total_dimensions}")
            lines.append("")
            lines.append(f"- **Targets Covered**: {summary.targets_covered}")
            lines.append(f"- **Targets Partial**: {summary.targets_partial}")
            lines.append(f"- **Targets Failed**: {summary.targets_failed}")
            lines.append(f"- **Targets Not Attempted**: {summary.targets_not_attempted}")
            lines.append("")
            lines.append(f"- **Execution Success**: {'Yes' if summary.execution_success else 'No'}")
            lines.append(f"- **Coverage Complete**: {'Yes' if summary.coverage_complete else 'No'}")
            lines.append("")
            lines.append(f"- **Target Coverage Rate**: {summary.target_coverage_rate:.1%}")
            lines.append(f"- **Dimension Coverage Rate**: {summary.dimension_coverage_rate:.1%}")
            lines.append(f"- **Successful Coverage Rate**: {summary.successful_coverage_rate:.1%}")
            lines.append("")

        if audit.gaps:
            lines.append("## Coverage Gaps")
            lines.append("")
            blocking = audit.get_blocking_gaps()
            if blocking:
                lines.append(f"### Blocking Gaps ({len(blocking)})")
                lines.append("")
                for gap in blocking:
                    lines.append(f"- **{gap.dimension.value}** on `{gap.target_id}`: {gap.reason}")
                lines.append("")

            non_blocking = [g for g in audit.gaps if not g.is_blocking]
            if non_blocking:
                lines.append(f"### Non-blocking Gaps ({len(non_blocking)})")
                lines.append("")
                for gap in non_blocking[:20]:
                    lines.append(f"- **{gap.dimension.value}** on `{gap.target_id}`: {gap.reason}")
                if len(non_blocking) > 20:
                    lines.append(f"- *... and {len(non_blocking) - 20} more*")
                lines.append("")

        return "\n".join(lines)

    def _summary_to_dict(self, summary: Optional[CoverageSummary]) -> Optional[Dict]:
        if not summary:
            return None
        return {
            "total_eligible_targets": summary.total_eligible_targets,
            "targets_covered": summary.targets_covered,
            "targets_partial": summary.targets_partial,
            "targets_failed": summary.targets_failed,
            "targets_not_attempted": summary.targets_not_attempted,
            "execution_success": summary.execution_success,
            "coverage_complete": summary.coverage_complete,
            "target_coverage_rate": summary.target_coverage_rate,
        }

    def _gap_to_dict(self, gap: CoverageGap) -> Dict:
        return {
            "gap_id": gap.gap_id,
            "dimension": gap.dimension.value,
            "target_id": gap.target_id,
            "state": gap.state.value,
            "reason": gap.reason,
            "severity": gap.severity.value,
            "is_blocking": gap.is_blocking,
        }


def render_report(report: Report, format: str = "json") -> str:
    """Render report to specified format."""
    if format == "json":
        renderer = JSONRenderer()
    elif format == "markdown":
        renderer = MarkdownRenderer()
    else:
        raise ValueError(f"Unknown format: {format}")
    return renderer.render(report)


def render_coverage_audit(audit: CoverageAudit, format: str = "markdown") -> str:
    """Render coverage audit to specified format."""
    renderer = CoverageRenderer(format=format)
    return renderer.render_audit(audit)
