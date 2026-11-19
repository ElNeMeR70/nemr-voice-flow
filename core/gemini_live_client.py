"""
Nemr Voice Flow - Gemini 3.8 Live API Bidirectional Streaming Client (v2.0.0)
Configures ultra-low latency WebSocket voice sessions, Arabic/English persona presets, and function-calling booking tools.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class VoiceSessionConfig:
    model: str = "gemini-3.8-live"
    voice_name: str = "Puck"
    system_instruction: str = (
        "أنت موظف استقبال وخدمة عملاء ذكي ومحترف لشركة النمر. تحدث باللهجة المصرية الراقية والمهذبة. "
        "أجب بإيجاز ووضوح، وساعد العميل في الاستفسار أو الحجز أو تأكيد الطلب بدون إطالة."
    )
    language_code: str = "ar-EG"
    vad_threshold: float = 0.5
    silence_duration_ms: int = 400
    temperature: float = 0.6
    enable_booking_tools: bool = False


PERSONA_PRESETS: Dict[str, VoiceSessionConfig] = {
    "clinic_eg": VoiceSessionConfig(
        voice_name="Aoede",
        language_code="ar-EG",
        system_instruction=(
            "أنت مساعد استقبال ذكي لعيادة طبية متخصصة في القاهرة. تحدث باللهجة المصرية الودودة والمهذبة، "
            "تحقق من المواعيد المتاحة أولاً باستخدام الأدوات، وأكّد اسم المريض ورقم الهاتف وتوقيت الكشف."
        ),
        enable_booking_tools=True,
    ),
    "ecommerce_eg": VoiceSessionConfig(
        voice_name="Puck",
        language_code="ar-EG",
        system_instruction=(
            "أنت مسؤول مبيعات وخدمة عملاء لمتجر إلكتروني مصري. تحدث بالمصرية السريعة والواضحة، "
            "وضح الأسعار بالجنيه المصري وأكّد بيانات الشحن وطريقة الدفع (فودافون كاش / عند الاستلام)."
        ),
        enable_booking_tools=False,
    ),
    "concierge_sa": VoiceSessionConfig(
        voice_name="Charon",
        language_code="ar-SA",
        system_instruction=(
            "أنت موظف كونسيرج وحجوزات راقٍ باللهجة السعودية البيضاء. رحّب بالضيف باحترام وأتمم حجزه أو استفساره بدقة واختصار."
        ),
        enable_booking_tools=True,
    ),
    "saas_en": VoiceSessionConfig(
        voice_name="Zephyr",
        language_code="en-US",
        system_instruction=(
            "You are a concise, technically sharp AI solutions specialist for a cloud SaaS platform. "
            "Help users schedule onboarding demos or troubleshoot API integration issues."
        ),
        enable_booking_tools=True,
    ),
}


class GeminiLiveClient:
    """Orchestrates bidirectional Gemini 3.8 Live API streaming sessions."""

    BOOKING_TOOL_DECLARATIONS: List[Dict[str, Any]] = [
        {
            "name": "check_available_slots",
            "description": "Lists available appointment time slots for a specific date (YYYY-MM-DD).",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "date": {"type": "STRING", "description": "Target date in YYYY-MM-DD format"}
                },
                "required": ["date"],
            },
        },
        {
            "name": "create_booking",
            "description": "Books an appointment slot after confirming customer details and verifying no conflict.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "customer_phone": {"type": "STRING"},
                    "customer_name": {"type": "STRING"},
                    "service": {"type": "STRING"},
                    "booking_date": {"type": "STRING", "description": "YYYY-MM-DD HH:MM:SS"},
                },
                "required": ["customer_phone", "customer_name", "service", "booking_date"],
            },
        },
        {
            "name": "cancel_booking",
            "description": "Cancels an existing booking by numeric booking ID.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "booking_id": {"type": "INTEGER"},
                },
                "required": ["booking_id"],
            },
        },
    ]

    def __init__(self, api_key: str = "", config: Optional[VoiceSessionConfig] = None):
        self.api_key = api_key
        self.config = config or VoiceSessionConfig()

    def build_setup_message(self, include_tools: Optional[bool] = None) -> Dict[str, Any]:
        """Constructs the initial setup frame sent over the WebSocket connection."""
        setup_body: Dict[str, Any] = {
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
                "temperature": self.config.temperature,
            },
            "systemInstruction": {
                "parts": [{"text": self.config.system_instruction}]
            },
        }
        use_tools = self.config.enable_booking_tools if include_tools is None else include_tools
        if use_tools:
            setup_body["tools"] = [{"functionDeclarations": self.BOOKING_TOOL_DECLARATIONS}]
        return {"setup": setup_body}

    def build_realtime_audio_chunk(self, pcm_base64: str) -> Dict[str, Any]:
        """Encapsulates raw PCM 16-bit 16kHz audio data into a realtime client content frame."""
        return {
            "realtimeInput": {
                "mediaChunks": [
                    {
                        "mimeType": "audio/pcm;rate=16000",
                        "data": pcm_base64,
                    }
                ]
            }
        }

    def build_tool_response_frame(
        self,
        call_id: str,
        name: str,
        output: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Constructs a Gemini Live API toolResponse frame after executing a booking tool."""
        return {
            "toolResponse": {
                "functionResponses": [
                    {
                        "id": call_id,
                        "name": name,
                        "response": output,
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
            "language": self.config.language_code,
        }
