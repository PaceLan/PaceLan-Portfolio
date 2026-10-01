"""Global Day/Night theme definitions for PacePilot M26.3."""

from dataclasses import dataclass
from typing import Literal


ThemeMode = Literal["night", "day"]


@dataclass(frozen=True)
class ThemePalette:
    background: str
    surface: str
    surface_elevated: str
    text: str
    text_muted: str
    border: str
    accent: str
    success: str
    warning: str
    error: str
    agent_running: str


NIGHT_THEME = ThemePalette(
    background="#0F1115",
    surface="#171A21",
    surface_elevated="#1E222B",
    text="#F3F6FA",
    text_muted="#9AA4B2",
    border="#2A303B",
    accent="#5B8DEF",
    success="#45C486",
    warning="#E6B450",
    error="#E05A67",
    agent_running="#8B7CF6",
)


DAY_THEME = ThemePalette(
    background="#F4F7FB",
    surface="#FFFFFF",
    surface_elevated="#EAF0F7",
    text="#172033",
    text_muted="#687386",
    border="#D5DDE8",
    accent="#3E73D8",
    success="#238A5B",
    warning="#B47712",
    error="#C83E4B",
    agent_running="#725BC7",
)


@dataclass(frozen=True)
class ThemeState:
    mode: ThemeMode = "night"

    @property
    def palette(self) -> ThemePalette:
        return NIGHT_THEME if self.mode == "night" else DAY_THEME

    @property
    def is_night(self) -> bool:
        return self.mode == "night"

    def toggled(self) -> "ThemeState":
        return ThemeState("day" if self.is_night else "night")


def palette_for(mode: ThemeMode) -> ThemePalette:
    return NIGHT_THEME if mode == "night" else DAY_THEME
