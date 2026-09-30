"""Tkinter rendering adapter for the immutable UX composition layer."""

import tkinter as tk
from tkinter import ttk

from .visual_composition import UXComposition
from .visual_semantic_mapper import VisualSemanticMapper


class VisualRenderer:
    """Apply UX composition tokens to Tkinter widgets."""

    def __init__(self, root: tk.Tk, composition: UXComposition) -> None:
        self.root = root
        self.composition = composition
        self.tokens = composition.tokens
        self.style = ttk.Style(root)
        self.semantic_mapper = VisualSemanticMapper()

        self._configure_styles()

    def _configure_styles(self) -> None:
        colors = self.tokens.colors
        typography = self.tokens.typography
        borders = self.tokens.borders
        spacing = self.tokens.spacing

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
            selectbackground=colors["accent"],
            selectforeground=colors["text"],
            borderwidth=borders["thin"],
            highlightthickness=0,
            font=(
                typography["font_family"],
                typography["size_md"],
            ),
        )




