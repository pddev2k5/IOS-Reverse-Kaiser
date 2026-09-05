"""
Anti-Analysis Model for IOS REVERSE KAISER.

Provides normalized models for anti-analysis mechanism detection.

IMPORTANT: This identifies evidence of anti-analysis mechanisms, NOT confirmed protections.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any


class EvidenceStrength(Enum):
    """Evidence strength for anti-analysis findings."""
    STRING_HINT = "string_hint"          # Found in strings only
    REFERENCE = "reference"              # Symbol/import reference
    STRUCTURAL = "structural"          # From imports/structure
    CORRELATED = "correlated"           # Correlated with function
    VERIFIED = "verified"               # Confirmed mechanism


class AntiAnalysisCategory(Enum):
    """Categories of anti-analysis mechanisms."""
    DEBUGGER_DETECTION = "debugger_detection"
    JAILBREAK_INDICATOR = "jailbreak_indicator"
    INTEGRITY_CHECK = "integrity_check"
    ENVIRONMENT_CHECK = "environment_check"
    DYNAMIC_INSTRUMENTATION = "dynamic_instrumentation"
    ANTI_HOOKING = "anti_hooking"
    ANTI_TAMPER = "anti_tamper"
    OBFUSCATION = "obfuscation"
    PACKING = "packing"
    CODE_SIGNING = "code_signing"
    ENCRYPTION_STATE = "encryption_state"
    UNKNOWN = "unknown"


class IndicatorState(Enum):
    """State of an anti-analysis indicator."""
    INDICATOR = "indicator"              # Raw indicator found
    REFERENCE = "reference"             # Symbol/API reference
    CORRELATED_CHECK = "correlated_check"  # Correlated with function
    VERIFIED_MECHANISM = "verified_mechanism"  # Confirmed mechanism
    UNKNOWN = "unknown"


@dataclass
class AntiAnalysisIndicator:
    """An indicator of anti-analysis behavior."""
    indicator_id: str
    category: AntiAnalysisCategory
    name: str                           # Short name
    description: str                    # What it indicates
    state: IndicatorState = IndicatorState.INDICATOR

    # Evidence
    evidence_strength: EvidenceStrength = EvidenceStrength.STRING_HINT
    evidence_sources: List[str] = field(default_factory=list)

    # Location
    component_id: Optional[str] = None
    artifact_id: Optional[str] = None

    # Function context
    function_name: Optional[str] = None
    function_address: Optional[int] = None

    # Specific value if from string
    string_value: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "indicator_id": self.indicator_id,
            "category": self.category.value,
            "name": self.name,
            "description": self.description,
            "state": self.state.value,
            "evidence_strength": self.evidence_strength.value,
            "evidence_sources": self.evidence_sources,
            "component_id": self.component_id,
            "artifact_id": self.artifact_id,
            "function_name": self.function_name,
            "function_address": self.function_address,
            "string_value": self.string_value,
        }


@dataclass
class AntiAnalysisReference:
    """Reference to anti-analysis symbol/API."""
    reference_id: str
    symbol: str                         # Symbol/API name
    category: AntiAnalysisCategory
    presence: str = "imported"         # How detected
    evidence_strength: EvidenceStrength = EvidenceStrength.REFERENCE
    evidence_sources: List[str] = field(default_factory=list)
    component_id: Optional[str] = None
    artifact_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reference_id": self.reference_id,
            "symbol": self.symbol,
            "category": self.category.value,
            "presence": self.presence,
            "evidence_strength": self.evidence_strength.value,
            "evidence_sources": self.evidence_sources,
            "component_id": self.component_id,
            "artifact_id": self.artifact_id,
        }


@dataclass
class AntiAnalysisEvidence:
    """Individual piece of anti-analysis evidence."""
    evidence_id: str
    evidence_type: str                  # e.g., "import", "string", "symbol", "reference"
    content: str                       # What the evidence says
    category: AntiAnalysisCategory
    source_artifact_id: Optional[str] = None
    source_address: Optional[int] = None
    raw_value: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "evidence_type": self.evidence_type,
            "content": self.content,
            "category": self.category.value,
            "source_artifact_id": self.source_artifact_id,
            "source_address": self.source_address,
            "raw_value": self.raw_value,
        }


@dataclass
class AntiAnalysisFinding:
    """A finding/correlation from anti-analysis analysis."""
    finding_id: str
    category: AntiAnalysisCategory
    finding_type: str                   # e.g., "debugger_check", "jailbreak_path"
    description: str
    state: IndicatorState

    # Evidence
    evidence_level: EvidenceStrength
    evidence_ids: List[str] = field(default_factory=list)
    indicator_ids: List[str] = field(default_factory=list)
    reference_ids: List[str] = field(default_factory=list)

    # Context
    component_id: Optional[str] = None
    artifact_id: Optional[str] = None
    function_name: Optional[str] = None

    # Provenance
    provenance: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "category": self.category.value,
            "finding_type": self.finding_type,
            "description": self.description,
            "state": self.state.value,
            "evidence_level": self.evidence_level.value,
            "evidence_count": len(self.evidence_ids),
            "indicator_count": len(self.indicator_ids),
            "reference_count": len(self.reference_ids),
            "component_id": self.component_id,
            "artifact_id": self.artifact_id,
            "function_name": self.function_name,
            "provenance": self.provenance,
        }


@dataclass
class AntiAnalysisModel:
    """
    Complete anti-analysis model for an application.
    """
    artifact_path: str

    # Core elements
    indicators: List[AntiAnalysisIndicator] = field(default_factory=list)
    references: List[AntiAnalysisReference] = field(default_factory=list)
    findings: List[AntiAnalysisFinding] = field(default_factory=list)

    # Evidence
    evidence_records: List[AntiAnalysisEvidence] = field(default_factory=list)

    # Statistics
    category_distribution: Dict[str, int] = field(default_factory=dict)
    state_distribution: Dict[str, int] = field(default_factory=dict)
    evidence_level_distribution: Dict[str, int] = field(default_factory=dict)

    # Indexes
    _indicator_by_id: Dict[str, AntiAnalysisIndicator] = field(default_factory=dict, repr=False)
    _finding_by_id: Dict[str, AntiAnalysisFinding] = field(default_factory=dict, repr=False)

    def build_indexes(self):
        """Build lookup indexes after loading."""
        self._indicator_by_id = {i.indicator_id: i for i in self.indicators}
        self._finding_by_id = {f.finding_id: f for f in self.findings}

    def get_indicator(self, indicator_id: str) -> Optional[AntiAnalysisIndicator]:
        """Get indicator by ID."""
        return self._indicator_by_id.get(indicator_id)

    def get_finding(self, finding_id: str) -> Optional[AntiAnalysisFinding]:
        """Get finding by ID."""
        return self._finding_by_id.get(finding_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_path": self.artifact_path,
            "indicator_count": len(self.indicators),
            "reference_count": len(self.references),
            "finding_count": len(self.findings),
            "evidence_count": len(self.evidence_records),
            "category_distribution": self.category_distribution,
            "state_distribution": self.state_distribution,
            "evidence_level_distribution": self.evidence_level_distribution,
        }


def generate_indicator_id(content: str) -> str:
    """Generate deterministic indicator ID."""
    import hashlib
    hash_val = hashlib.sha256(content.encode()).hexdigest()[:16]
    return f"anti-ind-{hash_val}"


def generate_finding_id(category: str, content: str) -> str:
    """Generate deterministic finding ID."""
    import hashlib
    hash_val = hashlib.sha256(f"{category}:{content}".encode()).hexdigest()[:16]
    return f"anti-find-{hash_val}"


# Common anti-analysis patterns
DEBUGGER_API_PATTERNS = [
    'ptrace', 'sysctl', 'getpid', 'getppid', 'kill',
    'PT_DENY_ATTACH', 'sysctlbyname',
]

JAILBREAK_PATH_PATTERNS = [
    '/Applications/Cydia.app', '/Applications/Sileo.app',
    '/Applications/Zebra.app', '/Library/MobileSubstrate',
    '/usr/sbin/sshd', '/usr/bin/ssh',
    '/etc/apt', '/private/var/lib/apt/',
    '/private/var/lib/cydia', '/private/var/stash',
    '/var/cache/apt', '/var/lib/apt',
    '/var/log/syslog', '/bin/bash', '/bin/sh',
    '/usr/libexec/sftp-server', '/usr/libexec/ssh-keysign',
    '/usr/bin/cycript', '/usr/local/bin/cycript',
    '/usr/bin/ssh', '/etc/ssh/sshd_config',
]

INTEGRITY_CHECK_PATTERNS = [
    'SecCodeCheckValidity',
    'kSecCodeSignatureValid',
    'code', 'signature', 'sign',
]

ENVIRONMENT_CHECK_PATTERNS = [
    'simulator', 'x86_64', 'i386',
    'UIWindow', 'springboard',
]

DYNAMIC_INSTRUMENTATION_PATTERNS = [
    'fishhook', 'substrate', 'MobileSubstrate',
    'cynject', 'cycript', 'frida',
    'SSLKillSwitch', 'SSLKillSwitch2',
]

OBFUSCATION_PATTERNS = [
    'obfuscate', 'obfuscator',
    'xor', 'rot13',
]


def classify_string_to_category(value: str) -> Optional[AntiAnalysisCategory]:
    """Classify a string value to anti-analysis category."""
    value_lower = value.lower()

    # Jailbreak paths
    for path in JAILBREAK_PATH_PATTERNS:
        if path.lower() in value_lower:
            return AntiAnalysisCategory.JAILBREAK_INDICATOR

    # Dynamic instrumentation
    for pattern in DYNAMIC_INSTRUMENTATION_PATTERNS:
        if pattern.lower() in value_lower:
            return AntiAnalysisCategory.DYNAMIC_INSTRUMENTATION

    # Environment
    for pattern in ENVIRONMENT_CHECK_PATTERNS:
        if pattern.lower() in value_lower:
            return AntiAnalysisCategory.ENVIRONMENT_CHECK

    return None
