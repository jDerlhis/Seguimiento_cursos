"""Selectores Playwright — espejo de backend/scripts/*.ts."""

REPORTE_URL = (
    "https://antapaccay.sam.glencore.net/hsec_web/#/ReportePersonalCapacitado"
)

OPEN_MODAL_SELECTORS = [
    "button[title='Seleccionar persona']",
    "button.btn-persona",
    "button.k-button >> nth=1",
]

DNI_INPUT_SELECTORS = [
    "input[placeholder='Nº Documento']",
    "input[placeholder='N° Documento']",
    "input[aria-label*='Documento']",
]

BUSCAR_SELECTORS = [
    "button:has-text('Buscar')",
    ".k-dialog button:has-text('Buscar')",
]

RESULT_ROW_SELECTOR = ".k-grid-content tr:first-child"

SELECCIONAR_SELECTORS = [
    "button:has-text('Seleccionar')",
    "button.btn-success:has-text('Seleccionar')",
]

VER_REPORTE_SELECTORS = [
    "button:has-text('Ver reporte')",
    "button.k-button:has-text('Ver reporte')",
]

REPORT_ROW_SELECTOR = "table tr"

EXPECTED_COURSE_HEADERS = frozenset({
    "fecha", "duracion", "tema", "area", "tipo", "nota", "estado", "vencimiento",
})

USERNAME_SELECTORS = [
    "input[placeholder='Usuario']",
    "input[placeholder*='usuario' i]",
    "input[name='username']",
    "input[type='email']",
    "input[id*='user' i]",
    "input[placeholder*='user' i]",
]

PASSWORD_SELECTORS = [
    "input[placeholder='Password']",
    "input[placeholder*='password' i]",
    "input[name='password']",
    "input[type='password']",
]

SUBMIT_SELECTORS = [
    "button:has-text('Ingresar')",
    "button[type='submit']",
    "button:has-text('Sign in')",
    "button:has-text('Iniciar')",
    "button:has-text('Login')",
    "button:has-text('Entrar')",
]

MFA_INPUT_SELECTORS = [
    "input[placeholder*='6 dígitos' i]",
    "input[inputmode='numeric']",
    "input[autocomplete='one-time-code']",
    "input[name='code']",
    "input[name='otc']",
    "input[placeholder*='código' i]",
    "input[placeholder*='code' i]",
]

MFA_SUBMIT_SELECTORS = [
    "button:has-text('Validar acceso')",
    "button[type='submit']",
    "button:has-text('Verify')",
    "button:has-text('Verificar')",
    "button:has-text('Continuar')",
]

MFA_BODY_PATTERNS = [
    r"doble\s+factor",
    r"validaci[oó]n\s+de\s+acceso",
    r"c[oó]digo\s+enviado\s+al\s+correo",
    r"verification\s+code",
    r"c[oó]digo\s+de\s+verificaci[oó]n",
    r"one.?time",
    r"autenticador",
]
