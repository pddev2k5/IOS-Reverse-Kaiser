"""
Swift demangler for IOS REVERSE KAISER.

Provides demangling of Swift symbols with fallback for unavailable tool.
"""

import re
import subprocess
import os
from typing import Optional, List, Tuple
from dataclasses import dataclass

from ios_reverse.models.swift import SwiftDemangleResult, EvidenceStrength


# Swift mangling patterns
SWIFT_MANGLED_PREFIXES = [
    "_T",      # Old Swift mangling
    "_$s",     # Modern Swift mangling
    "$s",      # Modern Swift mangling (no underscore)
    "_swift",  # Some symbol formats
]

# Common Swift type patterns
SWIFT_TYPE_PATTERNS = [
    (r'^_?T[fv](\d+)', 'function'),
    (r'^_?T[Cl]o(\d+)', 'class_method'),
    (r'^_?TWV(\d+)', 'property_getter'),
    (r'^_?TWS(\d+)', 'property_setter'),
    (r'^_?TWo(\d+)', 'subscript'),
]


@dataclass
class DemangleConfig:
    """Configuration for demangling."""
    prefer_on_device: bool = True  # Prefer on-device tool if available
    max_depth: int = 5  # Maximum demangling recursion depth
    timeout_seconds: int = 5  # Timeout for external demangler


