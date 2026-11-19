#!/usr/bin/env python3
"""Unit tests for Nemr Voice Flow v2.0.0."""

import hashlib
import hmac
import math
import struct
import sys
import tempfile
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.gemini_live_client import GeminiLiveClient, VoiceSessionConfig, PERSONA_PRESETS
from core.whatsapp_voice_router import WhatsAppVoiceRouter
from core.booking_engine import BookingEngine
from core.audio_codec import AudioCodec
from core.conversation_memory import ConversationMemory
from core.twiml_sip_bridge import TwimlSipBridge


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
        engine.close()

    # v2.0.0 Tests
    def test_audio_codec_roundtrip_and_vad(self):
        # Generate 100ms of 440Hz sine wave PCM16 at 16kHz (speech-like energy)
        sample_rate = 16000
        num_samples = 1600
        tone_samples = [int(8000 * math.sin(2 * math.pi * 440 * i / sample_rate)) for i in range(num_samples)]
        pcm_tone = struct.pack(f"<{num_samples}h", *tone_samples)

        wav_bytes = AudioCodec.pcm16_to_wav_bytes(pcm_tone, sample_rate=sample_rate)
        self.assertTrue(wav_bytes.startswith(b"RIFF"))
        unpacked = AudioCodec.wav_bytes_to_pcm16(wav_bytes)
        self.assertEqual(unpacked["pcm_bytes"], pcm_tone)
        self.assertEqual(unpacked["sample_rate"], sample_rate)

        chunks = AudioCodec.chunk_pcm_base64(pcm_tone, chunk_ms=50, sample_rate=sample_rate)
        self.assertEqual(len(chunks), 2)

        vad_speech = AudioCodec.detect_voice_activity(pcm_tone)
        self.assertTrue(vad_speech["is_speech"])
        silence = b"\x00\x00" * 1600
        vad_silence = AudioCodec.detect_voice_activity(silence)
        self.assertFalse(vad_silence["is_speech"])

    def test_gemini_live_tools_and_personas(self):
        cfg = PERSONA_PRESETS["clinic_eg"]
        client = GeminiLiveClient(config=cfg)
        setup = client.build_setup_message()
        self.assertIn("tools", setup["setup"])
        fn_names = [f["name"] for f in setup["setup"]["tools"][0]["functionDeclarations"]]
        self.assertIn("create_booking", fn_names)

        tool_frame = client.build_tool_response_frame("call_1", "check_available_slots", {"slots": ["10:00"]})
        self.assertEqual(tool_frame["toolResponse"]["functionResponses"][0]["name"], "check_available_slots")

    def test_whatsapp_signature_and_interactive_buttons(self):
        secret = "meta_app_secret_xyz"
        raw = b'{"entry":[]}'
        sig = "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
        self.assertTrue(WhatsAppVoiceRouter.verify_signature(raw, sig, secret))
        self.assertFalse(WhatsAppVoiceRouter.verify_signature(raw, "sha256=deadbeef", secret))

        buttons_msg = WhatsAppVoiceRouter.build_interactive_buttons(
            "201012345678",
            "اختر التوقيت:",
            [{"id": "slot_10", "title": "10:00 AM"}, {"id": "slot_11", "title": "11:00 AM"}],
        )
        self.assertEqual(buttons_msg["type"], "interactive")
        self.assertEqual(len(buttons_msg["interactive"]["action"]["buttons"]), 2)

    def test_booking_engine_conflict_and_slots(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_file = str(Path(tmpdir) / "bookings.db")
            engine = BookingEngine(db_path=db_file)
            r1 = engine.create_booking("2010111", "منى", "كشف", "2026-11-20 10:00:00")
            with self.assertRaises(ValueError):
                engine.create_booking("2010222", "سارة", "كشف", "2026-11-20 10:15:00")

            slots = engine.get_available_slots("2026-11-20", start_hour=10, end_hour=12, slot_minutes=30)
            self.assertNotIn("2026-11-20 10:00:00", slots)
            self.assertIn("2026-11-20 10:30:00", slots)

            self.assertTrue(engine.cancel_booking(r1.id))
            slots_after_cancel = engine.get_available_slots("2026-11-20", start_hour=10, end_hour=12, slot_minutes=30)
            self.assertIn("2026-11-20 10:00:00", slots_after_cancel)
            engine.close()

    def test_php_webhook_scaffold(self):
        php = WhatsAppVoiceRouter.generate_php_webhook_scaffold("my_token")
        self.assertIn("HTTP_X_HUB_SIGNATURE_256", php)
        self.assertIn("hash_hmac('sha256'", php)
        self.assertIn("my_token", php)

    # v3.0.0 Tests
    def test_conversation_memory_and_escalation(self):
        mem = ConversationMemory(db_path=":memory:")
        mem.add_turn("caller_1", "user", "السلام عليكم عايز أحجز", intent="BOOKING", audio_sec=3.0)
        mem.add_turn("caller_1", "agent", "أهلاً بحضرتك، متاح بكرة الساعة 2", intent="BOOKING", audio_sec=4.0)
        mem.add_turn("caller_1", "user", "تمام شكراً", intent="CONFIRM", audio_sec=1.5)
        ctx = mem.get_context_window("caller_1", max_turns=2)
        self.assertEqual(len(ctx), 2)
        self.assertEqual(ctx[0]["role"], "agent")
        mem.close()

        esc = ConversationMemory.detect_escalation("عندي مشكلة كبيرة وعايز أحولني لموظف أو مدير فوراً")
        self.assertTrue(esc["escalate"])
        self.assertGreaterEqual(len(esc["matched_triggers"]), 2)
        calm = ConversationMemory.detect_escalation("عايز استفسر عن مواعيد العمل")
        self.assertFalse(calm["escalate"])

    def test_session_cost_estimator(self):
        est = ConversationMemory.estimate_session_cost(audio_in_sec=40.0, audio_out_sec=60.0, text_tokens=500)
        self.assertEqual(est["audio_in_tokens"], 1000.0)
        self.assertEqual(est["audio_out_tokens"], 1500.0)
        self.assertEqual(est["total_tokens"], 3000.0)
        self.assertGreater(est["estimated_cost_usd"], 0.0)

    def test_twiml_and_ulaw_pcm16_roundtrip(self):
        twiml = TwimlSipBridge.generate_twiml_stream("wss://voice.elnemer-ai.com/stream", greeting_text="أهلاً بكم")
        self.assertIn("<Response>", twiml)
        self.assertIn('<Stream url="wss://voice.elnemer-ai.com/stream"', twiml)

        raw_samples = [0, 4000, -4000, 12000, -12000]
        pcm_in = struct.pack(f"<{len(raw_samples)}h", *raw_samples)
        ulaw = TwimlSipBridge.pcm16_to_ulaw(pcm_in)
        self.assertEqual(len(ulaw), len(raw_samples))
        pcm_out = TwimlSipBridge.ulaw_to_pcm16(ulaw)
        recovered = struct.unpack(f"<{len(raw_samples)}h", pcm_out)
        for orig, rec in zip(raw_samples, recovered):
            self.assertAlmostEqual(orig, rec, delta=600)


if __name__ == "__main__":
    unittest.main()
