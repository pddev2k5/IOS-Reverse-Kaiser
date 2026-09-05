"""
Crypto Model for IOS REVERSE KAISER.

Provides normalized models for cryptographic operation detection and analysis.

IMPORTANT: This identifies evidence-driven crypto candidates, NOT verified behavior.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any


class EvidenceStrength(Enum):
    """Evidence strength for crypto findings."""
    STRING_HINT = "string_hint"          # Found in strings only
    REFERENCE = "reference"              # Symbol/import reference
    STRUCTURAL = "structural"            # From parsing/imports
    CORRELATED = "correlated"           # Correlated with other evidence
    VERIFIED = "verified"               # Confirmed by analysis


class PrimitiveCategory(Enum):
    """Categories of cryptographic primitives."""
    HASH = "hash"
    MAC = "mac"
    SYMMETRIC_CIPHER = "symmetric_cipher"
    ASYMMETRIC_CIPHER = "asymmetric_cipher"
    KDF = "kdf"
    SIGNATURE = "signature"
    RANDOMNESS = "randomness"
    KEYCHAIN = "keychain"
    TLS_RELATED = "tls_related"
    ENCODING = "encoding"
    UNKNOWN = "unknown"


class Algorithm(Enum):
    """Specific cryptographic algorithms."""
    MD5 = "MD5"
    SHA1 = "SHA1"
    SHA256 = "SHA256"
    SHA384 = "SHA384"
    SHA512 = "SHA512"
    HMAC_SHA1 = "HMAC-SHA1"
    HMAC_SHA256 = "HMAC-SHA256"
    AES = "AES"
    AES_128 = "AES-128"
    AES_256 = "AES-256"
    ChaCha20 = "ChaCha20"
    RSA = "RSA"
    EC = "EC"
    ECDSA = "ECDSA"
    PBKDF2 = "PBKDF2"
    HKDF = "HKDF"
    BLOWFISH = "Blowfish"
    DES = "DES"
    TripleDES = "3DES"
    RC4 = "RC4"
    UNKNOWN = "Unknown"


class CryptoLibrary(Enum):
    """Crypto library/framework sources."""
    COMMON_CRYPTO = "CommonCrypto"
    SECURITY_FRAMEWORK = "Security.framework"
    CRYPTOKIT = "CryptoKit"
    OPENSSL = "OpenSSL"
    LIBTOM = "LibTom"
    CUSTOM = "custom"
    UNKNOWN = "unknown"


class LibraryPresence(Enum):
    """Library presence vs usage distinction."""
    LINKED = "linked"
    USAGE_SUSPECTED = "usage_suspected"
    USAGE_CONFIRMED = "usage_confirmed"
    UNKNOWN = "unknown"


@dataclass
class CryptoReference:
    """Reference to a crypto symbol/API."""
    reference_id: str
    symbol: str                           # Symbol/API name
    library: CryptoLibrary
    presence: LibraryPresence = LibraryPresence.UNKNOWN
    component_id: Optional[str] = None
    artifact_id: Optional[str] = None
    evidence_strength: EvidenceStrength = EvidenceStrength.REFERENCE
    evidence_sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reference_id": self.reference_id,
            "symbol": self.symbol,
            "library": self.library.value,
            "presence": self.presence.value,
            "component_id": self.component_id,
            "artifact_id": self.artifact_id,
            "evidence_strength": self.evidence_strength.value,
            "evidence_sources": self.evidence_sources,
        }


@dataclass
class CryptoOperationCandidate:
    """
    Candidate cryptographic operation.

    Represents evidence of crypto usage, NOT confirmed behavior.
    """
    operation_id: str
    primitive_category: PrimitiveCategory
    algorithm: Algorithm = Algorithm.UNKNOWN

    # Evidence
    evidence_strength: EvidenceStrength = EvidenceStrength.STRING_HINT
    evidence_sources: List[str] = field(default_factory=list)

    # Provenance
    component_id: Optional[str] = None
    artifact_id: Optional[str] = None

    # Function/method context
    function_name: Optional[str] = None
    function_address: Optional[int] = None
    class_name: Optional[str] = None

    # Input/output roles (if known from evidence)
    input_role: Optional[str] = None   # e.g., "data", "key", "iv"
    output_role: Optional[str] = None  # e.g., "ciphertext", "digest"

    # Library
    library: CryptoLibrary = CryptoLibrary.UNKNOWN

    # Correlation
    correlated_references: List[str] = field(default_factory=list)  # Reference IDs

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "primitive_category": self.primitive_category.value,
            "algorithm": self.algorithm.value,
            "evidence_strength": self.evidence_strength.value,
            "evidence_sources": self.evidence_sources,
            "component_id": self.component_id,
            "artifact_id": self.artifact_id,
            "function_name": self.function_name,
            "function_address": self.function_address,
            "class_name": self.class_name,
            "input_role": self.input_role,
            "output_role": self.output_role,
            "library": self.library.value,
            "correlated_reference_count": len(self.correlated_references),
        }


@dataclass
class KeyMaterialCandidate:
    """
    Key material candidate.

    Conservative classification - do NOT claim actual key material.
    """
    candidate_id: str
    classification: str                # e.g., "literal", "configuration", "keychain_ref"
    evidence_strength: EvidenceStrength = EvidenceStrength.STRING_HINT
    evidence_sources: List[str] = field(default_factory=list)

    # Location
    component_id: Optional[str] = None
    artifact_id: Optional[str] = None
    address: Optional[int] = None

    # Context
    context: Optional[str] = None      # What the string appears near
    is_keychain_related: bool = False

    # Do NOT include actual key value - just evidence location

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "classification": self.classification,
            "evidence_strength": self.evidence_strength.value,
            "evidence_sources": self.evidence_sources,
            "component_id": self.component_id,
            "artifact_id": self.artifact_id,
            "address": self.address,
            "context": self.context,
            "is_keychain_related": self.is_keychain_related,
        }


@dataclass
class CryptoEvidence:
    """Individual piece of crypto evidence."""
    evidence_id: str
    evidence_type: str                  # e.g., "import", "symbol", "string", "reference"
    content: str                       # What the evidence says
    source_artifact_id: Optional[str] = None
    source_address: Optional[int] = None
    raw_value: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "evidence_type": self.evidence_type,
            "content": self.content,
            "source_artifact_id": self.source_artifact_id,
            "source_address": self.source_address,
            "raw_value": self.raw_value,
        }


@dataclass
class CryptoFinding:
    """A finding/correlation from crypto analysis."""
    finding_id: str
    finding_type: str                   # e.g., "hashing_operation", "encryption_candidate"
    description: str
    evidence_level: EvidenceStrength

    # Related entities
    operation_ids: List[str] = field(default_factory=list)
    reference_ids: List[str] = field(default_factory=list)

    # Evidence
    evidence_ids: List[str] = field(default_factory=list)
    provenance: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "finding_type": self.finding_type,
            "description": self.description,
            "evidence_level": self.evidence_level.value,
            "operation_count": len(self.operation_ids),
            "reference_count": len(self.reference_ids),
            "evidence_count": len(self.evidence_ids),
            "provenance": self.provenance,
        }


@dataclass
class CryptoModel:
    """
    Complete crypto model for an application.
    """
    artifact_path: str

    # Core elements
    library_presences: List[CryptoReference] = field(default_factory=list)
    operations: List[CryptoOperationCandidate] = field(default_factory=list)
    key_material_candidates: List[KeyMaterialCandidate] = field(default_factory=list)
    findings: List[CryptoFinding] = field(default_factory=list)

    # Evidence
    evidence_records: List[CryptoEvidence] = field(default_factory=list)

    # Statistics
    primitive_distribution: Dict[str, int] = field(default_factory=dict)
    algorithm_distribution: Dict[str, int] = field(default_factory=dict)
    evidence_level_distribution: Dict[str, int] = field(default_factory=dict)

    # Indexes
    _op_by_id: Dict[str, CryptoOperationCandidate] = field(default_factory=dict, repr=False)
    _ref_by_id: Dict[str, CryptoReference] = field(default_factory=dict, repr=False)

    def build_indexes(self):
        """Build lookup indexes after loading."""
        self._op_by_id = {o.operation_id: o for o in self.operations}
        self._ref_by_id = {r.reference_id: r for r in self.library_presences}

    def get_operation(self, operation_id: str) -> Optional[CryptoOperationCandidate]:
        """Get operation by ID."""
        return self._op_by_id.get(operation_id)

    def get_reference(self, reference_id: str) -> Optional[CryptoReference]:
        """Get reference by ID."""
        return self._ref_by_id.get(reference_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_path": self.artifact_path,
            "library_presence_count": len(self.library_presences),
            "operation_count": len(self.operations),
            "key_material_candidate_count": len(self.key_material_candidates),
            "finding_count": len(self.findings),
            "evidence_count": len(self.evidence_records),
            "primitive_distribution": self.primitive_distribution,
            "algorithm_distribution": self.algorithm_distribution,
            "evidence_level_distribution": self.evidence_level_distribution,
        }


def generate_operation_id(content: str) -> str:
    """Generate deterministic operation ID."""
    import hashlib
    hash_val = hashlib.sha256(content.encode()).hexdigest()[:16]
    return f"crypto-op-{hash_val}"


def generate_reference_id(symbol: str) -> str:
    """Generate deterministic reference ID."""
    import hashlib
    hash_val = hashlib.sha256(symbol.encode()).hexdigest()[:16]
    return f"crypto-ref-{hash_val}"


def map_symbol_to_library(symbol: str) -> CryptoLibrary:
    """Map symbol to crypto library."""
    symbol_lower = symbol.lower()

    if 'cccrypt' in symbol_lower or 'ccdigest' in symbol_lower or 'cccommon' in symbol_lower:
        return CryptoLibrary.COMMON_CRYPTO
    if 'security' in symbol_lower or 'seckey' in symbol_lower:
        return CryptoLibrary.SECURITY_FRAMEWORK
    if 'cryptokit' in symbol_lower or 'crypto_kit' in symbol_lower:
        return CryptoLibrary.CRYPTOKIT
    if 'ssl' in symbol_lower or 'tls' in symbol_lower:
        return CryptoLibrary.OPENSSL  # Likely

    return CryptoLibrary.UNKNOWN


def map_symbol_to_primitive(symbol: str) -> PrimitiveCategory:
    """Map symbol to primitive category."""
    symbol_lower = symbol.lower()

    # Hash functions
    if any(x in symbol_lower for x in ['digest', 'hash']):
        if 'md5' in symbol_lower:
            return PrimitiveCategory.HASH
        if 'sha' in symbol_lower:
            return PrimitiveCategory.HASH

    # MAC
    if 'hmac' in symbol_lower:
        return PrimitiveCategory.MAC

    # Symmetric cipher
    if 'crypt' in symbol_lower:
        return PrimitiveCategory.SYMMETRIC_CIPHER

    # Asymmetric
    if 'rsa' in symbol_lower or 'ec' in symbol_lower or 'key' in symbol_lower:
        if 'sign' in symbol_lower or 'encrypt' in symbol_lower:
            return PrimitiveCategory.ASYMMETRIC_CIPHER

    # KDF
    if 'kdf' in symbol_lower or 'pbkdf' in symbol_lower:
        return PrimitiveCategory.KDF

    # Randomness
    if 'random' in symbol_lower or 'arc4' in symbol_lower:
        return PrimitiveCategory.RANDOMNESS

    # Keychain
    if 'keychain' in symbol_lower:
        return PrimitiveCategory.KEYCHAIN

    return PrimitiveCategory.UNKNOWN


def map_symbol_to_algorithm(symbol: str) -> Algorithm:
    """Map symbol to specific algorithm (if determinable)."""
    symbol_lower = symbol.lower()

    if 'md5' in symbol_lower:
        return Algorithm.MD5
    if 'sha1' in symbol_lower:
        return Algorithm.SHA1
    if 'sha256' in symbol_lower:
        return Algorithm.SHA256
    if 'sha384' in symbol_lower:
        return Algorithm.SHA384
    if 'sha512' in symbol_lower:
        return Algorithm.SHA512
    if 'hmac' in symbol_lower:
        if 'sha256' in symbol_lower:
            return Algorithm.HMAC_SHA256
        return Algorithm.HMAC_SHA1
    if 'aes' in symbol_lower:
        if '256' in symbol_lower:
            return Algorithm.AES_256
        if '128' in symbol_lower:
            return Algorithm.AES_128
        return Algorithm.AES
    if 'rsa' in symbol_lower:
        return Algorithm.RSA
    if 'ec' in symbol_lower or 'ecdsa' in symbol_lower:
        return Algorithm.ECDSA
    if 'pbkdf2' in symbol_lower:
        return Algorithm.PBKDF2
    if 'hkdf' in symbol_lower:
        return Algorithm.HKDF
    if 'chacha' in symbol_lower:
        return Algorithm.ChaCha20
    if 'rc4' in symbol_lower:
        return Algorithm.RC4

    return Algorithm.UNKNOWN
