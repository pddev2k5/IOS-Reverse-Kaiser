"""
Nm Adapter for IOS REVERSE KAISER.

Symbol table analysis using nm command.
"""

from typing import Optional, Dict, Any, List
import subprocess
import shutil
import os

from ..base import SubprocessAdapter, AdapterResult


class NmAdapter(SubprocessAdapter):
    """
    Adapter for Apple's nm command.

    Symbol table analysis.
    """

    def __init__(self):
        super().__init__(
            command="nm",
            required=False,  # Optional
            min_version=None,
            version_flag="-V"
        )

    def get_symbols(self, path: str, format: str = "posix") -> AdapterResult:
        """
        Get symbol table from Mach-O file.

        Args:
            path: Path to Mach-O file
            format: Output format (posix, darwin, etc.)

        Returns:
            AdapterResult with symbols
        """
        if not self.is_available():
            return AdapterResult(
                success=False,
                error="nm is not available"
            )

        try:
            # Use -m for Mach-O specific output
            result = self.run("-m", path)

            if not result.success:
                # Try without -m
                result = self.run(path)

            return AdapterResult(
                success=True,
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
                metadata={
                    "format": "nm_symbols",
                    "path": path
                }
            )
        except Exception as e:
            return AdapterResult(
                success=False,
                error=str(e)
            )

    def get_defined_symbols(self, path: str) -> AdapterResult:
        """Get only defined symbols."""
        if not self.is_available():
            return AdapterResult(
                success=False,
                error="nm is not available"
            )

        try:
            # Defined symbols only
            result = self.run("-m", "-g", path)

            return AdapterResult(
                success=True,
                stdout=result.stdout,
                metadata={
                    "format": "nm_defined_symbols",
                    "path": path
                }
            )
        except Exception as e:
            return AdapterResult(
                success=False,
                error=str(e)
            )

    def get_undefined_symbols(self, path: str) -> AdapterResult:
        """Get only undefined symbols."""
        if not self.is_available():
            return AdapterResult(
                success=False,
                error="nm is not available"
            )

        try:
            # Undefined symbols only
            result = self.run("-m", "-u", path)

            return AdapterResult(
                success=True,
                stdout=result.stdout,
                metadata={
                    "format": "nm_undefined_symbols",
                    "path": path
                }
            )
        except Exception as e:
            return AdapterResult(
                success=False,
                error=str(e)
            )

    def get_imports(self, path: str) -> AdapterResult:
        """
        Get imported symbols (undefined, from dylibs).

        Args:
            path: Path to Mach-O file

        Returns:
            AdapterResult with imports
        """
        if not self.is_available():
            return AdapterResult(
                success=False,
                error="nm is not available"
            )

        try:
            # Undefined symbols = imports
            result = self.run("-m", "-u", path)

            if not result.success:
                return AdapterResult(
                    success=False,
                    error=f"nm failed: {result.stderr}"
                )

            # Parse imports
            imports = []
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line:
                    # nm -mu output format: [addr] [type] [name] ([library])
                    imports.append(line)

            return AdapterResult(
                success=True,
                stdout=result.stdout,
                metadata={
                    "format": "nm_imports",
                    "imports": imports,
                    "count": len(imports),
                    "path": path
                }
            )
        except Exception as e:
            return AdapterResult(
                success=False,
                error=str(e)
            )

    def get_exports(self, path: str) -> AdapterResult:
        """
        Get exported symbols.

        Args:
            path: Path to Mach-O file

        Returns:
            AdapterResult with exports
        """
        if not self.is_available():
            return AdapterResult(
                success=False,
                error="nm is not available"
            )

        try:
            # Exports on macOS use -X and filtering
            result = self.run("-m", "-g", path)

            if not result.success:
                return AdapterResult(
                    success=False,
                    error=f"nm failed: {result.stderr}"
                )

            exports = []
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line and ('[' in line or line.startswith('_')):
                    exports.append(line)

            return AdapterResult(
                success=True,
                stdout=result.stdout,
                metadata={
                    "format": "nm_exports",
                    "exports": exports,
                    "count": len(exports),
                    "path": path
                }
            )
        except Exception as e:
            return AdapterResult(
                success=False,
                error=str(e)
            )
