"""
Codesign Adapter for IOS REVERSE KAISER.

Provides entitlements extraction using the `codesign` command.
"""

from typing import Tuple, Optional, Dict, Any
import os
import json

from ..base import SubprocessAdapter, AdapterResult


class CodesignAdapter(SubprocessAdapter):
    """
    Adapter for the `codesign` command.

    Used for extracting code signing entitlements.
    """

    def __init__(self):
        super().__init__(
            command="codesign",
            required=True,  # macOS only
            min_version="1.0",
            version_flag="-d",  # Display version info
            version_pattern=None
        )

    def validate_environment(self) -> Tuple[bool, Optional[str]]:
        """Validate codesign is available (macOS only)."""
        import platform
        if platform.system() != "Darwin":
            return False, "codesign is only available on macOS"
        return super().validate_environment()

    def extract_entitlements(self, artifact_path: str) -> AdapterResult:
        """
        Extract code signing entitlements from an artifact.

        Args:
            artifact_path: Path to Mach-O binary or bundle

        Returns:
            AdapterResult with:
            - entitlements: Entitlement dictionary
            - entitlement_keys: List of keys
            - has_keychain_access: bool
            - has_network_access: bool
            - has_app_groups: bool
        """
        if not os.path.exists(artifact_path):
            return AdapterResult(
                success=False,
                error=f"Artifact not found: {artifact_path}"
            )

        # If it's a bundle, find the executable
        if artifact_path.endswith('.app'):
            executable = os.path.join(artifact_path, artifact_path.split('/')[-1].replace('.app', ''))
            if not os.path.exists(executable):
                # Try .app/Contents/MacOS/<name>
                executable = os.path.join(artifact_path, "Contents", "MacOS")
                if os.path.exists(executable):
                    files = os.listdir(executable)
                    if files:
                        executable = os.path.join(executable, files[0])
            if not os.path.exists(executable):
                return AdapterResult(
                    success=False,
                    error=f"Executable not found in bundle: {artifact_path}"
                )
        else:
            executable = artifact_path

        # Extract entitlements
        result = self.run("-d", "entitlements", "-", executable)

        if not result.success:
            return AdapterResult(
                success=False,
                error=f"Failed to extract entitlements: {result.stderr}"
            )

        # Parse entitlements
        entitlements = self._parse_entitlements(result.stdout)

        return AdapterResult(
            success=True,
            stdout=result.stdout,
            artifacts=[],
            metadata={
                "entitlements": entitlements,
                "entitlement_keys": list(entitlements.keys()) if entitlements else [],
                "has_keychain_access": self._check_keychain(entitlements),
                "has_network_access": self._check_network(entitlements),
                "has_app_groups": "com.apple.security.application-groups" in entitlements,
                "executable": executable
            }
        )

    def _parse_entitlements(self, output: str) -> Dict[str, Any]:
        """Parse entitlements from output."""
        entitlements = {}

        try:
            # Try to parse as XML plist
            import plistlib
            from io import BytesIO
            entitlements = plistlib.loads(output.encode('utf-8'))
        except Exception:
            # Try to parse as text
            current_key = None
            current_value = []

            for line in output.split('\n'):
                line = line.strip()
                if not line:
                    continue

                if '=' in line:
                    if current_key:
                        # Save previous
                        value_str = ''.join(current_value).strip()
                        entitlements[current_key] = self._parse_value(value_str)
                    current_key = line.split('=')[0].strip()
                    current_value = [line.split('=', 1)[1].strip()]
                else:
                    current_value.append(line)

            # Don't forget last entry
            if current_key:
                value_str = ''.join(current_value).strip()
                entitlements[current_key] = self._parse_value(value_str)

        return entitlements

    def _parse_value(self, value_str: str) -> Any:
        """Parse entitlement value."""
        value_str = value_str.strip()

        if value_str == '(':
            return []

        if value_str.startswith('(') or value_str.startswith('{'):
            # Array or dict
            items = []
            depth = 0
            current = ""

            for char in value_str:
                if char in '({':
                    depth += 1
                if char in ')}':
                    depth -= 1
                if char == ',' and depth == 0:
                    items.append(current.strip().strip('"').strip("'"))
                    current = ""
                else:
                    current += char

            if current.strip():
                items.append(current.strip().strip('"').strip("'"))

            return [i for i in items if i]

        if value_str in ('true', 'false'):
            return value_str == 'true'

        if value_str.isdigit():
            return int(value_str)

        return value_str.strip('"').strip("'")

    def _check_keychain(self, entitlements: Dict) -> bool:
        """Check if entitlements include keychain access."""
        keychain_keys = [
            'keychain-access-groups',
            'keychain-permission-flags',
        ]
        return any(k in entitlements for k in keychain_keys)

    def _check_network(self, entitlements: Dict) -> bool:
        """Check if entitlements include network access."""
        network_keys = [
            'com.apple.security.network.client',
            'com.apple.security.network.server',
            'com.apple.security.application-groups',  # Often used for network
        ]
        return any(k in entitlements for k in network_keys)
