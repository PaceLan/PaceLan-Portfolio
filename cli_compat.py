"""Legacy CLI entry retained for explicit history-store callers."""

from datetime import datetime, timezone
import subprocess
import sys
from pathlib import Path
from typing import Optional

from core.file_reader import FileReader
from core.file_writer import FileWriter
from core.project_manager import ProjectManager
from core.project_tree import ProjectTree, ProjectTreeNode
from history.history_core import HistoryEntry, HistoryStore


def _history_target(project_path: Path, relative_path: str) -> str:
    try:
        resolved_path = (project_path / relative_path).resolve()
        if not resolved_path.is_relative_to(project_path):
            return "<outside-project>"
        return resolved_path.relative_to(project_path).as_posix() or "."
    except (OSError, ValueError):
        return "<invalid-target>"


def _record_history(
    history_store: HistoryStore,
    operation: str,
    target: str,
    result: str,
    success: bool,
) -> None:
    entry = HistoryEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        operation=operation,
        target=target,
        result=result,
        success=success,
    )
    try:
        history_store.append(entry)
    except Exception:
        pass


def print_project_tree(node: ProjectTreeNode, indent: str = "") -> None:
    marker = "[D]" if node.is_directory else "[F]"
    print(f"{indent}{marker} {node.name}")
    if node.is_directory and not node.children:
        print(f"{indent}  (empty)")
        return

    for child in node.children:
        print_project_tree(child, indent + "  ")


def main(history_store: Optional[HistoryStore] = None) -> None:
    print("Coding Assistant")
    project_root = Path(__file__).resolve().parent
    project_manager = ProjectManager()
    project_manager.open_project(project_root)

    project_info = project_manager.get_project_info()
    project_path = project_manager.get_project_path()
    project_is_valid = bool(
        project_info["exists"] and project_info["is_directory"] and project_path
    )

    print(f"Project path: {project_info['project_path']}")
    print(f"Project name: {project_info['project_name']}")
    print(f"Project valid: {project_is_valid}")

    if not project_is_valid or project_path is None:
        print("Project tree: unavailable")
        return

    if history_store is None:
        history_store = HistoryStore(project_path / "history")

    file_reader = FileReader(project_path)
    file_writer = FileWriter(project_path)
    project_tree = ProjectTree(project_path).build_tree()
    file_count = 0
    directory_count = 0
    nodes = [project_tree]

    while nodes:
        node: ProjectTreeNode = nodes.pop()
        if node.is_directory:
            directory_count += 1
            nodes.extend(node.children)
        else:
            file_count += 1

    print(
        "Project tree: "
        f"root={project_tree.name}, directories={directory_count}, "
        f"files={file_count}"
    )

    while True:
        print("\n1. Show Project Tree")
        print("2. Read File")
        print("3. Write File")
        print("4. Run Python File")
        print("5. Exit")
        try:
            choice = input("Select an option: ").strip()
        except EOFError:
            print("Exiting.")
            return

        if choice == "1":
            try:
                print("\nProject Tree:")
                print_project_tree(ProjectTree(project_path).build_tree())
            except OSError as error:
                _record_history(
                    history_store,
                    "tree",
                    ".",
                    type(error).__name__,
                    False,
                )
                print(f"Unable to show project tree: {error}")
            else:
                _record_history(history_store, "tree", ".", "success", True)
        elif choice == "2":
            relative_path = ""
            try:
                relative_path = input(
                    "Enter a project-relative file path: "
                ).strip()
                contents = file_reader.read_file(relative_path)
                print("\nFile Contents:")
                print(contents)
            except (
                EOFError,
                FileNotFoundError,
                IsADirectoryError,
                ValueError,
                UnicodeDecodeError,
            ) as error:
                _record_history(
                    history_store,
                    "read",
                    _history_target(project_path, relative_path),
                    type(error).__name__,
                    False,
                )
                print(f"Unable to read file: {error}")
            else:
                _record_history(
                    history_store,
                    "read",
                    _history_target(project_path, relative_path),
                    "success",
                    True,
                )
        elif choice == "3":
            relative_path = ""
            try:
                relative_path = input(
                    "Enter a project-relative file path: "
                ).strip()
                contents = input("Enter content to write: ")
                target_path = file_writer.write_file(relative_path, contents)
                print(f"File written: {target_path}")
            except (
                EOFError,
                FileExistsError,
                FileNotFoundError,
                IsADirectoryError,
                NotADirectoryError,
                ValueError,
                UnicodeEncodeError,
            ) as error:
                _record_history(
                    history_store,
                    "write",
                    _history_target(project_path, relative_path),
                    type(error).__name__,
                    False,
                )
                print(f"Unable to write file: {error}")
            else:
                _record_history(
                    history_store,
                    "write",
                    _history_target(project_path, str(target_path)),
                    "success",
                    True,
                )
        elif choice == "4":
            relative_path = ""
            try:
                relative_path = input(
                    "Enter a project-relative Python file path: "
                ).strip()
                resolved_path = (project_path / relative_path).resolve()

                if not resolved_path.is_relative_to(project_path):
                    raise ValueError("Path is outside the project root")
                if not resolved_path.exists():
                    raise FileNotFoundError(
                        f"File does not exist: {relative_path}"
                    )
                if resolved_path.is_dir():
                    raise IsADirectoryError(
                        f"Path is a directory: {relative_path}"
                    )
                if resolved_path.suffix.lower() != ".py":
                    raise ValueError("Path must refer to a .py file")

                result = subprocess.run(
                    [sys.executable, str(resolved_path)],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                print("\nPython stdout:")
                print(result.stdout, end="")
                print("\nPython stderr:")
                print(result.stderr, end="")
                print(f"Python exit code: {result.returncode}")
                _record_history(
                    history_store,
                    "run",
                    _history_target(project_path, relative_path),
                    "success"
                    if result.returncode == 0
                    else f"exit_code_{result.returncode}",
                    result.returncode == 0,
                )
            except (
                EOFError,
                FileNotFoundError,
                IsADirectoryError,
                OSError,
                ValueError,
            ) as error:
                _record_history(
                    history_store,
                    "run",
                    _history_target(project_path, relative_path),
                    type(error).__name__,
                    False,
                )
                print(f"Unable to run Python file: {error}")
        elif choice == "5":
            print("Exiting.")
            return
        else:
            print("Invalid option. Please select 1, 2, 3, 4, or 5.")
