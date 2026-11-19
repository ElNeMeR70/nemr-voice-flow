"""Nemr Voice Flow Core Package (v3.0.0)."""

__version__ = "3.0.0"

from core.audio_codec import AudioCodec
from core.gemini_live_client import GeminiLiveClient, VoiceSessionConfig, PERSONA_PRESETS
from core.whatsapp_voice_router import WhatsAppVoiceRouter
from core.booking_engine import BookingEngine, BookingRecord
from core.conversation_memory import ConversationMemory
from core.twiml_sip_bridge import TwimlSipBridge

__all__ = [
    "__version__",
    "AudioCodec",
    "GeminiLiveClient",
    "VoiceSessionConfig",
    "PERSONA_PRESETS",
    "WhatsAppVoiceRouter",
    "BookingEngine",
    "BookingRecord",
    "ConversationMemory",
    "TwimlSipBridge",
]
