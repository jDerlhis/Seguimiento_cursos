# Flet Development Standards (v0.85.2 Compatibility)

This document outlines the specific syntax requirements and architectural constraints identified for the Flet environment in this project (verified with **flet 0.85.2**). Adhering to these standards prevents runtime `AttributeError`, `TypeError`, and msgpack serialization failures.

## Quick reference (errores frecuentes)

| Síntoma | Causa | Usar en su lugar |
|--------|--------|------------------|
| `padding` has no attribute `symmetric` | `ft.padding` es un submódulo, no la clase | `ft.Padding.symmetric(horizontal=12, vertical=10)` |
| `alignment` has no attribute `center` | `ft.alignment` es un submódulo | `ft.Alignment(0, 0)` |
| `Tab.__init__() got unexpected keyword 'text'` | API antigua | `ft.Tab(label="...")` |
| `Tabs.__init__() got unexpected keyword 'tabs'` | Constructor cambió en 0.85 | Ver §4 Tabs / preferir `SegmentedButton` |
| `can not serialize 'set' object` | msgpack no serializa `set` | `selected=["login"]` (lista), nunca `{"login"}` |
| `SURFACE_VARIANT` AttributeError | Constante inexistente en `ft.Colors` | `SURFACE_CONTAINER` o `ON_SURFACE_VARIANT` (texto) |

## 1. Alignment and Positioning
Always use **UPPERCASE** constants for alignment and positioning. Lowercase attributes are deprecated or unsupported in this build.

*   **Correct**: `ft.MainAxisAlignment.CENTER`, `ft.CrossAxisAlignment.START`, `ft.MainAxisAlignment.SPACE_BETWEEN`.
*   **Incorrect**: `ft.MainAxisAlignment.center`, `ft.CrossAxisAlignment.start`.

## 2. Style and Layout Objects
Instantiate style objects using the **class** on the root module (`ft.Padding`, `ft.Alignment`, `ft.Border`). The lowercase submodules (`ft.padding`, `ft.alignment`) exist but **no exponen** helpers como `.symmetric` o `.center`.

### Padding
```python
# Correct — clase ft.Padding
padding = ft.Padding(left=10, top=5, right=10, bottom=5)
padding = ft.Padding.symmetric(horizontal=12, vertical=10)
padding = ft.Padding.only(left=16)

# Incorrect — submódulo ft.padding
padding = ft.padding.symmetric(horizontal=12, vertical=10)  # AttributeError
```

### Border
Use the `ft.Border` and `ft.BorderSide` classes.
```python
# Correct
border = ft.Border.all(1, ft.Colors.GREY_800)
# For specific sides:
border = ft.Border(bottom=ft.BorderSide(1, ft.Colors.GREY_800))
```

### BorderRadius
Use the `ft.BorderRadius` class.
```python
# Correct
border_radius = ft.BorderRadius(top_left=5, top_right=5, bottom_left=0, bottom_right=0)
# For all sides:
border_radius = ft.BorderRadius.all(10)
```

## 3. Alignment Property
For the `alignment` property in `ft.Container`, use `ft.Alignment(x, y)` (valores -1.0 … 1.0). Do not use `ft.alignment.center`.
```python
# Correct — centrado
alignment = ft.Alignment(0, 0)

# Incorrect
alignment = ft.alignment.center  # AttributeError
```

## 4. Component Specifics

### ft.Tab
Use the `label` property instead of `text`.
*   **Correct**: `ft.Tab(label="My Tab")`
*   **Incorrect**: `ft.Tab(text="My Tab")`

### ft.Tabs
En **0.85.2** el constructor de `ft.Tabs` ya no acepta `tabs=[...]` en `__init__` y puede exigir argumentos distintos (`content`, `length`, etc.). Para un conmutador de dos modos (login / registro), preferir **`ft.SegmentedButton`** (patrón usado en `sign_in_view.py`).

Si usas `ft.Tabs`, crea el control y asigna pestañas después:
```python
tabs = ft.Tabs(selected_index=0, on_change=handler)
tabs.tabs = [ft.Tab(label="Tab 1"), ft.Tab(label="Tab 2")]
```

