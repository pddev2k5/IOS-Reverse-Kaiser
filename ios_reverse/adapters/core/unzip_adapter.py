"""
Unzip Adapter for IOS REVERSE KAISER.

Provides IPA extraction using the `unzip` command.
"""

from typing import Tuple, Optional, List
import os
import shutil

from ..base import SubprocessAdapter, AdapterResult


class UnzipAdapter(SubprocessAdapter):
    """
    Adapter for the `unzip` command.

    Primary adapter for IPA extraction.
    Falls back to Python zipfile if unzip is unavailable.
    """

    def __init__(self):
        super().__init__(
            command="unzip",
            required=False,  # Can fallback to Python
            min_version="6.0",
            version_flag="-v",
            version_pattern=r"UnZip [0-9.]+"
        )

    def validate_ipa(self, path: str) -> AdapterResult:
        """
        Validate that a file is a valid IPA archive.

        Args:
            path: Path to IPA file

        Returns:
            AdapterResult with:
            - is_valid: bool
            - errors: List of validation errors
            - warnings: List of warnings
        """
        errors = []
        warnings = []

        if not os.path.exists(path):
            return AdapterResult(
                success=False,
                error="File not found"
            )

        # Check if it's a valid zip
        try:
            result = self.run("-t", path)
        except Exception as e:
            # Tool execution failed - archive is likely corrupt
            return AdapterResult(
                success=False,
                error=f"Archive validation failed: {str(e)}",
                metadata={
                    "is_valid": False,
                    "errors": [f"Archive validation failed: {str(e)}"],
                    "warnings": warnings
                }
            )

        if not result.success:
            # Try to extract error message
            errors.append(f"Invalid zip archive: {result.stderr or 'test failed'}")

            # Fallback to Python zipfile
            return self._validate_with_python(path, errors, warnings)

        # Check for required contents
        list_result = self.run("-l", path)
        if list_result.success:
            contents = list_result.stdout

            # Check for Payload directory
            if "Payload/" not in contents and "Payload\\" not in contents:
                warnings.append("No Payload directory found")

        return AdapterResult(
            success=len(errors) == 0,
            stdout=result.stdout,
            stderr=list_result.stderr if not list_result.success else "",
            artifacts=[],
            metadata={
                "is_valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings
            },
            error=errors[0] if errors else None
        )

    def unpack(
        self,
        ipa_path: str,
        output_dir: str,
        overwrite: bool = False
    ) -> AdapterResult:
        """
        Extract IPA contents.

        Args:
            ipa_path: Path to IPA file
            output_dir: Output directory
            overwrite: Overwrite existing files

        Returns:
            AdapterResult with:
            - artifacts: List of extracted paths
            - metadata: Extraction statistics
        """
        if not os.path.exists(ipa_path):
            return AdapterResult(
                success=False,
                error=f"IPA not found: {ipa_path}"
            )

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Build command
        args = []
        if overwrite:
            args.append("-o")
        args.extend(["-q", ipa_path, "-d", output_dir])

        # Run unzip
        result = self.run(*args)

        if result.success:
            # Count extracted files
            file_count = sum(
                len(files)
                for _, _, files in os.walk(output_dir)
            )

            return AdapterResult(
                success=True,
                stdout=result.stdout,
                artifacts=[output_dir],
                metadata={
                    "output_dir": output_dir,
                    "files_extracted": file_count,
                    "total_size_bytes": self._dir_size(output_dir)
                }
            )
        else:
            # Check if partial extraction occurred
            if os.path.exists(output_dir):
                file_count = sum(
                    len(files)
                    for _, _, files in os.walk(output_dir)
                )
                if file_count > 0:
                    return AdapterResult(
                        success=False,
                        stderr=result.stderr,
                        artifacts=[output_dir],
                        metadata={
                            "output_dir": output_dir,
                            "files_extracted": file_count,
                            "partial": True,
                            "error": result.error
                        },
                        error=f"Extraction incomplete: {result.error}"
                    )

            return AdapterResult(
                success=False,
                stderr=result.stderr,
                error=f"Extraction failed: {result.error}"
            )

    def _validate_with_python(
        self,
        path: str,
        errors: List[str],
        warnings: List[str]
    ) -> AdapterResult:
        """Fallback validation using Python zipfile."""
        try:
            import zipfile
            with zipfile.ZipFile(path, 'r') as zf:
                # Test integrity
                bad_file = zf.testzip()
                if bad_file:
                    errors.append(f"Corrupt file in archive: {bad_file}")

                # Check for Payload
                names = zf.namelist()
                has_payload = any("Payload/" in n or "Payload\\" in n for n in names)
                if not has_payload:
                    warnings.append("No Payload directory found")

                return AdapterResult(
                    success=len(errors) == 0,
                    artifacts=[],
                    metadata={
                        "is_valid": len(errors) == 0,
                        "errors": errors,
                        "warnings": warnings,
                        "validated_with": "python_zipfile"
                    },
                    error=errors[0] if errors else None
                )
        except Exception as e:
            errors.append(f"Python zipfile validation failed: {e}")
            return AdapterResult(
                success=False,
                artifacts=[],
                metadata={
                    "is_valid": False,
                    "errors": errors,
                    "warnings": warnings
                },
                error=errors[0]
            )

    def _dir_size(self, path: str) -> int:
        """Calculate total size of directory."""
        total = 0
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total += os.path.getsize(fp)
        return total
