"""
File Adapter for IOS REVERSE KAISER.

Provides artifact type detection using the `file` command.
"""

from typing import Tuple, Optional, Dict, Any
import os
import shutil

from ..base import SubprocessAdapter, AdapterResult


class FileAdapter(SubprocessAdapter):
    """
    Adapter for the `file` command.

    Used for artifact type detection.
    """

    def __init__(self):
        super().__init__(
            command="file",
            required=True,
            min_version="5.0",
            version_flag="--version",
            version_pattern=r"file-([0-9.]+)"
        )

    def detect_type(self, path: str) -> AdapterResult:
        """
        Detect artifact type.

        Args:
            path: Path to file

        Returns:
            AdapterResult with:
            - artifact_type: ipa, app_bundle, macho, framework, dylib, unknown
            - mime_type: MIME type string
            - description: file description
        """
        if not os.path.exists(path):
            return AdapterResult(
                success=False,
                error=f"File not found: {path}"
            )

        if os.path.getsize(path) == 0:
            return AdapterResult(
                success=False,
                error="File is empty"
            )

        result = self.run("-b", "--mime-type", path)

        if not result.success:
            return AdapterResult(
                success=False,
                error=f"file command failed: {result.stderr}"
            )

        mime_type = result.stdout.strip()

        # Also get description
        desc_result = self.run("-b", path)
        description = desc_result.stdout.strip() if desc_result.success else ""

        # Classify artifact type
        artifact_type = self._classify_artifact(path, mime_type, description)

        return AdapterResult(
            success=True,
            stdout=result.stdout,
            artifacts=[],
            metadata={
                "artifact_type": artifact_type,
                "mime_type": mime_type,
                "description": description,
                "path": path,
                "size_bytes": os.path.getsize(path)
            }
        )

    def _classify_artifact(
        self,
        path: str,
        mime_type: str,
        description: str
    ) -> str:
        """Classify artifact type from file info."""
        # Check by extension first
        lower_path = path.lower()

        if lower_path.endswith('.ipa'):
            return "ipa"
        if lower_path.endswith('.app'):
            return "app_bundle"
        if lower_path.endswith('.framework'):
            return "framework"
        if lower_path.endswith('.dylib'):
            return "dylib"
        if lower_path.endswith('.appex'):
            return "extension"
        if lower_path.endswith('.a'):
            return "static_library"
        if lower_path.endswith('.plist') or lower_path.endswith('.entitlements'):
            return "plist"

        # Check by content
        if "Mach-O" in description:
            return "macho"
        if "Mach-O" in description and "executable" in description:
            return "macho_executable"
        if "Zip" in description:
            # Could be IPA or something else
            if mime_type == "application/zip":
                return "ipa"  # Assume IPA for .zip with .ipa content
            return "zip_archive"

        if "Mach-O" not in description and "Zip" not in description:
            # Try to detect by structure
            try:
                with open(path, 'rb') as f:
                    header = f.read(4)
                    # Check for Mach-O magic
                    if header in (b'\xfe\xed\xfa\xce', b'\xce\xfa\xed\xfe',  # 32-bit
                                  b'\xfe\xed\xfa\xcf', b'\xcf\xfa\xed\xfe',  # 64-bit
                                  b'\xca\xfe\xba\xbe', b'\xbe\xba\xfe\xca'):  # Fat
                        return "macho"
            except Exception:
                pass

        return "unknown"
