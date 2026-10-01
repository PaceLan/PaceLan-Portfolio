"""Small monochrome Tk PhotoImage icons for functional PacePilot controls."""

from __future__ import annotations

import math
import tkinter as tk

from ui.visual_tokens import DEFAULT_VISUAL_TOKENS, VisualTokens


class VisualIconSet:
    """Create a cached, consistent set of 16px outline icons without a dependency."""

    SIZE = 16

    def __init__(
        self,
        root: tk.Misc,
        tokens: VisualTokens = DEFAULT_VISUAL_TOKENS,
    ) -> None:
        self.foreground = tokens.colors["text_secondary"]
        self.accent = tokens.colors.get("accent_blue", tokens.colors["accent"])
        self._images = {
            name: self._build(root, name)
            for name in (
                "brand",
                "folder",
                "file",
                "workspace",
                "agent",
                "task",
                "understanding",
                "plan",
                "approval",
                "execution",
                "pause",
                "stop",
                "result",
                "history",
            )
        }

    def image(self, name: str) -> tk.PhotoImage:
        return self._images[name]

    def names(self) -> tuple[str, ...]:
        return tuple(self._images)

    def _build(self, root: tk.Misc, name: str) -> tk.PhotoImage:
        image = tk.PhotoImage(master=root, width=self.SIZE, height=self.SIZE)
        color = self.accent if name in {"brand", "folder"} else self.foreground
        line = self._line

        if name in {"brand", "agent"}:
            self._circle(image, 8, 8, 5, color)
            line(image, 8, 2, 8, 5, color)
            line(image, 8, 11, 8, 14, color)
            line(image, 2, 8, 5, 8, color)
            line(image, 11, 8, 14, 8, color)
            if name == "brand":
                line(image, 5, 5, 11, 11, color)
                line(image, 11, 5, 5, 11, color)
        elif name == "folder":
            for segment in (
                (1, 4, 5, 4),
                (5, 4, 7, 6),
                (7, 6, 15, 6),
                (15, 6, 14, 13),
                (14, 13, 2, 13),
                (2, 13, 1, 4),
            ):
                line(image, *segment, color)
        elif name == "file":
            for segment in (
                (4, 2, 10, 2),
                (10, 2, 13, 5),
                (13, 5, 13, 14),
                (13, 14, 4, 14),
                (4, 14, 4, 2),
                (10, 2, 10, 5),
                (10, 5, 13, 5),
                (6, 8, 11, 8),
                (6, 11, 11, 11),
            ):
                line(image, *segment, color)
        elif name == "workspace":
            self._rect(image, 2, 3, 14, 13, color)
            line(image, 2, 6, 14, 6, color)
            line(image, 6, 6, 6, 13, color)
        elif name == "task":
            for y in (4, 8, 12):
                self._rect(image, 2, y - 1, 4, y + 1, color)
                line(image, 7, y, 14, y, color)
        elif name == "understanding":
            self._circle(image, 7, 7, 4, color)
            line(image, 10, 10, 14, 14, color)
        elif name == "plan":
            for y in (3, 7, 11):
                line(image, 5, y, 14, y, color)
                image.put(color, to=(2, y))
        elif name == "approval":
            for segment in (
                (8, 1, 14, 4),
                (14, 4, 13, 10),
                (13, 10, 8, 15),
                (8, 15, 3, 10),
                (3, 10, 2, 4),
                (2, 4, 8, 1),
                (5, 8, 7, 10),
                (7, 10, 11, 6),
            ):
                line(image, *segment, color)
        elif name == "execution":
            for segment in (
                (5, 3, 12, 8),
                (12, 8, 5, 13),
                (5, 13, 5, 3),
            ):
                line(image, *segment, color)
        elif name == "pause":
            self._rect(image, 4, 3, 6, 13, color)
            self._rect(image, 10, 3, 12, 13, color)
        elif name == "stop":
            self._rect(image, 3, 3, 13, 13, color)
        elif name == "result":
            self._circle(image, 8, 8, 6, color)
            line(image, 4, 8, 7, 11, color)
            line(image, 7, 11, 12, 5, color)
        elif name == "history":
            self._circle(image, 8, 8, 6, color)
            line(image, 8, 4, 8, 8, color)
            line(image, 8, 8, 11, 10, color)
            line(image, 2, 4, 2, 8, color)
        return image

    @classmethod
    def _line(
        cls,
        image: tk.PhotoImage,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        color: str,
    ) -> None:
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        error = dx + dy
        while True:
            image.put(color, to=(x0, y0))
            if x0 == x1 and y0 == y1:
                break
            doubled = 2 * error
            if doubled >= dy:
                error += dy
                x0 += sx
            if doubled <= dx:
                error += dx
                y0 += sy

    @classmethod
    def _rect(
        cls,
        image: tk.PhotoImage,
        left: int,
        top: int,
        right: int,
        bottom: int,
        color: str,
    ) -> None:
        cls._line(image, left, top, right, top, color)
        cls._line(image, right, top, right, bottom, color)
        cls._line(image, right, bottom, left, bottom, color)
        cls._line(image, left, bottom, left, top, color)

    @classmethod
    def _circle(
        cls,
        image: tk.PhotoImage,
        center_x: int,
        center_y: int,
        radius: int,
        color: str,
    ) -> None:
        points = tuple(
            (
                round(center_x + math.cos(index * math.tau / 48) * radius),
                round(center_y + math.sin(index * math.tau / 48) * radius),
            )
            for index in range(49)
        )
        for first, second in zip(points, points[1:]):
            cls._line(image, *first, *second, color)


__all__ = ["VisualIconSet"]
