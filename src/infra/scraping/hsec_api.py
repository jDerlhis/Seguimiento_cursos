import json
from shared.logger import get_logger
import httpx
from infra.auth.session_store import session_path, has_saved_session

logger = get_logger(__name__)

def fetch_person_from_api(dni: str) -> dict | None:
    """
    Realiza una consulta a la API de HSEC para buscar una persona por su DNI.
    Utiliza el token JWT y las cookies almacenadas en sessions/hsec_storage_state.json.
    """
    if not has_saved_session():
        raise RuntimeError("No se encontró una sesión activa. Por favor, inicia sesión en HSEC Web primero.")

    path = session_path()
    
    # 1. Leer cookies y token del archivo de sesión
    token = None
    cookies_dict = {}
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)
        
        # Extraer cookies
        for cookie in state.get("cookies", []):
            cookies_dict[cookie["name"]] = cookie["value"]
            
        # Extraer token JWT de localStorage
        origins = state.get("origins", [])
        for origin_data in origins:
            local_storage = origin_data.get("localStorage", [])
            for item in local_storage:
                name = item.get("name", "")
                value = item.get("value", "")
                if "eyJhbGciOi" in value:
                    token = value
                    if token.startswith('"') and token.endswith('"'):
                        token = token[1:-1]
                    break
            if token:
                break
    except Exception as ex:
        raise RuntimeError(f"Error al leer el archivo de sesión: {ex}")

    if not token:
        raise RuntimeError("No se encontró un token JWT en la sesión guardada. Por favor, inicia sesión de nuevo.")

    # 2. Realizar petición POST con httpx
    url = "https://antapaccay.sam.glencore.net/Mhsec_web/MHSEC_Gen/api/Personas/Buscar"
    payload = {
        "pagina": 1,
        "paginaTamanio": 7,
        "codTipoPersona": "2",
        "codPosicion": 0,
        "nroDocumento": dni
    }
    
    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "authorization": f"Bearer {token}" if not token.startswith("Bearer ") else token,
        "origin": "https://antapaccay.sam.glencore.net",
        "referer": "https://antapaccay.sam.glencore.net/hsec_web/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
    }

    try:
        # Usamos httpx.Client para pasar cookies y headers de forma limpia
        with httpx.Client(verify=False) as client:
            logger.info(f"Buscando DNI {dni} en la API de HSEC...")
            response = client.post(url, json=payload, headers=headers, cookies=cookies_dict, timeout=30.0)
            
            if response.status_code == 401:
                raise RuntimeError("Sesión expirada o no autorizada (401). Inicia sesión de nuevo en HSEC Web.")
            
            response.raise_for_status()
            data = response.json()
            
            # Si count es 0 o la lista de personas está vacía, no existe el usuario
            if data.get("count", 0) == 0 or not data.get("lists", []):
                logger.info(f"La API retornó 0 resultados para el DNI {dni} (caso controlado).")
                return None
                
            return data["lists"][0]
            
    except httpx.HTTPStatusError as ex:
        raise RuntimeError(f"Error HTTP de la API ({ex.response.status_code}): {ex.response.text}")
    except httpx.RequestError as ex:
        raise RuntimeError(f"Error de conexión con la API de HSEC: {ex}")
