"""
Nemr Voice Flow - TwiML SIP Bridge & Pure-Stdlib ITU-T G.711 u-law Codec (v3.0.0)
Generates Twilio Media Streams TwiML and transcodes 8kHz G.711 u-law <-> 16-bit PCM without audioop.
"""

from __future__ import annotations
import struct
from xml.sax.saxutils import escape


class TwimlSipBridge:
    """Bridges PSTN telephony (Twilio Media Streams) to Gemini Live WebSockets."""

    BIAS = 0x84
    CLIP = 32635

    @classmethod
    def generate_twiml_stream(
        cls,
        wss_url: str,
        greeting_text: str = "أهلاً بك في خدمة عملاء النمر الذكية",
        language: str = "ar-EG",
    ) -> str:
        safe_url = escape(wss_url, {'"': "&quot;", "'": "&apos;"})
        safe_greeting = escape(greeting_text)
        safe_lang = escape(language, {'"': "&quot;"})
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            "<Response>\n"
            f'  <Say language="{safe_lang}">{safe_greeting}</Say>\n'
            "  <Connect>\n"
            f'    <Stream url="{safe_url}" />\n'
            "  </Connect>\n"
            "</Response>"
        )

    @classmethod
    def _linear_to_ulaw_byte(cls, sample: int) -> int:
        sign = (sample >> 8) & 0x80
        if sign != 0:
            sample = -sample
        if sample > cls.CLIP:
            sample = cls.CLIP
        sample += cls.BIAS

        exponent = 7
        exp_mask = 0x4000
        while exponent > 0 and (sample & exp_mask) == 0:
            exponent -= 1
            exp_mask >>= 1

        mantissa = (sample >> (exponent + 3)) & 0x0F
        ulaw = ~(sign | (exponent << 4) | mantissa) & 0xFF
        return ulaw

    @classmethod
    def _ulaw_byte_to_linear(cls, ulaw_byte: int) -> int:
        u = (~ulaw_byte) & 0xFF
        sign = u & 0x80
        exponent = (u >> 4) & 0x07
        mantissa = u & 0x0F
        sample = ((mantissa << 3) + cls.BIAS) << exponent
        sample -= cls.BIAS
        return -sample if sign != 0 else sample

    @classmethod
    def pcm16_to_ulaw(cls, pcm_bytes: bytes) -> bytes:
        count = len(pcm_bytes) // 2
        if count == 0:
            return b""
        samples = struct.unpack(f"<{count}h", pcm_bytes[:count * 2])
        return bytes(cls._linear_to_ulaw_byte(s) for s in samples)

    @classmethod
    def ulaw_to_pcm16(cls, ulaw_bytes: bytes) -> bytes:
        if not ulaw_bytes:
            return b""
        samples = [cls._ulaw_byte_to_linear(b) for b in ulaw_bytes]
        return struct.pack(f"<{len(samples)}h", *samples)
