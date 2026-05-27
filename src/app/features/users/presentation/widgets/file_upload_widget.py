import flet as ft
from shared.logger import get_logger

logger = get_logger(__name__)

class FileUploadWidget(ft.Container):
    def __init__(self, on_file_selected: callable):
        self._on_file_selected = on_file_selected
        self._file_picker = ft.FilePicker()

        self._upload_button = ft.OutlinedButton(
            "Importar archivo",
            icon=ft.Icons.UPLOAD_FILE_OUTLINED,
            on_click=self._on_upload_click,
        )

        super().__init__(
            content=self._upload_button,
        )

    def did_mount(self):
        # En Flet v0.85, FilePicker se agrega a la página de forma implícita cuando se usa, 
        # o podemos agregarlo al overlay si es necesario. Como es un Service, se puede agregar al overlay.
        # Pero los estándares dicen: "do NOT add it to page.overlay... No append! Just use it."
        pass

    def set_disabled(self, disabled: bool) -> None:
        self._upload_button.disabled = disabled
        self.update()

    async def _on_upload_click(self, e) -> None:
        try:
            # En Flet v0.85 el file picker no se añade a la página, solo se invoca pick_files
            files = await self._file_picker.pick_files(
                allow_multiple=False,
                allowed_extensions=["csv", "xlsx", "xls"],
            )
            if files and files[0].path:
                self._on_file_selected(files[0].path)
        except Exception as ex:
            logger.exception("Error al seleccionar archivo en widget")
            # Propagar o manejar el error
