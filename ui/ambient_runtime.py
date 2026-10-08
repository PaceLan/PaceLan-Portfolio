from __future__ import annotations

import tkinter as tk


class AmbientRuntime:
    """Runtime layer for global ambient visual experience."""

    def __init__(
        self,
        root,
        *,
        ambient,
        theme_state,
        visual_renderer,
        composition,
    ) -> None:
        self.root = root
        self.ambient = ambient
        self.theme_state = theme_state
        self.visual_renderer = visual_renderer
        self.composition = composition

        self.canvas = None
        self._after = None
        self._phase = 0.0

    def register_surface(self, widget) -> None:
        """Compatibility hook for VisualExperience surface registration.

        The baseline ambient runtime renders one global canvas behind the
        complete application, so individual surface registration is not
        required.
        """
        return

    def build(self) -> None:
        if self.canvas is not None:
            return

        colors = self.composition.tokens.colors

        self.canvas = tk.Canvas(
            self.root,
            highlightthickness=0,
            bd=0,
            bg=colors["background"],
        )

        self.canvas.place(
            relx=0,
            rely=0,
            relwidth=1,
            relheight=1,
        )
        self.canvas.tk.call("lower", self.canvas._w)

        self.root.bind(
            "<Configure>",
            self._on_resize,
            add="+",
        )
        self.root.bind(
            "<Destroy>",
            self._on_destroy,
            add="+",
        )

    def start(self) -> None:
        self.build()

        if self._after is not None:
            return

        self.ambient.start()
        self._animate()

    def stop(self) -> None:
        if self._after is not None:
            try:
                self.root.after_cancel(self._after)
            except tk.TclError:
                pass
            self._after = None

        self.ambient.stop()

    def _on_resize(self, _event) -> None:
        self.render()

    def _on_destroy(self, event) -> None:
        if event.widget is not self.root:
            return

        if self._after is not None:
            try:
                self.root.after_cancel(self._after)
            except tk.TclError:
                pass
            self._after = None

        self.ambient.stop()

    def _animate(self) -> None:
        self._after = None

        if not self.root.winfo_exists():
            return

        self._phase = (self._phase + 0.0035) % 1.0
        self.render()

        self._after = self.root.after(
            55,
            self._animate,
        )

    def render(self) -> None:
        if self.canvas is None:
            return

        canvas = self.canvas

        width = max(canvas.winfo_width(), 1)
        height = max(canvas.winfo_height(), 1)

        canvas.configure(
            bg=self.theme_state.palette.background,
        )
        canvas.delete("ambient")

        state = self.ambient.snapshot(self._phase)
        total_intensity = 0.0

        for layer in state.layers:
            pulse = self.ambient.layer_opacity(
                layer,
                state.phase,
                state.intensity,
            )

            total_intensity += pulse

            cx = width * layer.x
            cy = height * layer.y
            radius = min(width, height) * layer.radius

            for index in range(9, 0, -1):
                ratio = index / 9
                r = radius * ratio
                opacity = pulse * (1.0 - ratio) * 1.35

                fill = _blend_hex(
                    self.theme_state.palette.background,
                    layer.color,
                    opacity,
                )

                canvas.create_oval(
                    cx - r,
                    cy - r,
                    cx + r,
                    cy + r,
                    fill=fill,
                    outline="",
                    tags="ambient",
                )

        if self.visual_renderer is not None:
            self.visual_renderer.apply_ambient_field(
                total_intensity / max(len(state.layers), 1)
            )


def _blend_hex(base: str, overlay: str, amount: float) -> str:
    amount = max(0.0, min(amount, 1.0))

    def parse(value: str):
        value = value.lstrip("#")
        return (
            int(value[0:2], 16),
            int(value[2:4], 16),
            int(value[4:6], 16),
        )

    b = parse(base)
    o = parse(overlay)

    result = tuple(
        round(
            b[index] + (o[index] - b[index]) * amount
        )
        for index in range(3)
    )

    return "#{:02x}{:02x}{:02x}".format(*result)
