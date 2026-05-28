import threading
import flet as ft
from shared.logger import get_logger
from app.features.users.domain.course_service import sync_courses_for_dni, get_local_courses
from app.features.users.presentation.widgets.status_banner import StatusBanner
from app.features.users.presentation.widgets.courses_data_table import CoursesDataTable

logger = get_logger(__name__)


class SyncCoursesView(ft.Column):
    def __init__(self, page: ft.Page):
        self._page = page

        # Componentes
        self._progress = ft.ProgressBar(visible=False, height=2)
        self._status_banner = StatusBanner()
        self._data_table = CoursesDataTable()

        self._dni_input = ft.TextField(
            label="Buscar o Sincronizar por DNI",
            hint_text="Ej. 43556935",
            width=300,
            on_submit=self._on_sync_click,
            autofocus=True,
        )
        self._sync_btn = ft.FilledButton(
            "Obtener Datos HSEC",
            icon="cloud_download",
            on_click=self._on_sync_click,
        )
        self._local_btn = ft.OutlinedButton(
            "Ver Local",
            icon="storage",
            on_click=self._on_local_click,
        )

        actions_row = ft.Row(
            spacing=10,
            controls=[
                self._dni_input,
                self._sync_btn,
                self._local_btn,
            ],
        )

        super().__init__(
            expand=True,
            spacing=12,
            controls=[
                actions_row,
                self._progress,
                self._status_banner,
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                self._data_table,
            ],
        )

    def _show_status(self, message: str, is_error: bool = False, is_success: bool = False) -> None:
        self._status_banner.show(message, is_error=is_error, is_success=is_success)
        self._page.update()

    def _set_loading(self, loading: bool, message: str = "") -> None:
        self._progress.visible = loading
        self._dni_input.disabled = loading
        self._sync_btn.disabled = loading
        self._local_btn.disabled = loading
        if message:
            self._show_status(message)
        elif not loading:
            self._status_banner.hide()
        self._page.update()

    def _on_local_click(self, e) -> None:
        dni = self._dni_input.value.strip()
        if not dni:
            self._show_status("Por favor ingresa un DNI", is_error=True)
            return

        try:
            courses = get_local_courses(dni)
            if not courses:
                self._show_status(f"No hay cursos registrados localmente para DNI {dni}", is_error=True)
                self._data_table.clear()
            else:
                self._status_banner.hide()
                self._data_table.update_records(courses)
        except Exception as ex:
            self._show_status(f"Error local: {ex}", is_error=True)

    def _on_sync_click(self, e) -> None:
        dni = self._dni_input.value.strip()
        if not dni:
            self._show_status("Por favor ingresa un DNI", is_error=True)
            return

        self._set_loading(True, f"Conectando a HSEC (Modo Invisible) para extraer reporte de DNI {dni}...")
        self._data_table.clear()

        def task() -> None:
            try:
                courses, message = sync_courses_for_dni(dni, headless=True)
                if courses:
                    self._show_status(message, is_success=True)
                    self._data_table.update_records(courses)
                else:
                    self._show_status(message, is_error=True)
            except Exception as ex:
                logger.exception("Error sincronizando cursos desde HSEC")
                self._show_status(f"Error: {ex}", is_error=True)
            finally:
                self._set_loading(False)

        threading.Thread(target=task, daemon=True).start()