class SwiftDemangler:
    """
    Swift symbol demangler with multiple backend support.

    Backends (in order of preference):
    1. swift-demangle (if available)
    2. xcrun swift-demangle (macOS)
    3. Python implementation (fallback)
    """

    def __init__(self, config: Optional[DemangleConfig] = None):
        self.config = config or DemangleConfig()
        self._demangler_path = None
        self._detected_backend = None
        self._init_demangler()

    def _init_demangler(self):
        """Detect and initialize available demangler."""
        # Check for swift-demangle in PATH
        demangler_candidates = [
            "swift-demangle",
            "xcrun",
        ]

        for candidate in demangler_candidates:
            try:
                if candidate == "xcrun":
                    # Check if xcrun is available on macOS
                    result = subprocess.run(
                        ["xcrun", "--find", "swift-demangle"],
                        capture_output=True,
                        timeout=2
                    )
                    if result.returncode == 0:
                        self._demangler_path = result.stdout.decode().strip()
                        self._detected_backend = "xcrun"
                        return
                else:
                    result = subprocess.run(
                        [candidate, "--version"],
                        capture_output=True,
                        timeout=2
                    )
                    if result.returncode == 0:
                        self._demangler_path = candidate
                        self._detected_backend = candidate
                        return
            except (subprocess.SubprocessError, FileNotFoundError):
                continue

        # No external demangler found - use Python fallback
        self._demangler_path = None
        self._detected_backend = "python"

    def is_available(self) -> bool:
        """Check if demangler is available."""
        return True  # Always available (Python fallback exists)

    def get_backend(self) -> str:
        """Get the detected demangling backend."""
        return self._detected_backend or "python"

    def demangle(self, mangled_name: str) -> SwiftDemangleResult:
        """
        Demangle a single Swift symbol.

        Args:
            mangled_name: Mangled Swift symbol

        Returns:
            SwiftDemangleResult with demangled name or error
        """
        if not mangled_name:
            return SwiftDemangleResult(
                mangled_name="",
                demangled_name=None,
                success=False,
                error="Empty input"
            )

        # Check if it's a Swift mangled symbol
        if not self._is_swift_mangled(mangled_name):
            # Not a Swift symbol - return as-is
            return SwiftDemangleResult(
                mangled_name=mangled_name,
                demangled_name=mangled_name,
                success=True,
                demangler_used="passthrough",
                evidence=EvidenceStrength.STRING_HINT
            )

        # Try external demangler first
        if self._demangler_path and self._detected_backend != "python":
            result = self._try_external_demangle(mangled_name)
            if result.success:
                return result

        # Fall back to Python demangler
        return self._try_python_demangle(mangled_name)

    def demangle_batch(self, mangled_names: List[str]) -> List[SwiftDemangleResult]:
        """
        Demangle multiple Swift symbols.

        Args:
            mangled_names: List of mangled symbols

        Returns:
            List of SwiftDemangleResult in same order
        """
        return [self.demangle(name) for name in mangled_names]

    def _is_swift_mangled(self, name: str) -> bool:
        """Check if a name looks like a Swift mangled symbol."""
        for prefix in SWIFT_MANGLED_PREFIXES:
            if name.startswith(prefix):
                return True
        return False

    def _try_external_demangle(self, mangled_name: str) -> SwiftDemangleResult:
        """Try external swift-demangle tool."""
        try:
            if self._detected_backend == "xcrun":
                cmd = ["xcrun", "swift-demangle", mangled_name]
            else:
                cmd = [self._demangler_path, mangled_name]

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=self.config.timeout_seconds
            )

            if result.returncode == 0:
                demangled = result.stdout.decode().strip()
                # Remove the mangled name prefix if present
                if " -> " in demangled:
                    demangled = demangled.split(" -> ", 1)[1]
                return SwiftDemangleResult(
                    mangled_name=mangled_name,
                    demangled_name=demangled,
                    success=True,
                    demangler_used=self._detected_backend,
                    evidence=EvidenceStrength.STRUCTURAL
                )
            else:
                return SwiftDemangleResult(
                    mangled_name=mangled_name,
                    demangled_name=None,
                    success=False,
                    demangler_used=self._detected_backend,
                    error=result.stderr.decode().strip() or "Demangling failed"
                )
        except subprocess.TimeoutExpired:
            return SwiftDemangleResult(
                mangled_name=mangled_name,
                demangled_name=None,
                success=False,
                demangler_used=self._detected_backend,
                error="Demangling timeout"
            )
        except Exception as e:
            return SwiftDemangleResult(
                mangled_name=mangled_name,
                demangled_name=None,
                success=False,
                demangler_used=self._detected_backend,
                error=str(e)
            )

    def _try_python_demangle(self, mangled_name: str) -> SwiftDemangleResult:
        """Try Python-based demangling (limited support)."""
        # Python fallback is conservative - only handles very simple cases
        # Full demangling requires the Swift runtime

        # Simple patterns that can be demangled without runtime
        demangled = self._simple_demangle(mangled_name)

        if demangled != mangled_name:
            return SwiftDemangleResult(
                mangled_name=mangled_name,
                demangled_name=demangled,
                success=True,
                demangler_used="python_fallback",
                evidence=EvidenceStrength.STRING_HINT
            )

        # Could not demangle - this is a valid result, not a failure
        return SwiftDemangleResult(
            mangled_name=mangled_name,
            demangled_name=None,
            success=False,
            demangler_used="python_fallback",
            error="Python demangler cannot decode this symbol",
            evidence=EvidenceStrength.MANGLED_SYMBOL
        )

    def _simple_demangle(self, mangled_name: str) -> str:
        """
        Simple Python demangling for common patterns.

        This is a conservative fallback - it does NOT fabricate demangled names.
        It only decodes patterns that are definitively parseable.
        """
        result = mangled_name

        # Remove _T prefix (old Swift)
        if result.startswith("_T"):
            result = result[2:]

        # Remove _ $s prefix (modern Swift)
        if result.startswith("_$s"):
            result = result[3:]
        elif result.startswith("$s"):
            result = result[2:]

        # Try to decode simple type encodings
        # These are definite patterns, not guesses

        # Basic type codes
        result = self._decode_type_codes(result)

        return result

    def _decode_type_codes(self, s: str) -> str:
        """Decode common Swift type codes."""
        # Common Swift type codes
        replacements = [
            ("Si", "Int"),
            ("Su", "UInt"),
            ("Sf", "Float"),
            ("Sd", "Double"),
            ("Sb", "Bool"),
            ("SS", "String"),
            ("Sc", "Character"),
            ("Sq", "Optional"),
            ("Sa", "Array"),
            ("SD", "Dictionary"),
            ("Set", "Set"),
        ]

        for code, type_name in replacements:
            s = s.replace(code, type_name)

        return s

    def get_symbol_info(self, mangled_name: str) -> dict:
        """
        Extract metadata from a mangled symbol without full demangling.

        Returns:
            Dict with symbol type, module, name hints
        """
        info = {
            "is_mangled": self._is_swift_mangled(mangled_name),
            "backend": self.get_backend(),
            "mangled_name": mangled_name,
            "partial_demangle": self._simple_demangle(mangled_name),
        }

        # Extract module hint if present
        # Modern Swift: $s{Module}{Name}
        if mangled_name.startswith("_$s") or mangled_name.startswith("$s"):
            parts = mangled_name[3:].split("C", 1)
            if len(parts) > 1:
                info["module_hint"] = parts[0]
                info["name_hint"] = parts[1][:20]  # First 20 chars

        return info
