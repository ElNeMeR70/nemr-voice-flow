#!/usr/bin/env python3
"""Unit tests for Nemr Voice Flow."""

import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.gemini_live_client import GeminiLiveClient, VoiceSessionConfig
from core.whatsapp_voice_router import WhatsAppVoiceRouter
from core.booking_engine import BookingEngine


class TestVoiceFlow(unittest.TestCase):
    def test_gemini_live_setup_message(self):
        client = GeminiLiveClient(api_key="test_key")
        setup = client.build_setup_message()
        self.assertIn("setup", setup)
        self.assertEqual(setup["setup"]["model"], "models/gemini-3.8-live")
        self.assertIn("AUDIO", setup["setup"]["generationConfig"]["responseModalities"])

    def test_gemini_live_turn_simulation(self):
        client = GeminiLiveClient()
        turn_booking = client.simulate_turn_response("عايز أحجز موعد استشارة")
        self.assertEqual(turn_booking["intent"], "BOOKING")

        turn_pricing = client.simulate_turn_response("بكام أسعار الخدمات؟")
        self.assertEqual(turn_pricing["intent"], "PRICING")

    def test_whatsapp_webhook_verification(self):
        router = WhatsAppVoiceRouter(verify_token="secret_token_123")
        verified = router.verify_webhook("subscribe", "secret_token_123", "challenge_abc")
        self.assertEqual(verified, "challenge_abc")

        failed = router.verify_webhook("subscribe", "wrong_token", "challenge_abc")
        self.assertIsNone(failed)

    def test_whatsapp_parse_voice_message(self):
        router = WhatsAppVoiceRouter()
        payload = {
            "entry": [{"changes": [{"value": {"messages": [{
                "from": "201011112222",
                "id": "msg_001",
                "timestamp": "1731900000",
                "type": "audio",
                "audio": {"id": "media_789", "mime_type": "audio/ogg", "voice": True}
            }]}}]}]
        }
        res = router.parse_incoming_message(payload)
        self.assertIsNotNone(res)
        self.assertEqual(res["sender"], "201011112222")
        self.assertEqual(res["media_id"], "media_789")

    def test_booking_engine(self):
        engine = BookingEngine()
        rec = engine.create_booking("201099990000", "أحمد علي", "صيانة", "2026-11-25 10:00:00")
        self.assertEqual(rec.id, 1)
        self.assertEqual(rec.customer_name, "أحمد علي")
        self.assertIn("CREATE TABLE IF NOT EXISTS `voice_bookings`", engine.get_sql_schema())


if __name__ == "__main__":
    unittest.main()
