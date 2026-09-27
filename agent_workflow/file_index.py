"""Index project files discovered by ProjectScanner."""

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from agent_workflow.project_scanner import ProjectScanResult


@dataclass(frozen=True)
class FileIndexEntry:
    """Indexed information about one project file."""

    relative_path: Path
    extension: str
    file_type: str


@dataclass(frozen=True)
class FileIndex:
    """Immutable index of discovered project files."""

    root_path: Path
    entries: Tuple[FileIndexEntry, ...]

    @classmethod
    def from_scan_result(cls, result: ProjectScanResult) -> "FileIndex":
        entries = tuple(
            FileIndexEntry(
                relative_path=file.relative_path,
                extension=file.extension,
                file_type=_classify_file_type(file.extension),
            )
            for file in result.files
        )

        return cls(
            root_path=result.root_path,
            entries=entries,
        )

    def get(self, relative_path: Path) -> FileIndexEntry | None:
        for entry in self.entries:
            if entry.relative_path == relative_path:
                return entry
        return None


def _classify_file_type(extension: str) -> str:
    extension = extension.lower()

    if extension == ".py":
        return "python"
    if extension == ".md":
        return "markdown"
    if extension == ".json":
        return "json"
    if extension == ".txt":
        return "text"

    return "other"
