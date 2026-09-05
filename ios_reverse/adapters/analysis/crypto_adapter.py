"""
Crypto Analysis Adapter for IOS REVERSE KAISER.

Provides cryptographic operation detection and analysis.
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

from ios_reverse.adapters.base import ToolAdapter, ToolInfo, AdapterResult
from ios_reverse.models.crypto import (
    EvidenceStrength, PrimitiveCategory, Algorithm, CryptoLibrary, LibraryPresence,
    CryptoReference, CryptoOperationCandidate, KeyMaterialCandidate,
    CryptoEvidence, CryptoFinding, CryptoModel,
    generate_operation_id, generate_reference_id,
    map_symbol_to_library, map_symbol_to_primitive, map_symbol_to_algorithm
)


class CryptoAnalysisAdapter(ToolAdapter):
    """
    Adapter for crypto detection and analysis.

    IMPORTANT:
    - Library presence != confirmed usage
    - String "AES" alone is STRING_HINT
    - Does not invent parameters or key material
    """

    # Crypto-related string patterns
    CRYPTO_STRING_PATTERNS = [
        'aes', 'AES', 'aes128', 'aes256',
        'des', 'DES', '3des', '3DES',
        'rc4', 'RC4', 'chacha', 'ChaCha',
        'md5', 'MD5', 'sha1', 'SHA1', 'sha256', 'SHA256', 'sha384', 'SHA384', 'sha512', 'SHA512',
        'hmac', 'HMAC', 'pbkdf2', 'PBKDF2', 'hkdf', 'HKDF',
        'rsa', 'RSA', 'ecdsa', 'ECDSA', 'ecc', 'ECC',
        'encrypt', 'decrypt', 'cipher', 'ciphertext',
        'crypt', 'key', 'iv', 'nonce', 'salt',
        'random', 'secure', 'crypto', 'Crypto',
    ]

    # Known crypto APIs/symbols
    CRYPTO_API_PATTERNS = {
        'CCCrypt': PrimitiveCategory.SYMMETRIC_CIPHER,
        'CCCryptorCreate': PrimitiveCategory.SYMMETRIC_CIPHER,
        'CCCryptorFinal': PrimitiveCategory.SYMMETRIC_CIPHER,
        'CCDigest': PrimitiveCategory.HASH,
        'CC_SHA': PrimitiveCategory.HASH,
        'CC_MD5': PrimitiveCategory.HASH,
        'CC_HMAC': PrimitiveCategory.MAC,
        'CCKeyDerivationPBKDF': PrimitiveCategory.KDF,
        'SecKeyEncrypt': PrimitiveCategory.ASYMMETRIC_CIPHER,
        'SecKeyDecrypt': PrimitiveCategory.ASYMMETRIC_CIPHER,
        'SecKeyCreateSignature': PrimitiveCategory.SIGNATURE,
        'SecKeyVerifySignature': PrimitiveCategory.SIGNATURE,
        'SecRandomCopyBytes': PrimitiveCategory.RANDOMNESS,
        'SecKeyGenerate': PrimitiveCategory.ASYMMETRIC_CIPHER,
        'kSecAttrKeyTypeRSA': PrimitiveCategory.ASYMMETRIC_CIPHER,
        'kSecAttrKeyTypeECSECPrimeRandom': PrimitiveCategory.ASYMMETRIC_CIPHER,
        'SecItemAdd': PrimitiveCategory.KEYCHAIN,
        'SecItemCopyMatching': PrimitiveCategory.KEYCHAIN,
        'SecItemDelete': PrimitiveCategory.KEYCHAIN,
        'SecItemUpdate': PrimitiveCategory.KEYCHAIN,
        'Keychain': PrimitiveCategory.KEYCHAIN,
        'SecAccessControl': PrimitiveCategory.KEYCHAIN,
        'SecTrust': PrimitiveCategory.TLS_RELATED,
        'SecCertificate': PrimitiveCategory.TLS_RELATED,
        'SecPolicy': PrimitiveCategory.TLS_RELATED,
        'TLS': PrimitiveCategory.TLS_RELATED,
        'SSL': PrimitiveCategory.TLS_RELATED,
    }

    # Library patterns
    LIBRARY_PATTERNS = {
        'CommonCrypto': CryptoLibrary.COMMON_CRYPTO,
        'Security.framework': CryptoLibrary.SECURITY_FRAMEWORK,
        'CryptoKit': CryptoLibrary.CRYPTOKIT,
        'OpenSSL': CryptoLibrary.OPENSSL,
        'Crypto': CryptoLibrary.UNKNOWN,
    }

    def __init__(self):
        super().__init__("crypto_analysis_adapter", "1.0.0")
        self._id_counter = 0

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="crypto_analysis_adapter",
            path="internal",
            version="1.0.0"
        )

    def validate_environment(self) -> Tuple[bool, Optional[str]]:
        return True, None

    def execute(self, command, cwd=None, env=None, input_data=None):
        return AdapterResult(success=True, stdout="Pure Python adapter")

    def is_available(self) -> bool:
        return True

    def detect_library_presences(
        self,
        imports: Optional[List[str]] = None,
        symbols: Optional[List[str]] = None,
        strings_data: str = "",
        component_id: Optional[str] = None,
        artifact_id: Optional[str] = None
    ) -> List[CryptoReference]:
        """
        Detect crypto library presence.

        Note: Library presence != confirmed usage.
        """
        references = []
        seen = set()

        # Check imports
        if imports:
            for imp in imports:
                for lib_name, lib_enum in self.LIBRARY_PATTERNS.items():
                    if lib_name.lower() in imp.lower():
                        ref_id = generate_reference_id(imp)
                        if ref_id in seen:
                            continue
                        seen.add(ref_id)

                        references.append(CryptoReference(
                            reference_id=ref_id,
                            symbol=imp,
                            library=lib_enum,
                            presence=LibraryPresence.LINKED,
                            component_id=component_id,
                            artifact_id=artifact_id,
                            evidence_strength=EvidenceStrength.STRUCTURAL,
                            evidence_sources=[f"import:{imp}"]
                        ))

        # Check symbols
        if symbols:
            for sym in symbols:
                sym_lower = sym.lower()

                # Check for crypto APIs
                for api_name, category in self.CRYPTO_API_PATTERNS.items():
                    if api_name.lower() in sym_lower:
                        ref_id = generate_reference_id(sym)
                        if ref_id in seen:
                            continue
                        seen.add(ref_id)

                        lib = map_symbol_to_library(sym)

                        references.append(CryptoReference(
                            reference_id=ref_id,
                            symbol=sym,
                            library=lib,
                            presence=LibraryPresence.LINKED,
                            component_id=component_id,
                            artifact_id=artifact_id,
                            evidence_strength=EvidenceStrength.REFERENCE,
                            evidence_sources=[f"symbol:{sym}"]
                        ))

        # Check strings for library evidence
        for lib_name, lib_enum in self.LIBRARY_PATTERNS.items():
            if lib_name in strings_data:
                ref_id = generate_reference_id(f"strings:{lib_name}")
                if ref_id not in seen:
                    seen.add(ref_id)
                    references.append(CryptoReference(
                        reference_id=ref_id,
                        symbol=lib_name,
                        library=lib_enum,
                        presence="linked",
                        component_id=component_id,
                        artifact_id=artifact_id,
                        evidence_strength=EvidenceStrength.STRING_HINT,
                        evidence_sources=[f"strings:{lib_name}"]
                    ))

        return references

    def detect_operations(
        self,
        imports: Optional[List[str]] = None,
        symbols: Optional[List[str]] = None,
        objc_metadata: Optional[Dict] = None,
        component_id: Optional[str] = None,
        artifact_id: Optional[str] = None
    ) -> List[CryptoOperationCandidate]:
        """
        Detect crypto operation candidates.

        Note: These are candidates only. Do not claim confirmed behavior.
        """
        operations = []
        seen = set()

        # From imports
        if imports:
            for imp in imports:
                for api_name, category in self.CRYPTO_API_PATTERNS.items():
                    if api_name.lower() in imp.lower():
                        op_id = generate_operation_id(imp)
                        if op_id in seen:
                            continue
                        seen.add(op_id)

                        operations.append(CryptoOperationCandidate(
                            operation_id=op_id,
                            primitive_category=category,
                            algorithm=map_symbol_to_algorithm(imp),
                            evidence_strength=EvidenceStrength.REFERENCE,
                            evidence_sources=[f"import:{imp}"],
                            component_id=component_id,
                            artifact_id=artifact_id,
                            function_name=imp,
                            library=map_symbol_to_library(imp),
                        ))

        # From symbols
        if symbols:
            for sym in symbols:
                for api_name, category in self.CRYPTO_API_PATTERNS.items():
                    if api_name.lower() in sym.lower():
                        op_id = generate_operation_id(sym)
                        if op_id in seen:
                            continue
                        seen.add(op_id)

                        operations.append(CryptoOperationCandidate(
                            operation_id=op_id,
                            primitive_category=category,
                            algorithm=map_symbol_to_algorithm(sym),
                            evidence_strength=EvidenceStrength.REFERENCE,
                            evidence_sources=[f"symbol:{sym}"],
                            component_id=component_id,
                            artifact_id=artifact_id,
                            function_name=sym,
                            library=map_symbol_to_library(sym),
                        ))

        # From ObjC metadata
        if objc_metadata:
            classes = objc_metadata.get('classes', [])
            for cls in classes:
                cls_name = cls.get('name', '')

                # Check for crypto-related class names
                for api_name, category in self.CRYPTO_API_PATTERNS.items():
                    if api_name.lower() in cls_name.lower():
                        op_id = generate_operation_id(cls_name)
                        if op_id not in seen:
                            seen.add(op_id)

                            operations.append(CryptoOperationCandidate(
                                operation_id=op_id,
                                primitive_category=category,
                                algorithm=map_symbol_to_algorithm(cls_name),
                                evidence_strength=EvidenceStrength.REFERENCE,
                                evidence_sources=[f"objc:{cls_name}"],
                                component_id=component_id,
                                artifact_id=artifact_id,
                                class_name=cls_name,
                                library=map_symbol_to_library(cls_name),
                            ))

        return operations

    def detect_from_strings(
        self,
        strings_data: str,
        component_id: Optional[str] = None,
        artifact_id: Optional[str] = None
    ) -> List[CryptoOperationCandidate]:
        """
        Detect crypto from strings.

        Note: String evidence alone is STRING_HINT only.
        Do NOT elevate to higher evidence levels.
        """
        operations = []
        seen = set()

        for pattern in self.CRYPTO_STRING_PATTERNS:
            if pattern in strings_data:
                op_id = generate_operation_id(f"strings:{pattern}")
                if op_id in seen:
                    continue
                seen.add(op_id)

                # Determine category
                category = PrimitiveCategory.UNKNOWN
                algorithm = Algorithm.UNKNOWN
                pattern_lower = pattern.lower()

                if 'hash' in pattern_lower or 'md' in pattern_lower or 'sha' in pattern_lower:
                    category = PrimitiveCategory.HASH
                    algorithm = map_symbol_to_algorithm(pattern)
                elif 'hmac' in pattern_lower:
                    category = PrimitiveCategory.MAC
                elif 'crypt' in pattern_lower or 'cipher' in pattern_lower or 'encrypt' in pattern_lower or 'decrypt' in pattern_lower:
                    category = PrimitiveCategory.SYMMETRIC_CIPHER
                    algorithm = map_symbol_to_algorithm(pattern)
                elif 'rsa' in pattern_lower or 'ec' in pattern_lower or 'ecc' in pattern_lower:
                    category = PrimitiveCategory.ASYMMETRIC_CIPHER
                    algorithm = map_symbol_to_algorithm(pattern)
                elif 'kdf' in pattern_lower or 'pbkdf' in pattern_lower or 'hkdf' in pattern_lower:
                    category = PrimitiveCategory.KDF
                    algorithm = map_symbol_to_algorithm(pattern)
                elif 'keychain' in pattern_lower:
                    category = PrimitiveCategory.KEYCHAIN
                elif 'random' in pattern_lower:
                    category = PrimitiveCategory.RANDOMNESS
                elif 'ssl' in pattern_lower or 'tls' in pattern_lower:
                    category = PrimitiveCategory.TLS_RELATED

                operations.append(CryptoOperationCandidate(
                    operation_id=op_id,
                    primitive_category=category,
                    algorithm=algorithm,
                    evidence_strength=EvidenceStrength.STRING_HINT,
                    evidence_sources=[f"strings:{pattern}"],
                    component_id=component_id,
                    artifact_id=artifact_id,
                ))

        return operations

    def build_model(
        self,
        imports: Optional[List[str]] = None,
        symbols: Optional[List[str]] = None,
        strings_data: str = "",
        objc_metadata: Optional[Dict] = None,
        component_id: Optional[str] = None,
        artifact_id: Optional[str] = None,
        artifact_path: str = ""
    ) -> CryptoModel:
        """
        Build complete crypto model.
        """
        # Detect library presences
        library_presences = self.detect_library_presences(
            imports, symbols, strings_data, component_id, artifact_id
        )

        # Detect operations from imports/symbols (stronger evidence)
        operations = self.detect_operations(
            imports, symbols, objc_metadata, component_id, artifact_id
        )

        # Detect from strings (weaker evidence)
        string_operations = self.detect_from_strings(
            strings_data, component_id, artifact_id
        )

        # Merge operations (don't duplicate)
        existing_ids = {o.operation_id for o in operations}
        for op in string_operations:
            if op.operation_id not in existing_ids:
                operations.append(op)

        # Build model
        model = CryptoModel(
            artifact_path=artifact_path,
            library_presences=library_presences,
            operations=operations,
        )

        # Build indexes
        model.build_indexes()

        # Compute distributions
        model.primitive_distribution = {}
        model.algorithm_distribution = {}
        model.evidence_level_distribution = {}

        for op in operations:
            model.primitive_distribution[op.primitive_category.value] = \
                model.primitive_distribution.get(op.primitive_category.value, 0) + 1
            model.algorithm_distribution[op.algorithm.value] = \
                model.algorithm_distribution.get(op.algorithm.value, 0) + 1
            model.evidence_level_distribution[op.evidence_strength.value] = \
                model.evidence_level_distribution.get(op.evidence_strength.value, 0) + 1

        return model
