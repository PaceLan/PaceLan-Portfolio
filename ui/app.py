from pathlib import Path
import tkinter as tk
from tkinter import filedialog, ttk
from typing import Optional, Union

from application.workspace import ApplicationTreeNode
from ui.controller import ApplicationController
from ui.agent_panel import AgentInteractionPanel
from ui.agent_state import AgentInteractionState
from ui.animation_accessibility import AnimationAccessibility
from ui.visual_system import AgentStage, AgentVisualSystem
from ui.visual_composition import DEFAULT_UX_COMPOSITION, UXComposition
from ui.visual_layout import WorkspaceLayout
from ui.visual_renderer import VisualRenderer
from ui.visual_icons import VisualIconSet
from ui.pointer_visuals import PointerVisualLayer
from ui.workspace_empty_state import WorkspaceEmptyState
from ui.workspace_state import (
    SelectedFile,
    TreeState,
    ViewerState,
    WorkspaceState,
)


class CodingAssistantApp:
    """Build the read-only Phase 7.1 application shell."""

    _IGNORED_PROJECT_DIRECTORIES = {
        ".git",
        ".venv",
        ".tox",
        "venv",
        "__pycache__",
        "__pypackages__",
        "build",
        "dist",
        "_internal",
        "runtime",
        "python-runtime",
        "site-packages",
        "node_modules",
    }
    _IGNORED_PROJECT_SUFFIXES = {
        ".dll",
        ".exe",
        ".pyd",
        ".pyc",
        ".so",
        ".dylib",
    }

    def __init__(
        self,
        root: tk.Tk,
        controller: Optional[ApplicationController] = None,
        project_root: Optional[Union[str, Path]] = None,
        layout: Optional[WorkspaceLayout] = None,
        composition: Optional[UXComposition] = None,
        agent_service=None,
        accessibility: Optional[AnimationAccessibility] = None,
    ) -> None:
        self.root = root
        self.controller = controller or ApplicationController(
            agent_service=agent_service,
        )
        self.composition = composition or DEFAULT_UX_COMPOSITION
        self.accessibility = accessibility or AnimationAccessibility()
        self.icons = VisualIconSet(root, self.composition.tokens)
        self.layout = layout or self.composition.layout
        self.visual_renderer = VisualRenderer(root, self.composition)

        self.root.title("PacePilot")
        self.root.minsize(800, 500)
        self._tree_paths: dict[str, tuple[str, bool]] = {}
        self.workspace_state = self.controller.initial_state()
        self._build_layout()
        self._build_pointer_layer()

        if project_root is not None:
            self.controller.open_project(project_root)
            self._set_project_state()
            self._load_project_tree()
        else:
            self.status_label.configure(text="Open a project to begin")

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        self._build_header()

        content = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        self.content_pane = content
        self.visual_renderer.apply_panedwindow(content)
        content.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        navigation = self._build_navigation(content)
        main_content = self._build_main_workspace(content)
        agent_panel = self._build_agent_panel(content)
        self.project_panel = navigation
        self.workspace_panel = main_content

        content.add(navigation, weight=1)
        content.add(main_content, weight=3)
        content.add(agent_panel, weight=2)

        self._build_status()

    def _build_header(self) -> None:
        header = ttk.Frame(self.root, padding=(12, 10))
        self.header_frame = header
        self.visual_renderer.apply_header_frame(header)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=2)

        title = ttk.Label(
            header,
            text="PacePilot",
            image=self.icons.image("brand"),
            compound=tk.LEFT,
        )
        title.grid(row=0, column=0, sticky="w")
        self.visual_renderer.apply_header(title)

        self.project_context_label = ttk.Label(
            header,
            text="No project open",
            anchor="w",
        )
        self.project_context_label.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(20, 12),
        )
        self.visual_renderer.apply_header_context(self.project_context_label)

        self.open_project_button = ttk.Button(
            header,
            text="Open Project",
            image=self.icons.image("folder"),
            compound=tk.LEFT,
            command=self._choose_project,
        )
        self.visual_renderer.apply_primary_action(self.open_project_button)
        self.open_project_button.grid(row=0, column=2, sticky="e")

    def _build_pointer_layer(self) -> None:
        self.pointer_layer = PointerVisualLayer(
            self.root,
            accessibility=self.accessibility,
        )
        renderer = self.visual_renderer
        for surface in (
            self.header_frame,
            self.project_panel,
            self.workspace_panel,
            self.agent_panel,
            self.open_project_button,
        ):
            self.pointer_layer.register(
                surface,
                lambda _x, _y, amount, target=surface: (
                    renderer.apply_pointer_surface(target, amount)
                ),
            )
        self.pointer_layer.register(
            self.empty_state,
            self.empty_state.set_pointer_visual,
        )
        self.pointer_layer.register(
            self.file_viewer,
            lambda _x, _y, amount: renderer.apply_pointer_text(
                self.file_viewer,
                amount,
            ),
        )
        self.pointer_layer.register(
            self.tree_view,
            self._set_project_tree_pointer,
        )
        for stage, frame in self.agent_panel._stage_frames.items():
            self.pointer_layer.register(
                frame,
                lambda _x, _y, amount, target_stage=stage: (
                    self.agent_panel.visual_system.set_pointer(
                        target_stage,
                        amount,
                    )
                ),
            )

    def _set_project_tree_pointer(
        self,
        _x: int,
        y: int,
        intensity: float,
    ) -> None:
        row = self.tree_view.identify_row(y) if intensity > 0.01 else ""
        previous = getattr(self, "_pointer_tree_item", None)
        if previous and previous != row:
            tags = tuple(
                tag
                for tag in self.tree_view.item(previous, "tags")
                if tag != "pointer-hover"
            )
            self.tree_view.item(previous, tags=tags)
        self._pointer_tree_item = row or None
        if row:
            tags = tuple(self.tree_view.item(row, "tags"))
            if "pointer-hover" not in tags:
                self.tree_view.item(row, tags=tags + ("pointer-hover",))

    def _build_navigation(self, parent: ttk.Panedwindow) -> ttk.LabelFrame:
        navigation = ttk.LabelFrame(parent, text="", padding=8)
        self.project_heading = ttk.Label(
            navigation,
            text="Project",
            image=self.icons.image("folder"),
            compound=tk.LEFT,
            style="PacePilot.Panel.TLabelframe.Label",
        )
        navigation.configure(labelwidget=self.project_heading)
        navigation.columnconfigure(0, weight=1)
        navigation.rowconfigure(0, weight=1)
        self.visual_renderer.apply_navigation(navigation)

        self.tree_view = ttk.Treeview(navigation, show="tree")
        self.tree_view.tag_configure(
            "pointer-hover",
            background=self.composition.tokens.colors["surface_elevated"],
            foreground=self.composition.tokens.colors["text"],
        )
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
        main_content = ttk.LabelFrame(parent, text="", padding=16)
        self.workspace_heading = ttk.Label(
            main_content,
            text="Workspace",
            image=self.icons.image("workspace"),
            compound=tk.LEFT,
            style="PacePilot.Panel.TLabelframe.Label",
        )
        main_content.configure(labelwidget=self.workspace_heading)
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

        self.file_scrollbar = ttk.Scrollbar(
            main_content,
            orient=tk.VERTICAL,
            command=self.file_viewer.yview,
        )
        self.file_scrollbar.grid(row=1, column=1, sticky="ns")
        self.file_viewer.configure(yscrollcommand=self.file_scrollbar.set)

        self.empty_state = WorkspaceEmptyState(
            main_content,
            accessibility=self.accessibility,
            tokens=self.composition.tokens,
        )
        self.empty_state.grid(row=1, column=0, sticky="nsew")
        self.file_viewer.grid_remove()
        self.file_scrollbar.grid_remove()

        return main_content

    def _build_agent_panel(
        self,
        parent: ttk.Panedwindow,
    ) -> AgentInteractionPanel:
        self.agent_panel = AgentInteractionPanel(
            parent,
            self.controller.agent_state,
            composition=self.composition,
            accessibility=self.accessibility,
            icons=self.icons,
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
        projection = AgentVisualSystem.project(state)
        self.empty_state.set_agent_active(projection.stage is not AgentStage.IDLE)
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
        self.tree_view.delete(*self.tree_view.get_children())
        self._tree_paths.clear()
        tree = self.controller.get_project_tree()
        self._insert_tree_node("", tree)
        self.workspace_state = WorkspaceState(
            project=self.controller.project_context,
            tree=TreeState(loaded=True),
            selected_file=SelectedFile(),
            viewer=ViewerState(),
            status="Project loaded",
        )
        self.empty_state.set_project_open(True)
        self.file_path_label.configure(text="No file selected")
        self.project_context_label.configure(
            text=self.controller.project_context.name or "Open Project"
        )
        self.status_label.configure(text=self.workspace_state.status)

    def _choose_project(self) -> None:
        project_path = filedialog.askdirectory(
            parent=self.root,
            title="Open Project",
            mustexist=True,
        )
        if not project_path:
            return

        try:
            self.controller.open_project(project_path)
            self._set_project_state()
            self._load_project_tree()
            self.status_label.configure(text="Project loaded")
        except (OSError, ValueError) as error:
            self.status_label.configure(
                text=f"Unable to open project: {error}"
            )

    @classmethod
    def _is_user_project_node(cls, node: ApplicationTreeNode) -> bool:
        if node.is_directory:
            return node.name.casefold() not in cls._IGNORED_PROJECT_DIRECTORIES
        return node.path.suffix.casefold() not in cls._IGNORED_PROJECT_SUFFIXES

    def _insert_tree_node(self, parent: str, node: ApplicationTreeNode) -> str:
        item_id = self.tree_view.insert(
            parent,
            "end",
            text=node.name,
            image=self.icons.image("folder" if node.is_directory else "file"),
            open=True,
        )
        project_path = self.controller.project_context.path
        relative_path = "."
        if project_path is not None:
            relative_path = node.path.relative_to(project_path).as_posix() or "."
        self._tree_paths[item_id] = (relative_path, node.is_directory)
        for child in node.children:
            if not self._is_user_project_node(child):
                continue
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
            empty_state = getattr(self, "empty_state", None)
            if empty_state is not None:
                empty_state.grid_remove()
            file_viewer = getattr(self, "file_viewer", None)
            if file_viewer is not None:
                file_viewer.grid()
            file_scrollbar = getattr(self, "file_scrollbar", None)
            if file_scrollbar is not None:
                file_scrollbar.grid()
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
        empty_state = getattr(self, "empty_state", None)
        if empty_state is not None:
            empty_state.set_project_open(
                self.controller.project_context.path is not None
            )
            empty_state.grid()
        for widget_name in ("file_viewer", "file_scrollbar"):
            widget = getattr(self, widget_name, None)
            if widget is not None:
                widget.grid_remove()


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
    from ui.app_entry import main as desktop_main

    desktop_main()


if __name__ == "__main__":
    main()
