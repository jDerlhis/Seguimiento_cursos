import sys
from pathlib import Path

import flet as ft

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.router.root_router import build_root  # noqa: E402
from infra.initializer import initialize_app  # noqa: E402


def main(page: ft.Page) -> None:
    initialize_app()
    page.title = "Omnimina"
    page.theme_mode = ft.ThemeMode.SYSTEM
    page.padding = 0
    page.spacing = 0
    page.window.width = 1100
    page.window.height = 720
    page.window.min_width = 900
    page.window.min_height = 560

    page.add(build_root(page))


if __name__ == "__main__":
    ft.run(main)
