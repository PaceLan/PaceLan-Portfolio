"""Read UTF-8 text files within a project root."""

from pathlib import Path
from typing import Union


class FileReader:
    """Read text files without allowing access outside a project root."""

    def __init__(self, project_root: Union[str, Path]) -> None:
        self.project_root = Path(project_root).resolve()

    def read_file(self, relative_path: Union[str, Path]) -> str:
        """Return the UTF-8 contents of a file inside the project root.

        Raises:
            ValueError: If the resolved path is outside the project root.
            FileNotFoundError: If the requested file does not exist.
            IsADirectoryError: If the requested path is a directory.
            UnicodeDecodeError: If the file is not valid UTF-8.
        """
        requested_path = (self.project_root / relative_path).resolve()

        if not requested_path.is_relative_to(self.project_root):
            raise ValueError(
                f"Requested path is outside the project root: {relative_path}"
            )

        if not requested_path.exists():
            raise FileNotFoundError(f"File does not exist: {relative_path}")

        if requested_path.is_dir():
            raise IsADirectoryError(f"Path is a directory: {relative_path}")

        return requested_path.read_text(encoding="utf-8")
