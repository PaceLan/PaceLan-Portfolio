"""PacePilot product-growth history presentation."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .product_history import ProductGrowthEvent, ProductHistory
from .visual_tokens import DEFAULT_VISUAL_TOKENS


class ProductHistoryView:
    """Present product-growth history as a standalone read-only view."""

    def __init__(
        self,
        parent,
        history: ProductHistory,
        *,
        tokens=None,
    ) -> None:
        self.parent = parent
        self.history = history
        self.tokens = tokens or DEFAULT_VISUAL_TOKENS

        colors = self.tokens.colors
        typography = self.tokens.typography
        spacing = self.tokens.spacing
        borders = self.tokens.borders

        self.frame = ttk.Frame(
            parent,
            padding=spacing["lg"],
        )
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=2)
        self.frame.rowconfigure(2, weight=1)

        self.heading = tk.Label(
            self.frame,
            text="PacePilot Growth History",
            anchor="w",
            bg=colors["background"],
            fg=colors["text"],
            font=(
                typography["font_family"],
                typography["size_xl"],
                typography["weight_medium"],
            ),
        )
        self.heading.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(0, spacing["sm"]),
        )

        self.summary = tk.Label(
            self.frame,
            text="",
            anchor="w",
            justify="left",
            wraplength=900,
            bg=colors["background"],
            fg=colors["text_secondary"],
            font=(
                typography["font_family"],
                typography["size_sm"],
                typography["weight_regular"],
            ),
        )
        self.summary.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(0, spacing["md"]),
        )

        timeline_frame = ttk.Frame(self.frame)
        timeline_frame.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=(0, spacing["md"]),
        )
        timeline_frame.rowconfigure(0, weight=1)
        timeline_frame.columnconfigure(0, weight=1)

        self.timeline = tk.Listbox(
            timeline_frame,
            activestyle="none",
            exportselection=False,
            bg=colors["surface"],
            fg=colors["text"],
            selectbackground=colors["accent"],
            selectforeground=colors["text"],
            highlightbackground=colors["border"],
            highlightcolor=colors["accent"],
            highlightthickness=borders["thin"],
            relief="flat",
            font=(
                typography["font_family"],
                typography["size_sm"],
                typography["weight_regular"],
            ),
        )
        self.timeline.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        timeline_scrollbar = ttk.Scrollbar(
            timeline_frame,
            orient="vertical",
            command=self.timeline.yview,
        )
        timeline_scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )
        self.timeline.configure(
            yscrollcommand=timeline_scrollbar.set,
        )

        self.details = tk.Text(
            self.frame,
            wrap="word",
            state="disabled",
            height=18,
            bg=colors["surface"],
            fg=colors["text"],
            insertbackground=colors["text"],
            selectbackground=colors["accent"],
            selectforeground=colors["text"],
            highlightbackground=colors["border"],
            highlightcolor=colors["accent"],
            highlightthickness=borders["thin"],
            relief="flat",
            padx=spacing["md"],
            pady=spacing["md"],
            font=(
                typography["font_family"],
                typography["size_sm"],
                typography["weight_regular"],
            ),
        )
        self.details.grid(
            row=2,
            column=1,
            sticky="nsew",
        )

        self.timeline.bind(
            "<<ListboxSelect>>",
            self._on_selection,
        )

        self._render()

    def _render(self) -> None:
        self.timeline.delete(0, tk.END)
        self._clear_details()

        self.summary.configure(
            text=self.history.summary(),
        )

        events = self.history.timeline()

        for event in events:
            self.timeline.insert(
                tk.END,
                f"{event.date}  •  {event.title}  •  {event.version}",
            )

        if events:
            self.timeline.selection_set(0)
            self.timeline.activate(0)
            self._show_event(events[0])

    def _on_selection(self, _event=None) -> None:
        selection = self.timeline.curselection()
        if not selection:
            self._clear_details()
            return

        events = self.history.timeline()
        index = selection[0]

        if index >= len(events):
            self._clear_details()
            return

        self._show_event(events[index])

    def _show_event(self, event: ProductGrowthEvent) -> None:
        lines = [
            event.title,
            "",
            f"Date: {event.date}",
            f"Version: {event.version}",
            f"Module: {event.module}",
            f"Category: {event.category}",
        ]

        sections = (
            ("Added", event.added),
            ("Changed", event.changed),
            ("Fixed", event.fixed),
            ("Notes", event.notes),
        )

        for label, value in sections:
            if value.strip():
                lines.extend(("", f"{label}:", value))

        self.details.configure(state="normal")
        self.details.delete("1.0", tk.END)
        self.details.insert("1.0", "\n".join(lines))
        self.details.configure(state="disabled")

    def _clear_details(self) -> None:
        self.details.configure(state="normal")
        self.details.delete("1.0", tk.END)
        self.details.configure(state="disabled")

    def refresh(self, history: ProductHistory) -> None:
        self.history = history
        self._render()

    def pack(self, **kwargs) -> None:
        self.frame.pack(**kwargs)

    def grid(self, **kwargs) -> None:
        self.frame.grid(**kwargs)

    def destroy(self) -> None:
        self.frame.destroy()


__all__ = ["ProductHistoryView"]
