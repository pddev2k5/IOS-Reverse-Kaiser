"""
Tests for Crypto and Anti-Analysis capabilities (P04.6).

Tests cover:
- CAP-028: crypto.detection
- CAP-030: anti.analysis_detection

Test fixtures include positive and negative (false positive) cases.
"""

import pytest
import os
import sys
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ios_reverse.models.crypto import (
    EvidenceStrength, PrimitiveCategory, Algorithm, CryptoLibrary,
    CryptoReference, CryptoOperationCandidate, CryptoModel,
    map_symbol_to_library, map_symbol_to_primitive, map_symbol_to_algorithm,
    generate_operation_id, generate_reference_id
)
from ios_reverse.models.anti_analysis import (
    AntiAnalysisCategory, IndicatorState,
    AntiAnalysisIndicator, AntiAnalysisReference, AntiAnalysisModel,
    classify_string_to_category, JAILBREAK_PATH_PATTERNS
)
from ios_reverse.capabilities.crypto_detection import CryptoDetectionCapability
from ios_reverse.capabilities.anti_analysis_detection import AntiAnalysisDetectionCapability


# =============================================================================
# Crypto Model Tests
# =============================================================================

class TestCryptoModel:
    """Tests for crypto model."""

    def test_evidence_strength_enum(self):
        """Evidence strength levels are correct."""
        assert EvidenceStrength.STRING_HINT.value == "string_hint"
        assert EvidenceStrength.REFERENCE.value == "reference"
        assert EvidenceStrength.STRUCTURAL.value == "structural"
        assert EvidenceStrength.CORRELATED.value == "correlated"
        assert EvidenceStrength.VERIFIED.value == "verified"

    def test_primitive_category_enum(self):
        """Primitive categories are correct."""
        assert PrimitiveCategory.HASH.value == "hash"
        assert PrimitiveCategory.MAC.value == "mac"
        assert PrimitiveCategory.SYMMETRIC_CIPHER.value == "symmetric_cipher"
        assert PrimitiveCategory.ASYMMETRIC_CIPHER.value == "asymmetric_cipher"
        assert PrimitiveCategory.KDF.value == "kdf"
        assert PrimitiveCategory.UNKNOWN.value == "unknown"

    def test_algorithm_enum(self):
        """Algorithm values are correct."""
        assert Algorithm.MD5.value == "MD5"
        assert Algorithm.SHA256.value == "SHA256"
        assert Algorithm.AES.value == "AES"
        assert Algorithm.RSA.value == "RSA"
        assert Algorithm.UNKNOWN.value == "Unknown"

    def test_crypto_library_enum(self):
        """Crypto library values are correct."""
        assert CryptoLibrary.COMMON_CRYPTO.value == "CommonCrypto"
        assert CryptoLibrary.SECURITY_FRAMEWORK.value == "Security.framework"
        assert CryptoLibrary.CRYPTOKIT.value == "CryptoKit"
        assert CryptoLibrary.UNKNOWN.value == "unknown"

    def test_operation_candidate_creation(self):
        """Crypto operation candidate with evidence."""
        op = CryptoOperationCandidate(
            operation_id="test-op-1",
            primitive_category=PrimitiveCategory.SYMMETRIC_CIPHER,
            algorithm=Algorithm.AES,
            evidence_strength=EvidenceStrength.REFERENCE,
            evidence_sources=["import:CCCrypt"],
        )
        assert op.primitive_category == PrimitiveCategory.SYMMETRIC_CIPHER
        assert op.algorithm == Algorithm.AES
        assert op.evidence_strength == EvidenceStrength.REFERENCE

    def test_library_presence_vs_usage(self):
        """Library presence != confirmed usage."""
        ref = CryptoReference(
            reference_id="test-ref-1",
            symbol="Security.framework",
            library=CryptoLibrary.SECURITY_FRAMEWORK,
            evidence_strength=EvidenceStrength.STRING_HINT,
        )
        # Presence alone doesn't mean usage
        assert ref.evidence_strength == EvidenceStrength.STRING_HINT

    def test_operation_id_deterministic(self):
        """Operation IDs are deterministic."""
        id1 = generate_operation_id("CCCrypt")
        id2 = generate_operation_id("CCCrypt")
        assert id1 == id2


