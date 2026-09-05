"""
Report Model for IOS REVERSE KAISER.

Provides normalized models for report generation.

IMPORTANT:
- Report model is separate from renderers
- Claim/evidence strength is preserved
- Sensitive data is handled conservatively
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, Set


class ReportSection(Enum):
    """Available report sections."""
    EXECUTIVE_SUMMARY = "executive_summary"
    ARTIFACT_OVERVIEW = "artifact_overview"
    COMPONENTS = "components"
    BINARY_SUMMARY = "binary_summary"
    OBJC = "objc"
    SWIFT = "swift"
    FRAMEWORKS = "frameworks"
    NETWORK = "network"
    ARCHITECTURE = "architecture"
    CALLFLOWS = "callflows"
    CRYPTO = "crypto"
    ANTI_ANALYSIS = "anti_analysis"
    COVERAGE = "coverage"
    EVIDENCE = "evidence"
    UNRESOLVED = "unresolved"
    FAILURES = "failures"
    PROVENANCE = "provenance"


class ClaimStrength(Enum):
    """Claim epistemic strength for reporting."""
    SUSPECTED = "suspected"         # Low confidence
    INFERRED = "inferred"           # Medium confidence
    DETECTED = "detected"          # Higher confidence
    VERIFIED = "verified"          # High confidence
    UNKNOWN = "unknown"            # Unknown strength


class FindingType(Enum):
    """Types of findings."""
    NETWORK_ENDPOINT = "network_endpoint"
    ARCHITECTURE_COMPONENT = "architecture_component"
    CALLFLOW = "callflow"
    CRYPTO_INDICATOR = "crypto_indicator"
    ANTI_ANALYSIS_INDICATOR = "anti_analysis_indicator"
    METADATA = "metadata"
    STRUCTURE = "structure"
    OTHER = "other"


@dataclass
class ReportFinding:
    """A finding in the report."""
    finding_id: str
    finding_type: FindingType
    title: str
    description: str
    strength: ClaimStrength

    # Evidence links
    evidence_ids: List[str] = field(default_factory=list)
    artifact_ids: List[str] = field(default_factory=list)

    # Component
    component_id: Optional[str] = None

    # Context
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "finding_type": self.finding_type.value,
            "title": self.title,
            "description": self.description,
            "strength": self.strength.value,
            "evidence_count": len(self.evidence_ids),
            "artifact_count": len(self.artifact_ids),
            "component_id": self.component_id,
            "category": self.category,
            "tags": self.tags,
        }


@dataclass
class ReportSectionData:
    """Data for a report section."""
    section: ReportSection
    title: str

    # Content
    summary: str = ""
    findings: List[ReportFinding] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)

    # References to detailed artifacts
    artifact_references: List[str] = field(default_factory=list)

    # Errors/warnings specific to this section
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section": self.section.value,
            "title": self.title,
            "summary": self.summary,
            "finding_count": len(self.findings),
            "statistics": self.statistics,
            "artifact_reference_count": len(self.artifact_references),
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
        }


@dataclass
class ReportMetadata:
    """Metadata for the report."""
    report_id: str
    artifact_path: str
    workflow: str
    depth: str
    generated_at: str

    # Analysis info
    analysis_version: str = "1.0.0"
    analysis_duration_seconds: Optional[float] = None

    # Coverage
    coverage_audit_id: Optional[str] = None

    # Status
    execution_success: bool = False
    coverage_complete: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "artifact_path": self.artifact_path,
            "workflow": self.workflow,
            "depth": self.depth,
            "generated_at": self.generated_at,
            "analysis_version": self.analysis_version,
            "analysis_duration_seconds": self.analysis_duration_seconds,
            "coverage_audit_id": self.coverage_audit_id,
            "execution_success": self.execution_success,
            "coverage_complete": self.coverage_complete,
        }


@dataclass
class Report:
    """
    Complete report.

    Contains all normalized analytical findings and coverage information.
    """
    metadata: ReportMetadata

    # Sections
    sections: List[ReportSectionData] = field(default_factory=list)

    # Global evidence and artifacts
    evidence_ids: List[str] = field(default_factory=list)
    artifact_ids: List[str] = field(default_factory=list)

    # Global errors and warnings
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Unresolved findings
    unresolved_findings: List[ReportFinding] = field(default_factory=list)

    # Indexes
    _section_by_type: Dict[ReportSection, ReportSectionData] = field(default_factory=dict, repr=False)

    def build_indexes(self):
        """Build lookup indexes."""
        self._section_by_type = {s.section: s for s in self.sections}

    def get_section(self, section: ReportSection) -> Optional[ReportSectionData]:
        """Get section by type."""
        return self._section_by_type.get(section)

    def get_all_findings(self) -> List[ReportFinding]:
        """Get all findings from all sections."""
        findings = []
        for section in self.sections:
            findings.extend(section.findings)
        return findings

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": self.metadata.to_dict(),
            "section_count": len(self.sections),
            "evidence_count": len(self.evidence_ids),
            "artifact_count": len(self.artifact_ids),
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "unresolved_finding_count": len(self.unresolved_findings),
            "sections": [s.to_dict() for s in self.sections],
        }


# Evidence strength to claim strength mapping
def evidence_to_claim_strength(evidence_level: str) -> ClaimStrength:
    """Map evidence level to claim strength for reporting."""
    mapping = {
        "string_hint": ClaimStrength.SUSPECTED,
        "reference": ClaimStrength.INFERRED,
        "structural": ClaimStrength.DETECTED,
        "correlated": ClaimStrength.DETECTED,
        "verified": ClaimStrength.VERIFIED,
    }
    return mapping.get(evidence_level, ClaimStrength.UNKNOWN)


# Sensitive value handling
SENSITIVE_PATTERNS = [
    "key", "token", "secret", "password", "credential",
    "api_key", "apikey", "auth_token", "bearer",
]


def is_sensitive_key(key: str) -> bool:
    """Check if a key name suggests sensitive data."""
    key_lower = key.lower()
    return any(pattern in key_lower for pattern in SENSITIVE_PATTERNS)


def redact_sensitive_value(value: str) -> str:
    """Redact a potentially sensitive value."""
    if len(value) <= 4:
        return "****"
    return value[:2] + "*" * (len(value) - 4) + value[-2:]


def redact_sensitive_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Redact sensitive values in a dictionary."""
    result = {}
    for key, value in data.items():
        if is_sensitive_key(key):
            if isinstance(value, str):
                result[key] = redact_sensitive_value(value)
            else:
                result[key] = "[REDACTED]"
        elif isinstance(value, dict):
            result[key] = redact_sensitive_dict(value)
        elif isinstance(value, list):
            result[key] = [redact_sensitive_dict(v) if isinstance(v, dict) else v for v in value]
        else:
            result[key] = value
    return result
