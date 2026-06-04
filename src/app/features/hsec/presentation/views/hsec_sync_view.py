import threading

import flet as ft

from app.features.hsec.domain import hsec_service
from app.common.modules.hsec import SyncResult
from shared.logger import get_logger

logger = get_logger(__name__)


class HsecSyncView(ft.Column):
    def __init__(self, page: ft.Page):
        self._page = page

        self._dnis_field = ft.TextField(
            label="DNIs a sincronizar",
            hint_text="Uno por línea: 12345678\n87654321",
            prefix_icon=ft.Icons.BADGE_OUTLINED,
            multiline=True,
            min_lines=4,
            max_lines=8,
            border_radius=12,
        )

        self._sync_btn = ft.FilledButton(
            "Sincronizar",
            icon=ft.Icons.SYNC_ROUNDED,
            on_click=self._on_sync,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
        )

        self._progress_text = ft.Text("", size=13, color=ft.Colors.ON_SURFACE_VARIANT)
        self._progress_row = ft.Row(
            [
                ft.ProgressRing(width=18, height=18, stroke_width=2.5),
                self._progress_text,
            ],
            spacing=10,
            visible=False,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self._results_list = ft.Column(spacing=6, visible=False)

        super().__init__(
            spacing=16,
            controls=[
                self._dnis_field,
                ft.Row(
                    [self._sync_btn, self._progress_row],
                    spacing=16,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                self._results_list,
            ],
        )

    # ─── Acciones ─────────────────────────────────────────────────────────────

    def _on_sync(self, _e) -> None:
        raw = (self._dnis_field.value or "").strip()
        dnis = [d.strip() for d in raw.splitlines() if d.strip()]

        if not dnis:
            self._dnis_field.error_text = "Ingresa al menos un DNI."
            self._dnis_field.update()
            return

        self._dnis_field.error_text = None
        self._sync_btn.disabled = True
        self._progress_text.value = f"Sincronizando {len(dnis)} DNI(s)..."
        self._progress_row.visible = True
        self._results_list.visible = False
        self._results_list.controls.clear()
        self._page.update()

        def _run() -> None:
            try:
                results = hsec_service.sync(dnis)
                self._render_results(results)
            except Exception as ex:
                logger.exception("Sync HSEC")
                self._render_error(str(ex))
            finally:
                self._sync_btn.disabled = False
                self._progress_row.visible = False
                self._page.update()

        threading.Thread(target=_run, daemon=True).start()

    def _render_results(self, results: list[SyncResult]) -> None:
        self._results_list.controls.clear()

        ok = sum(1 for r in results if not r.error)
        total_cursos = sum(r.cursos_upserted for r in results)

        summary_color = ft.Colors.PRIMARY_CONTAINER if ok == len(results) else ft.Colors.ERROR_CONTAINER
        summary_text_color = ft.Colors.ON_PRIMARY_CONTAINER if ok == len(results) else ft.Colors.ON_ERROR_CONTAINER

        self._results_list.controls.append(
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=14, vertical=10),
                border_radius=10,
                bgcolor=summary_color,
                content=ft.Text(
                    f"{ok}/{len(results)} sincronizados · {total_cursos} cursos guardados",
                    size=13,
                    weight=ft.FontWeight.W_500,
                    color=summary_text_color,
                ),
            )
        )

        for r in results:
            is_ok = not r.error
            icon = ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED if is_ok else ft.Icons.ERROR_OUTLINE_ROUNDED
            color = ft.Colors.ON_SURFACE_VARIANT if is_ok else ft.Colors.ERROR
            detail = f"{r.cursos_upserted} cursos" if is_ok else r.error

            self._results_list.controls.append(
                ft.Row(
                    [
                        ft.Icon(icon, size=15, color=color),
                        ft.Text(r.dni, size=13, weight=ft.FontWeight.W_500, width=100),
                        ft.Text(detail, size=12, color=ft.Colors.ON_SURFACE_VARIANT, expand=True),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )

        self._results_list.visible = True

    def _render_error(self, message: str) -> None:
        self._results_list.controls.clear()
        self._results_list.controls.append(
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=14, vertical=10),
                border_radius=10,
                bgcolor=ft.Colors.ERROR_CONTAINER,
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, size=16, color=ft.Colors.ON_ERROR_CONTAINER),
                        ft.Text(message, size=13, color=ft.Colors.ON_ERROR_CONTAINER, expand=True),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
        )
        self._results_list.visible = True


def build_hsec_sync_view(page: ft.Page) -> HsecSyncView:
    return HsecSyncView(page)
