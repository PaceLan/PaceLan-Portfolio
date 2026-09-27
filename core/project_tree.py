"""Build a lightweight, read-only representation of a project directory tree."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Union


IGNORED_DIRECTORIES = {".git", ".venv", "__pycache__"}


@dataclass
class ProjectTreeNode:
    """A file or directory in a project tree."""

    name: str
    path: Path
    is_directory: bool
    children: List["ProjectTreeNode"] = field(default_factory=list)


class ProjectTree:
    """Build a read-only tree of files and directories below a project root."""

    def __init__(self, root_path: Union[str, Path]) -> None:
        self.root_path = Path(root_path).resolve()

    def build_tree(self) -> ProjectTreeNode:
        """Return the project tree rooted at ``root_path``.

        The filesystem is inspected for names and directory status only; file
        contents are never opened or changed.
        """
        return self._build_node(self.root_path)

    def _build_node(self, path: Path) -> ProjectTreeNode:
        is_directory = path.is_dir()
        node = ProjectTreeNode(
            name=path.name or str(path),
            path=path,
            is_directory=is_directory,
        )

        if not is_directory:
            return node

        for child_path in sorted(
            path.iterdir(),
            key=lambda item: item.name.lower(),
        ):
            if child_path.is_dir() and child_path.name in IGNORED_DIRECTORIES:
                continue

            node.children.append(self._build_node(child_path))

        return node