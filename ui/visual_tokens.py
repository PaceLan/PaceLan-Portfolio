"""Framework-agnostic visual design tokens for PacePilot."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class VisualTokens:
    """Immutable visual language foundation shared by UI implementations."""

    colors: Mapping[str, str] = MappingProxyType({
        "background": "#0F1115",
        "surface": "#171A21",
        "surface_elevated": "#1E222B",
        "text": "#F2F4F7",
        "text_secondary": "#A7AFBC",
        "text_muted": "#737C8A",
        "border": "#303641",
        "accent": "#5B8DEF",
        "info": "#4FA3FF",
        "success": "#45C486",
        "warning": "#E6B450",
        "error": "#E05A67",
        "agent_running": "#8B7CF6",
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
