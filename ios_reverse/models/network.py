"""
Network Model for IOS REVERSE KAISER.

Provides normalized models for network framework detection, endpoint discovery,
and request-related evidence tracking.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any


class EvidenceStrength(Enum):
    """Evidence strength for network entities."""
    STRING_HINT = "string_hint"      # Found in strings only
    REFERENCE = "reference"          # Referenced by code
    STRUCTURAL = "structural"        # From parsing structures
    CORRELATED = "correlated"        # Correlated with other evidence
    VERIFIED = "verified"           # Confirmed by analysis


class HTTPMethod(Enum):
    """HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    UNKNOWN = "unknown"


class NetworkFramework(Enum):
    """Network framework types."""
    URLSESSION = "URLSession"          # NSURLSession / URLSession
    CFNETWORK = "CFNetwork"           # CFNetwork
    NETWORK_FRAMEWORK = "Network.framework"  # Swift Network.framework
    ALAMOFIRE = "Alamofire"           # Alamofire HTTP library
    AFNETWORKING = "AFNetworking"      # AFNetworking
    AFASKIT = "AFASKit"               # Another AF variant
    SWIFT_REQUEST = "Swift.request"    # Swift request-related types
    CUSTOM = "custom"                 # Custom/network wrapper
    UNKNOWN = "unknown"


class FrameworkPresence(Enum):
    """Framework presence vs usage distinction."""
    EMBEDDED = "embedded"              # Framework binary is present
    USAGE_SUSPECTED = "usage_suspected"  # Framework appears to be used
    USAGE_CONFIRMED = "usage_confirmed"  # Confirmed usage via metadata
    USAGE_UNKNOWN = "usage_unknown"     # Cannot determine


@dataclass
class NetworkAddress:
    """Network address with location information."""
    component_id: str                    # Which component
    artifact_id: str                     # Which binary
    offset: int = 0                     # Offset in binary
    string_value: Optional[str] = None   # Raw string value if from strings
    evidence_ids: List[str] = field(default_factory=list)  # Evidence references

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component_id": self.component_id,
            "artifact_id": self.artifact_id,
            "offset": self.offset,
            "string_value": self.string_value,
            "evidence_ids": self.evidence_ids,
        }


@dataclass
class EndpointCandidate:
    """
    Network endpoint candidate.

    Normalized endpoint with evidence strength.
    NOT promoted to verified endpoint without sufficient evidence.
    """
    candidate_id: str                   # Stable deterministic ID
    scheme: Optional[str] = None        # http, https, etc.
    host: Optional[str] = None           # Hostname
    port: Optional[int] = None          # Port number
    base_path: Optional[str] = None     # Base path (e.g., /api/v1)
    path: Optional[str] = None          # Full or relative path
    full_url: Optional[str] = None      # Full URL if available
    method: HTTPMethod = HTTPMethod.UNKNOWN  # Method with evidence
    evidence_strength: EvidenceStrength = EvidenceStrength.STRING_HINT
    evidence_sources: List[str] = field(default_factory=list)
    component_ids: List[str] = field(default_factory=list)  # Components with evidence
    artifact_ids: List[str] = field(default_factory=list)  # Artifacts with evidence
    addresses: List[NetworkAddress] = field(default_factory=list)  # Location info
    confidence_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "scheme": self.scheme,
            "host": self.host,
            "port": self.port,
            "base_path": self.base_path,
            "path": self.path,
            "full_url": self.full_url,
            "method": self.method.value,
            "evidence_strength": self.evidence_strength.value,
            "evidence_sources": self.evidence_sources,
            "component_ids": self.component_ids,
            "artifact_ids": self.artifact_ids,
            "addresses": [a.to_dict() for a in self.addresses],
            "confidence_notes": self.confidence_notes,
        }


@dataclass
class PathCandidate:
    """Path candidate discovered separately."""
    candidate_id: str
    path: str
    parent_url_candidate_id: Optional[str] = None  # May combine with URL
    method: HTTPMethod = HTTPMethod.UNKNOWN
    evidence_strength: EvidenceStrength = EvidenceStrength.STRING_HINT
    evidence_sources: List[str] = field(default_factory=list)
    component_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "path": self.path,
            "parent_url_candidate_id": self.parent_url_candidate_id,
            "method": self.method.value,
            "evidence_strength": self.evidence_strength.value,
            "evidence_sources": self.evidence_sources,
            "component_ids": self.component_ids,
        }


@dataclass
class HeaderCandidate:
    """HTTP header candidate."""
    header_id: str
    name: str                           # Header name
    possible_values: List[str] = field(default_factory=list)  # Possible values
    producer: Optional[str] = None       # Function/producer (if evidenced)
    producer_component_id: Optional[str] = None
    evidence_strength: EvidenceStrength = EvidenceStrength.STRING_HINT
    evidence_sources: List[str] = field(default_factory=list)
    addresses: List[NetworkAddress] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "header_id": self.header_id,
            "name": self.name,
            "possible_values": self.possible_values,
            "producer": self.producer,
            "producer_component_id": self.producer_component_id,
            "evidence_strength": self.evidence_strength.value,
            "evidence_sources": self.evidence_sources,
            "addresses": [a.to_dict() for a in self.addresses],
        }


@dataclass
class ParameterCandidate:
    """Request parameter candidate."""
    parameter_id: str
    name: str
    location: str = "body"              # body, query, header, path
    possible_values: List[str] = field(default_factory=list)
    producer: Optional[str] = None      # Function producing this param
    producer_component_id: Optional[str] = None
    evidence_strength: EvidenceStrength = EvidenceStrength.STRING_HINT
    evidence_sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "parameter_id": self.parameter_id,
            "name": self.name,
            "location": self.location,
            "possible_values": self.possible_values,
            "producer": self.producer,
            "producer_component_id": self.producer_component_id,
            "evidence_strength": self.evidence_strength.value,
            "evidence_sources": self.evidence_sources,
        }


