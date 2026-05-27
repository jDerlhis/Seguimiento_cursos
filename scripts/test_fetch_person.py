import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(ROOT))

from infra.auth.session_store import session_path, has_saved_session
from playwright.sync_api import sync_playwright

def main():
    print("=== Test Fetch Person ===")
    if not has_saved_session():
        print("Error: No hay sesión guardada en sessions/hsec_storage_state.json")
        return 1

    path = session_path()
    print(f"Cargando estado de sesión desde: {path}")

    # 1. Leer hsec_storage_state.json para buscar tokens JWT en localStorage
    token = None
    try:
        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)
            
        origins = state.get("origins", [])
        for origin_data in origins:
            local_storage = origin_data.get("localStorage", [])
            for item in local_storage:
                name = item.get("name", "")
                value = item.get("value", "")
                # Buscar JWT token
                if "eyJhbGciOi" in value:
                    print(f"Token encontrado en localStorage con nombre: {name}")
                    token = value
                    # Quitar comillas si están presentes en la serialización JSON del valor de localStorage
                    if token.startswith('"') and token.endswith('"'):
                        token = token[1:-1]
                    break
            if token:
                break
    except Exception as ex:
        print(f"Error al analizar el archivo de sesión: {ex}")

    if not token:
        print("No se encontró un token JWT (eyJ...) en localStorage del archivo de sesión.")
        print("Intentaremos buscarlo abriendo la página...")

    # 2. Iniciar Playwright y realizar la consulta de API
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=str(path))
        page = context.new_page()

        # Si no pudimos obtener el token del JSON directo, podemos evaluar localStorage en la página
        if not token:
            try:
                # Navegamos a la URL base para que el contexto cargue el dominio y localStorage
                from infra.config.settings import HSEC_DASHBOARD_URL
                page.goto(HSEC_DASHBOARD_URL, wait_until="domcontentloaded")
                token = page.evaluate("() => localStorage.getItem('token') || localStorage.getItem('id_token') || sessionStorage.getItem('token')")
                print(f"Token obtenido via JS: {token}")
            except Exception as ex:
                print(f"Error al obtener token vía JS: {ex}")

        if not token:
            # Buscar cualquier item en localStorage que tenga forma de JWT
            try:
                token = page.evaluate("""() => {
                    for (let i = 0; i < localStorage.length; i++) {
                        let k = localStorage.key(i);
                        let v = localStorage.getItem(k);
                        if (v && v.includes('eyJhbGciOi')) return v;
                    }
                    return null;
                }""")
                if token:
                    if token.startswith('"') and token.endswith('"'):
                        token = token[1:-1]
                    print(f"Token JWT encontrado buscando en localStorage: {token[:30]}...")
            except Exception as ex:
                print(f"Error buscando token en todo localStorage: {ex}")

        if not token:
            print("No se pudo obtener el token de autorización. Se cancela la consulta.")
            browser.close()
            return 1

        # Agregar prefijo Bearer si no lo tiene
        auth_header = token if token.startswith("Bearer ") else f"Bearer {token}"

        # Realizar la solicitud POST a la API de Buscar Persona
        url = "https://antapaccay.sam.glencore.net/Mhsec_web/MHSEC_Gen/api/Personas/Buscar"
        payload = {
            "pagina": 1,
            "paginaTamanio": 7,
            "codTipoPersona": "2",
            "codPosicion": 0,
            "nroDocumento": "46897109"
        }

        print(f"Realizando POST a: {url}")
        print(f"Payload: {payload}")

        try:
            # Usar el request context de Playwright que automáticamente incluye cookies
            headers = {
                "accept": "application/json, text/plain, */*",
                "content-type": "application/json",
                "authorization": auth_header,
                "origin": "https://antapaccay.sam.glencore.net",
                "referer": "https://antapaccay.sam.glencore.net/hsec_web/"
            }
            
            response = context.request.post(
                url,
                data=payload,
                headers=headers
            )
            
            print(f"Status Code: {response.status} {response.status_text}")
            if response.status == 200:
                data = response.json()
                print("\nRespuesta obtenida con éxito:")
                print(json.dumps(data, indent=4, ensure_ascii=False))
            else:
                print(f"Fallo la petición. Cuerpo de respuesta: {response.text()}")
        except Exception as ex:
            print(f"Error al realizar la petición API: {ex}")

        browser.close()

if __name__ == "__main__":
    sys.exit(main())
