---
name: nemr-voice-flow
description: Autonomous multimodal AI voice agent, telephony SIP/TwiML bridge & WhatsApp Business audio router v3.0.0. Integrates Gemini 3.8 Live API WebSocket setup with booking tool declarations and Arabic/English personas, SQLite multi-turn conversation memory + anger escalation & USD cost estimation, pure-Python PCM16/WAV/G.711 u-law audio codecs & RMS VAD, TwiML XML streaming, Meta X-Hub-Signature-256 verification, PHP 8.3 webhook export, and SQLite conflict-checked slot booking. Use when building voice agents, phone bots, or WhatsApp audio automation.
---

# Nemr Voice Flow v3.0.0 (محرك بوتات الصوت والواتساب والاتصالات الهاتفية)

Autonomous real-time conversational voice agent, PCM16/WAV/G.711 u-law audio codec suite, Twilio TwiML telephony bridge, SQLite multi-turn memory & escalation detector, WhatsApp Business router, and conflict-checked booking engine.

## Key Capabilities

1. **TwiML Telephony Bridge & ITU-T G.711 u-law Codec (`twiml`, `TwimlSipBridge`)**:
   - Emits Twilio `<Response><Say/><Connect><Stream/></Connect></Response>` XML and performs stdlib `pcm16_to_ulaw` / `ulaw_to_pcm16` transcoding without deprecated `audioop`.
2. **Multi-Turn Memory, Escalation & FinOps Estimator (`cost-estimate`, `escalation-check`)**:
   - Stores caller transcripts in SQLite, detects Arabic/English complaint/human-agent handoff triggers, and estimates audio+text token spend in USD.
3. **PCM16/WAV Audio Codec & RMS VAD (`AudioCodec`)**:
   - Transcodes PCM16 <-> RIFF WAV, chunks base64 streaming audio frames, and runs RMS/dBFS Voice Activity Detection.
4. **Gemini 3.8 Live Personas & Booking Tools (`personas`)**:
   - Ready-to-use `clinic_eg`, `ecommerce_eg`, `concierge_sa`, and `saas_en` system instructions with booking `functionDeclarations`.
5. **WhatsApp Signature Router & Conflict-Checked Slot Engine (`whatsapp-scaffold`, `export-php-webhook`, `booking`, `slots`)**:
   - Validates `X-Hub-Signature-256`, exports PHP 8.3 webhooks, and prevents double-booked appointment slots.

## CLI Quick Reference

```bash
python cli.py --version
python cli.py twiml --wss wss://voice.elnemer-ai.com/stream --greeting "أهلاً بك في خدمة عملاء النمر"
python cli.py cost-estimate --in-sec 45 --out-sec 65 --json
python cli.py escalation-check "عندي مشكلة كبيرة وعايز أحولني لموظف" --json
python cli.py personas --preset clinic_eg --with-tools
python cli.py slots --date 2026-11-20 --db clinic.db
python cli.py export-php-webhook --out whatsapp_webhook.php
```
