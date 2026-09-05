"""
Extension inventory adapter for IOS REVERSE KAISER.

Discovers and normalizes application extensions (.appex bundles).
"""

import os
import plistlib
import hashlib
from typing import Dict, Any, Optional, List, Set, Tuple

from ios_reverse.models.components import (
    ComponentType, ExtensionComponent, ExecutableIdentity, ArchitectureInfo,
    ComponentGraph, generate_component_id
)
from ios_reverse.adapters.base import ToolAdapter, ToolInfo, AdapterResult
from ios_reverse.adapters.components.base import ComponentTraversal, TraversalContext


class ExtensionAdapter(ToolAdapter):
    """
    Adapter for discovering application extensions.

    Handles various extension types:
    - Widgets
    - Share extensions
    - Notification extensions
    - Intents
    - Keyboard extensions
    - Other extension points
    """

    def __init__(self):
        super().__init__("extension_adapter", "1.0.0")
        self._id_counter = 0

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="extension_adapter",
            path="internal",
            version="1.0.0"
        )

    def validate_environment(self) -> Tuple[bool, Optional[str]]:
        return True, None

    def execute(self, command, cwd=None, env=None, input_data=None):
        return AdapterResult(success=True, stdout="Pure Python adapter")

    def is_available(self) -> bool:
        return True

    def discover_extensions(
        self,
        base_path: str,
        context: Optional[TraversalContext] = None,
        parent_id: Optional[str] = None
    ) -> List[ExtensionComponent]:
        """
        Discover extension bundles in a path.

        Args:
            base_path: Path to search for extensions
            context: Optional traversal context
            parent_id: Parent component ID

        Returns:
            List of ExtensionComponent
        """
        if context is None:
            context = TraversalContext(
                root_path=base_path,
                visited_paths=set(),
                visited_artifacts=set()
            )

        extensions = []

        # Check PlugIns directory
        plugins_dir = os.path.join(base_path, "PlugIns")
        if os.path.isdir(plugins_dir):
            for entry in os.listdir(plugins_dir):
                if entry.endswith(".appex"):
                    ext_path = os.path.join(plugins_dir, entry)
                    if context.mark_visited(ext_path):
                        rel_path = os.path.join("PlugIns", entry)
                        extension = self._parse_extension(
                            ext_path, rel_path, context, parent_id
                        )
                        if extension:
                            extensions.append(extension)

        # Also check Frameworks for extensions (rare but possible)
        frameworks_dir = os.path.join(base_path, "Frameworks")
        if os.path.isdir(frameworks_dir):
            for entry in os.listdir(frameworks_dir):
                if entry.endswith(".appex"):
                    ext_path = os.path.join(frameworks_dir, entry)
                    if context.mark_visited(ext_path):
                        rel_path = os.path.join("Frameworks", entry)
                        extension = self._parse_extension(
                            ext_path, rel_path, context, parent_id
                        )
                        if extension:
                            extensions.append(extension)

        return extensions

    def _parse_extension(
        self,
        extension_path: str,
        bundle_path: str,
        context: TraversalContext,
        parent_id: Optional[str]
    ) -> Optional[ExtensionComponent]:
        """
        Parse an extension bundle into an ExtensionComponent.
        """
        if not os.path.isdir(extension_path):
            return None

        ext_name = os.path.basename(extension_path).replace('.appex', '')

        # Compute artifact ID
        artifact_id = self._compute_bundle_artifact_id(extension_path)
        if not artifact_id:
            return None

        if not context.mark_artifact_visited(artifact_id):
            return None

        # Generate component ID
        component_id = generate_component_id(ext_name, artifact_id, bundle_path)

        # Parse Info.plist
        info_plist_path = os.path.join(extension_path, "Info.plist")
        bundle_identifier = None
        extension_point = None
        version = None
        entitlements_path = None

        if os.path.exists(info_plist_path):
            try:
                with open(info_plist_path, 'rb') as f:
                    plist = plistlib.load(f)
                    bundle_identifier = plist.get("CFBundleIdentifier")
                    version = plist.get("CFBundleVersion")
                    extension_point = plist.get("NSExtension", {}).get("NSExtensionPointIdentifier")
            except Exception:
                pass

        # Find executable
        executable = self._find_extension_executable(extension_path, artifact_id)

        return ExtensionComponent(
            component_id=component_id,
            component_type=ComponentType.EXTENSION,
            name=ext_name,
            bundle_path=bundle_path,
            artifact_id=artifact_id,
            bundle_identifier=bundle_identifier,
            extension_point=extension_point,
            version=version,
            executable=executable,
            info_plist_path="Info.plist",
            entitlements_path=entitlements_path,
            parent_component_id=parent_id,
            provenance=["filesystem_discovery", "info_plist"],
        )

    def _compute_bundle_artifact_id(self, bundle_path: str) -> Optional[str]:
        """Compute artifact ID for a bundle."""
        hasher = hashlib.sha256()
        hasher.update(bundle_path.encode())

        info_path = os.path.join(bundle_path, "Info.plist")
        if os.path.exists(info_path):
            try:
                with open(info_path, 'rb') as f:
                    hasher.update(f.read())
            except Exception:
                pass

        return hasher.hexdigest()

    def _find_extension_executable(
        self,
        extension_path: str,
        bundle_artifact_id: str
    ) -> Optional[ExecutableIdentity]:
        """
        Find the executable within an extension bundle.
        """
        ext_name = os.path.basename(extension_path).replace('.appex', '')

        # Common locations
        candidates = [
            os.path.join(extension_path, ext_name),
            os.path.join(extension_path, "MacOS", ext_name),
            os.path.join(extension_path, "Contents", "MacOS", ext_name),
        ]

        for candidate in candidates:
            if os.path.isfile(candidate):
                try:
                    with open(candidate, 'rb') as f:
                        data = f.read()
                        sha256 = hashlib.sha256(data).hexdigest()

                        archs = self._detect_architectures(data)

                        return ExecutableIdentity(
                            path=os.path.relpath(candidate, extension_path),
                            artifact_id=sha256,
                            sha256=sha256,
                            size=len(data),
                            architectures=archs,
                            is_fat=len(archs) > 1,
                            slice_count=len(archs)
                        )
                except Exception:
                    pass

        return None

    def _detect_architectures(self, data: bytes) -> List[ArchitectureInfo]:
        """Detect Mach-O architectures in binary data."""
        import struct

        archs = []
        if len(data) < 32:
            return archs

        magic = struct.unpack('<I', data[:4])[0]

        if magic == 0xfeedfacf:
            cputype = struct.unpack('<I', data[4:8])[0]
            if cputype == 0x0100000c:
                archs.append(ArchitectureInfo(0x0100000c, 0, "arm64", True))
            elif cputype == 0x01000007:
                archs.append(ArchitectureInfo(0x01000007, 0, "x86_64", True))

        return archs

    def get_extension_point_name(self, point_identifier: str) -> str:
        """
        Get human-readable name for an extension point.
        """
        point_names = {
            "com.apple.widget-extension": "Widget",
            "com.apple.share-extension": "Share Extension",
            "com.apple.notification-content-extension": "Notification Content",
            "com.apple.intents-service": "Intents Service",
            "com.apple.intents-extension": "Intents Extension",
            "com.apple.keyboard-service": "Keyboard",
            "com.apple.network-extension": "Network Extension",
            "com.apple.app-extension": "App Extension",
        }
        return point_names.get(point_identifier, point_identifier)
