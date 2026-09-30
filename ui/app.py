from pathlib import Path
import tkinter as tk
from tkinter import ttk
from typing import Optional, Union

from application.workspace import ApplicationTreeNode
from ui.controller import ApplicationController
from ui.agent_panel import AgentInteractionPanel
from ui.agent_state import AgentInteractionState
from ui.visual_composition import DEFAULT_UX_COMPOSITION, UXComposition
from ui.visual_layout import WorkspaceLayout
from ui.visual_renderer import VisualRenderer
from ui.workspace_state import (
    SelectedFile,
    TreeState,
    ViewerState,
    WorkspaceState,
)


class CodingAssistantApp:
    """Build the read-only Phase 7.1 application shell."""

    def __init__(
        self,
        root: tk.Tk,
        controller: Optional[ApplicationController] = None,
        project_root: Optional[Union[str, Path]] = None,
        layout: Optional[WorkspaceLayout] = None,
        composition: Optional[UXComposition] = None,
        agent_service=None,
    ) -> None:
        self.root = root
        self.controller = controller or ApplicationController(
            agent_service=agent_service,
        )
        self.composition = composition or DEFAULT_UX_COMPOSITION
        self.layout = layout or self.composition.layout
        self.visual_renderer = VisualRenderer(root, self.composition)

        self.root.title("Coding Assistant")
        self.root.minsize(800, 500)
        self._tree_paths: dict[str, tuple[str, bool]] = {}
        self.workspace_state = self.controller.initial_state()
        self._build_layout()

        if project_root is not None:
            self.controller.open_project(project_root)
            self._set_project_state()
            self._load_project_tree()
        else:
            self.status_label.configure(text=self.workspace_state.status)

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        self._build_header()

        content = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        content.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        navigation = self._build_navigation(content)
        main_content = self._build_main_workspace(content)
        agent_panel = self._build_agent_panel(content)

        content.add(navigation, weight=1)
        content.add(main_content, weight=3)
        content.add(agent_panel, weight=2)

        self._build_status()

    def _build_header(self) -> None:
        header = ttk.Frame(self.root, padding=(12, 10))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        title = ttk.Label(
            header,
            text="Coding Assistant",
        )
        title.grid(row=0, column=0, sticky="w")
        self.visual_renderer.apply_header(title)

    def _build_navigation(self, parent: ttk.Panedwindow) -> ttk.LabelFrame:
        navigation = ttk.LabelFrame(parent, text="Project", padding=8)
        navigation.columnconfigure(0, weight=1)
        navigation.rowconfigure(0, weight=1)
        self.visual_renderer.apply_navigation(navigation)

        self.tree_view = ttk.Treeview(navigation, show="tree")
        self.tree_view.grid(row=0, column=0, sticky="nsew")
        self.tree_view.bind("<<TreeviewSelect>>", self._on_tree_selection)
        self.visual_renderer.apply_tree(self.tree_view)

        tree_scrollbar = ttk.Scrollbar(
            navigation,
            orient=tk.VERTICAL,
            command=self.tree_view.yview,
        )
        tree_scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree_view.configure(yscrollcommand=tree_scrollbar.set)

        return navigation

    def _build_main_workspace(
        self,
        parent: ttk.Panedwindow,
    ) -> ttk.LabelFrame:
        main_content = ttk.LabelFrame(parent, text="Workspace", padding=16)
        main_content.columnconfigure(0, weight=1)
        main_content.rowconfigure(1, weight=1)
        self.visual_renderer.apply_workspace(main_content)

        self.file_path_label = ttk.Label(
            main_content,
            text="No file selected",
            anchor="w",
        )
        self.file_path_label.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 8),
        )
        self.visual_renderer.apply_text_label(self.file_path_label)

        self.file_viewer = tk.Text(
            main_content,
            wrap=tk.NONE,
            state=tk.DISABLED,
        )
        self.file_viewer.grid(row=1, column=0, sticky="nsew")
        self.visual_renderer.apply_text_viewer(self.file_viewer)

        file_scrollbar = ttk.Scrollbar(
            main_content,
            orient=tk.VERTICAL,
            command=self.file_viewer.yview,
        )
        file_scrollbar.grid(row=1, column=1, sticky="ns")
        self.file_viewer.configure(yscrollcommand=file_scrollbar.set)

        return main_content

    def _build_agent_panel(
        self,
        parent: ttk.Panedwindow,
    ) -> AgentInteractionPanel:
        self.agent_panel = AgentInteractionPanel(
            parent,
            self.controller.agent_state,
            composition=self.composition,
        )
        self.agent_panel.set_history_selection_callback(
            self._on_agent_history_selected
        )
        return self.agent_panel

    def _render_agent_state(
        self,
        state: AgentInteractionState,
    ) -> AgentInteractionState:
        self.agent_panel.render(state)
        return state

    def _on_agent_history_selected(self, run_id: str) -> None:
        state = self.controller.select_agent_history(run_id)
        self._render_agent_state(state)

    def _build_status(self) -> None:
        self.status_label = tk.Label(
            self.root,
            text="Ready",
            relief=tk.SUNKEN,
            anchor="w",
        )
        self.status_label.grid(row=2, column=0, sticky="ew")
        self.visual_renderer.apply_status(self.status_label)

    def _set_project_state(self) -> None:
        self.workspace_state = WorkspaceState(
            project=self.controller.project_context,
            tree=self.workspace_state.tree,
            selected_file=self.workspace_state.selected_file,
            viewer=self.workspace_state.viewer,
            status=self.workspace_state.status,
        )

    def _load_project_tree(self) -> None:
        tree = self.controller.get_project_tree()
        self._insert_tree_node("", tree)
        self.workspace_state = WorkspaceState(
            project=self.controller.project_context,
            tree=TreeState(loaded=True),
            selected_file=SelectedFile(),
            viewer=ViewerState(),
            status="Project loaded",
        )
        self.status_label.configure(text=self.workspace_state.status)

    def _insert_tree_node(self, parent: str, node: ApplicationTreeNode) -> str:
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
            status = f"Selected directory: {relative_path}"
            self.workspace_state = WorkspaceState(
                project=self.workspace_state.project,
                tree=TreeState(
                    loaded=self.workspace_state.tree.loaded,
                    selected_path=relative_path,
                    selected_is_directory=True,
                ),
                selected_file=SelectedFile(),
                viewer=ViewerState(),
                status=status,
            )
            self._clear_file_viewer("No file selected")
            self.status_label.configure(text=status)
            return

        result = self.controller.select_file(relative_path)

        if result.success:
            self.workspace_state = WorkspaceState(
                project=self.workspace_state.project,
                tree=TreeState(
                    loaded=self.workspace_state.tree.loaded,
                    selected_path=relative_path,
                    selected_is_directory=False,
                ),
                selected_file=SelectedFile(path=result.path),
                viewer=ViewerState(
                    path=result.path,
                    contents=result.contents,
                    loaded=True,
                ),
                status=f"Loaded: {result.path}",
            )
            self.file_path_label.configure(text=result.path)
            self._set_file_contents(result.contents)
            self.status_label.configure(text=self.workspace_state.status)
        else:
            self.workspace_state = WorkspaceState(
                project=self.workspace_state.project,
                tree=TreeState(
                    loaded=self.workspace_state.tree.loaded,
                    selected_path=relative_path,
                    selected_is_directory=False,
                ),
                selected_file=SelectedFile(path=result.path),
                viewer=ViewerState(
                    path=result.path,
                    contents="",
                    loaded=False,
                    error=result.error,
                ),
                status="Unable to load file",
            )
            self._clear_file_viewer("Unable to load file")
            self.status_label.configure(text=self.workspace_state.status)

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
    controller: Optional[ApplicationController] = None,
    agent_service=None,
) -> CodingAssistantApp:
    """Create the UI shell without starting the Tk event loop."""

    return CodingAssistantApp(
        root,
        controller=controller,
        project_root=project_root,
        agent_service=agent_service,
    )


def main() -> None:
    """Start the standalone UI shell."""
    root = tk.Tk()
    create_app(root, Path(__file__).resolve().parent.parent)
    root.mainloop()


if __name__ == "__main__":
    main()
