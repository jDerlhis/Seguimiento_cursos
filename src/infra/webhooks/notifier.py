import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

from infra.config.settings import PYFLOW_WEBHOOK_URL
from shared.logger import get_logger

logger = get_logger(__name__)


def notify_webhook(event: str, payload: dict[str, Any] | None = None) -> bool:
    """Envía un evento al webhook configurado (PYFLOW_WEBHOOK_URL)."""
    if not PYFLOW_WEBHOOK_URL:
        logger.debug("Webhook no configurado; evento omitido: %s", event)
        return False

    body = {
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": payload or {},
    }

    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        PYFLOW_WEBHOOK_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            logger.info("Webhook %s → HTTP %s", event, response.status)
            return True
    except urllib.error.URLError as ex:
        logger.warning("Webhook %s falló: %s", event, ex)
        return False