@dataclass
class RequestBuilder:
    """
    Request builder metadata.

    Represents evidence of request construction without claiming the builder itself.
    """
    builder_id: str
    builder_name: Optional[str] = None      # Class/function name if available
    component_id: Optional[str] = None
    framework: NetworkFramework = NetworkFramework.UNKNOWN
    evidence_strength: EvidenceStrength = EvidenceStrength.STRING_HINT
    evidence_sources: List[str] = field(default_factory=list)
    associated_endpoint_ids: List[str] = field(default_factory=list)  # Potentially uses
    headers: List[str] = field(default_factory=list)  # Associated headers
    parameters: List[str] = field(default_factory=list)  # Associated parameters

    def to_dict(self) -> Dict[str, Any]:
        return {
            "builder_id": self.builder_id,
            "builder_name": self.builder_name,
            "component_id": self.component_id,
            "framework": self.framework.value,
            "evidence_strength": self.evidence_strength.value,
            "evidence_sources": self.evidence_sources,
            "associated_endpoint_ids": self.associated_endpoint_ids,
            "headers": self.headers,
            "parameters": self.parameters,
        }


@dataclass
class NetworkFrameworkPresence:
    """
    Network framework presence record.

    Distinguishes framework presence from framework usage.
    """
    framework: NetworkFramework
    presence: FrameworkPresence
    component_id: Optional[str] = None      # Where detected
    artifact_id: Optional[str] = None       # Which artifact
    version: Optional[str] = None           # Version if available
    evidence_sources: List[str] = field(default_factory=list)
    evidence_strength: EvidenceStrength = EvidenceStrength.STRING_HINT

    def to_dict(self) -> Dict[str, Any]:
        return {
            "framework": self.framework.value,
            "presence": self.presence.value,
            "component_id": self.component_id,
            "artifact_id": self.artifact_id,
            "version": self.version,
            "evidence_sources": self.evidence_sources,
            "evidence_strength": self.evidence_strength.value,
        }


@dataclass
class NetworkReference:
    """
    Reference between network entities.

    Links endpoints to builders, headers, parameters, etc.
    """
    reference_id: str
    reference_type: str                  # e.g., "uses", "sets", "references"
    source_type: str                     # endpoint, builder, header, etc.
    source_id: str
    target_type: str
    target_id: str
    evidence_strength: EvidenceStrength = EvidenceStrength.STRING_HINT
    evidence_sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reference_id": self.reference_id,
            "reference_type": self.reference_type,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "evidence_strength": self.evidence_strength.value,
            "evidence_sources": self.evidence_sources,
        }


@dataclass
class NetworkModel:
    """
    Complete network metadata for an application.
    """
    artifact_path: str
    framework_presences: List[NetworkFrameworkPresence] = field(default_factory=list)
    endpoint_candidates: List[EndpointCandidate] = field(default_factory=list)
    path_candidates: List[PathCandidate] = field(default_factory=list)
    header_candidates: List[HeaderCandidate] = field(default_factory=list)
    parameter_candidates: List[ParameterCandidate] = field(default_factory=list)
    request_builders: List[RequestBuilder] = field(default_factory=list)
    references: List[NetworkReference] = field(default_factory=list)
    evidence_strength_distribution: Dict[str, int] = field(default_factory=dict)

    # Indexes
    _endpoint_by_id: Dict[str, EndpointCandidate] = field(default_factory=dict, repr=False)
    _endpoint_by_host: Dict[str, List[EndpointCandidate]] = field(default_factory=dict, repr=False)

    def build_indexes(self):
        """Build lookup indexes after loading."""
        self._endpoint_by_id = {e.candidate_id: e for e in self.endpoint_candidates}
        self._endpoint_by_host = {}
        for ep in self.endpoint_candidates:
            if ep.host:
                if ep.host not in self._endpoint_by_host:
                    self._endpoint_by_host[ep.host] = []
                self._endpoint_by_host[ep.host].append(ep)

    def get_endpoint(self, candidate_id: str) -> Optional[EndpointCandidate]:
        """Get endpoint by ID."""
        return self._endpoint_by_id.get(candidate_id)

    def get_endpoints_by_host(self, host: str) -> List[EndpointCandidate]:
        """Get endpoints for a host."""
        return self._endpoint_by_host.get(host, [])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_path": self.artifact_path,
            "framework_count": len(self.framework_presences),
            "endpoint_count": len(self.endpoint_candidates),
            "path_count": len(self.path_candidates),
            "header_count": len(self.header_candidates),
            "parameter_count": len(self.parameter_candidates),
            "builder_count": len(self.request_builders),
            "reference_count": len(self.references),
            "evidence_distribution": self.evidence_strength_distribution,
            "frameworks": [f.to_dict() for f in self.framework_presences],
            "endpoints": [e.to_dict() for e in self.endpoint_candidates],
            "paths": [p.to_dict() for p in self.path_candidates],
            "headers": [h.to_dict() for h in self.header_candidates],
            "parameters": [p.to_dict() for p in self.parameter_candidates],
            "builders": [b.to_dict() for b in self.request_builders],
            "references": [r.to_dict() for r in self.references],
        }


def generate_candidate_id(content: str) -> str:
    """Generate deterministic candidate ID from content."""
    import hashlib
    hash_val = hashlib.sha256(content.encode()).hexdigest()[:16]
    return f"net-{hash_val}"
