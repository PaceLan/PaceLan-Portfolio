"""Scan project files without reading or modifying their contents."""

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple, Union

from core.project_tree import IGNORED_DIRECTORIES


@dataclass(frozen=True)
class ProjectFile:
    """A file discovered during project scanning."""

    relative_path: Path
    extension: str


@dataclass(frozen=True)
class ProjectScanResult:
    """The immutable result of a project scan."""

    root_path: Path
    files: Tuple[ProjectFile, ...]


class ProjectScanner:
    """Discover project files without reading or changing them."""

    def __init__(self, root_path: Union[str, Path]) -> None:
        self.root_path = Path(root_path).resolve()

    def scan(self) -> ProjectScanResult:
        """Return all files below the project root.

        Ignored directories follow the existing ProjectTree contract.
        Files are returned in stable relative-path order.
        """
        files = []

        if not self.root_path.exists():
            raise FileNotFoundError(
                f"Project root does not exist: {self.root_path}"
            )

        if not self.root_path.is_dir():
            raise NotADirectoryError(
                f"Project root is not a directory: {self.root_path}"
            )

        for path in self._iter_files(self.root_path):
            relative_path = path.relative_to(self.root_path)
            files.append(
                ProjectFile(
                    relative_path=relative_path,
                    extension=path.suffix,
                )
            )

        files.sort(key=lambda item: str(item.relative_path).lower())

        return ProjectScanResult(
            root_path=self.root_path,
            files=tuple(files),
        )

    def _iter_files(self, directory: Path):
        """Yield files recursively while respecting ignored directories."""
        for child_path in sorted(
            directory.iterdir(),
            key=lambda item: item.name.lower(),
        ):
            if child_path.is_dir():
                if child_path.name in IGNORED_DIRECTORIES:
                    continue
                yield from self._iter_files(child_path)
            elif child_path.is_file():
                yield child_path