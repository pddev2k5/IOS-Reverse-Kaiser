"""
Anti-Analysis Adapter for IOS REVERSE KAISER.

Provides anti-analysis mechanism detection.
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

from ios_reverse.adapters.base import ToolAdapter, ToolInfo, AdapterResult
from ios_reverse.models.anti_analysis import (
    EvidenceStrength, AntiAnalysisCategory, IndicatorState,
    AntiAnalysisIndicator, AntiAnalysisReference, AntiAnalysisEvidence,
    AntiAnalysisFinding, AntiAnalysisModel,
    generate_indicator_id, generate_finding_id,
    classify_string_to_category, DEBUGGER_API_PATTERNS, JAILBREAK_PATH_PATTERNS,
    INTEGRITY_CHECK_PATTERNS, ENVIRONMENT_CHECK_PATTERNS,
    DYNAMIC_INSTRUMENTATION_PATTERNS, OBFUSCATION_PATTERNS
)


class AntiAnalysisAdapter(ToolAdapter):
    """
    Adapter for anti-analysis detection.

    IMPORTANT:
    - String "jailbreak" alone is INDICATOR, not VERIFIED
    - Debugger API import is REFERENCE, not verified mechanism
    - Does not fabricate protection effectiveness
    """

    # Debugger detection APIs
    DEBUGGER_APIS = {
        'ptrace': AntiAnalysisCategory.DEBUGGER_DETECTION,
        'sysctl': AntiAnalysisCategory.DEBUGGER_DETECTION,
        'sysctlbyname': AntiAnalysisCategory.DEBUGGER_DETECTION,
        'IsDebuggerConnected': AntiAnalysisCategory.DEBUGGER_DETECTION,
        'PT_DENY_ATTACH': AntiAnalysisCategory.DEBUGGER_DETECTION,
        'getpid': AntiAnalysisCategory.DEBUGGER_DETECTION,
        'getppid': AntiAnalysisCategory.DEBUGGER_DETECTION,
        'kill': AntiAnalysisCategory.DEBUGGER_DETECTION,
        'fork': AntiAnalysisCategory.DEBUGGER_DETECTION,
        'raise': AntiAnalysisCategory.DEBUGGER_DETECTION,
    }

    # Integrity check APIs
    INTEGRITY_APIS = {
        'SecCodeCheckValidity': AntiAnalysisCategory.INTEGRITY_CHECK,
        'SecCodeCopyStaticCode': AntiAnalysisCategory.INTEGRITY_CHECK,
        'SecStaticCodeCreateWithPath': AntiAnalysisCategory.INTEGRITY_CHECK,
        'SecCodeVerify': AntiAnalysisCategory.INTEGRITY_CHECK,
        'kSecCodeSignatureValid': AntiAnalysisCategory.INTEGRITY_CHECK,
    }

    # Anti-hooking APIs
    ANTI_HOOKING_APIS = {
        'fishhook': AntiAnalysisCategory.ANTI_HOOKING,
        'MSHookFunction': AntiAnalysisCategory.ANTI_HOOKING,
        'MSFindSymbol': AntiAnalysisCategory.ANTI_HOOKING,
        'substrate': AntiAnalysisCategory.ANTI_HOOKING,
        'MobileSubstrate': AntiAnalysisCategory.ANTI_HOOKING,
    }

    def __init__(self):
        super().__init__("anti_analysis_adapter", "1.0.0")
        self._id_counter = 0

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="anti_analysis_adapter",
            path="internal",
            version="1.0.0"
        )

    def validate_environment(self) -> Tuple[bool, Optional[str]]:
        return True, None

    def execute(self, command, cwd=None, env=None, input_data=None):
        return AdapterResult(success=True, stdout="Pure Python adapter")

    def is_available(self) -> bool:
        return True

    def detect_indicators(
        self,
        strings_data: str = "",
        component_id: Optional[str] = None,
        artifact_id: Optional[str] = None
    ) -> List[AntiAnalysisIndicator]:
        """
        Detect anti-analysis indicators from strings.

        Note: String evidence alone is STRING_HINT / INDICATOR.
        Do NOT claim verified mechanisms.
        """
        indicators = []
        seen = set()

        # Jailbreak paths
        for path in JAILBREAK_PATH_PATTERNS:
            if path in strings_data:
                ind_id = generate_indicator_id(f"jailbreak:{path}")
                if ind_id in seen:
                    continue
                seen.add(ind_id)

                indicators.append(AntiAnalysisIndicator(
                    indicator_id=ind_id,
                    category=AntiAnalysisCategory.JAILBREAK_INDICATOR,
                    name=f"Jailbreak path: {path}",
                    description=f"String containing jailbreak-related path: {path}",
                    state=IndicatorState.INDICATOR,
                    evidence_strength=EvidenceStrength.STRING_HINT,
                    evidence_sources=[f"strings:{path}"],
                    component_id=component_id,
                    artifact_id=artifact_id,
                    string_value=path,
                ))

        # Dynamic instrumentation strings
        for pattern in DYNAMIC_INSTRUMENTATION_PATTERNS:
            if pattern in strings_data:
                ind_id = generate_indicator_id(f"dyninst:{pattern}")
                if ind_id in seen:
                    continue
                seen.add(ind_id)

                indicators.append(AntiAnalysisIndicator(
                    indicator_id=ind_id,
                    category=AntiAnalysisCategory.DYNAMIC_INSTRUMENTATION,
                    name=f"Dynamic instrumentation: {pattern}",
                    description=f"String containing instrumentation-related content: {pattern}",
                    state=IndicatorState.INDICATOR,
                    evidence_strength=EvidenceStrength.STRING_HINT,
                    evidence_sources=[f"strings:{pattern}"],
                    component_id=component_id,
                    artifact_id=artifact_id,
                    string_value=pattern,
                ))

        # Environment check strings
        for pattern in ENVIRONMENT_CHECK_PATTERNS:
            if pattern in strings_data:
                ind_id = generate_indicator_id(f"env:{pattern}")
                if ind_id in seen:
                    continue
                seen.add(ind_id)

                indicators.append(AntiAnalysisIndicator(
                    indicator_id=ind_id,
                    category=AntiAnalysisCategory.ENVIRONMENT_CHECK,
                    name=f"Environment indicator: {pattern}",
                    description=f"String containing environment check: {pattern}",
                    state=IndicatorState.INDICATOR,
                    evidence_strength=EvidenceStrength.STRING_HINT,
                    evidence_sources=[f"strings:{pattern}"],
                    component_id=component_id,
                    artifact_id=artifact_id,
                    string_value=pattern,
                ))

        # Obfuscation strings
        for pattern in OBFUSCATION_PATTERNS:
            if pattern in strings_data:
                ind_id = generate_indicator_id(f"obf:{pattern}")
                if ind_id in seen:
                    continue
                seen.add(ind_id)

                indicators.append(AntiAnalysisIndicator(
                    indicator_id=ind_id,
                    category=AntiAnalysisCategory.OBFUSCATION,
                    name=f"Obfuscation indicator: {pattern}",
                    description=f"String containing obfuscation-related content: {pattern}",
                    state=IndicatorState.INDICATOR,
                    evidence_strength=EvidenceStrength.STRING_HINT,
                    evidence_sources=[f"strings:{pattern}"],
                    component_id=component_id,
                    artifact_id=artifact_id,
                    string_value=pattern,
                ))

        return indicators

    def detect_references(
        self,
        imports: Optional[List[str]] = None,
        symbols: Optional[List[str]] = None,
        component_id: Optional[str] = None,
        artifact_id: Optional[str] = None
    ) -> List[AntiAnalysisReference]:
        """
        Detect anti-analysis API references.

        Note: Import/symbol evidence is REFERENCE, not verified mechanism.
        """
        references = []
        seen = set()

        # Check debugger APIs
        for api, category in self.DEBUGGER_APIS.items():
            api_lower = api.lower()

            if imports:
                for imp in imports:
                    if api_lower in imp.lower():
                        ref_id = generate_indicator_id(f"import:{api}")
                        if ref_id in seen:
                            continue
                        seen.add(ref_id)

                        references.append(AntiAnalysisReference(
                            reference_id=ref_id,
                            symbol=imp,
                            category=category,
                            presence="imported",
                            evidence_strength=EvidenceStrength.REFERENCE,
                            evidence_sources=[f"import:{imp}"],
                            component_id=component_id,
                            artifact_id=artifact_id,
                        ))

            if symbols:
                for sym in symbols:
                    if api_lower in sym.lower():
                        ref_id = generate_indicator_id(f"symbol:{api}")
                        if ref_id in seen:
                            continue
                        seen.add(ref_id)

                        references.append(AntiAnalysisReference(
                            reference_id=ref_id,
                            symbol=sym,
                            category=category,
                            presence="exported",
                            evidence_strength=EvidenceStrength.REFERENCE,
                            evidence_sources=[f"symbol:{sym}"],
                            component_id=component_id,
                            artifact_id=artifact_id,
                        ))

        # Check integrity APIs
        for api, category in self.INTEGRITY_APIS.items():
            api_lower = api.lower()

            if imports:
                for imp in imports:
                    if api_lower in imp.lower():
                        ref_id = generate_indicator_id(f"import:{api}")
                        if ref_id in seen:
                            continue
                        seen.add(ref_id)

                        references.append(AntiAnalysisReference(
                            reference_id=ref_id,
                            symbol=imp,
                            category=category,
                            presence="imported",
                            evidence_strength=EvidenceStrength.REFERENCE,
                            evidence_sources=[f"import:{imp}"],
                            component_id=component_id,
                            artifact_id=artifact_id,
                        ))

        # Check anti-hooking APIs
        for api, category in self.ANTI_HOOKING_APIS.items():
            api_lower = api.lower()

            if imports:
                for imp in imports:
                    if api_lower in imp.lower():
                        ref_id = generate_indicator_id(f"import:{api}")
                        if ref_id in seen:
                            continue
                        seen.add(ref_id)

                        references.append(AntiAnalysisReference(
                            reference_id=ref_id,
                            symbol=imp,
                            category=category,
                            presence="imported",
                            evidence_strength=EvidenceStrength.REFERENCE,
                            evidence_sources=[f"import:{imp}"],
                            component_id=component_id,
                            artifact_id=artifact_id,
                        ))

        return references

    def build_findings(
        self,
        indicators: List[AntiAnalysisIndicator],
        references: List[AntiAnalysisReference],
        component_id: Optional[str] = None,
        artifact_id: Optional[str] = None
    ) -> List[AntiAnalysisFinding]:
        """
        Build findings from indicators and references.

        Each finding is a normalized aggregation of related evidence.
        """
        findings = []
        seen = set()

        # Group by category
        by_category = {}
        for ind in indicators:
            cat = ind.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(ind)

        for ref in references:
            cat = ref.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(ref)

        # Create finding per category
        for cat_str, items in by_category.items():
            if not items:
                continue

            category = AntiAnalysisCategory(cat_str)
            ind_ids = [i.indicator_id for i in items if isinstance(i, AntiAnalysisIndicator)]
            ref_ids = [r.reference_id for r in items if isinstance(r, AntiAnalysisReference)]

            finding_id = generate_finding_id(cat_str, f"category-{len(items)}")
            if finding_id in seen:
                continue
            seen.add(finding_id)

            # Determine strongest evidence level
            max_strength = EvidenceStrength.STRING_HINT
            for item in items:
                if hasattr(item, 'evidence_strength'):
                    if item.evidence_strength == EvidenceStrength.REFERENCE:
                        max_strength = EvidenceStrength.REFERENCE
                    elif item.evidence_strength == EvidenceStrength.STRUCTURAL:
                        max_strength = EvidenceStrength.STRUCTURAL

            # Determine state
            state = IndicatorState.INDICATOR
            if any(isinstance(i, AntiAnalysisReference) for i in items):
                state = IndicatorState.REFERENCE

            findings.append(AntiAnalysisFinding(
                finding_id=finding_id,
                category=category,
                finding_type=f"{cat_str}_indicator",
                description=f"Anti-analysis {category.value.replace('_', ' ')} indicators detected",
                state=state,
                evidence_level=max_strength,
                indicator_ids=ind_ids,
                reference_ids=ref_ids,
                component_id=component_id,
                artifact_id=artifact_id,
                provenance=[f"aggregated from {len(items)} evidence items"],
            ))

        return findings

    def build_model(
        self,
        strings_data: str = "",
        imports: Optional[List[str]] = None,
        symbols: Optional[List[str]] = None,
        component_id: Optional[str] = None,
        artifact_id: Optional[str] = None,
        artifact_path: str = ""
    ) -> AntiAnalysisModel:
        """
        Build complete anti-analysis model.
        """
        # Detect indicators (strings)
        indicators = self.detect_indicators(
            strings_data, component_id, artifact_id
        )

        # Detect references (imports/symbols)
        references = self.detect_references(
            imports, symbols, component_id, artifact_id
        )

        # Build findings
        findings = self.build_findings(
            indicators, references, component_id, artifact_id
        )

        # Build model
        model = AntiAnalysisModel(
            artifact_path=artifact_path,
            indicators=indicators,
            references=references,
            findings=findings,
        )

        # Build indexes
        model.build_indexes()

        # Compute distributions
        model.category_distribution = {}
        model.state_distribution = {}
        model.evidence_level_distribution = {}

        for finding in findings:
            model.category_distribution[finding.category.value] = \
                model.category_distribution.get(finding.category.value, 0) + 1
            model.state_distribution[finding.state.value] = \
                model.state_distribution.get(finding.state.value, 0) + 1
            model.evidence_level_distribution[finding.evidence_level.value] = \
                model.evidence_level_distribution.get(finding.evidence_level.value, 0) + 1

        return model
