# 🎙️ Nemr Voice Flow (محرك بوتات الصوت والواتساب الفورية)

Autonomous real-time conversational voice agent and WhatsApp Business audio routing engine.

## 🚀 Capabilities

- **Gemini 3.8 Live API WebSocket Streaming**: Ultra-low latency voice streaming with VAD and native Arabic speech synthesis.
- **WhatsApp Cloud API Integration**: Automated voice note ingestion, intent routing, and audio replies.
- **Structured Booking Engine**: Turn-by-turn reservation capture and MySQL relational persistence.

## 📦 Usage

```bash
python cli.py simulate-call "عايز أعرف أسعار الباقات"
python cli.py whatsapp-scaffold
python cli.py booking --phone "201012345678" --name "سلطان النمر"
```

## 🧪 Testing

```bash
python -m unittest discover -s tests
```