### ft.SegmentedButton
La propiedad `selected` debe ser una **lista de strings** serializable por msgpack. Flet puede devolver un `set` en eventos; convierte con `list(e.control.selected)` al leer, pero **nunca** pases un `set` al crear o actualizar el control.
```python
# Correct
ft.SegmentedButton(
    selected=["login"],
    segments=[
        ft.Segment(value="login", label=ft.Text("Iniciar sesión")),
        ft.Segment(value="register", label=ft.Text("Registrarse")),
    ],
    on_change=self._on_mode_change,
)

# Incorrect — TypeError al hacer page.update()
ft.SegmentedButton(selected={"login"}, ...)
```

### ft.PopupMenuItem
Use the `content` property with an `ft.Text` object instead of `text`.
*   Note: **Dividers are NOT supported** (`divider=True` or `ft.PopupMenuDivider` will fail). Avoid using them in this build.
*   **Correct**: `ft.PopupMenuItem(content=ft.Text("Item Name"))`

### ft.Animation
Use the class directly from the root module: `ft.Animation` and `ft.AnimationCurve`. The submodule `ft.animation` is not available.
*   **Correct**: `ft.Animation(200, ft.AnimationCurve.EASE_OUT)`
*   **Incorrect**: `ft.animation.Animation(...)`

### ft.FilePicker
In Flet v0.85, the `FilePicker` is classified as a `Service` control. Do **NOT** add it to `page.overlay` using `page.overlay.append(file_picker)`. If added, Flet will try to render it visually and throw a `RuntimeError: Unknown control: FilePicker`.
*   **Correct**:
    ```python
    file_picker = ft.FilePicker()
    # No append! Just use it.
    ```
*   **Incorrect**:
    ```python
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)  # Throws Unknown control: FilePicker
    ```
Also, the `FilePicker` constructor does not accept `on_result` in this version. Instead, invoke the async method `pick_files()` directly inside an `async def` event handler:
```python
async def on_click(e):
    files = await file_picker.pick_files()
```

### ft.AlertDialog
Always use the classic method to display dialogs. Assign the dialog to `page.dialog`, set `dialog.open = True`, and then call `page.update()`. Do NOT use `page.open(dialog)` as it is not supported in this version.
```python
# Correct
page.dialog = dialog
dialog.open = True
page.update()
```

## 5. Icons
Always verify icon availability. If an icon name (like `INFINITY`) fails, check Material Design naming (e.g., use `ALL_INCLUSIVE` or `AUTO_RENEW`).

## 6. Colors — Deprecated / Missing Constants

> [!WARNING]
> `ft.Colors.SURFACE_VARIANT` does NOT exist in Flet v0.85 and throws `AttributeError: 'super' object has no attribute '__getattr__'` at runtime. Use `ft.Colors.SURFACE_CONTAINER` instead.

Available surface palette (verified):
- `SURFACE`, `SURFACE_DIM`, `SURFACE_BRIGHT`, `SURFACE_TINT`
- `SURFACE_CONTAINER_LOWEST`, `SURFACE_CONTAINER_LOW`, `SURFACE_CONTAINER`, `SURFACE_CONTAINER_HIGH`, `SURFACE_CONTAINER_HIGHEST`
- `ON_SURFACE`, `ON_SURFACE_VARIANT`, `INVERSE_SURFACE`, `ON_INVERSE_SURFACE`

**Green semantic colors** — no `GREEN_CONTAINER` / `ON_GREEN_CONTAINER`. Use numeric shades instead:
```python
# Correct — success banner pattern
self._status_banner.bgcolor = ft.Colors.GREEN_100
self._status_text.color = ft.Colors.GREEN_900
self._status_banner.border = ft.Border.all(1, ft.Colors.GREEN_700)
```

Available semantic colors (verified): `PRIMARY`, `PRIMARY_CONTAINER`, `ON_PRIMARY`, `ON_PRIMARY_CONTAINER`, `SECONDARY`, `SECONDARY_CONTAINER`, `ON_SECONDARY`, `ON_SECONDARY_CONTAINER`, `ERROR`, `ERROR_CONTAINER`, `ON_ERROR`, `ON_ERROR_CONTAINER`.

