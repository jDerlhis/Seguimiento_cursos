import threading
import flet as ft
from shared.logger import get_logger
from app.features.users.domain import people_repository
from app.features.users.domain.person_service import import_people_from_file

# Widgets
from app.features.users.presentation.widgets.status_banner import StatusBanner
from app.features.users.presentation.widgets.file_upload_widget import FileUploadWidget
from app.features.users.presentation.widgets.people_data_table import PeopleDataTable

logger = get_logger(__name__)


class ImportPersonView(ft.Column):
    def __init__(self, page: ft.Page):
        self._page = page

        # ─── Componentes ───────────────────────────────────────────────────────
        self._progress = ft.ProgressBar(visible=False, height=2)
        self._status_banner = StatusBanner()

        self._upload_widget = FileUploadWidget(
            on_file_selected=self._on_file_uploaded,
        )

        self._data_table = PeopleDataTable(
            on_delete_click=self._show_delete_dialog,
            on_filter_change=self._load_people,
        )

        # ─── Diálogo de eliminación ────────────────────────────────────────────
        self._delete_dni = None
        self._delete_confirm_dialog = ft.AlertDialog(
            title=ft.Text("Eliminar usuario"),
            content=ft.Text(""),
            actions=[
                ft.TextButton("Cancelar", on_click=self._close_delete_dialog),
                ft.FilledButton(
                    "Eliminar",
                    bgcolor=ft.Colors.ERROR,
                    color=ft.Colors.ON_ERROR,
                    on_click=self._execute_delete_person,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        # ─── Layout ────────────────────────────────────────────────────────────
        actions_row = ft.Row(
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                self._upload_widget,
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
        self._load_people()

    # ─── Helpers de estado ─────────────────────────────────────────────────────

    def _show_status(self, message: str, is_error: bool = False, is_success: bool = False) -> None:
        self._status_banner.show(message, is_error=is_error, is_success=is_success)

    def _set_loading(self, loading: bool, message: str = "") -> None:
        self._progress.visible = loading
        self._upload_widget.set_disabled(loading)
        if message:
            self._show_status(message)
        elif not loading:
            self._status_banner.hide()

    # ─── Callbacks de archivo ──────────────────────────────────────────────────

    def _on_file_uploaded(self, file_path: str) -> None:
        self._set_loading(True, "Procesando archivo e importando a HSEC...")

        def task() -> None:
            try:
                def progress_cb(current: int, total: int, dni_act: str) -> None:
                    self._show_status(f"Procesando {current}/{total} — DNI {dni_act}")

                result = import_people_from_file(file_path, progress_callback=progress_cb)
                if result["total"] == 0:
                    self._show_status("No se encontraron DNIs válidos en el archivo.", is_error=True)
                else:
                    self._show_status(
                        f"Completado: {result['added']} nuevos, {result['already_exists']} existentes, {result['not_found']} no encontrados.",
                        is_success=True,
                    )
                self._load_people()
            except Exception as ex:
                logger.exception("Error en carga masiva")
                self._show_status(f"Error: {ex}", is_error=True)
            finally:
                self._set_loading(False)

        threading.Thread(target=task, daemon=True).start()

    # ─── Callbacks de eliminación y filtrado ───────────────────────────────────

    def _show_delete_dialog(self, dni: str, name: str) -> None:
        self._delete_dni = dni
        self._delete_confirm_dialog.content = ft.Text(f"¿Eliminar a {name} (DNI {dni}) del registro local?")
        self._page.dialog = self._delete_confirm_dialog
        self._delete_confirm_dialog.open = True
        self._page.update()

    def _close_delete_dialog(self, e) -> None:
        self._delete_confirm_dialog.open = False
        self._page.update()

    def _execute_delete_person(self, e) -> None:
        self._delete_confirm_dialog.open = False
        if self._delete_dni:
            dni = self._delete_dni
            self._delete_dni = None
            try:
                people_repository.delete_person(dni)
                self._show_status(f"DNI {dni} eliminado.", is_success=True)
                self._load_people()
            except Exception as ex:
                self._show_status(f"Error al eliminar: {ex}", is_error=True)
        self._page.update()

    def _load_people(self) -> None:
        people = people_repository.list_people()
        total_count = len(people)
        filter_val = self._data_table.get_filter_value()

        if filter_val:
            people = [
                p for p in people
                if (
                    filter_val in p.nro_documento.lower()
                    or filter_val in p.nombres.lower()
                    or filter_val in p.apellido_paterno.lower()
                    or (p.apellido_materno and filter_val in p.apellido_materno.lower())
                    or (p.empresa and filter_val in p.empresa.lower())
                )
            ]

        self._data_table.update_records(people, total_count)
