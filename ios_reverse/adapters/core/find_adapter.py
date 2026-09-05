"""
Find Adapter for IOS REVERSE KAISER.

Provides file enumeration using the `find` command.
"""

from typing import Tuple, Optional, List, Dict, Any
import os
import subprocess

from ..base import SubprocessAdapter, AdapterResult


class FindAdapter(SubprocessAdapter):
    """
    Adapter for the `find` command.

    Used for bundle inventory and file enumeration.
    Falls back to Python os.walk when find is unavailable.
    """

    def __init__(self):
        super().__init__(
            command="find",
            required=False,  # Falls back to Python
            min_version="4.0",
            version_flag="-version",
            version_pattern=None  # find doesn't have standard version
        )

    def inventory_directory(
        self,
        directory: str,
        max_depth: Optional[int] = None,
        file_types: Optional[List[str]] = None
    ) -> AdapterResult:
        """
        Inventory a directory.

        Args:
            directory: Directory to inventory
            max_depth: Maximum depth to traverse
            file_types: File extensions to include (e.g., ['.dylib', '.framework'])

        Returns:
            AdapterResult with:
            - files: List of file paths
            - directories: List of directory paths
            - file_count: Total file count
            - total_size: Total size in bytes
        """
        if not os.path.exists(directory):
            return AdapterResult(
                success=False,
                error=f"Directory not found: {directory}"
            )

        if not os.path.isdir(directory):
            return AdapterResult(
                success=False,
                error=f"Not a directory: {directory}"
            )

        # Try find command first
        try:
            result = self._inventory_with_find(directory, max_depth, file_types)
            if result.success:
                return result
        except Exception:
            pass

        # Fall back to Python os.walk
        return self._inventory_with_python(directory, max_depth, file_types)

    def _inventory_with_find(
        self,
        directory: str,
        max_depth: Optional[int],
        file_types: Optional[List[str]]
    ) -> AdapterResult:
        """Inventory using find command."""
        # Build find command
        args = [directory]

        if max_depth:
            args.extend(["-maxdepth", str(max_depth)])

        args.append("-type")
        args.append("f")

        # Add file type filter if specified
        if file_types:
            name_args = []
            for ft in file_types:
                ext = ft if ft.startswith('.') else f'.{ft}'
                name_args.extend(["-name", f"*{ext}"])
            if name_args:
                args.extend(["(",] + name_args + [")"])

        result = self.run(*args)

        if not result.success:
            raise Exception(f"find command failed: {result.stderr}")

        # Parse output
        files = [f.strip() for f in result.stdout.split('\n') if f.strip()]

        # Get directory listing too
        dir_result = self.run(directory, "-type", "d")
        directories = [d.strip() for d in dir_result.stdout.split('\n') if d.strip()] if dir_result.success else []

        # Calculate statistics
        total_size = 0
        file_type_counts: Dict[str, int] = {}

        for filepath in files:
            try:
                total_size += os.path.getsize(filepath)
                ext = os.path.splitext(filepath)[1].lower()
                file_type_counts[ext] = file_type_counts.get(ext, 0) + 1
            except Exception:
                pass

        return AdapterResult(
            success=True,
            stdout=result.stdout,
            artifacts=files + directories,
            metadata={
                "files": files,
                "directories": directories,
                "file_count": len(files),
                "directory_count": len(directories),
                "total_size_bytes": total_size,
                "file_types": file_type_counts,
                "directory": directory
            }
        )

    def _inventory_with_python(
        self,
        directory: str,
        max_depth: Optional[int],
        file_types: Optional[List[str]]
    ) -> AdapterResult:
        """Inventory using Python os.walk."""
        files = []
        directories = []
        total_size = 0
        file_type_counts: Dict[str, int] = {}

        for root, dirs, filenames in os.walk(directory):
            # Check depth
            if max_depth:
                depth = root.replace(directory, '').count(os.sep)
                if depth >= max_depth:
                    dirs.clear()
                    continue

            # Add directories
            for d in dirs:
                dir_path = os.path.join(root, d)
                directories.append(dir_path)

            # Add files
            for f in filenames:
                file_path = os.path.join(root, f)

                # Filter by file type if specified
                if file_types:
                    ext = os.path.splitext(f)[1].lower()
                    if not ext:
                        continue
                    ext = ext if ext.startswith('.') else f'.{ext}'
                    if ext not in file_types:
                        continue

                files.append(file_path)
                try:
                    total_size += os.path.getsize(file_path)
                    ext = os.path.splitext(f)[1].lower()
                    file_type_counts[ext] = file_type_counts.get(ext, 0) + 1
                except Exception:
                    pass

        return AdapterResult(
            success=True,
            artifacts=files + directories,
            metadata={
                "files": files,
                "directories": directories,
                "file_count": len(files),
                "directory_count": len(directories),
                "total_size_bytes": total_size,
                "file_types": file_type_counts,
                "directory": directory,
                "method": "python_os_walk"
            }
        )

    def find_files(
        self,
        directory: str,
        pattern: str,
        case_sensitive: bool = True
    ) -> AdapterResult:
        """
        Find files matching a pattern.

        Args:
            directory: Directory to search
            pattern: Glob pattern (e.g., '*.dylib')
            case_sensitive: Whether search is case sensitive

        Returns:
            AdapterResult with list of matching files
        """
        if not os.path.exists(directory):
            return AdapterResult(
                success=False,
                error=f"Directory not found: {directory}"
            )

        # Build find command
        args = [directory]

        if case_sensitive:
            args.extend(["-name", pattern])
        else:
            args.extend(["-iname", pattern])

        args.extend(["-type", "f", "-print"])

        result = self.run(*args)

        if not result.success:
            return AdapterResult(
                success=False,
                error=f"find command failed: {result.stderr}"
            )

        files = [f.strip() for f in result.stdout.split('\n') if f.strip()]

        return AdapterResult(
            success=True,
            stdout=result.stdout,
            artifacts=files,
            metadata={
                "files": files,
                "file_count": len(files),
                "pattern": pattern,
                "case_sensitive": case_sensitive
            }
        )

    def find_frameworks(self, directory: str) -> AdapterResult:
        """Find all frameworks in a directory."""
        return self.find_files(directory, "*.framework")

    def find_dylibs(self, directory: str) -> AdapterResult:
        """Find all dylibs in a directory."""
        return self.find_files(directory, "*.dylib")

    def find_extensions(self, directory: str) -> AdapterResult:
        """Find all app extensions in a directory."""
        return self.find_files(directory, "*.appex")
