"""
Nemr Voice Flow - Gemini 3.8 Live API Bidirectional Streaming Client
Configures ultra-low latency WebSocket voice sessions with Voice Activity Detection (VAD) and Egyptian Arabic personas.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class VoiceSessionConfig:
    model: str = "gemini-3.8-live"
    voice_name: str = "Puck"  # Or Zephyr, Charon, Aoede
    system_instruction: str = (
        "أنت موظف استقبال وخدمة عملاء ذكي ومحترف لشركة النمر. تحدث باللهجة المصرية الراقية والمهذبة. "
        "أجب بإيجاز ووضوح، وساعد العميل في الاستفسار أو الحجز أو تأكيد الطلب بدون إطالة."
    )
    language_code: str = "ar-EG"
    vad_threshold: float = 0.5
    silence_duration_ms: int = 400
    temperature: float = 0.6


class GeminiLiveClient:
    """Orchestrates bidirectional Gemini 3.8 Live API streaming sessions."""

    def __init__(self, api_key: str = "", config: Optional[VoiceSessionConfig] = None):
        self.api_key = api_key
        self.config = config or VoiceSessionConfig()

    def build_setup_message(self) -> Dict[str, Any]:
        """Constructs the initial setup frame sent over the WebSocket connection."""
        return {
            "setup": {
                "model": f"models/{self.config.model}",
                "generationConfig": {
                    "responseModalities": ["AUDIO", "TEXT"],
                    "speechConfig": {
                        "voiceConfig": {
                            "prebuiltVoiceConfig": {
                                "voiceName": self.config.voice_name
                            }
                        }
                    },
                    "temperature": self.config.temperature
                },
                "systemInstruction": {
                    "parts": [{"text": self.config.system_instruction}]
                }
            }
        }

    def build_realtime_audio_chunk(self, pcm_base64: str) -> Dict[str, Any]:
        """Encapsulates raw PCM 16-bit 16kHz audio data into a realtime client content frame."""
        return {
            "realtimeInput": {
                "mediaChunks": [
                    {
                        "mimeType": "audio/pcm;rate=16000",
                        "data": pcm_base64
                    }
                ]
            }
        }

    def simulate_turn_response(self, user_text: str) -> Dict[str, Any]:
        """Simulates turn-by-turn conversational inference for testing."""
        clean_text = user_text.strip()
        if "حجز" in clean_text or "ميعاد" in clean_text:
            reply = "أهلاً بك يا فندم! يشرفنا حجز موعد لحضرتك. تحب الموعد يكون بكرة الساعة كام؟"
            intent = "BOOKING"
        elif "سعر" in clean_text or "بكام" in clean_text or "تكلفة" in clean_text:
            reply = "باقات وأسعار الخدمات متاحة مع عروض خاصة اليوم. تقدر تحدد الخدمة المطلوبة بالتحديد؟"
            intent = "PRICING"
        else:
            reply = "تحت أمرك يا فندم في أي استفسار، إزاي أقدر أساعد حضرتك النهاردة؟"
            intent = "GENERAL_INQUIRY"

        return {
            "user_prompt": clean_text,
            "agent_response": reply,
            "intent": intent,
            "language": "ar-EG"
        }
