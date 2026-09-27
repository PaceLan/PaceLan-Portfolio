"""Scan project structure without reading or modifying file contents."""

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple, Union

from core.project_tree import IGNORED_DIRECTORIES


@dataclass(frozen=True)
class ProjectFile:
    """A file discovered during project scanning."""

    relative_path: Path
    extension: str
    name: str = ""
    size: int = 0
    type: str = "file"

    def __post_init__(self) -> None:
        if not self.name:
            object.__setattr__(
                self,
                "name",
                self.relative_path.name,
            )


@dataclass(frozen=True)
class ProjectDirectory:
    """A directory discovered during project scanning."""

    relative_path: Path
    name: str
    files: Tuple[Path, ...] = ()
    subdirectories: Tuple[Path, ...] = ()
    type: str = "directory"


@dataclass(frozen=True)
class ProjectScanStatistics:
    """Summary information for a project scan."""

    file_count: int = 0
    directory_count: int = 0
    total_size: int = 0
    ignored_count: int = 0


@dataclass(frozen=True)
class ProjectScanResult:
    """Immutable result of a project scan."""

    root_path: Path
    files: Tuple[ProjectFile, ...]
    directories: Tuple[ProjectDirectory, ...] = ()
    statistics: ProjectScanStatistics = ProjectScanStatistics()
    errors: Tuple[str, ...] = ()

    @property
    def successful(self) -> bool:
        """Return whether the scan completed without recorded errors."""
        return not self.errors


class ProjectScanner:
    """Discover project files and directories safely."""

    def __init__(
        self,
        root_path: Union[str, Path],
        ignored_directories: set[str] | None = None,
    ) -> None:
        self.root_path = Path(root_path).resolve()
        self.ignored_directories = (
            set(ignored_directories)
            if ignored_directories is not None
            else set(IGNORED_DIRECTORIES)
        )

    def scan(self) -> ProjectScanResult:
        """Scan the project and return structured information."""

        if not self.root_path.exists():
            raise FileNotFoundError(
                f"Project root does not exist: {self.root_path}"
            )

        if not self.root_path.is_dir():
            raise NotADirectoryError(
                f"Project root is not a directory: {self.root_path}"
            )

        files: list[ProjectFile] = []
        directories: list[ProjectDirectory] = []
        errors: list[str] = []

        self._scan_directory(
            self.root_path,
            files,
            directories,
            errors,
        )

        ignored_count = self._count_ignored_directories()

        files.sort(
            key=lambda item: str(item.relative_path).lower()
        )
        directories.sort(
            key=lambda item: str(item.relative_path).lower()
        )

        statistics = ProjectScanStatistics(
            file_count=len(files),
            directory_count=len(directories),
            total_size=sum(item.size for item in files),
            ignored_count=ignored_count,
        )

        return ProjectScanResult(
            root_path=self.root_path,
            files=tuple(files),
            directories=tuple(directories),
            statistics=statistics,
            errors=tuple(errors),
        )

    def _scan_directory(
        self,
        directory: Path,
        files: list[ProjectFile],
        directories: list[ProjectDirectory],
        errors: list[str],
    ) -> None:
        try:
            children = sorted(
                directory.iterdir(),
                key=lambda item: item.name.lower(),
            )
        except (PermissionError, FileNotFoundError, OSError) as exc:
            errors.append(
                f"{directory}: {type(exc).__name__}: {exc}"
            )
            return

        child_files: list[Path] = []
        child_directories: list[Path] = []

        for child_path in children:
            if child_path.name in self.ignored_directories:
                continue

            try:
                if child_path.is_symlink():
                    continue

                if not child_path.is_relative_to(self.root_path):
                    errors.append(
                        f"{child_path}: path is outside project root"
                    )
                    continue

                if child_path.is_dir():
                    child_directories.append(child_path)

                    self._scan_directory(
                        child_path,
                        files,
                        directories,
                        errors,
                    )
                    continue

                if not child_path.is_file():
                    continue

                relative_path = child_path.relative_to(
                    self.root_path
                )

                try:
                    size = child_path.stat().st_size
                except (
                    PermissionError,
                    FileNotFoundError,
                    OSError,
                ) as exc:
                    errors.append(
                        f"{child_path}: "
                        f"{type(exc).__name__}: {exc}"
                    )
                    continue

                files.append(
                    ProjectFile(
                        relative_path=relative_path,
                        extension=child_path.suffix,
                        name=child_path.name,
                        size=size,
                    )
                )
                child_files.append(relative_path)

            except (PermissionError, FileNotFoundError, OSError) as exc:
                errors.append(
                    f"{child_path}: {type(exc).__name__}: {exc}"
                )

        relative_directory = directory.relative_to(
            self.root_path
        )

        directories.append(
            ProjectDirectory(
                relative_path=relative_directory,
                name=directory.name,
                files=tuple(
                    sorted(
                        child_files,
                        key=str,
                    )
                ),
                subdirectories=tuple(
                    sorted(
                        (
                            path.relative_to(self.root_path)
                            for path in child_directories
                        ),
                        key=str,
                    )
                ),
            )
        )

    def _count_ignored_directories(self) -> int:
        """Count ignored directories without following symlinks."""

        count = 0
        stack = [self.root_path]

        while stack:
            directory = stack.pop()

            try:
                children = directory.iterdir()
            except (PermissionError, FileNotFoundError, OSError):
                continue

            for child in children:
                if child.name in self.ignored_directories:
                    count += 1
                    continue

                try:
                    if child.is_symlink():
                        continue

                    if (
                        child.is_dir()
                        and child.is_relative_to(self.root_path)
                    ):
                        stack.append(child)

                except (
                    PermissionError,
                    FileNotFoundError,
                    OSError,
                ):
                    continue

        return count

    def _iter_files(self, directory: Path):
        """Yield files recursively for legacy compatibility."""

        try:
            children = sorted(
                directory.iterdir(),
                key=lambda item: item.name.lower(),
            )
        except (PermissionError, FileNotFoundError, OSError):
            return

        for child_path in children:
            if child_path.name in self.ignored_directories:
                continue

            try:
                if child_path.is_symlink():
                    continue

                if not child_path.is_relative_to(self.root_path):
                    continue

                if child_path.is_dir():
                    yield from self._iter_files(child_path)
                elif child_path.is_file():
                    yield child_path

            except (PermissionError, FileNotFoundError, OSError):
                continue