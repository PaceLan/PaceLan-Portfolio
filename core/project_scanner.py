"""Legacy project scanner for compatibility."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectFile:
    """A file discovered during project scanning."""

    path: str
    name: str
    extension: str
    size: int


@dataclass(frozen=True)
class ProjectDirectory:
    """A directory discovered during project scanning."""

    path: str
    name: str
    files: tuple[str, ...] = ()
    subdirectories: tuple[str, ...] = ()


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

    root: str
    directories: tuple[ProjectDirectory, ...] = ()
    files: tuple[ProjectFile, ...] = ()
    statistics: ProjectScanStatistics = ProjectScanStatistics()
    errors: tuple[str, ...] = ()

    @property
    def successful(self) -> bool:
        return not self.errors


class ProjectScanner:
    """Scan a project without reading or modifying file contents."""

    DEFAULT_IGNORED_NAMES = {
        ".git",
        ".venv",
        "__pycache__",
    }

    def __init__(
        self,
        project_root: str | Path,
        ignored_names: set[str] | None = None,
    ) -> None:
        self.project_root = Path(project_root).expanduser().resolve()
        self.ignored_names = (
            set(ignored_names)
            if ignored_names is not None
            else set(self.DEFAULT_IGNORED_NAMES)
        )

    def scan(self) -> ProjectScanResult:
        """Scan the project and return structured information."""

        errors: list[str] = []
        files: list[ProjectFile] = []
        directories: list[ProjectDirectory] = []
        ignored_count = 0
        total_size = 0

        root = self.project_root

        try:
            if not root.exists():
                return ProjectScanResult(
                    root=str(root),
                    errors=(f"Project root not found: {root}",),
                )

            if not root.is_dir():
                return ProjectScanResult(
                    root=str(root),
                    errors=(
                        f"Project root is not a directory: {root}",
                    ),
                )

            for current_path in self._walk(root):
                relative_path = current_path.relative_to(root)

                if current_path.is_dir():
                    directory_files: list[str] = []
                    subdirectories: list[str] = []

                    try:
                        for child in current_path.iterdir():
                            if self._is_ignored(child):
                                ignored_count += 1
                                continue

                            child_relative = (
                                child.relative_to(root).as_posix()
                            )

                            if (
                                child.is_dir()
                                and not child.is_symlink()
                            ):
                                subdirectories.append(
                                    child_relative
                                )
                            elif child.is_file():
                                directory_files.append(
                                    child_relative
                                )

                    except (
                        PermissionError,
                        FileNotFoundError,
                        OSError,
                    ) as exc:
                        errors.append(
                            f"{current_path}: "
                            f"{type(exc).__name__}: {exc}"
                        )

                    directories.append(
                        ProjectDirectory(
                            path=relative_path.as_posix(),
                            name=current_path.name,
                            files=tuple(
                                sorted(directory_files)
                            ),
                            subdirectories=tuple(
                                sorted(subdirectories)
                            ),
                        )
                    )

                elif current_path.is_file():
                    try:
                        size = current_path.stat().st_size
                        total_size += size

                        files.append(
                            ProjectFile(
                                path=relative_path.as_posix(),
                                name=current_path.name,
                                extension=current_path.suffix.lower(),
                                size=size,
                            )
                        )

                    except (
                        PermissionError,
                        FileNotFoundError,
                        OSError,
                    ) as exc:
                        errors.append(
                            f"{current_path}: "
                            f"{type(exc).__name__}: {exc}"
                        )

        except (
            PermissionError,
            FileNotFoundError,
            OSError,
        ) as exc:
            errors.append(
                f"{root}: {type(exc).__name__}: {exc}"
            )

        statistics = ProjectScanStatistics(
            file_count=len(files),
            directory_count=len(directories),
            total_size=total_size,
            ignored_count=ignored_count,
        )

        return ProjectScanResult(
            root=str(root),
            directories=tuple(directories),
            files=tuple(files),
            statistics=statistics,
            errors=tuple(errors),
        )

    def _walk(self, root: Path):
        """Walk the project without entering ignored directories."""

        stack = [root]

        while stack:
            current = stack.pop()

            yield current

            if current.is_symlink() or not current.is_dir():
                continue

            try:
                children = list(current.iterdir())
            except (
                PermissionError,
                FileNotFoundError,
                OSError,
            ):
                continue

            for child in reversed(children):
                if self._is_ignored(child):
                    continue

                if child.is_symlink():
                    continue

                if child.is_dir():
                    stack.append(child)
                elif child.is_file():
                    yield child

    def _is_ignored(self, path: Path) -> bool:
        """Return whether a path name should be ignored."""

        return path.name in self.ignored_names