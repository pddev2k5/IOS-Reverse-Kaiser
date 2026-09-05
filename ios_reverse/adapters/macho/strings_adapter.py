"""
Strings Adapter for IOS REVERSE KAISER.

String extraction from binary files.
"""

from typing import Optional, List, Dict, Any, Generator
import subprocess
import os
import re

from ..base import SubprocessAdapter, AdapterResult


class StringsAdapter(SubprocessAdapter):
    """
    Adapter for the strings command.

    String extraction with offset and encoding info.
    """

    def __init__(self):
        super().__init__(
            command="strings",
            required=False,  # Optional - Python fallback available
            min_version=None,
            version_flag="-V"
        )

    def extract_strings(
        self,
        path: str,
        min_length: int = 4,
        include_offsets: bool = True,
        encoding: str = "ascii"
    ) -> AdapterResult:
        """
        Extract strings from binary.

        Args:
            path: Path to binary file
            min_length: Minimum string length
            include_offsets: Include file offsets
            encoding: Character encoding (ascii, utf8, etc.)

        Returns:
            AdapterResult with extracted strings
        """
        if self.is_available():
            return self._extract_with_tool(path, min_length, include_offsets)
        else:
            return self._extract_with_python(path, min_length, include_offsets)

    def _extract_with_tool(
        self,
        path: str,
        min_length: int,
        include_offsets: bool
    ) -> AdapterResult:
        """Extract using strings command."""
        try:
            args = []

            # Minimum length
            args.extend(["-n", str(min_length)])

            # Include offsets
            if include_offsets:
                args.append("-t")

            # Encoding
            if encoding == "ascii":
                args.append("-e", "s")  # Single-byte characters

            args.append(path)

            result = self.run(*args)

            if not result.success:
                return AdapterResult(
                    success=False,
                    error=f"strings failed: {result.stderr}"
                )

            # Parse output
            strings = []
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line:
                    parts = line.split(None, 1)
                    if len(parts) == 2:
                        strings.append({
                            "offset": parts[0],
                            "value": parts[1]
                        })
                    else:
                        strings.append({
                            "offset": "",
                            "value": line
                        })

            return AdapterResult(
                success=True,
                stdout=result.stdout,
                metadata={
                    "format": "strings_tool",
                    "strings": strings,
                    "count": len(strings),
                    "path": path,
                    "min_length": min_length,
                    "method": "tool"
                }
            )
        except Exception as e:
            return AdapterResult(
                success=False,
                error=str(e)
            )

    def _extract_with_python(
        self,
        path: str,
        min_length: int,
        include_offsets: bool
    ) -> AdapterResult:
        """Extract using Python (fallback)."""
        try:
            strings = []
            current_string = bytearray()
            offset = 0

            with open(path, 'rb') as f:
                while True:
                    byte = f.read(1)
                    if not byte:
                        break

                    byte_val = byte[0]

                    # ASCII printable range
                    if 0x20 <= byte_val <= 0x7E:
                        current_string.append(byte_val)
                        offset += 1
                    else:
                        if len(current_string) >= min_length:
                            str_val = current_string.decode('ascii', errors='replace')
                            if include_offsets:
                                strings.append({
                                    "offset": hex(offset - len(current_string)),
                                    "value": str_val
                                })
                            else:
                                strings.append({
                                    "value": str_val
                                })
                        current_string = bytearray()
                        offset += 1

            return AdapterResult(
                success=True,
                metadata={
                    "format": "strings_python",
                    "strings": strings,
                    "count": len(strings),
                    "path": path,
                    "min_length": min_length,
                    "method": "python"
                }
            )
        except Exception as e:
            return AdapterResult(
                success=False,
                error=str(e)
            )

    def extract_urls(self, path: str) -> AdapterResult:
        """
        Extract URLs from binary.

        Args:
            path: Path to binary file

        Returns:
            AdapterResult with URLs
        """
        result = self.extract_strings(path, min_length=7)

        if not result.success:
            return result

        urls = []
        url_pattern = re.compile(
            rb'https?://[^\s<>"{}|\\^`\[\]]+',
            re.IGNORECASE
        )

        try:
            with open(path, 'rb') as f:
                data = f.read()

            matches = url_pattern.findall(data)
            for match in matches:
                try:
                    urls.append(match.decode('utf-8', errors='replace'))
                except:
                    pass

            # Remove duplicates while preserving order
            seen = set()
            unique_urls = []
            for url in urls:
                if url not in seen:
                    seen.add(url)
                    unique_urls.append(url)

            return AdapterResult(
                success=True,
                metadata={
                    "format": "strings_urls",
                    "urls": unique_urls,
                    "count": len(unique_urls),
                    "path": path
                }
            )
        except Exception as e:
            return AdapterResult(
                success=False,
                error=str(e)
            )

    def extract_domains(self, path: str) -> AdapterResult:
        """
        Extract domain names from binary.

        Args:
            path: Path to binary file

        Returns:
            AdapterResult with domains
        """
        result = self.extract_strings(path, min_length=4)

        if not result.success:
            return result

        domains = set()

        # Domain pattern
        domain_pattern = re.compile(
            rb'[a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,}'
        )

        try:
            with open(path, 'rb') as f:
                data = f.read()

            matches = domain_pattern.findall(data)
            for match in matches:
                try:
                    domains.add(match.decode('ascii', errors='replace'))
                except:
                    pass

            return AdapterResult(
                success=True,
                metadata={
                    "format": "strings_domains",
                    "domains": list(domains),
                    "count": len(domains),
                    "path": path
                }
            )
        except Exception as e:
            return AdapterResult(
                success=False,
                error=str(e)
            )
