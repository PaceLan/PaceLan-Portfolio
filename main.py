from cli_compat import main as _legacy_cli_main
from ui.app_entry import main

_desktop_main = main
_UNSET = object()


def main(history_store=_UNSET):
    """Start Desktop, or use the legacy CLI for explicit store callers."""
    if history_store is _UNSET:
        return _desktop_main()
    return _legacy_cli_main(history_store)


if __name__ == "__main__":
    main()
