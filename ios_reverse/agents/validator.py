"""
Evidence Validator for IOS REVERSE KAISER.

Validates claims against evidence.
"""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

from .model import ValidationResult, ConflictResolution, ClaimConflict


class EvidenceStrength(str, Enum):
    """Evidence strength levels."""
    STRING_HINT = "string_hint"
    REFERENCE = "reference"
    STRUCTURAL = "structural"
    CORRELATED = "correlated"
    VERIFIED = "verified"


@dataclass
class Claim:
    """A claim to validate."""
    claim_id: str
    claim_type: str  # e.g., "endpoint", "crypto_usage", "class_name"
    claim_value: Any
    evidence_refs: List[str]
    strength: EvidenceStrength
    source: str  # agent role or capability ID
    provenance: List[str] = field(default_factory=list)


@dataclass
class Evidence:
    """Evidence reference."""
    evidence_id: str
    evidence_type: str  # e.g., "string", "import", "metadata"
    content: Any
    source_artifact: str
    strength: EvidenceStrength
    timestamp: str


@dataclass
class ValidationReport:
    """Validation report for a claim."""
    claim_id: str
    result: ValidationResult
    reason: str
    downgrade_reason: str = ""
    required_evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "claim_id": self.claim_id,
            "result": self.result.value,
            "reason": self.reason,
            "downgrade_reason": self.downgrade_reason,
            "required_evidence": self.required_evidence,
        }


class EvidenceValidator:
    """
    Evidence validator.

    Validates claims against available evidence.
    """

    def __init__(self):
        self.evidence: Dict[str, Evidence] = {}
        self.conflicts: List[ClaimConflict] = []

    def add_evidence(self, evidence: Evidence):
        """Add evidence to validator."""
        self.evidence[evidence.evidence_id] = evidence

    def add_evidence_batch(self, evidence_list: List[Evidence]):
        """Add multiple evidence items."""
        for e in evidence_list:
            self.add_evidence(e)

    def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        """Get evidence by ID."""
        return self.evidence.get(evidence_id)

    def validate_claim(self, claim: Claim) -> ValidationReport:
        """
        Validate a claim against evidence.

        Returns ValidationReport with result.
        """
        # Check if all evidence refs exist
        missing_evidence = []
        for ref in claim.evidence_refs:
            if ref not in self.evidence:
                missing_evidence.append(ref)

        if missing_evidence:
            return ValidationReport(
                claim_id=claim.claim_id,
                result=ValidationResult.NEEDS_MORE_EVIDENCE,
                reason=f"Missing evidence: {missing_evidence}",
                required_evidence=missing_evidence
            )

        # Check evidence strength
        min_required_strength = self._get_min_strength_for_claim_type(claim.claim_type)
        evidence_strengths = [self.evidence[ref].strength for ref in claim.evidence_refs if ref in self.evidence]

        if not evidence_strengths:
            return ValidationReport(
                claim_id=claim.claim_id,
                result=ValidationResult.REJECT,
                reason="No valid evidence found"
            )

        # Get minimum evidence strength
        min_strength = min(evidence_strengths, key=lambda s: self._strength_rank(s))

        # Check if claim strength exceeds evidence strength
        if self._strength_rank(claim.strength) > self._strength_rank(min_strength):
            return ValidationReport(
                claim_id=claim.claim_id,
                result=ValidationResult.DOWNGRADE,
                reason=f"Claim strength {claim.strength.value} exceeds evidence strength {min_strength.value}",
                downgrade_reason=f"Evidence only supports {min_strength.value}, not {claim.strength.value}",
                required_evidence=self._get_required_evidence_types(claim.claim_type)
            )

        # All checks passed
        return ValidationReport(
            claim_id=claim.claim_id,
            result=ValidationResult.ACCEPT,
            reason="Evidence supports claim at declared strength"
        )

    def validate_claims_batch(self, claims: List[Claim]) -> List[ValidationReport]:
        """Validate multiple claims."""
        return [self.validate_claim(claim) for claim in claims]

    def check_for_conflicts(
        self,
        claim_a: Claim,
        claim_b: Claim
    ) -> Optional[ClaimConflict]:
        """
        Check if two claims conflict.

        Returns ClaimConflict if they conflict, None otherwise.
        """
        # Check if both claims have been validated
        if claim_a.claim_type != claim_b.claim_type:
            return None  # Different claim types don't conflict

        # Check for direct value conflicts
        if claim_a.claim_value != claim_b.claim_value:
            return ClaimConflict(
                conflict_id=f"conflict-{claim_a.claim_id}-{claim_b.claim_id}",
                claim_a=claim_a.__dict__,
                claim_b=claim_b.__dict__,
                evidence_set_a=claim_a.evidence_refs,
                evidence_set_b=claim_b.evidence_refs,
                agent_source_a=claim_a.source,
                agent_source_b=claim_b.source,
            )

        return None

    def resolve_conflict(self, conflict: ClaimConflict, resolution: ConflictResolution):
        """Record conflict resolution."""
        conflict.resolution = resolution
        conflict.resolved_at = "2024-01-01T00:00:00Z"  # Would use datetime
        self.conflicts.append(conflict)

    def get_conflicts(self) -> List[ClaimConflict]:
        """Get all tracked conflicts."""
        return self.conflicts

    def _strength_rank(self, strength: EvidenceStrength) -> int:
        """Get numeric rank for strength."""
        ranks = {
            EvidenceStrength.STRING_HINT: 1,
            EvidenceStrength.REFERENCE: 2,
            EvidenceStrength.STRUCTURAL: 3,
            EvidenceStrength.CORRELATED: 4,
            EvidenceStrength.VERIFIED: 5,
        }
        return ranks.get(strength, 0)

    def _get_min_strength_for_claim_type(self, claim_type: str) -> EvidenceStrength:
        """Get minimum required evidence strength for claim type."""
        # Endpoint claims need at least REFERENCE
        if "endpoint" in claim_type.lower():
            return EvidenceStrength.REFERENCE

        # Crypto claims need at least REFERENCE
        if "crypto" in claim_type.lower():
            return EvidenceStrength.REFERENCE

        # Class/method claims need at least REFERENCE
        if "class" in claim_type.lower() or "method" in claim_type.lower():
            return EvidenceStrength.REFERENCE

        # Default to STRING_HINT
        return EvidenceStrength.STRING_HINT

    def _get_required_evidence_types(self, claim_type: str) -> List[str]:
        """Get required evidence types for claim type upgrade."""
        if "endpoint" in claim_type.lower():
            return ["import_reference", "call_reference"]
        if "crypto" in claim_type.lower():
            return ["import_reference", "function_symbol"]
        return ["reference"]


