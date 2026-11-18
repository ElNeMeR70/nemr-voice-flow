---
name: nemr-voice-flow
description: Autonomous multimodal AI voice agent and WhatsApp Business audio router. Integrates Gemini 3.8 Live API WebSocket bidirectional streaming, Arabic/Egyptian persona prompt engineering, WhatsApp voice note (.ogg/.opus) processing, and conversational appointment bookings. Use when the user asks to build voice agents, speech-to-speech bots, or WhatsApp voice note automation.
---

# Nemr Voice Flow (محرك بوتات الصوت والواتساب الفورية)

Autonomous real-time conversational voice agent and WhatsApp Business audio routing engine.

## Key Capabilities

1. **Gemini 3.8 Live API Bidirectional Streaming Client (`simulate-call`)**:
   - WebSocket frame generation with Voice Activity Detection (VAD) and custom audio modalities (`audio/pcm;rate=16000`).
   - Pre-tuned Egyptian Arabic business reception personas.

2. **WhatsApp Cloud API Voice Note Webhook Router (`whatsapp-scaffold`)**:
   - Validates Meta webhook verification challenges.
   - Ingests incoming voice notes, extracts media IDs, routes intents, and formats outbound audio responses.

3. **Conversational Booking & Slot Persistence (`booking`)**:
   - Validates appointment slots and exports production-grade MySQL schema for reservations.

## CLI Quick Reference

```bash
# 1. Simulate Voice Conversation Turn
python cli.py simulate-call "عايز أحجز ميعاد كشف بكرة"

# 2. Inspect WhatsApp Cloud API Webhook Parser
python cli.py whatsapp-scaffold

# 3. Create Voice Booking Record
python cli.py booking --phone "201012345678" --name "محمود النمر" --service "استشارة برمجية"
```