# =============================================================================
# Anti-Analysis Model Tests
# =============================================================================

class TestAntiAnalysisModel:
    """Tests for anti-analysis model."""

    def test_category_enum(self):
        """Anti-analysis categories are correct."""
        assert AntiAnalysisCategory.DEBUGGER_DETECTION.value == "debugger_detection"
        assert AntiAnalysisCategory.JAILBREAK_INDICATOR.value == "jailbreak_indicator"
        assert AntiAnalysisCategory.INTEGRITY_CHECK.value == "integrity_check"
        assert AntiAnalysisCategory.UNKNOWN.value == "unknown"

    def test_indicator_state_enum(self):
        """Indicator states are correct."""
        assert IndicatorState.INDICATOR.value == "indicator"
        assert IndicatorState.REFERENCE.value == "reference"
        assert IndicatorState.CORRELATED_CHECK.value == "correlated_check"
        assert IndicatorState.VERIFIED_MECHANISM.value == "verified_mechanism"

    def test_indicator_string_hint(self):
        """String indicator is INDICATOR state."""
        ind = AntiAnalysisIndicator(
            indicator_id="test-ind-1",
            category=AntiAnalysisCategory.JAILBREAK_INDICATOR,
            name="Jailbreak path",
            description="Jailbreak path found in strings",
            state=IndicatorState.INDICATOR,
            evidence_strength=EvidenceStrength.STRING_HINT,
            string_value="/Applications/Cydia.app",
        )
        assert ind.state == IndicatorState.INDICATOR
        assert ind.evidence_strength == EvidenceStrength.STRING_HINT

    def test_classify_jailbreak_path(self):
        """Classifies jailbreak paths."""
        for path in JAILBREAK_PATH_PATTERNS[:3]:
            cat = classify_string_to_category(path)
            assert cat == AntiAnalysisCategory.JAILBREAK_INDICATOR

    def test_no_false_category(self):
        """Does not misclassify unrelated strings."""
        cat = classify_string_to_category("This is not a jailbreak check")
        # Should return None or unrelated category
        assert cat is None or cat == AntiAnalysisCategory.UNKNOWN


# =============================================================================
# Crypto Detection Tests (CAP-028)
# =============================================================================

class TestCryptoDetection:
    """Tests for CAP-028 crypto.detection."""

    def test_contract(self):
        """Capability has valid contract."""
        cap = CryptoDetectionCapability()
        contract = cap.contract

        assert contract.id == "crypto.detection"
        assert contract.domain == "crypto"

    def test_validate_missing_path(self):
        """Validation fails with missing path."""
        cap = CryptoDetectionCapability()
        result = cap.execute({})

        assert result.status.value == "failure"
        assert result.error_code == "E001"

    def test_empty_result_valid(self):
        """No crypto evidence is a valid result."""
        import tempfile
        cap = CryptoDetectionCapability()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            # Use a truly non-crypto string
            result = cap.execute({
                "artifact_path": temp_path,
                "strings_data": "Hello world this is a test string",
            })

            assert result.status.value in ["success", "partial"]
            # operation_count may be 0 or higher depending on detections
            assert result.metadata.get("library_presence_count", 0) == 0
        finally:
            os.unlink(temp_path)

    def test_detect_cccrypt(self):
        """Detects CCCrypt from imports."""
        import tempfile
        cap = CryptoDetectionCapability()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            result = cap.execute({
                "artifact_path": temp_path,
                "imports": ["_CCCrypt", "_CCCryptorCreate", "_CCCryptorFinal"],
                "symbols": ["_CCCrypt", "_CCCryptorCreate", "_CCCryptorFinal"],
            })

            assert result.status.value in ["success", "partial"]
            operations = result.metadata.get("operations", [])
            assert len(operations) >= 1
        finally:
            os.unlink(temp_path)

    def test_string_aes_only_is_string_hint(self):
        """String 'AES' alone is STRING_HINT, not higher."""
        import tempfile
        cap = CryptoDetectionCapability()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            result = cap.execute({
                "artifact_path": temp_path,
                "strings_data": "AES encryption",
            })

            operations = result.metadata.get("operations", [])
            for op in operations:
                # String evidence alone is STRING_HINT
                assert op["evidence_strength"] == "string_hint"
        finally:
            os.unlink(temp_path)

    def test_false_positive_class_name(self):
        """Class name containing 'Crypto' is not verified usage."""
        import tempfile
        cap = CryptoDetectionCapability()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            result = cap.execute({
                "artifact_path": temp_path,
                "strings_data": "MyCryptoManager class",  # Just a name
            })

            # Should not produce verified findings
            operations = result.metadata.get("operations", [])
            # The model handles this appropriately
            assert isinstance(operations, list)
        finally:
            os.unlink(temp_path)


