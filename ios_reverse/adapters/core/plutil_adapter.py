"""
Plutil Adapter for IOS REVERSE KAISER.

Provides plist parsing using the `plutil` command.
"""

from typing import Tuple, Optional, Dict, Any
import os
import json

from ..base import SubprocessAdapter, AdapterResult


class PlutilAdapter(SubprocessAdapter):
    """
    Adapter for the `plutil` command.

    Used for parsing Info.plist and entitlements files.
    """

    def __init__(self):
        super().__init__(
            command="plutil",
            required=True,  # macOS only
            min_version="1.0",
            version_flag="-help",
            version_pattern=None  # plutil doesn't have version flag
        )

    def validate_environment(self) -> Tuple[bool, Optional[str]]:
        """Validate plutil is available (macOS only)."""
        import platform
        if platform.system() != "Darwin":
            return False, "plutil is only available on macOS"
        return super().validate_environment()

    def parse_plist(self, plist_path: str) -> AdapterResult:
        """
        Parse a plist file to JSON.

        Args:
            plist_path: Path to plist file

        Returns:
            AdapterResult with:
            - plist_data: Parsed plist as dict
            - format: binary, xml, or json
        """
        if not os.path.exists(plist_path):
            return AdapterResult(
                success=False,
                error=f"Plist not found: {plist_path}"
            )

        # First, convert to XML/JSON to determine format
        result = self.run("-convert", "xml1", "-o", "-", plist_path)

        if not result.success:
            return AdapterResult(
                success=False,
                error=f"Failed to convert plist: {result.stderr}"
            )

        # Now parse to JSON
        json_result = self.run("-convert", "json", "-o", "-", plist_path)

        if not json_result.success:
            # Fallback: parse XML output
            return AdapterResult(
                success=False,
                error=f"Failed to parse plist to JSON: {json_result.stderr}"
            )

        try:
            # Parse JSON output
            json_str = json_result.stdout.strip()
            if json_str.startswith('{') or json_str.startswith('['):
                plist_data = json.loads(json_str)
            else:
                # Empty or invalid JSON
                plist_data = {}

            return AdapterResult(
                success=True,
                stdout=json_str,
                artifacts=[],
                metadata={
                    "plist_data": plist_data,
                    "format": "json",
                    "path": plist_path,
                    "raw_xml": result.stdout if result.success else None
                }
            )
        except json.JSONDecodeError as e:
            return AdapterResult(
                success=False,
                error=f"Failed to parse JSON: {e}"
            )

    def extract_info(self, bundle_path: str) -> AdapterResult:
        """
        Extract Info.plist from a bundle.

        Args:
            bundle_path: Path to bundle (.app, .framework, etc.)

        Returns:
            AdapterResult with plist data
        """
        info_plist_path = os.path.join(bundle_path, "Info.plist")

        if not os.path.exists(info_plist_path):
            return AdapterResult(
                success=False,
                error=f"Info.plist not found in bundle: {bundle_path}"
            )

        return self.parse_plist(info_plist_path)

    def extract_value(
        self,
        plist_path: str,
        key: str
    ) -> AdapterResult:
        """
        Extract a specific value from a plist.

        Args:
            plist_path: Path to plist file
            key: Key to extract

        Returns:
            AdapterResult with extracted value
        """
        # First parse the plist
        parse_result = self.parse_plist(plist_path)

        if not parse_result.success:
            return parse_result

        # Extract value
        plist_data = parse_result.metadata.get("plist_data", {})
        value = plist_data.get(key)

        return AdapterResult(
            success=True,
            artifacts=[],
            metadata={
                "key": key,
                "value": value,
                "type": type(value).__name__ if value is not None else "none"
            }
        )
