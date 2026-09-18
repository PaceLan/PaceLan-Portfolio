"""Minimal Tkinter desktop shell for Coding Assistant."""

from pathlib import Path
import tkinter as tk
from tkinter import ttk
from typing import Optional, Union

from ui.controller import ApplicationController
from core.project_tree import ProjectTreeNode


class CodingAssistantApp:
    """Build the read-only Phase 7.1 application shell."""

    def __init__(
        self,
        root: tk.Tk,
        controller: Optional[ApplicationController] = None,
        project_root: Optional[Union[str, Path]] = None,
    ) -> None:
        self.root = root
        self.controller = controller or ApplicationController()
        self.root.title("Coding Assistant")
        self.root.minsize(800, 500)
        self._tree_paths: dict[str, tuple[str, bool]] = {}
        self._build_layout()

        if project_root is not None:
            self.controller.open_project(project_root)
            self._load_project_tree()
        else:
            self.status_label.configure(text="Ready")

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        header = ttk.Frame(self.root, padding=(12, 10))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(
            header,
            text="Coding Assistant",
            font=("TkDefaultFont", 16, "bold"),
        ).grid(row=0, column=0, sticky="w")

        content = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        content.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        navigation = ttk.LabelFrame(content, text="Project", padding=8)
        navigation.columnconfigure(0, weight=1)
        navigation.rowconfigure(0, weight=1)
        self.tree_view = ttk.Treeview(navigation, show="tree")
        self.tree_view.grid(row=0, column=0, sticky="nsew")
        self.tree_view.bind("<<TreeviewSelect>>", self._on_tree_selection)
        tree_scrollbar = ttk.Scrollbar(
            navigation,
            orient=tk.VERTICAL,
            command=self.tree_view.yview,
        )
        tree_scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree_view.configure(yscrollcommand=tree_scrollbar.set)

        main_content = ttk.LabelFrame(content, text="Workspace", padding=16)
        main_content.columnconfigure(0, weight=1)
        main_content.rowconfigure(1, weight=1)
        self.file_path_label = ttk.Label(
            main_content,
            text="No file selected",
            anchor="w",
        )
        self.file_path_label.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.file_viewer = tk.Text(
            main_content,
            wrap=tk.NONE,
            state=tk.DISABLED,
        )
        self.file_viewer.grid(row=1, column=0, sticky="nsew")
        file_scrollbar = ttk.Scrollbar(
            main_content,
            orient=tk.VERTICAL,
            command=self.file_viewer.yview,
        )
        file_scrollbar.grid(row=1, column=1, sticky="ns")
        self.file_viewer.configure(yscrollcommand=file_scrollbar.set)

        content.add(navigation, weight=1)
        content.add(main_content, weight=3)

        self.status_label = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor="w")
        self.status_label.grid(row=2, column=0, sticky="ew")

    def _load_project_tree(self) -> None:
        tree = self.controller.get_project_tree()
        self._insert_tree_node("", tree)
        self.status_label.configure(text="Project loaded")

    def _insert_tree_node(self, parent: str, node: ProjectTreeNode) -> str:
        item_id = self.tree_view.insert(parent, "end", text=node.name, open=True)
        project_path = self.controller.project_context.path
        relative_path = "."
        if project_path is not None:
            relative_path = node.path.relative_to(project_path).as_posix() or "."
        self._tree_paths[item_id] = (relative_path, node.is_directory)
        for child in node.children:
            self._insert_tree_node(item_id, child)
        return item_id

    def _on_tree_selection(self, _event: tk.Event) -> None:
        selection = self.tree_view.selection()
        if not selection:
            return
        relative_path, is_directory = self._tree_paths[selection[0]]
        if is_directory:
            self._clear_file_viewer("No file selected")
            self.status_label.configure(text=f"Selected directory: {relative_path}")
            return

        result = self.controller.select_file(relative_path)
        if result.success:
            self.file_path_label.configure(text=result.path)
            self._set_file_contents(result.contents)
            self.status_label.configure(text=f"Loaded: {result.path}")
        else:
            self._clear_file_viewer("Unable to load file")
            self.status_label.configure(text="Unable to load file")

    def _set_file_contents(self, contents: str) -> None:
        self.file_viewer.configure(state=tk.NORMAL)
        self.file_viewer.delete("1.0", tk.END)
        self.file_viewer.insert("1.0", contents)
        self.file_viewer.configure(state=tk.DISABLED)

    def _clear_file_viewer(self, label: str) -> None:
        self.file_path_label.configure(text=label)
        self._set_file_contents("")


def create_app(
    root: tk.Tk,
    project_root: Optional[Union[str, Path]] = None,
) -> CodingAssistantApp:
    """Create the UI shell without starting the Tk event loop."""
    return CodingAssistantApp(root, project_root=project_root)


def main() -> None:
    """Start the standalone UI shell."""
    root = tk.Tk()
    create_app(root, Path(__file__).resolve().parent.parent)
    root.mainloop()


if __name__ == "__main__":
    main()
