from app.models import AuthState
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings


class TelegramUserbotService:
    async def generate_qr(self, session_id: int) -> dict:
        return {"session_id": session_id, "qr_token": f"qr-{session_id}"}

    async def verify_2fa(self, password: str) -> bool:
        return bool(password.strip())

    async def detect_2fa_required(self) -> bool:
        return True

    async def can_send_as_channel(self, chat_id: str) -> bool:
        return chat_id.startswith("-100") or chat_id.startswith("@")

    @retry(stop=stop_after_attempt(settings.max_publish_retries), wait=wait_exponential(multiplier=1, min=1, max=8), reraise=True)
    async def publish(self, chat_id: str, text: str) -> str:
        return f"msg-{abs(hash((chat_id, text))) % 10**8}"

    @retry(stop=stop_after_attempt(settings.max_publish_retries), wait=wait_exponential(multiplier=1, min=1, max=8), reraise=True)
    async def edit(self, chat_id: str, message_id: str, text: str) -> str:
        return message_id


def next_auth_state(needs_2fa: bool) -> AuthState:
    return AuthState.pending_2fa if needs_2fa else AuthState.authorized
