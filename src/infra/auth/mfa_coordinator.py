import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from infra.config.settings import MFA_WAIT_TIMEOUT_SEC
from shared.logger import get_logger

logger = get_logger(__name__)




@dataclass(frozen=True)
class MfaRequest:
    message: str


@dataclass
class MfaStatus:
    countdown_text: str | None = None
    expired: bool = False


class MfaActionType(Enum):
    CODE = "code"
    RESEND = "resend"
    CANCEL = "cancel"


@dataclass(frozen=True)
class MfaAction:
    type: MfaActionType
    code: str = ""


class MfaCoordinator:
    """Puente entre Playwright (hilo scraper) y el modal MFA (UI Flet)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._code_event = threading.Event()
        self._resend_event = threading.Event()
        self._cancel_event = threading.Event()
        self._code: str | None = None
        self._ui_handler: Callable[[MfaRequest], None] | None = None
        self._error_handler: Callable[[str], None] | None = None
        self._status_handler: Callable[[MfaStatus], None] | None = None
        self._close_handler: Callable[[], None] | None = None
        self._status = MfaStatus()
        self._session_active = False
        self._resend_fn: Callable[[], None] | None = None
        self._status_fn: Callable[[], MfaStatus] | None = None

    def set_ui_handler(self, handler: Callable[[MfaRequest], None] | None) -> None:
        with self._lock:
            self._ui_handler = handler

    def set_error_handler(self, handler: Callable[[str], None] | None) -> None:
        with self._lock:
            self._error_handler = handler

    def set_status_handler(self, handler: Callable[[MfaStatus], None] | None) -> None:
        with self._lock:
            self._status_handler = handler

    def set_close_handler(self, handler: Callable[[], None] | None) -> None:
        with self._lock:
            self._close_handler = handler

    def close_ui(self) -> None:
        with self._lock:
            handler = self._close_handler
        if handler:
            handler()

    def begin_session(
        self,
        resend_fn: Callable[[], None],
        status_fn: Callable[[], MfaStatus],
    ) -> None:
        with self._lock:
            self._session_active = True
            self._resend_fn = resend_fn
            self._status_fn = status_fn
            self._cancel_event.clear()
            self._reset_wait_state_locked()

    def end_session(self, *, close_dialog: bool = True) -> None:
        with self._lock:
            self._session_active = False
            self._resend_fn = None
            self._status_fn = None
            self._cancel_event.clear()
            self._reset_wait_state_locked()
        if close_dialog:
            self.close_ui()

    def get_status(self) -> MfaStatus:
        with self._lock:
            return MfaStatus(
                countdown_text=self._status.countdown_text,
                expired=self._status.expired,
            )

    def is_session_active(self) -> bool:
        with self._lock:
            return self._session_active

    def update_status(self, status: MfaStatus) -> None:
        handler = None
        with self._lock:
            self._status = status
            handler = self._status_handler
        if handler:
            handler(status)

    def poll_page_status(self) -> None:
        with self._lock:
            fn = self._status_fn
        if fn:
            self.update_status(fn())

    def notify_error(self, message: str, *, reset_wait: bool = True) -> None:
        handler = None
        with self._lock:
            handler = self._error_handler
            if reset_wait:
                self._reset_wait_state_locked()
        if handler:
            handler(message)

    def open_prompt(self, message: str) -> None:
        with self._lock:
            handler = self._ui_handler
        if handler is None:
            raise RuntimeError(
                "No hay UI registrada para MFA. Abre la vista HSEC en la app."
            )
        handler(MfaRequest(message=message))

    def _resolve_timeout(self, timeout_sec: int | None) -> int | None:
        if timeout_sec is not None:
            return timeout_sec if timeout_sec > 0 else None
        if MFA_WAIT_TIMEOUT_SEC > 0:
            return MFA_WAIT_TIMEOUT_SEC
        return None

    def wait_for_action(self, timeout_sec: int | None = None) -> MfaAction:
        timeout = self._resolve_timeout(timeout_sec)
        deadline = time.monotonic() + timeout if timeout else None
        expired_notified = False

        while True:
            if deadline is not None and time.monotonic() >= deadline:
                raise TimeoutError(
                    f"No se recibió acción MFA en {timeout} segundos."
                )

            self.poll_page_status()
            status = self.get_status()

            if status.expired:
                deadline = None
                if not expired_notified:
                    self.notify_error(
                        "El código expiró. Pulsa «Reenviar código» y usa el nuevo.",
                        reset_wait=False,
                    )
                    expired_notified = True
            elif expired_notified:
                expired_notified = False

            if self._cancel_event.is_set():
                self._cancel_event.clear()
                self._reset_wait_state()
                return MfaAction(type=MfaActionType.CANCEL)

            if self._resend_event.is_set():
                self._resend_event.clear()
                try:
                    self._execute_resend()
                except Exception as ex:
                    self.notify_error(f"No se pudo reenviar el código: {ex}")
                    continue
                self._reset_wait_state()
                return MfaAction(type=MfaActionType.RESEND)

            if self._code_event.wait(timeout=0.35):
                with self._lock:
                    code = (self._code or "").strip()
                    self._code_event.clear()
                if not code:
                    if self._cancel_event.is_set():
                        continue
                    self.notify_error("Ingresa el código de 6 dígitos.")
                    continue
                self._reset_wait_state()
                return MfaAction(type=MfaActionType.CODE, code=code)

    def submit_code(self, code: str) -> None:
        with self._lock:
            self._code = code
            self._code_event.set()

    def request_resend(self) -> None:
        self._resend_event.set()

    def cancel(self) -> None:
        """Solo debe llamarse cuando el usuario pulsa Cancelar en el modal."""
        self._cancel_event.set()

    def _execute_resend(self) -> None:
        with self._lock:
            fn = self._resend_fn
        if fn is None:
            raise RuntimeError("No hay sesión MFA activa para reenviar el código.")
        fn()

    def _reset_wait_state(self) -> None:
        with self._lock:
            self._reset_wait_state_locked()

    def _reset_wait_state_locked(self) -> None:
        self._code = None
        self._code_event.clear()
        self._resend_event.clear()
        # No limpiar _cancel_event aquí: solo al consumirlo o al iniciar sesión.


mfa_coordinator = MfaCoordinator()
