"""Write UTF-8 text files within a project root."""

from pathlib import Path
from typing import Union


class FileWriter:
    """Write text files without allowing access outside a project root."""

    def __init__(self, project_root: Union[str, Path]) -> None:
        self.project_root = Path(project_root).resolve()

    def write_file(
        self,
        relative_path: Union[str, Path],
        contents: str,
        overwrite: bool = False,
    ) -> Path:
        """Write UTF-8 ``contents`` and return the resolved target path.

        Parent directories must already exist. Existing files are protected
        unless ``overwrite`` is explicitly set to ``True``.

        Raises:
            ValueError: If the target is outside the project root.
            FileNotFoundError: If the target's parent directory is missing.
            IsADirectoryError: If the target or its parent is a directory or
                not a directory, respectively.
            FileExistsError: If the target exists and overwrite is false.
            UnicodeEncodeError: If the contents cannot be encoded as UTF-8.
        """
        target_path = (self.project_root / relative_path).resolve()

        if not target_path.is_relative_to(self.project_root):
            raise ValueError(
                f"Requested path is outside the project root: {relative_path}"
            )

        parent_path = target_path.parent
        if not parent_path.exists():
            raise FileNotFoundError(
                f"Parent directory does not exist: {parent_path}"
            )
        if not parent_path.is_dir():
            raise NotADirectoryError(f"Parent path is not a directory: {parent_path}")
        if target_path.is_dir():
            raise IsADirectoryError(f"Path is a directory: {relative_path}")
        if target_path.exists() and not overwrite:
            raise FileExistsError(f"File already exists: {relative_path}")

        if overwrite:
            target_path.write_text(contents, encoding="utf-8")
        else:
            with target_path.open("x", encoding="utf-8") as file_handle:
                file_handle.write(contents)

        return target_path
