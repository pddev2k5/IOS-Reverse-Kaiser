"""
Otool Adapter for IOS REVERSE KAISER.

macOS-only adapter for Mach-O analysis using otool.
"""

from typing import Optional, Dict, Any
import subprocess
import shutil
import os

from ..base import SubprocessAdapter, AdapterResult


class OtoolAdapter(SubprocessAdapter):
    """
    Adapter for Apple's otool command.

    macOS only. Use MachOParserAdapter on other platforms.
    """

    def __init__(self):
        super().__init__(
            command="otool",
            required=False,  # Optional - parser is preferred
            min_version=None,
            version_flag="-v"
        )

    def get_load_commands(self, path: str) -> AdapterResult:
        """
        Get load commands from Mach-O file.

        Args:
            path: Path to Mach-O file

        Returns:
            AdapterResult with load commands
        """
        if not self.is_available():
            return AdapterResult(
                success=False,
                error="otool is not available (macOS only)"
            )

        try:
            result = self.run("-hv", path)

            if not result.success:
                return AdapterResult(
                    success=False,
                    error=f"otool failed: {result.stderr}"
                )

            return AdapterResult(
                success=True,
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
                metadata={
                    "format": "otool_load_commands",
                    "path": path
                }
            )
        except Exception as e:
            return AdapterResult(
                success=False,
                error=str(e)
            )

    def get_dylibs(self, path: str) -> AdapterResult:
        """
        Get dynamic libraries from Mach-O file.

        Args:
            path: Path to Mach-O file

        Returns:
            AdapterResult with dylib list
        """
        if not self.is_available():
            return AdapterResult(
                success=False,
                error="otool is not available (macOS only)"
            )

        try:
            result = self.run("-L", path)

            if not result.success:
                return AdapterResult(
                    success=False,
                    error=f"otool failed: {result.stderr}"
                )

            # Parse library names
            libraries = []
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line and not line.startswith('('):
                    libraries.append(line)

            return AdapterResult(
                success=True,
                stdout=result.stdout,
                metadata={
                    "format": "otool_dylibs",
                    "libraries": libraries,
                    "path": path
                }
            )
        except Exception as e:
            return AdapterResult(
                success=False,
                error=str(e)
            )

    def get_segments(self, path: str) -> AdapterResult:
        """
        Get segment information.

        Args:
            path: Path to Mach-O file

        Returns:
            AdapterResult with segments
        """
        if not self.is_available():
            return AdapterResult(
                success=False,
                error="otool is not available (macOS only)"
            )

        try:
            result = self.run("-lv", path)

            if not result.success:
                return AdapterResult(
                    success=False,
                    error=f"otool failed: {result.stderr}"
                )

            return AdapterResult(
                success=True,
                stdout=result.stdout,
                metadata={
                    "format": "otool_segments",
                    "path": path
                }
            )
        except Exception as e:
            return AdapterResult(
                success=False,
                error=str(e)
            )

    def get_header(self, path: str) -> AdapterResult:
        """
        Get Mach-O header.

        Args:
            path: Path to Mach-O file

        Returns:
            AdapterResult with header
        """
        if not self.is_available():
            return AdapterResult(
                success=False,
                error="otool is not available (macOS only)"
            )

        try:
            result = self.run("-h", path)

            if not result.success:
                return AdapterResult(
                    success=False,
                    error=f"otool failed: {result.stderr}"
                )

            return AdapterResult(
                success=True,
                stdout=result.stdout,
                metadata={
                    "format": "otool_header",
                    "path": path
                }
            )
        except Exception as e:
            return AdapterResult(
                success=False,
                error=str(e)
            )
