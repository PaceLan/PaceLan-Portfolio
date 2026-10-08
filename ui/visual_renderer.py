"""Tkinter rendering adapter for the immutable UX composition layer."""

import tkinter as tk
from tkinter import ttk

from .visual_composition import UXComposition
from .visual_semantic_mapper import VisualSemanticMapper
from .theme import ThemePalette, ThemeState


class VisualRenderer:
    """Apply UX composition tokens to Tkinter widgets."""

    def __init__(self, root: tk.Tk, composition: UXComposition) -> None:
        self.root = root
        self.composition = composition
        self.tokens = composition.tokens
        self.style = ttk.Style(root)
        self.semantic_mapper = VisualSemanticMapper()
        self.colors = self.tokens.colors
        self.theme_state = ThemeState()
        self.accent_blue = self.colors.get(
            "accent_blue",
            self.colors["accent"],
        )
        self.accent_purple = self.colors.get(
            "accent_purple",
            self.colors.get("agent_running", self.accent_blue),
        )
        self._pointer_text_colors: dict[str, tuple[object, str]] = {}
        self._ambient_surfaces: dict[str, tuple[object, str]] = {}

        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")
        toplevel = root.winfo_toplevel()
        if isinstance(toplevel, tk.Tk):
            toplevel.configure(background=self.colors["background"])

        self._configure_styles()

    def apply_theme(self, state: ThemeState) -> None:
        self.theme_state = state
        palette = state.palette

        self.colors = {
            "background": palette.background,
            "surface": palette.surface,
            "surface_elevated": palette.surface_elevated,
            "text": palette.text,
            "text_muted": palette.text_muted,
            "text_secondary": palette.text_muted,
            "border": palette.border,
            "accent": palette.accent,
            "accent_blue": palette.accent,
            "accent_purple": palette.agent_running,
            "success": palette.success,
            "warning": palette.warning,
            "error": palette.error,
            "agent_running": palette.agent_running,
        }

        self.accent_blue = palette.accent
        self.accent_purple = palette.agent_running
        self._configure_styles()

        try:
            self.root.configure(background=palette.background)
        except tk.TclError:
            pass

        for widget, _original in tuple(self._ambient_surfaces.values()):
            try:
                widget.configure(
                    style=self.style_name_for_surface(widget)
                )
            except tk.TclError:
                continue

    def style_name_for_surface(self, widget) -> str:
        name = f"PacePilot.Theme{id(widget)}.{widget.winfo_class()}"
        palette = self.theme_state.palette

        if widget.winfo_class() == "TLabelframe":
            self.style.configure(
                name,
                background=palette.surface,
                foreground=palette.text,
                bordercolor=palette.border,
                lightcolor=palette.border,
                darkcolor=palette.border,
            )
            self.style.configure(
                f"{name}.Label",
                background=palette.surface,
                foreground=palette.text,
            )
        else:
            self.style.configure(
                name,
                background=palette.background,
                foreground=palette.text,
            )

        return name

    def _configure_styles(self) -> None:
        colors = self.tokens.colors
        typography = self.tokens.typography
        borders = self.tokens.borders
        spacing = self.tokens.spacing
        font = (
            typography["font_family"],
            typography["size_md"],
            typography["weight_regular"],
        )

        self.style.configure(
            "TFrame",
            background=colors["background"],
        )
        self.style.configure(
            "TLabel",
            background=colors["surface"],
            foreground=colors["text_secondary"],
            font=font,
        )
        self.style.configure(
            "TLabelframe",
            background=colors["surface"],
            foreground=colors["text"],
            bordercolor=colors["border"],
            lightcolor=colors["border"],
            darkcolor=colors["border"],
        )
        self.style.configure(
            "TLabelframe.Label",
            background=colors["surface"],
            foreground=colors["text"],
            font=(
                typography["font_family"],
                typography["size_lg"],
                typography["weight_medium"],
            ),
        )
        self.style.configure(
            "TButton",
            background=colors["surface_elevated"],
            foreground=colors["text"],
            bordercolor=colors["border"],
            lightcolor=colors["border"],
            darkcolor=colors["border"],
            focuscolor=self.accent_blue,
            padding=(spacing["md"], spacing["sm"]),
            font=font,
        )
        self.style.map(
            "TButton",
            background=[
                ("disabled", colors["surface"]),
                ("pressed", colors["surface"]),
                ("active", colors["surface_elevated"]),
            ],
            foreground=[
                ("disabled", colors["text_muted"]),
                ("!disabled", colors["text"]),
            ],
        )
        self.style.configure(
            "TPanedwindow",
            background=colors["background"],
            sashthickness=6,
        )
        self.style.configure(
            "TScrollbar",
            background=colors["surface_elevated"],
            troughcolor=colors["background"],
            arrowcolor=colors["text_secondary"],
            bordercolor=colors["background"],
            lightcolor=colors["surface_elevated"],
            darkcolor=colors["surface_elevated"],
        )
        self.style.configure(
            "TEntry",
            fieldbackground=colors["surface_elevated"],
            foreground=colors["text"],
            insertcolor=colors["text"],
            bordercolor=colors["border"],
        )
        self.style.configure(
            "PacePilot.Section.TFrame",
            background=colors["surface_elevated"],
        )
        self.style.configure(
            "PacePilot.Section.TLabel",
            background=colors["surface_elevated"],
            foreground=colors["text_secondary"],
            font=font,
        )
        self.style.configure(
            "PacePilot.SectionHeader.TLabel",
            background=colors["surface_elevated"],
            foreground=colors["text"],
            font=(
                typography["font_family"],
                typography["size_sm"],
                typography["weight_medium"],
            ),
        )
        self.style.configure(
            "PacePilot.Primary.TButton",
            background=_mix_color(
                colors["surface_elevated"],
                self.accent_blue,
                0.76,
            ),
            foreground=colors["text"],
            bordercolor=self.accent_blue,
            lightcolor=self.accent_blue,
            darkcolor=self.accent_blue,
            focuscolor=self.accent_purple,
            padding=(spacing["lg"], spacing["sm"]),
            font=(
                typography["font_family"],
                typography["size_md"],
                typography["weight_medium"],
            ),
        )
        self.style.map(
            "PacePilot.Primary.TButton",
            background=[
                ("disabled", colors["surface_elevated"]),
                ("pressed", self.accent_purple),
                ("active", self.accent_purple),
            ],
            foreground=[("disabled", colors["text_muted"])],
        )

        self.style.configure(
            "PacePilot.TFrame",
            background=colors["background"],
            borderwidth=borders["thin"],
        )
        self.style.configure(
            "PacePilot.Panel.TLabelframe",
            background=colors["surface"],
            foreground=colors["text"],
            borderwidth=borders["thin"],
            padding=spacing["md"],
        )
        self.style.configure(
            "PacePilot.Panel.TLabelframe.Label",
            background=colors["surface"],
            foreground=colors["text"],
            borderwidth=borders["thin"],
            font=(
                typography["font_family"],
                typography["size_lg"],
                typography["weight_medium"],
            ),
        )
        self.style.configure(
            "PacePilot.Header.TLabel",
            background=colors["background"],
            foreground=colors["text"],
            font=(
                typography["font_family"],
                typography["size_xl"],
                typography["weight_medium"],
            ),
        )
        self.style.configure(
            "PacePilot.HeaderContext.TLabel",
            background=colors["background"],
            foreground=colors["text_muted"],
            font=(
                typography["font_family"],
                typography["size_sm"],
                typography["weight_regular"],
            ),
        )
        self.style.configure(
            "PacePilot.Text.TLabel",
            background=colors["surface"],
            foreground=colors["text_secondary"],
            font=(
                typography["font_family"],
                typography["size_md"],
                typography["weight_regular"],
            ),
        )
        self.style.configure(
            "PacePilot.Status.TLabel",
            background=colors["surface_elevated"],
            foreground=colors["text_secondary"],
            borderwidth=borders["thin"],
            font=(
                typography["font_family"],
                typography["size_sm"],
                typography["weight_regular"],
            ),
        )
        self.style.configure(
            "PacePilot.Treeview",
            background=colors["surface"],
            fieldbackground=colors["surface"],
            foreground=colors["text"],
            borderwidth=borders["thin"],
            font=(
                typography["font_family"],
                typography["size_md"],
                typography["weight_regular"],
            ),
        )
        self.style.map(
            "PacePilot.Treeview",
            background=[("selected", colors["accent"])],
            foreground=[("selected", colors["text"])],
        )

    def apply_root(self, widget: tk.Tk) -> None:
        widget.configure(background=self.tokens.colors["background"])

    def register_ambient_surface(self, widget) -> None:
        key = str(widget)
        if key in self._ambient_surfaces:
            return
        try:
            original = widget.cget("style") or widget.winfo_class()
        except tk.TclError:
            return
        self._ambient_surfaces[key] = (widget, original)

    def apply_ambient_field(self, intensity: float) -> None:
        intensity = min(max(float(intensity), 0.0), 1.0)

        for widget, original in tuple(self._ambient_surfaces.values()):
            try:
                base = (
                    self.colors["surface"]
                    if "TLabelframe" in str(original)
                    else self.colors["background"]
                )
                color = _mix_color(
                    base,
                    self.accent_blue,
                    intensity * 0.055,
                )
                style_name = (
                    f"PacePilot.Ambient{id(widget)}.{widget.winfo_class()}"
                )
                self.style.configure(
                    style_name,
                    background=color,
                    foreground=self.style.lookup(
                        original,
                        "foreground",
                    ) or self.colors["text"],
                )
                if widget.winfo_class() == "TLabelframe":
                    self.style.configure(
                        f"{style_name}.Label",
                        background=color,
                        foreground=self.colors["text"],
                    )
                widget.configure(style=style_name)
            except tk.TclError:
                continue

    def apply_header_frame(self, widget: ttk.Frame) -> None:
        widget.configure(style="PacePilot.TFrame")

    def apply_header_context(self, widget: ttk.Label) -> None:
        widget.configure(style="PacePilot.HeaderContext.TLabel")

    def apply_panedwindow(self, widget: ttk.Panedwindow) -> None:
        widget.configure(style="PacePilot.TPanedwindow")

    def apply_section_frame(self, widget: ttk.Frame) -> None:
        widget.configure(style="PacePilot.Section.TFrame")

    def apply_section_label(self, widget: ttk.Label) -> None:
        widget.configure(style="PacePilot.Section.TLabel")

    def apply_section_header(self, widget: ttk.Label) -> None:
        widget.configure(style="PacePilot.SectionHeader.TLabel")

    def apply_primary_action(self, widget: ttk.Button) -> None:
        widget.configure(style="PacePilot.Primary.TButton")

    def apply_listbox(self, widget: tk.Listbox) -> None:
        colors = self.tokens.colors
        widget.configure(
            background=colors["surface"],
            foreground=colors["text_secondary"],
            selectbackground=self.accent_blue,
            selectforeground=colors["text"],
            highlightbackground=colors["border"],
            highlightcolor=self.accent_purple,
            highlightthickness=1,
            borderwidth=0,
            relief=tk.FLAT,
            activestyle="none",
        )


    def apply_pointer_text(self, widget: tk.Text, intensity: float) -> None:
        key = str(widget)
        if key not in self._pointer_text_colors:
            self._pointer_text_colors[key] = (
                widget,
                str(widget.cget("background")),
            )
        widget, original = self._pointer_text_colors[key]
        if intensity <= 0.01:
            widget.configure(background=original)
            return
        widget.configure(
            background=_mix_color(
                original,
                self.accent_blue,
                min(max(intensity, 0.0), 0.3) * 0.18,
            )
        )

    def apply_header(self, widget: ttk.Label) -> None:
        widget.configure(style="PacePilot.Header.TLabel")

    def apply_navigation(self, widget: ttk.LabelFrame) -> None:
        widget.configure(style="PacePilot.Panel.TLabelframe")

    def apply_workspace(self, widget: ttk.LabelFrame) -> None:
        widget.configure(style="PacePilot.Panel.TLabelframe")

    def apply_tree(self, widget: ttk.Treeview) -> None:
        widget.configure(style="PacePilot.Treeview")

    def apply_text_label(self, widget: ttk.Label) -> None:
        widget.configure(style="PacePilot.Text.TLabel")

    def apply_status(
        self,
        widget: tk.Label,
        interaction_state: str = "ready",
    ) -> None:
        colors = self.tokens.colors
        typography = self.tokens.typography
        borders = self.tokens.borders

        widget.configure(
            background=colors["surface_elevated"],
            foreground=colors["text_secondary"],
            borderwidth=borders["thin"],
            font=(
                typography["font_family"],
                typography["size_sm"],
                typography["weight_regular"],
            ),
        )

        semantic = self.semantic_mapper.semantic_for(interaction_state)
        self.apply_status_semantic(widget, semantic)

    def apply_status_semantic(
        self,
        widget: tk.Label,
        semantic: str,
    ) -> None:
        token_name = self.semantic_mapper.color_token_for(semantic)
        widget.configure(
            foreground=self.tokens.colors[token_name],
        )

    def apply_text_viewer(self, widget: tk.Text) -> None:
        colors = self.tokens.colors
        borders = self.tokens.borders
        typography = self.tokens.typography

        widget.configure(
            background=colors["surface"],
            foreground=colors["text"],
            insertbackground=colors["text"],
            selectbackground=self.accent_blue,
            selectforeground=colors["text"],
            borderwidth=borders["thin"],
            highlightthickness=0,
            font=(
                typography["font_family"],
                typography["size_md"],
            ),
        )


def _mix_color(start: str, end: str, ratio: float) -> str:
    ratio = min(max(ratio, 0.0), 1.0)
    channels = tuple(
        round(
            int(start[index:index + 2], 16) * (1 - ratio)
            + int(end[index:index + 2], 16) * ratio
        )
        for index in (1, 3, 5)
    )
    return "#" + "".join(f"{channel:02X}" for channel in channels)




