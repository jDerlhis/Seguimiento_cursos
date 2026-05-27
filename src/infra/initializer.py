import base64
import json
import time
from data.database import init_db
from infra.auth.session_store import has_saved_session, session_path
from shared.logger import get_logger, setup_logging

logger = get_logger(__name__)

def check_session_status() -> dict:
    """
    Comprueba el estado de la sesión HSEC local (si existe, si expiró, etc.).
    Retorna un diccionario con el estado:
        {
            "exists": bool,
            "expired": bool,
            "username": str | None,
            "expiration_time": str | None,
            "token_found": bool
        }
    """
    status = {
        "exists": False,
        "expired": True,
        "username": None,
        "expiration_time": None,
        "token_found": False
    }
    
    if not has_saved_session():
        return status
        
    status["exists"] = True
    
    try:
        path = session_path()
        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)
            
        token = None
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
                
        if not token:
            return status
            
        status["token_found"] = True
        
        # Decodificar payload JWT
        parts = token.split(".")
        if len(parts) >= 2:
            payload_b64 = parts[1]
            missing_padding = len(payload_b64) % 4
            if missing_padding:
                payload_b64 += "=" * (4 - missing_padding)
            payload_bytes = base64.urlsafe_b64decode(payload_b64)
            payload = json.loads(payload_bytes)
            
            status["username"] = payload.get("unique_name")
            exp = payload.get("exp")
            if exp:
                status["expired"] = time.time() >= exp
                status["expiration_time"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(exp))
            else:
                status["expired"] = False
                
    except Exception as ex:
        logger.warning(f"Error al analizar el archivo de sesión: {ex}")
        
    return status


def initialize_app() -> None:
    """
    Inicializa los servicios de infraestructura de la aplicación (base de datos, etc.).
    """
    setup_logging()
    logger.info("Iniciando servicios de infraestructura...")
    init_db()
    
    # Comprobar el estado de la sesión al inicializar
    status = check_session_status()
    if not status["exists"]:
        logger.warning("No se encontró ninguna sesión HSEC activa registrada.")
    elif status["expired"]:
        logger.warning(f"La sesión HSEC del usuario '{status['username']}' ha expirado ({status['expiration_time']}).")
    else:
        logger.info(f"Sesión HSEC activa del usuario '{status['username']}' válida hasta {status['expiration_time']}.")