def validate_claim(
    claim: Claim,
    evidence: List[Evidence]
) -> ValidationReport:
    """
    Convenience function to validate a single claim.

    Args:
        claim: Claim to validate
        evidence: Available evidence

    Returns:
        ValidationReport
    """
    validator = EvidenceValidator()
    validator.add_evidence_batch(evidence)
    return validator.validate_claim(claim)


def validate_findings(
    findings: Dict[str, Any],
    evidence_refs: List[str],
    agent_source: str
) -> Tuple[List[ValidationReport], List[ClaimConflict]]:
    """
    Validate findings from an agent.

    Args:
        findings: Agent findings
        evidence_refs: Evidence references
        agent_source: Source agent role

    Returns:
        Tuple of (validation_reports, conflicts)
    """
    validator = EvidenceValidator()
    reports = []
    conflicts = []

    # Extract claims from findings
    claims = _extract_claims_from_findings(findings, evidence_refs, agent_source)

    # Add evidence
    # (In real implementation, evidence would be loaded from case)

    # Validate each claim
    for claim in claims:
        report = validator.validate_claim(claim)
        reports.append(report)

    return reports, conflicts


def _extract_claims_from_findings(
    findings: Dict[str, Any],
    evidence_refs: List[str],
    agent_source: str
) -> List[Claim]:
    """Extract claims from findings."""
    claims = []

    # Look for claims in findings
    if "endpoints" in findings:
        for i, endpoint in enumerate(findings["endpoints"]):
            claims.append(Claim(
                claim_id=f"endpoint-{i}",
                claim_type="endpoint",
                claim_value=endpoint.get("url", ""),
                evidence_refs=evidence_refs,
                strength=EvidenceStrength(endpoint.get("strength", "reference")),
                source=agent_source,
            ))

    if "crypto_primitives" in findings:
        for i, primitive in enumerate(findings["crypto_primitives"]):
            claims.append(Claim(
                claim_id=f"crypto-{i}",
                claim_type="crypto_usage",
                claim_value=primitive.get("name", ""),
                evidence_refs=evidence_refs,
                strength=EvidenceStrength(primitive.get("strength", "reference")),
                source=agent_source,
            ))

    if "classes" in findings:
        for i, cls in enumerate(findings["classes"]):
            claims.append(Claim(
                claim_id=f"class-{i}",
                claim_type="class_name",
                claim_value=cls.get("name", ""),
                evidence_refs=evidence_refs,
                strength=EvidenceStrength(cls.get("strength", "reference")),
                source=agent_source,
            ))

    return claims