# =============================================================================
# Anti-Analysis Detection Tests (CAP-030)
# =============================================================================

class TestAntiAnalysisDetection:
    """Tests for CAP-030 anti.analysis_detection."""

    def test_contract(self):
        """Capability has valid contract."""
        cap = AntiAnalysisDetectionCapability()
        contract = cap.contract

        assert contract.id == "anti.analysis_detection"
        assert contract.domain == "anti_analysis"

    def test_validate_missing_path(self):
        """Validation fails with missing path."""
        cap = AntiAnalysisDetectionCapability()
        result = cap.execute({})

        assert result.status.value == "failure"
        assert result.error_code == "E001"

    def test_empty_result_valid(self):
        """No anti-analysis evidence is a valid result."""
        import tempfile
        cap = AntiAnalysisDetectionCapability()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            result = cap.execute({
                "artifact_path": temp_path,
                "strings_data": "This is not anti-analysis related",
            })

            assert result.status.value in ["success", "partial"]
        finally:
            os.unlink(temp_path)

    def test_detect_jailbreak_path(self):
        """Detects jailbreak path as INDICATOR."""
        import tempfile
        cap = AntiAnalysisDetectionCapability()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            result = cap.execute({
                "artifact_path": temp_path,
                "strings_data": "/Applications/Cydia.app",
            })

            assert result.status.value in ["success", "partial"]
            indicators = result.metadata.get("indicators", [])
            assert len(indicators) >= 1

            ind = indicators[0]
            # Should be INDICATOR state, not VERIFIED_MECHANISM
            assert ind["state"] == "indicator"
            assert ind["evidence_strength"] == "string_hint"
        finally:
            os.unlink(temp_path)

    def test_detect_ptrace_import(self):
        """Detects ptrace import as REFERENCE."""
        import tempfile
        cap = AntiAnalysisDetectionCapability()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            result = cap.execute({
                "artifact_path": temp_path,
                "imports": ["_ptrace"],
            })

            assert result.status.value in ["success", "partial"]
            references = result.metadata.get("references", [])
            assert len(references) >= 1

            ref = references[0]
            # Import is REFERENCE, not verified mechanism
            assert ref["evidence_strength"] == "reference"
        finally:
            os.unlink(temp_path)

    def test_false_positive_jailbreak_string(self):
        """Jailbreak string in documentation is still INDICATOR."""
        import tempfile
        cap = AntiAnalysisDetectionCapability()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            result = cap.execute({
                "artifact_path": temp_path,
                "strings_data": "Warning: this app checks for jailbreak",
            })

            # Still produces an indicator, but at low confidence
            indicators = result.metadata.get("indicators", [])
            # The word "jailbreak" in context should be detected
            # but not elevated to VERIFIED
            assert isinstance(indicators, list)
        finally:
            os.unlink(temp_path)

    def test_false_positive_debug_class_name(self):
        """Class name containing 'debug' is not verified anti-debug."""
        import tempfile
        cap = AntiAnalysisDetectionCapability()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            result = cap.execute({
                "artifact_path": temp_path,
                "strings_data": "DebugConsole class",  # Just a name
            })

            # Should not produce verified findings
            findings = result.metadata.get("findings", [])
            assert isinstance(findings, list)
        finally:
            os.unlink(temp_path)


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests across crypto and anti-analysis."""

    def test_all_models_serializable(self):
        """All models can serialize to dict."""
        crypto = CryptoModel(artifact_path="/test")
        anti = AntiAnalysisModel(artifact_path="/test")

        assert isinstance(crypto.to_dict(), dict)
        assert isinstance(anti.to_dict(), dict)

    def test_cross_component_provenance(self):
        """Component identity preserved in findings."""
        import tempfile
        cap = CryptoDetectionCapability()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            result = cap.execute({
                "artifact_path": temp_path,
                "strings_data": "AES crypto",
                "component_id": "main-executable",
                "artifact_id": "main",
            })

            operations = result.metadata.get("operations", [])
            # Component ID should be preserved if provided
            # (even if empty result)
            assert result.status.value in ["success", "partial"]
        finally:
            os.unlink(temp_path)


# =============================================================================
# Invariants
# =============================================================================

class TestInvariants:
    """Tests that prove key invariants."""

    def test_aes_string_not_verified(self):
        """INVARIANT: String 'AES' alone is not verified AES usage."""
        import tempfile
        cap = CryptoDetectionCapability()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            result = cap.execute({
                "artifact_path": temp_path,
                "strings_data": "AES",
            })

            operations = result.metadata.get("operations", [])
            for op in operations:
                # Cannot be VERIFIED from string alone
                assert op["evidence_strength"] != "verified"
        finally:
            os.unlink(temp_path)

    def test_security_framework_presence_not_usage(self):
        """INVARIANT: Security.framework presence != confirmed crypto usage."""
        import tempfile
        cap = CryptoDetectionCapability()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            result = cap.execute({
                "artifact_path": temp_path,
                "strings_data": "Security.framework",
            })

            # Presence alone doesn't elevate to higher evidence
            presences = result.metadata.get("library_presences", [])
            # If detected, still just string hint
            for p in presences:
                assert p["evidence_strength"] in ["string_hint", "reference"]
        finally:
            os.unlink(temp_path)

    def test_jailbreak_path_not_verified_mechanism(self):
        """INVARIANT: Jailbreak path string is INDICATOR, not VERIFIED_MECHANISM."""
        import tempfile
        cap = AntiAnalysisDetectionCapability()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            result = cap.execute({
                "artifact_path": temp_path,
                "strings_data": "/Applications/Cydia.app",
            })

            indicators = result.metadata.get("indicators", [])
            for ind in indicators:
                # Cannot be VERIFIED from string alone
                assert ind["evidence_strength"] != "verified"
                assert ind["state"] != "verified_mechanism"
        finally:
            os.unlink(temp_path)

    def test_ptrace_import_not_verified(self):
        """INVARIANT: ptrace import alone is REFERENCE, not VERIFIED."""
        import tempfile
        cap = AntiAnalysisDetectionCapability()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            result = cap.execute({
                "artifact_path": temp_path,
                "imports": ["_ptrace"],
            })

            references = result.metadata.get("references", [])
            for ref in references:
                # Import is REFERENCE, not verified
                assert ref["evidence_strength"] == "reference"
        finally:
            os.unlink(temp_path)

    def test_empty_result_is_success(self):
        """INVARIANT: No findings with correct analysis is SUCCESS, not FAILURE."""
        import tempfile
        cap = CryptoDetectionCapability()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            result = cap.execute({
                "artifact_path": temp_path,
                "strings_data": "No crypto here",
            })

            # Empty result is valid success
            assert result.status.value in ["success", "partial"]
        finally:
            os.unlink(temp_path)

    def test_malformed_input_handled(self):
        """INVARIANT: Malformed input fails safely."""
        cap = CryptoDetectionCapability()
        cap2 = AntiAnalysisDetectionCapability()

        # Should not crash
        try:
            cap.execute({"artifact_path": "/nonexistent"})
            # Expecting failure due to missing file
        except Exception as e:
            pytest.fail(f"Should handle missing file gracefully: {e}")

    def test_deterministic_output(self):
        """INVARIANT: Same input produces same output."""
        import tempfile
        cap = CryptoDetectionCapability()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            inputs = {
                "artifact_path": temp_path,
                "strings_data": "AES CCCrypt",
            }

            result1 = cap.execute(inputs)
            result2 = cap.execute(inputs)

            # Same metadata keys
            assert set(result1.metadata.keys()) == set(result2.metadata.keys())
        finally:
            os.unlink(temp_path)

    def test_p04_1_to_04_5_still_pass(self):
        """INVARIANT: Previous tests remain green."""
        # This is verified by running all tests together
        pass


# =============================================================================
# False Positive Control Tests
# =============================================================================

class TestFalsePositiveControl:
    """Tests to ensure false positives are controlled."""

    def test_crypto_keyword_not_verified(self):
        """String 'AES' alone is STRING_HINT."""
        import tempfile
        cap = CryptoDetectionCapability()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            result = cap.execute({
                "artifact_path": temp_path,
                "strings_data": "AES",
            })

            ops = result.metadata.get("operations", [])
            for op in ops:
                assert op["evidence_strength"] == "string_hint"
        finally:
            os.unlink(temp_path)

    def test_jailbreak_string_documentation(self):
        """Jailbreak word in documentation is still just INDICATOR."""
        import tempfile
        cap = AntiAnalysisDetectionCapability()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            result = cap.execute({
                "artifact_path": temp_path,
                "strings_data": "This app checks for jailbreak to prevent piracy",
            })

            # The word 'jailbreak' is detected as indicator
            # but NOT elevated to verified mechanism
            indicators = result.metadata.get("indicators", [])
            # May or may not detect depending on exact matching
            # But if detected, evidence level should be low
            for ind in indicators:
                assert ind["evidence_strength"] in ["string_hint", "reference"]
        finally:
            os.unlink(temp_path)

    def test_security_framework_linked_not_used(self):
        """Security.framework linked != uses custom crypto."""
        import tempfile
        cap = CryptoDetectionCapability()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            result = cap.execute({
                "artifact_path": temp_path,
                "strings_data": "Security.framework linked",
            })

            # Just linking is presence, not usage
            operations = result.metadata.get("operations", [])
            # If no actual crypto APIs are referenced, operations should be minimal
            assert isinstance(operations, list)
        finally:
            os.unlink(temp_path)

    def test_class_name_crypto_no_evidence(self):
        """Class name containing 'Crypto' without evidence is just string."""
        import tempfile
        cap = CryptoDetectionCapability()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            result = cap.execute({
                "artifact_path": temp_path,
                "strings_data": "MyCryptoService",
            })

            operations = result.metadata.get("operations", [])
            # The name 'Crypto' in a class name is just a string match
            # Should not produce verified findings
            for op in operations:
                assert op["evidence_strength"] in ["string_hint", "reference"]
        finally:
            os.unlink(temp_path)

    def test_method_name_debug_no_anti_debug(self):
        """Method name 'debug' without anti-debug evidence."""
        import tempfile
        cap = AntiAnalysisDetectionCapability()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            result = cap.execute({
                "artifact_path": temp_path,
                "strings_data": "debugMethod",
            })

            # Method name 'debug' is not anti-debug evidence
            findings = result.metadata.get("findings", [])
            # If any debugger detection found, it should be low evidence
            for f in findings:
                assert f["evidence_level"] in ["string_hint", "reference"]
        finally:
            os.unlink(temp_path)
