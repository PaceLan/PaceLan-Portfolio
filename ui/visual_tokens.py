"""Framework-agnostic visual design tokens for PacePilot."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class VisualTokens:
    """Immutable visual language foundation shared by UI implementations."""

    colors: Mapping[str, str] = MappingProxyType({
        "background": "#0B0F17",
        "surface": "#121722",
        "surface_elevated": "#1A2030",
        "text": "#E8ECF5",
        "text_secondary": "#929DB2",
        "text_muted": "#6F7B93",
        "border": "#28334A",
        "accent": "#5B8DEF",
        "accent_blue": "#5B8DEF",
        "accent_purple": "#8B7CF6",
        "info": "#79A9FF",
        "success": "#45C486",
        "warning": "#E6B450",
        "error": "#E05A67",
        "agent_running": "#8B7CF6",
        "agent_waiting": "#746CE0",
    })

    typography: Mapping[str, object] = MappingProxyType({
        "font_family": "TkDefaultFont",
        "size_xs": 10,
        "size_sm": 11,
        "size_md": 12,
        "size_lg": 14,
        "size_xl": 16,
        "size_xxl": 20,
        "weight_regular": "normal",
        "weight_medium": "bold",
    })

    spacing: Mapping[str, int] = MappingProxyType({
        "xs": 4,
        "sm": 8,
        "md": 12,
        "lg": 16,
        "xl": 24,
        "xxl": 32,
    })

    radius: Mapping[str, int] = MappingProxyType({
        "sm": 4,
        "md": 8,
        "lg": 12,
    })

    borders: Mapping[str, int] = MappingProxyType({
        "thin": 1,
        "medium": 2,
    })


DEFAULT_VISUAL_TOKENS = VisualTokens()
