from data import schema
from infra.supabase.client import get_client
from shared.logger import get_logger

logger = get_logger(__name__)


def init_db() -> None:
    get_client().table(schema.HSEC_PEOPLE).select("id").limit(1).execute()
    logger.debug("Conexión Supabase OK")
