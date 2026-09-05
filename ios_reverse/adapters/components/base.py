"""
Base component adapter for IOS REVERSE KAISER.

Provides common traversal and discovery utilities.
"""

import os
import hashlib
from typing import Dict, Any, Optional, List, Set, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod

from ios_reverse.models.components import (
    ComponentType, ArchitectureInfo, ExecutableIdentity,
    BaseComponent, AppComponent, ComponentGraph,
    generate_component_id
)
from ios_reverse.adapters.base import ToolAdapter, ToolInfo, AdapterResult


@dataclass
class TraversalContext:
    """Context for safe traversal."""
    root_path: str
    visited_paths: Set[str]  # Paths we've already traversed
    visited_artifacts: Set[str]  # Artifact IDs we've seen
    max_depth: int = 50
    current_depth: int = 0

    def should_continue(self) -> bool:
        """Check if we should continue traversal."""
        return self.current_depth < self.max_depth

    def mark_visited(self, path: str) -> bool:
        """
        Mark a path as visited. Returns True if first visit.
        """
        real_path = os.path.realpath(path) if os.path.exists(path) else path
        if real_path in self.visited_paths:
            return False
        self.visited_paths.add(real_path)
        return True

    def mark_artifact_visited(self, artifact_id: str) -> bool:
        """
        Mark an artifact as visited. Returns True if first visit.
        """
        if artifact_id in self.visited_artifacts:
            return False
        self.visited_artifacts.add(artifact_id)
        return True


