"""
Nemr Voice Flow - WhatsApp Cloud API Voice Webhook Router (v2.0.0)
Handles HMAC X-Hub-Signature-256 verification, voice note parsing, interactive reply buttons,
and production PHP 8.3 webhook scaffolding.
"""

from __future__ import annotations
import hashlib
import hmac
from typing import Any, Dict, List, Optional


class WhatsAppVoiceRouter:
    """Manages WhatsApp Business Cloud API incoming messages, security signatures, and outbound dispatch."""

    def __init__(self, verify_token: str = "nemr_voice_webhook_token_2026"):
        self.verify_token = verify_token

    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Validates Meta webhook verification request."""
        if mode == "subscribe" and token == self.verify_token:
            return challenge
        return None

    @classmethod
    def verify_signature(cls, raw_body: bytes, signature_header: str, app_secret: str) -> bool:
        """Verifies Meta X-Hub-Signature-256 (`sha256=<hex>`) with constant-time comparison."""
        if not signature_header or not signature_header.startswith("sha256=") or not app_secret:
            return False
        provided_hex = signature_header.split("=", 1)[1].strip().lower()
        expected_hex = hmac.new(app_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected_hex, provided_hex)

    def parse_incoming_message(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extracts sender phone number, message type (audio/text/interactive), and media ID."""
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

            result: Dict[str, Any] = {
                "sender": sender,
                "type": msg_type,
                "timestamp": msg.get("timestamp"),
                "message_id": msg.get("id"),
            }

            if msg_type == "audio":
                audio = msg.get("audio", {})
                result["media_id"] = audio.get("id")
                result["mime_type"] = audio.get("mime_type")
                result["voice"] = audio.get("voice", False)
            elif msg_type == "text":
                result["text"] = msg.get("text", {}).get("body", "")
            elif msg_type == "interactive":
                reply = msg.get("interactive", {}).get("button_reply", {})
                result["button_id"] = reply.get("id")
                result["button_title"] = reply.get("title")

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
                "id": audio_media_id,
            },
        }

    @classmethod
    def build_interactive_buttons(
        cls,
        to_phone: str,
        body_text: str,
        buttons: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """Builds a WhatsApp Cloud API interactive reply button payload (max 3 buttons, 20-char titles)."""
        if not buttons or len(buttons) > 3:
            raise ValueError("WhatsApp Cloud API allows between 1 and 3 reply buttons.")

        formatted_buttons = []
        for idx, btn in enumerate(buttons, 1):
            btn_id = str(btn.get("id") or f"btn_{idx}")[:256]
            title = str(btn.get("title") or f"Option {idx}")[:20]
            formatted_buttons.append({
                "type": "reply",
                "reply": {
                    "id": btn_id,
                    "title": title,
                },
            })

        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body_text},
                "action": {"buttons": formatted_buttons},
            },
        }

    @classmethod
    def generate_php_webhook_scaffold(cls, verify_token: str = "nemr_voice_webhook_token_2026") -> str:
        """Returns a production-ready PHP 8.3 WhatsApp Business voice webhook handler."""
        return f"""<?php
declare(strict_types=1);

/**
 * Nemr Voice Flow v2.0.0 - Production PHP 8.3 WhatsApp Cloud API Webhook
 */

$verifyToken = getenv('WA_VERIFY_TOKEN') ?: '{verify_token}';
$appSecret = getenv('WA_APP_SECRET') ?: '';

if ($_SERVER['REQUEST_METHOD'] === 'GET') {{
    $mode = $_GET['hub_mode'] ?? '';
    $token = $_GET['hub_verify_token'] ?? '';
    $challenge = $_GET['hub_challenge'] ?? '';

    if ($mode === 'subscribe' && hash_equals($verifyToken, $token)) {{
        http_response_code(200);
        echo $challenge;
        exit;
    }}
    http_response_code(403);
    exit;
}}

$rawBody = file_get_contents('php://input') ?: '';
$sigHeader = $_SERVER['HTTP_X_HUB_SIGNATURE_256'] ?? '';

if ($appSecret !== '') {{
    $expected = 'sha256=' . hash_hmac('sha256', $rawBody, $appSecret);
    if (!hash_equals($expected, strtolower($sigHeader))) {{
        http_response_code(401);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'Invalid X-Hub-Signature-256']);
        exit;
    }}
}}

$payload = json_decode($rawBody, true);
$msg = $payload['entry'][0]['changes'][0]['value']['messages'][0] ?? null;

header('Content-Type: application/json');
if (!$msg) {{
    echo json_encode(['status' => 'ignored']);
    exit;
}}

$type = $msg['type'] ?? 'unknown';
$from = $msg['from'] ?? '';

$event = match ($type) {{
    'audio' => [
        'kind' => 'voice_note',
        'from' => $from,
        'media_id' => $msg['audio']['id'] ?? null,
        'mime_type' => $msg['audio']['mime_type'] ?? null,
    ],
    'text' => [
        'kind' => 'text_message',
        'from' => $from,
        'body' => $msg['text']['body'] ?? '',
    ],
    default => ['kind' => $type, 'from' => $from],
}};

echo json_encode(['status' => 'received', 'event' => $event]);
"""
