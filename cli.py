#!/usr/bin/env python3
"""
Nemr Voice Flow - Unified CLI
Real-time Gemini 3.8 Live API Voice Agent & WhatsApp Business Audio Webhook Router.
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.gemini_live_client import GeminiLiveClient, VoiceSessionConfig
from core.whatsapp_voice_router import WhatsAppVoiceRouter
from core.booking_engine import BookingEngine


def cmd_simulate(args: argparse.Namespace) -> None:
    client = GeminiLiveClient()
    print(f"\n🎙️ Simulating Live Voice Turn for Customer Query: '{args.query}'...\n")
    turn = client.simulate_turn_response(args.query)
    print("=" * 60)
    print(f"Customer: {turn['user_prompt']}")
    print(f"Agent (ar-EG): {turn['agent_response']}")
    print(f"Detected Intent: {turn['intent']}")
    print("=" * 60 + "\n")


def cmd_whatsapp(args: argparse.Namespace) -> None:
    router = WhatsAppVoiceRouter()
    print("\n📱 WhatsApp Cloud API Audio Webhook Scaffold:\n")
    sample_webhook = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "201012345678",
                        "id": "wamid.HBgLMjAx...",
                        "timestamp": "1731900000",
                        "type": "audio",
                        "audio": {
                            "id": "media_98234823",
                            "mime_type": "audio/ogg; codecs=opus",
                            "voice": True
                        }
                    }]
                }
            }]
        }]
    }
    parsed = router.parse_incoming_message(sample_webhook)
    print("Parsed Incoming Voice Note:")
    print(json.dumps(parsed, indent=2))
    print("\nOutbound Audio Payload:")
    outbound = router.build_audio_response_payload("201012345678", "media_98234823")
    print(json.dumps(outbound, indent=2) + "\n")


def cmd_booking(args: argparse.Namespace) -> None:
    engine = BookingEngine()
    rec = engine.create_booking(
        customer_phone=args.phone,
        customer_name=args.name,
        service=args.service,
        date_str=args.date
    )
    print(f"\n✓ Booking Confirmed [ID #{rec.id}]: {rec.customer_name} ({rec.customer_phone}) for {rec.service} at {rec.booking_date}\n")
    print("MySQL DDL Schema:")
    print(engine.get_sql_schema() + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Nemr Voice Flow: Realtime Conversational Voice & WhatsApp Agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # simulate-call
    p_sim = subparsers.add_parser("simulate-call", help="Simulate a conversational turn")
    p_sim.add_argument("query", type=str, help="Customer verbal prompt")
    p_sim.set_defaults(func=cmd_simulate)

    # whatsapp-scaffold
    p_wa = subparsers.add_parser("whatsapp-scaffold", help="Inspect WhatsApp audio webhook parser")
    p_wa.set_defaults(func=cmd_whatsapp)

    # booking
    p_book = subparsers.add_parser("booking", help="Create a voice booking record")
    p_book.add_argument("--phone", type=str, default="201099998888", help="Customer phone")
    p_book.add_argument("--name", type=str, default="عميل تجريبي", help="Customer name")
    p_book.add_argument("--service", type=str, default="استشارة تقنية", help="Service name")
    p_book.add_argument("--date", type=str, default="2026-11-20 14:00:00", help="Booking date")
    p_book.set_defaults(func=cmd_booking)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
