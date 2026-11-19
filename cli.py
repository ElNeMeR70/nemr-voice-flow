#!/usr/bin/env python3
"""
Nemr Voice Flow v3.0.0 - Unified CLI (Sovereign Edition)
Gemini 3.8 Live API Voice Agent, PCM16/WAV/G.711 u-law Audio Codec, TwiML Telephony Bridge,
Conversation Memory + Escalation Detector + Cost FinOps, WhatsApp Signature Router, and SQLite Slot Booking.
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.gemini_live_client import GeminiLiveClient, PERSONA_PRESETS
from core.whatsapp_voice_router import WhatsAppVoiceRouter
from core.booking_engine import BookingEngine
from core.conversation_memory import ConversationMemory
from core.twiml_sip_bridge import TwimlSipBridge

VERSION = "3.0.0"


def cmd_simulate(args: argparse.Namespace) -> None:
    cfg = PERSONA_PRESETS.get(args.preset) if args.preset else None
    client = GeminiLiveClient(config=cfg)
    print(f"\n🎙️ Simulating Live Voice Turn for Customer Query: '{args.query}'...\n")
    turn = client.simulate_turn_response(args.query)
    print("=" * 60)
    print(f"Customer: {turn['user_prompt']}")
    print(f"Agent ({turn['language']}): {turn['agent_response']}")
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
                            "voice": True,
                        },
                    }]
                }
            }]
        }]
    }
    parsed = router.parse_incoming_message(sample_webhook)
    print("Parsed Incoming Voice Note:")
    print(json.dumps(parsed, indent=2))
    print("\nOutbound Interactive Buttons Preview:")
    buttons = router.build_interactive_buttons(
        "201012345678",
        "هل تود تأكيد الموعد؟",
        [{"id": "confirm", "title": "تأكيد الحجز"}, {"id": "cancel", "title": "تعديل الموعد"}],
    )
    print(json.dumps(buttons, indent=2, ensure_ascii=False) + "\n")


def cmd_booking(args: argparse.Namespace) -> None:
    engine = BookingEngine(db_path=args.db or ":memory:")
    try:
        rec = engine.create_booking(
            customer_phone=args.phone,
            customer_name=args.name,
            service=args.service,
            date_str=args.date,
        )
        print(f"\n✓ Booking Confirmed [ID #{rec.id}]: {rec.customer_name} ({rec.customer_phone}) for {rec.service} at {rec.booking_date}\n")
        print("MySQL DDL Schema:")
        print(engine.get_sql_schema() + "\n")
    except ValueError as err:
        print(f"\n❌ Booking Rejected: {err}\n")
        sys.exit(1)
    finally:
        engine.close()


def cmd_personas(args: argparse.Namespace) -> None:
    if args.preset:
        cfg = PERSONA_PRESETS[args.preset]
        client = GeminiLiveClient(config=cfg)
        frame = client.build_setup_message(include_tools=args.with_tools or cfg.enable_booking_tools)
        print(f"\n🎭 Persona `{args.preset}` WebSocket Setup Frame:\n" + "=" * 60)
        print(json.dumps(frame, indent=2, ensure_ascii=False))
        print("=" * 60 + "\n")
    else:
        print("\n🎭 Available Persona Presets:")
        for key, cfg in PERSONA_PRESETS.items():
            print(f"  - {key:14} ({cfg.language_code}, voice={cfg.voice_name}, tools={cfg.enable_booking_tools})")
        print()


def cmd_slots(args: argparse.Namespace) -> None:
    engine = BookingEngine(db_path=args.db or ":memory:")
    try:
        available = engine.get_available_slots(args.date)
        print(f"\n📅 Available 30m Slots on {args.date} ({len(available)} open):\n")
        for slot in available:
            print(f"  • {slot}")
        print()
    finally:
        engine.close()


def cmd_export_php_webhook(args: argparse.Namespace) -> None:
    code = WhatsAppVoiceRouter.generate_php_webhook_scaffold(verify_token=args.verify_token)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(code, encoding="utf-8")
        print(f"\n✓ Exported PHP 8.3 WhatsApp webhook handler to: {out_path}\n")
    else:
        print(code)


def cmd_twiml(args: argparse.Namespace) -> None:
    xml_out = TwimlSipBridge.generate_twiml_stream(
        wss_url=args.wss,
        greeting_text=args.greeting,
        language=args.language,
    )
    print(xml_out)


def cmd_cost_estimate(args: argparse.Namespace) -> None:
    est = ConversationMemory.estimate_session_cost(
        audio_in_sec=args.in_sec,
        audio_out_sec=args.out_sec,
        text_tokens=args.text_tokens,
    )
    if args.json:
        print(json.dumps(est, indent=2))
        return
    print(f"\n💰 Voice Session Cost Estimate ({args.in_sec}s in, {args.out_sec}s out):")
    print(f"  Audio In Tokens:  {int(est['audio_in_tokens'])}")
    print(f"  Audio Out Tokens: {int(est['audio_out_tokens'])}")
    print(f"  Total Tokens:     {int(est['total_tokens'])}")
    print(f"  Estimated USD:    ${est['estimated_cost_usd']:.6f}\n")


def cmd_escalation_check(args: argparse.Namespace) -> None:
    res = ConversationMemory.detect_escalation(args.text)
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return
    status = "🚨 ESCALATE TO HUMAN" if res["escalate"] else "✓ CONTINUE AI FLOW"
    print(f"\n{status}")
    if res["matched_triggers"]:
        print(f"  Triggers: {', '.join(res['matched_triggers'])}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Nemr Voice Flow v3.0.0: Realtime Voice, TwiML & WhatsApp Agent")
    parser.add_argument("--version", action="version", version=VERSION)
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_sim = subparsers.add_parser("simulate-call", help="Simulate a conversational turn")
    p_sim.add_argument("query", type=str, help="Customer verbal prompt")
    p_sim.add_argument("--preset", type=str, default=None, choices=list(PERSONA_PRESETS.keys()), help="Optional persona preset")
    p_sim.set_defaults(func=cmd_simulate)

    p_wa = subparsers.add_parser("whatsapp-scaffold", help="Inspect WhatsApp audio & interactive button payloads")
    p_wa.set_defaults(func=cmd_whatsapp)

    p_book = subparsers.add_parser("booking", help="Create a voice booking record with conflict protection")
    p_book.add_argument("--phone", type=str, default="201099998888", help="Customer phone")
    p_book.add_argument("--name", type=str, default="عميل تجريبي", help="Customer name")
    p_book.add_argument("--service", type=str, default="استشارة تقنية", help="Service name")
    p_book.add_argument("--date", type=str, default="2026-11-20 14:00:00", help="Booking date")
    p_book.add_argument("--db", type=str, default=None, help="SQLite DB file path")
    p_book.set_defaults(func=cmd_booking)

    p_pers = subparsers.add_parser("personas", help="List presets or emit Gemini Live WebSocket setup JSON")
    p_pers.add_argument("--preset", type=str, default=None, choices=list(PERSONA_PRESETS.keys()), help="Persona preset")
    p_pers.add_argument("--with-tools", action="store_true", help="Include booking functionDeclarations")
    p_pers.set_defaults(func=cmd_personas)

    p_slots = subparsers.add_parser("slots", help="List open appointment slots for a date")
    p_slots.add_argument("--date", type=str, required=True, help="Date YYYY-MM-DD")
    p_slots.add_argument("--db", type=str, default=None, help="SQLite DB file path")
    p_slots.set_defaults(func=cmd_slots)

    p_php = subparsers.add_parser("export-php-webhook", help="Generate production PHP 8.3 WhatsApp webhook script")
    p_php.add_argument("--out", type=str, default=None, help="Output PHP file path")
    p_php.add_argument("--verify-token", type=str, default="nemr_voice_webhook_token_2026", help="Verify token")
    p_php.set_defaults(func=cmd_export_php_webhook)

    p_twiml = subparsers.add_parser("twiml", help="Emit Twilio Media Streams TwiML XML linking to Gemini WSS")
    p_twiml.add_argument("--wss", type=str, required=True, help="WebSocket stream URL (wss://...)")
    p_twiml.add_argument("--greeting", type=str, default="أهلاً بك في خدمة عملاء النمر الذكية", help="Greeting text")
    p_twiml.add_argument("--language", type=str, default="ar-EG", help="Greeting language")
    p_twiml.set_defaults(func=cmd_twiml)

    p_cost = subparsers.add_parser("cost-estimate", help="Estimate voice call tokens & USD cost")
    p_cost.add_argument("--in-sec", type=float, required=True, help="Inbound caller audio seconds")
    p_cost.add_argument("--out-sec", type=float, required=True, help="Outbound agent audio seconds")
    p_cost.add_argument("--text-tokens", type=int, default=500, help="System + text tokens")
    p_cost.add_argument("--json", action="store_true", help="Emit JSON output")
    p_cost.set_defaults(func=cmd_cost_estimate)

    p_esc = subparsers.add_parser("escalation-check", help="Detect frustration or human-handoff triggers")
    p_esc.add_argument("text", type=str, help="Transcript snippet to evaluate")
    p_esc.add_argument("--json", action="store_true", help="Emit JSON output")
    p_esc.set_defaults(func=cmd_escalation_check)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
