"""
Nemr Voice Flow - WhatsApp Cloud API Voice Webhook Router
Parses incoming WhatsApp voice notes, extracts media IDs, routes intents, and formats voice note responses.
"""

from __future__ import annotations
from typing import Dict, Any, Optional


class WhatsAppVoiceRouter:
    """Manages WhatsApp Business Cloud API incoming messages and voice note dispatch."""

    def __init__(self, verify_token: str = "nemr_voice_webhook_token_2026"):
        self.verify_token = verify_token

    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Validates Facebook Meta webhook verification request."""
        if mode == "subscribe" and token == self.verify_token:
            return challenge
        return None

    def parse_incoming_message(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extracts sender phone number, message type (audio/text), and media ID."""
        try:
            entry = payload.get("entry", [])[0]
            change = entry.get("changes", [])[0]
            val = change.get("value", {})
            messages = val.get("messages", [])

            if not messages:
                return None

            msg = messages[0]
            sender = msg.get("from")
            msg_type = msg.get("type")

            result = {
                "sender": sender,
                "type": msg_type,
                "timestamp": msg.get("timestamp"),
                "message_id": msg.get("id")
            }

            if msg_type == "audio":
                audio = msg.get("audio", {})
                result["media_id"] = audio.get("id")
                result["mime_type"] = audio.get("mime_type")
                result["voice"] = audio.get("voice", False)
            elif msg_type == "text":
                result["text"] = msg.get("text", {}).get("body", "")

            return result
        except (IndexError, KeyError):
            return None

    def build_audio_response_payload(self, to_phone: str, audio_media_id: str) -> Dict[str, Any]:
        """Constructs a WhatsApp Cloud API outbound audio message."""
        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "audio",
            "audio": {
                "id": audio_media_id
            }
        }
