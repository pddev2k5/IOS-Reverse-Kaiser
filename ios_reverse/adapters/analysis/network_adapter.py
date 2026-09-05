"""
Network Analysis Adapter for IOS REVERSE KAISER.

Provides network framework detection and endpoint discovery.
"""

import re
import hashlib
import plistlib
from typing import Dict, Any, Optional, List, Set, Tuple
from dataclasses import dataclass

from ios_reverse.adapters.base import ToolAdapter, ToolInfo, AdapterResult
from ios_reverse.models.network import (
    EvidenceStrength, HTTPMethod, NetworkFramework, FrameworkPresence,
    EndpointCandidate, PathCandidate, HeaderCandidate, ParameterCandidate,
    RequestBuilder, NetworkFrameworkPresence, NetworkReference,
    NetworkModel, NetworkAddress, generate_candidate_id
)


class NetworkAnalysisAdapter(ToolAdapter):
    """
    Adapter for network framework detection and endpoint discovery.

    Distinguishes:
    - Framework presence (binary includes the framework)
    - Framework usage (confirmed that the app uses the framework)
    """

    # Known network-related strings
    URL_PATTERNS = [
        r'https?://[^\s<>"{}|\\^`\[\]]+',  # URLs
        r'wss?://[^\s<>"{}|\\^`\[\]]+',     # WebSocket URLs
    ]

    # HTTP methods (as separate tokens)
    HTTP_METHODS = {'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS', 'TRACE', 'CONNECT'}

    # Common API path patterns
    API_PATH_PATTERNS = [
        r'/api/v?\d+[^\s]*',
        r'/rest[^\s]*',
        r'/v\d+[^\s]*',
        r'/auth[^\s]*',
        r'/login[^\s]*',
        r'/user[^\s]*',
        r'/data[^\s]*',
        r'/config[^\s]*',
    ]

    # Network framework indicators
    FRAMEWORK_INDICATORS = {
        NetworkFramework.URLSESSION: [
            'NSURLSession', 'urlsession', 'URLSession',
            'NSMutableURLRequest', 'NSHTTPURLResponse',
        ],
        NetworkFramework.CFNETWORK: [
            'CFNetwork', 'CFHTTP', 'CFFTP',
        ],
        NetworkFramework.NETWORK_FRAMEWORK: [
            'NWConnection', 'NWEndpoint', 'NWBrowser',
            'network.framework',
        ],
        NetworkFramework.ALAMOFIRE: [
            'Alamofire', 'AFSession', 'AFHTTPSessionManager',
            'Session.request', 'AFResponseSerializer',
        ],
        NetworkFramework.AFNETWORKING: [
            'AFNetworking', 'AFHTTPSessionManager',
            'AFSecurityPolicy', 'AFNetworkReachability',
        ],
    }

    def __init__(self):
        super().__init__("network_analysis_adapter", "1.0.0")
        self._id_counter = 0

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="network_analysis_adapter",
            path="internal",
            version="1.0.0"
        )

    def validate_environment(self) -> Tuple[bool, Optional[str]]:
        return True, None

    def execute(self, command, cwd=None, env=None, input_data=None):
        return AdapterResult(success=True, stdout="Pure Python adapter")

    def is_available(self) -> bool:
        return True

    def detect_frameworks(
        self,
        strings_data: str,
        objc_metadata: Optional[Dict] = None,
        swift_metadata: Optional[Dict] = None,
        component_id: Optional[str] = None,
        artifact_id: Optional[str] = None
    ) -> List[NetworkFrameworkPresence]:
        """
        Detect network framework presence.

        Args:
            strings_data: Strings from binary
            objc_metadata: ObjC metadata (optional)
            swift_metadata: Swift metadata (optional)
            component_id: Component ID (optional)
            artifact_id: Artifact ID (optional)

        Returns:
            List of NetworkFrameworkPresence
        """
        presences = []

        for framework, indicators in self.FRAMEWORK_INDICATORS.items():
            evidence_sources = []

            # Check strings
            for indicator in indicators:
                if indicator in strings_data:
                    evidence_sources.append(f"strings:{indicator}")

            # Check ObjC metadata
            if objc_metadata:
                classes = objc_metadata.get('classes', [])
                for cls in classes:
                    cls_name = cls.get('name', '')
                    for indicator in indicators:
                        if indicator in cls_name:
                            evidence_sources.append(f"objc:{cls_name}")

            # Check Swift metadata
            if swift_metadata:
                types = swift_metadata.get('types', [])
                for typ in types:
                    type_name = typ.get('name', '')
                    for indicator in indicators:
                        if indicator in type_name:
                            evidence_sources.append(f"swift:{type_name}")

            if evidence_sources:
                # Determine presence level
                if len(evidence_sources) >= 3:
                    presence = FrameworkPresence.USAGE_SUSPECTED
                else:
                    presence = FrameworkPresence.EMBEDDED

                presences.append(NetworkFrameworkPresence(
                    framework=framework,
                    presence=presence,
                    component_id=component_id,
                    artifact_id=artifact_id,
                    evidence_sources=evidence_sources,
                    evidence_strength=self._infer_evidence_strength(evidence_sources)
                ))

        return presences

    def discover_endpoints(
        self,
        strings_data: str,
        objc_metadata: Optional[Dict] = None,
        swift_metadata: Optional[Dict] = None,
        component_ids: Optional[List[str]] = None,
        artifact_ids: Optional[List[str]] = None
    ) -> Tuple[List[EndpointCandidate], List[PathCandidate]]:
        """
        Discover endpoint candidates from evidence.

        Returns:
            Tuple of (endpoint_candidates, path_candidates)
        """
        endpoints = []
        paths = []

        # Deduplication map: URL string -> candidate
        seen_urls = {}

        # Extract URLs from strings
        for pattern in self.URL_PATTERNS:
            for match in re.finditer(pattern, strings_data):
                url = match.group(0)
                offset = match.start()

                # Skip very short URLs
                if len(url) < 10:
                    continue

                # Generate candidate ID
                candidate_id = generate_candidate_id(url)

                # Check for duplicates
                if candidate_id in seen_urls:
                    # Add additional evidence to existing candidate
                    existing = seen_urls[candidate_id]
                    if component_ids:
                        existing.component_ids.extend(component_ids)
                    if artifact_ids:
                        existing.artifact_ids.extend(artifact_ids)
                    existing.addresses.append(NetworkAddress(
                        component_id=component_ids[0] if component_ids else None,
                        artifact_id=artifact_ids[0] if artifact_ids else None,
                        offset=offset,
                        string_value=url,
                        evidence_ids=[candidate_id]
                    ))
                    continue

                # Parse URL components
                parsed = self._parse_url(url)

                # Determine evidence strength
                strength = EvidenceStrength.STRING_HINT

                # Check for additional evidence
                evidence_sources = [f"strings:{url[:50]}..."]

                # Look for HTTP method evidence near this URL
                method = self._find_method_near(strings_data, offset)

                endpoint = EndpointCandidate(
                    candidate_id=candidate_id,
                    scheme=parsed.get('scheme'),
                    host=parsed.get('host'),
                    port=parsed.get('port'),
                    base_path=parsed.get('base_path'),
                    path=parsed.get('path'),
                    full_url=url,
                    method=method,
                    evidence_strength=strength,
                    evidence_sources=evidence_sources,
                    component_ids=component_ids or [],
                    artifact_ids=artifact_ids or [],
                    addresses=[NetworkAddress(
                        component_id=component_ids[0] if component_ids else None,
                        artifact_id=artifact_ids[0] if artifact_ids else None,
                        offset=offset,
                        string_value=url
                    )]
                )

                endpoints.append(endpoint)
                seen_urls[candidate_id] = endpoint

        # Discover path candidates (without full URL)
        for pattern in self.API_PATH_PATTERNS:
            for match in re.finditer(pattern, strings_data):
                path = match.group(0)
                offset = match.start()

                # Skip if this path is part of a URL we already found
                if any(path in ep.full_url for ep in endpoints if ep.full_url):
                    continue

                candidate_id = generate_candidate_id(path)

                # Check for method evidence
                method = self._find_method_near(strings_data, offset)

                paths.append(PathCandidate(
                    candidate_id=candidate_id,
                    path=path,
                    method=method,
                    evidence_strength=EvidenceStrength.STRING_HINT,
                    evidence_sources=[f"strings:{path}"],
                    component_ids=component_ids or []
                ))

        return endpoints, paths

    def discover_headers(
        self,
        strings_data: str,
        component_id: Optional[str] = None,
        artifact_id: Optional[str] = None
    ) -> List[HeaderCandidate]:
        """
        Discover HTTP header candidates.

        Note: Headers are candidates only. Producers remain unresolved without evidence.
        """
        headers = []
        seen = set()

        # Common HTTP headers
        common_headers = [
            'Authorization', 'Content-Type', 'Accept', 'Accept-Language',
            'Accept-Encoding', 'User-Agent', 'X-Requested-With',
            'X-API-Key', 'X-Auth-Token', 'X-CSRF-Token',
            'Cookie', 'Set-Cookie', 'Cache-Control',
            'Content-Length', 'Host', 'Origin', 'Referer',
        ]

        for header in common_headers:
            if header in strings_data:
                if header in seen:
                    continue
                seen.add(header)

                # Look for value evidence
                values = []
                value_pattern = f'{header}[=:]["\\s]*([^"\\s,]+)'
                for match in re.finditer(value_pattern, strings_data, re.IGNORECASE):
                    values.append(match.group(1))

                headers.append(HeaderCandidate(
                    header_id=generate_candidate_id(f"header:{header}"),
                    name=header,
                    possible_values=values[:5],  # Limit to first 5
                    producer=None,  # Unresolved
                    evidence_strength=EvidenceStrength.STRING_HINT if not values else EvidenceStrength.REFERENCE,
                    evidence_sources=[f"strings:{header}"]
                ))

        return headers

    def discover_request_builders(
        self,
        objc_metadata: Optional[Dict] = None,
        swift_metadata: Optional[Dict] = None,
        component_id: Optional[str] = None
    ) -> List[RequestBuilder]:
        """
        Discover request builder candidates.
        """
        builders = []
        seen = set()

        # ObjC classes related to networking
        if objc_metadata:
            for cls in objc_metadata.get('classes', []):
                cls_name = cls.get('name', '')

                # Look for networking-related class names
                if any(indicator in cls_name.lower() for indicator in ['request', 'session', 'client', 'http', 'api']):
                    if cls_name in seen:
                        continue
                    seen.add(cls_name)

                    # Determine framework
                    framework = NetworkFramework.UNKNOWN
                    for fw, indicators in self.FRAMEWORK_INDICATORS.items():
                        if any(ind in cls_name for ind in indicators):
                            framework = fw
                            break

                    builders.append(RequestBuilder(
                        builder_id=generate_candidate_id(f"builder:{cls_name}"),
                        builder_name=cls_name,
                        component_id=component_id,
                        framework=framework,
                        evidence_strength=EvidenceStrength.REFERENCE,
                        evidence_sources=[f"objc:{cls_name}"]
                    ))

        # Swift types
        if swift_metadata:
            for typ in swift_metadata.get('types', []):
                type_name = typ.get('name', '')

                if any(indicator in type_name.lower() for indicator in ['request', 'session', 'client', 'http', 'api', 'endpoint']):
                    if type_name in seen:
                        continue
                    seen.add(type_name)

                    builders.append(RequestBuilder(
                        builder_id=generate_candidate_id(f"builder:{type_name}"),
                        builder_name=type_name,
                        component_id=component_id,
                        framework=NetworkFramework.SWIFT_REQUEST,
                        evidence_strength=EvidenceStrength.REFERENCE,
                        evidence_sources=[f"swift:{type_name}"]
                    ))

        return builders

    def _parse_url(self, url: str) -> Dict[str, Any]:
        """Parse URL into components."""
        result = {
            'scheme': None,
            'host': None,
            'port': None,
            'base_path': None,
            'path': None,
        }

        # Simple regex-based parsing
        scheme_match = re.match(r'(https?)://', url, re.IGNORECASE)
        if scheme_match:
            result['scheme'] = scheme_match.group(1).lower()
            rest = url[len(scheme_match.group(0)):]

            # Extract host and path
            host_match = re.match(r'([^/:]+)(?::(\d+))?(.*)', rest)
            if host_match:
                result['host'] = host_match.group(1)
                if host_match.group(2):
                    result['port'] = int(host_match.group(2))
                path = host_match.group(3) or '/'

                # Split path into base and full
                parts = path.rsplit('/', 1)
                if len(parts) > 1:
                    result['base_path'] = parts[0] + '/'
                    result['path'] = path
                else:
                    result['base_path'] = path
                    result['path'] = path

        return result

    def _find_method_near(self, data: str, offset: int, window: int = 200) -> HTTPMethod:
        """
        Look for HTTP method evidence near an offset.

        Returns UNKNOWN if no method evidence found.
        """
        start = max(0, offset - window)
        end = min(len(data), offset + window)
        context = data[start:end]

        # Look for method names
        for method in self.HTTP_METHODS:
            # Check if the method appears near this location
            pattern = rf'\b{method}\b'
            if re.search(pattern, context, re.IGNORECASE):
                try:
                    return HTTPMethod[method]
                except KeyError:
                    pass

        return HTTPMethod.UNKNOWN

    def _infer_evidence_strength(self, evidence_sources: List[str]) -> EvidenceStrength:
        """Infer evidence strength from sources."""
        if not evidence_sources:
            return EvidenceStrength.STRING_HINT

        # Structural > Reference > String
        if any(s.startswith('objc:') or s.startswith('swift:') for s in evidence_sources):
            if any(s.startswith('swift:struct') or s.startswith('objc:struct') for s in evidence_sources):
                return EvidenceStrength.STRUCTURAL
            return EvidenceStrength.REFERENCE

        if any(s.startswith('strings:') for s in evidence_sources):
            return EvidenceStrength.STRING_HINT

        return EvidenceStrength.STRING_HINT

    def build_model(
        self,
        strings_data: str,
        objc_metadata: Optional[Dict] = None,
        swift_metadata: Optional[Dict] = None,
        component_ids: Optional[List[str]] = None,
        artifact_ids: Optional[List[str]] = None,
        artifact_path: str = ""
    ) -> NetworkModel:
        """
        Build complete network model from evidence.
        """
        # Detect frameworks
        frameworks = self.detect_frameworks(
            strings_data, objc_metadata, swift_metadata,
            component_ids[0] if component_ids else None,
            artifact_ids[0] if artifact_ids else None
        )

        # Discover endpoints and paths
        endpoints, paths = self.discover_endpoints(
            strings_data, objc_metadata, swift_metadata,
            component_ids, artifact_ids
        )

        # Discover headers
        headers = self.discover_headers(
            strings_data,
            component_ids[0] if component_ids else None,
            artifact_ids[0] if artifact_ids else None
        )

        # Discover request builders
        builders = self.discover_request_builders(
            objc_metadata, swift_metadata,
            component_ids[0] if component_ids else None
        )

        # Build model
        model = NetworkModel(
            artifact_path=artifact_path,
            framework_presences=frameworks,
            endpoint_candidates=endpoints,
            path_candidates=paths,
            header_candidates=headers,
            request_builders=builders,
        )

        # Build indexes
        model.build_indexes()

        # Compute evidence distribution
        model.evidence_strength_distribution = {
            'string_hint': sum(1 for e in endpoints if e.evidence_strength == EvidenceStrength.STRING_HINT),
            'reference': sum(1 for e in endpoints if e.evidence_strength == EvidenceStrength.REFERENCE),
            'structural': sum(1 for e in endpoints if e.evidence_strength == EvidenceStrength.STRUCTURAL),
            'correlated': sum(1 for e in endpoints if e.evidence_strength == EvidenceStrength.CORRELATED),
            'verified': sum(1 for e in endpoints if e.evidence_strength == EvidenceStrength.VERIFIED),
        }

        return model
