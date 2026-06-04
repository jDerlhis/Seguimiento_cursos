from infra.supabase.init_db import init_db
from shared.logger import get_logger, setup_logging

logger = get_logger(__name__)


def initialize_app() -> None:
    setup_logging()
    logger.info("Inicializando aplicación...")
    try:
        init_db()
    except Exception as ex:
        logger.warning("Supabase no disponible al inicio: %s", ex)