## 7. ft.ExpansionTile — Avoid in SidebarMenu

> [!CAUTION]
> `ft.ExpansionTile` is unstable with dynamic section rebuilds (calling `update_section()`). Avoid using it for collapsible menu groups that need to be rebuilt programmatically. Prefer a `ft.Column` with a labeled header row and a sub-`ft.Column` of `ft.ListTile` items.

```python
# Preferred pattern for menu groups
ft.Column(controls=[
    ft.Container(content=ft.Row(controls=[ft.Icon(...), ft.Text("Group Title")])),
    ft.Column(controls=[ft.ListTile(...) for item in items]),
])
```

## 8. ft.Container — animate_size

Animating width changes (e.g., collapsible panels) requires the `animate_size` property with `ft.Animation`:
```python
container = ft.Container(
    width=240,
    animate_size=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
)
# Then set container.width = new_value and call container.update()
```
`ft.AnimationCurve` is accessed from the root module (`ft.AnimationCurve.EASE_OUT`), NOT from `ft.animation`.

## 9. ft.Padding — Constructor Argument Order

> [!IMPORTANT]
> `ft.Padding` positional arguments follow `(left, top, right, bottom)`. Always use **keyword arguments** to avoid silent layout bugs:
> ```python
> ft.Padding(left=12, top=10, right=12, bottom=10)  # Correct
> ft.Padding(12, 10, 12, 10)  # Risky — positional order may differ
> ```
> Usa **`ft.Padding.symmetric(...)`** y **`ft.Padding.only(...)`** en la clase `ft.Padding`, no en el submódulo `ft.padding` (ver §2).

## 10. ft.Icon — name property reassignment

`ft.Icon.name` can be reassigned dynamically (e.g., swapping from `INFO_OUTLINED` to `ERROR_OUTLINE`). After reassignment, call `page.update()` to reflect the change:
```python
self._icon.name = ft.Icons.ERROR_OUTLINE
self._icon.color = ft.Colors.ERROR
self._page.update()
```

## 11. self.update() y self.page.update() en la Inicialización

> [!CAUTION]
> Llamar a `self.update()` o `self.page.update()` durante el constructor (`__init__`) o en métodos ejecutados durante el arranque (antes de que el control sea agregado a la página) lanzará la excepción `RuntimeError: Control must be added to the page first`.
> Además, acceder al getter público `self.page` cuando el control no ha sido montado también lanza esta excepción.

*   **Regla**: Evita llamadas directas a `update()` en el constructor.
*   **Buenas Prácticas**: Si un método es llamado tanto en la inicialización como en eventos posteriores, protege la llamada de `update()` comprobando de manera segura el atributo interno `_page` usando `getattr` para evitar que un `AttributeError` ocurra si el atributo aún no se ha inicializado en el objeto:
    ```python
    if getattr(self, "_page", None):
        self.update()
    ```

## 12. Componentes anidados en Rows/Columns (restricciones de `expand=True`)

> [!WARNING]
> Si un control secundario tiene `expand=True` para ocupar el espacio disponible de su contenedor padre (`Row` o `Column`), pero el contenedor padre en sí mismo está envuelto en otro layout externo sin `expand=True` o sin propiedades de estiramiento (`horizontal_alignment=ft.CrossAxisAlignment.STRETCH`), el componente colapsará visualmente a un ancho o alto de 0 píxeles.

*   **Regla**: Si un widget personalizado (ej. que hereda de `ft.Column` o `ft.Row`) contiene elementos internos expandibles (`expand=True`), asegúrate de:
    1. Definir `expand=True` en el constructor del widget para que se expanda horizontalmente dentro de su contenedor padre.
    2. Si el widget es un `ft.Column` y contiene filas horizontales (`ft.Row`), define `horizontal_alignment=ft.CrossAxisAlignment.STRETCH` para forzar a las filas a ocupar todo el ancho del Column, permitiendo que sus inputs internos se expandan adecuadamente.