class ComponentTraversal:
    """Safe component traversal utilities."""

    # Known system frameworks that should not be traversed
    SYSTEM_FRAMEWORKS = {
        "UIKit.framework",
        "Foundation.framework",
        "CoreFoundation.framework",
        "CoreGraphics.framework",
        "CoreText.framework",
        "CoreImage.framework",
        "QuartzCore.framework",
        "OpenGLES.framework",
        "Metal.framework",
        "MetalKit.framework",
        "AVFoundation.framework",
        "AudioToolbox.framework",
        "CoreMedia.framework",
        "CoreVideo.framework",
        "Security.framework",
        "System.framework",
        "libSystem.B.dylib",
        "libobjc.A.dylib",
    }

    # Known system paths
    SYSTEM_PATHS = {
        "/System/",
        "/usr/lib/",
        "/System/Library/Frameworks/",
    }

    @staticmethod
    def is_system_path(path: str) -> bool:
        """Check if a path refers to a system component."""
        for sys_path in ComponentTraversal.SYSTEM_PATHS:
            if sys_path in path:
                return True
        return False

    @staticmethod
    def is_system_framework(name: str) -> bool:
        """Check if a framework name is a known system framework."""
        return name in ComponentTraversal.SYSTEM_FRAMEWORKS

    @staticmethod
    def compute_artifact_id(file_path: str) -> Optional[str]:
        """Compute SHA-256 artifact ID for a file."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return None

    @staticmethod
    def compute_file_hash(file_path: str) -> Optional[str]:
        """Compute SHA-256 hash of a file."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return None

    @staticmethod
    def safe_join(root: str, *parts: str) -> Optional[str]:
        """
        Safely join paths, preventing directory traversal.
        """
        try:
            base = os.path.abspath(root)
            result = os.path.abspath(os.path.join(root, *parts))
            # Ensure result is within root
            if not result.startswith(base):
                return None
            return result
        except Exception:
            return None

    @staticmethod
    def discover_frameworks(base_path: str) -> List[str]:
        """
        Discover framework directories in a path.

        Returns list of relative paths to frameworks.
        """
        frameworks = []

        frameworks_dir = os.path.join(base_path, "Frameworks")
        if os.path.isdir(frameworks_dir):
            for entry in os.listdir(frameworks_dir):
                if entry.endswith(".framework"):
                    frameworks.append(os.path.join("Frameworks", entry))

        # Also check PlugIns for embedded frameworks
        plugins_dir = os.path.join(base_path, "PlugIns")
        if os.path.isdir(plugins_dir):
            for entry in os.listdir(plugins_dir):
                ext_path = os.path.join(base_path, "PlugIns", entry)
                if os.path.isdir(ext_path) and entry.endswith(".appex"):
                    nested_frameworks = ComponentTraversal.discover_frameworks(ext_path)
                    for fw in nested_frameworks:
                        frameworks.append(os.path.join("PlugIns", entry, fw))

        return frameworks

    @staticmethod
    def discover_dylibs(base_path: str) -> List[str]:
        """
        Discover embedded dylib files in a path.

        Returns list of relative paths to dylibs.
        """
        dylibs = []

        # Common locations for embedded dylibs
        search_dirs = [
            os.path.join(base_path, ""),  # Root
            os.path.join(base_path, "Frameworks"),
            os.path.join(base_path, "PlugIns"),
        ]

        for search_dir in search_dirs:
            if not os.path.isdir(search_dir):
                continue

            try:
                for entry in os.listdir(search_dir):
                    if entry.endswith((".dylib", ".so")):
                        if search_dir == base_path:
                            rel_path = entry
                        else:
                            rel_path = os.path.join(os.path.basename(search_dir), entry)
                        dylibs.append(rel_path)
            except PermissionError:
                pass

        return dylibs

    @staticmethod
    def discover_extensions(base_path: str) -> List[str]:
        """
        Discover extension bundles in a path.

        Returns list of relative paths to extensions.
        """
        extensions = []

        # Check PlugIns directory
        plugins_dir = os.path.join(base_path, "PlugIns")
        if os.path.isdir(plugins_dir):
            for entry in os.listdir(plugins_dir):
                if entry.endswith(".appex"):
                    extensions.append(os.path.join("PlugIns", entry))

        # Check for extensions in Frameworks (rare but possible)
        frameworks_dir = os.path.join(base_path, "Frameworks")
        if os.path.isdir(frameworks_dir):
            for entry in os.listdir(frameworks_dir):
                if entry.endswith(".appex"):
                    extensions.append(os.path.join("Frameworks", entry))

        return extensions

    @staticmethod
    def find_executable_in_bundle(bundle_path: str) -> Optional[str]:
        """
        Find the main executable in a bundle.

        Returns relative path to executable within bundle.
        """
        # Standard: executable has same name as bundle
        bundle_name = os.path.basename(bundle_path)
        base_name = bundle_name.rsplit('.', 1)[0]

        # Common executable locations
        candidates = [
            os.path.join(bundle_path, base_name),
            os.path.join(bundle_path, "MacOS", base_name),
            os.path.join(bundle_path, "Resources"),
        ]

        for candidate in candidates:
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate

        # Fallback: look for any executable in bundle
        for root, dirs, files in os.walk(bundle_path):
            for f in files:
                full_path = os.path.join(root, f)
                if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                    # Return relative path
                    try:
                        return os.path.relpath(full_path, bundle_path)
                    except ValueError:
                        pass

        return None

    @staticmethod
    def parse_install_name(name: str) -> Tuple[str, str, str]:
        """
        Parse an install name into components.

        Returns (type, path, name):
        - type: 'rpath', 'loader_path', 'executable_path', 'absolute', 'system', 'unknown'
        - path: The path portion
        - name: The library/component name
        """
        if name.startswith("@rpath/"):
            return ("rpath", name[7:], name[7:].rsplit('/', 1)[0] if '/' in name[7:] else "")
        elif name.startswith("@loader_path/"):
            return ("loader_path", name[13:], name[13:].rsplit('/', 1)[0] if '/' in name[13:] else "")
        elif name.startswith("@executable_path/"):
            return ("executable_path", name[16:], name[16:].rsplit('/', 1)[0] if '/' in name[16:] else "")
        elif name.startswith("/System/") or name.startswith("/usr/lib/"):
            return ("system", name, os.path.basename(name))
        elif name.startswith("/"):
            return ("absolute", name, os.path.basename(name))
        else:
            return ("unknown", name, os.path.basename(name))
