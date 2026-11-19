"""
Nemr Voice Flow - Pure-Stdlib PCM16 / WAV Audio Codec & Energy VAD (v2.0.0)
Provides bidirectional PCM16 <-> RIFF WAV transcoding, real-time base64 frame chunking, and RMS voice activity detection.
"""

from __future__ import annotations
import base64
import io
import math
import struct
import wave
from typing import Any, Dict, List


class AudioCodec:
    """Zero-dependency PCM16/WAV transcoding and Voice Activity Detection utilities."""

    @classmethod
    def pcm16_to_wav_bytes(
        cls,
        pcm_bytes: bytes,
        sample_rate: int = 24000,
        channels: int = 1,
    ) -> bytes:
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)  # 16-bit signed PCM
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_bytes)
        return buf.getvalue()

    @classmethod
    def wav_bytes_to_pcm16(cls, wav_bytes: bytes) -> Dict[str, Any]:
        buf = io.BytesIO(wav_bytes)
        with wave.open(buf, "rb") as wf:
            sample_rate = wf.getframerate()
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            nframes = wf.getnframes()
            pcm_data = wf.readframes(nframes)

        duration_ms = round((nframes / sample_rate) * 1000.0, 2) if sample_rate > 0 else 0.0
        return {
            "pcm_bytes": pcm_data,
            "sample_rate": sample_rate,
            "channels": channels,
            "sample_width": sample_width,
            "duration_ms": duration_ms,
        }

    @classmethod
    def chunk_pcm_base64(
        cls,
        pcm_bytes: bytes,
        chunk_ms: int = 100,
        sample_rate: int = 16000,
    ) -> List[str]:
        bytes_per_chunk = max(2, int(sample_rate * 2 * (chunk_ms / 1000.0)))
        if bytes_per_chunk % 2 != 0:
            bytes_per_chunk += 1

        chunks: List[str] = []
        for offset in range(0, len(pcm_bytes), bytes_per_chunk):
            slice_bytes = pcm_bytes[offset:offset + bytes_per_chunk]
            chunks.append(base64.b64encode(slice_bytes).decode("ascii"))
        return chunks

    @classmethod
    def detect_voice_activity(
        cls,
        pcm_bytes: bytes,
        threshold_rms: float = 300.0,
    ) -> Dict[str, Any]:
        sample_count = len(pcm_bytes) // 2
        if sample_count == 0:
            return {"is_speech": False, "rms": 0.0, "dbfs": -96.0}

        samples = struct.unpack(f"<{sample_count}h", pcm_bytes[:sample_count * 2])
        sum_sq = sum(s * s for s in samples)
        rms = math.sqrt(sum_sq / sample_count)
        if rms <= 0.0:
            dbfs = -96.0
        else:
            dbfs = round(20.0 * math.log10(rms / 32768.0), 2)

        return {
            "is_speech": rms >= threshold_rms,
            "rms": round(rms, 2),
            "dbfs": dbfs,
        }
