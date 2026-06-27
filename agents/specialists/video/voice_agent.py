import asyncio
import json
import os
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

# FFmpeg: primero busca en PATH, luego en la instalación de MoneyPrinterTurbo
_MPT_FFMPEG = Path(r"C:\MPT\MoneyPrinterTurbo-Portable-Windows-1.2.6\lib\ffmpeg\ffmpeg-7.0-essentials_build\ffmpeg.exe")
FFMPEG = "ffmpeg" if subprocess.run(["where", "ffmpeg"], capture_output=True).returncode == 0 else str(_MPT_FFMPEG)

# ── Voces por nicho/idioma ───────────────────────────────────────────────────

# edge-tts voices: es-ES (España), es-MX (México neutro/LATAM)
VOICE_PROFILES = {
    "biohacking":   {"es": "es-ES-AlvaroNeural",   "en": "en-US-GuyNeural"},
    "finanzas":     {"es": "es-ES-AlvaroNeural",   "en": "en-US-GuyNeural"},
    "motivacion":   {"es": "es-MX-JorgeNeural",    "en": "en-US-AndrewNeural"},
    "tecnologia":   {"es": "es-ES-AlvaroNeural",   "en": "en-US-GuyNeural"},
    "curiosidades": {"es": "es-MX-JorgeNeural",    "en": "en-US-AndrewNeural"},
    "default":      {"es": "es-ES-AlvaroNeural",   "en": "en-US-GuyNeural"},
}

# Ajuste de velocidad por nicho (edge-tts format: +10% / -5%)
RATE_BY_NICHE = {
    "biohacking":   "+0%",
    "finanzas":     "+5%",
    "motivacion":   "+10%",
    "tecnologia":   "+5%",
    "curiosidades": "+12%",
    "default":      "+0%",
}

# ── Modelos de datos ─────────────────────────────────────────────────────────

@dataclass
class WordTimestamp:
    word: str
    start: float   # segundos
    end: float


@dataclass
class SectionAudio:
    section_id: int
    audio_file: str        # ruta al .mp3
    duration_seconds: float
    word_timestamps: list[WordTimestamp]


@dataclass
class VoiceOutput:
    provider: str
    voice_name: str
    language: str
    niche: str
    full_audio_file: str          # audio completo concatenado
    total_duration_seconds: float
    sections: list[SectionAudio]
    narration_text: str           # texto completo utilizado

    def to_dict(self) -> dict:
        return asdict(self)


# ── Agente ───────────────────────────────────────────────────────────────────

class VoiceAgent:
    name = "VoiceAgent"
    description = "Convierte guiones en audio TTS con timestamps por palabra (Edge TTS gratis / ElevenLabs premium)"

    def __init__(self, elevenlabs_api_key: str = ""):
        from config import settings
        self._el_key = elevenlabs_api_key or getattr(settings, "elevenlabs_api_key", "")

    # ── API pública ──────────────────────────────────────────────────────────

    def run(
        self,
        script_data: dict,
        output_dir: str,
        language: str = "es",
        provider: str = "edge",          # "edge" | "elevenlabs"
        voice_override: Optional[str] = None,
    ) -> VoiceOutput:
        """Genera audio completo + timestamps a partir del dict del ScriptAgent.

        Args:
            script_data:    dict con la estructura del VideoScript (script_agent.py)
            output_dir:     carpeta donde guardar los archivos de audio
            language:       "es" | "en"
            provider:       "edge" (gratis) | "elevenlabs" (premium)
            voice_override: nombre exacto de voz, anula el perfil automático por nicho
        """
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        niche = script_data.get("niche", "default")
        voice = voice_override or VOICE_PROFILES.get(niche, VOICE_PROFILES["default"])[language]
        rate = RATE_BY_NICHE.get(niche, "+0%")

        if provider == "elevenlabs":
            return self._run_elevenlabs(script_data, out, voice, language, niche)
        else:
            return self._run_edge(script_data, out, voice, rate, language, niche)

    def run_from_file(
        self,
        script_json_path: str,
        output_dir: str,
        **kwargs,
    ) -> VoiceOutput:
        """Carga el JSON generado por ScriptAgent y produce el audio."""
        with open(script_json_path, encoding="utf-8") as f:
            script_data = json.load(f)
        return self.run(script_data, output_dir, **kwargs)

    # ── Edge TTS (gratis) ────────────────────────────────────────────────────

    def _run_edge(self, script_data, out: Path, voice: str, rate: str, language: str, niche: str) -> VoiceOutput:
        import edge_tts

        sections_audio: list[SectionAudio] = []
        audio_files: list[str] = []

        # Hook
        hook_file = str(out / "hook.mp3")
        hook_timestamps = asyncio.run(
            self._edge_synthesize(script_data["hook"], voice, rate, hook_file)
        )
        hook_duration = self._get_duration(hook_file)
        sections_audio.append(SectionAudio(
            section_id=0,
            audio_file=hook_file,
            duration_seconds=hook_duration,
            word_timestamps=hook_timestamps,
        ))
        audio_files.append(hook_file)

        # Secciones
        for s in script_data["sections"]:
            text = ""
            if s.get("re_hook"):
                text = s["re_hook"] + " " + s["narration"]
            else:
                text = s["narration"]

            section_file = str(out / f"section_{s['section_id']}.mp3")
            timestamps = asyncio.run(
                self._edge_synthesize(text, voice, rate, section_file)
            )
            duration = self._get_duration(section_file)
            sections_audio.append(SectionAudio(
                section_id=s["section_id"],
                audio_file=section_file,
                duration_seconds=duration,
                word_timestamps=timestamps,
            ))
            audio_files.append(section_file)

        # Outro
        outro_file = str(out / "outro.mp3")
        outro_timestamps = asyncio.run(
            self._edge_synthesize(script_data["outro"], voice, rate, outro_file)
        )
        outro_duration = self._get_duration(outro_file)
        sections_audio.append(SectionAudio(
            section_id=999,
            audio_file=outro_file,
            duration_seconds=outro_duration,
            word_timestamps=outro_timestamps,
        ))
        audio_files.append(outro_file)

        # Concatenar todo en un solo MP3
        full_audio = str(out / "full_audio.mp3")
        self._concat_mp3(audio_files, full_audio)
        total_duration = sum(s.duration_seconds for s in sections_audio)

        # Texto completo
        full_text = script_data["hook"] + "\n\n"
        for s in script_data["sections"]:
            if s.get("re_hook"):
                full_text += s["re_hook"] + " "
            full_text += s["narration"] + "\n\n"
        full_text += script_data["outro"]

        return VoiceOutput(
            provider="edge-tts",
            voice_name=voice,
            language=language,
            niche=niche,
            full_audio_file=full_audio,
            total_duration_seconds=total_duration,
            sections=sections_audio,
            narration_text=full_text,
        )

    async def _edge_synthesize(self, text: str, voice: str, rate: str, output_file: str) -> list[WordTimestamp]:
        """Sintetiza texto con Edge TTS y guarda el audio.

        Edge TTS 7.x eliminó WordBoundary — los timestamps exactos los genera
        el SubtitleAgent con faster-whisper sobre el audio real.
        Aquí devolvemos timestamps lineales estimados como aproximación inicial.
        """
        import edge_tts

        communicator = edge_tts.Communicate(text=text, voice=voice, rate=rate)
        with open(output_file, "wb") as f:
            async for chunk in communicator.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])

        # Timestamps estimados linealmente (SubtitleAgent los refina después)
        duration = self._get_duration(output_file)
        return self._estimate_timestamps(text, duration)

    # ── ElevenLabs (premium) ─────────────────────────────────────────────────

    # IDs de voces multilingües de ElevenLabs (válidas en la API v2)
    EL_VOICE_IDS = {
        "biohacking":   "onwK4e9ZLuTAKqWW03F9",   # Daniel  — científico, neutro
        "finanzas":     "pNInz6obpgDQGcFmaJgB",   # Adam    — autoridad clara
        "motivacion":   "ErXwobaYiN019PkySvjV",   # Antoni  — energético
        "tecnologia":   "TxGEqnHWrfWFTfGW9XjX",   # Josh    — experto directo
        "curiosidades": "N2lVS1w4EtoT3dr4eOWO",   # Callum  — narrador ameno
    }
    EL_VOICE_NAMES = {
        "biohacking":   "Daniel",
        "finanzas":     "Adam",
        "motivacion":   "Antoni",
        "tecnologia":   "Josh",
        "curiosidades": "Callum",
    }

    def _run_elevenlabs(self, script_data, out: Path, voice: str, language: str, niche: str) -> VoiceOutput:
        """Genera audio con ElevenLabs v2 API y estima timestamps por velocidad de locución."""
        try:
            from elevenlabs.client import ElevenLabs
        except ImportError:
            raise ImportError("Instala: pip install elevenlabs")

        if not self._el_key:
            raise ValueError("ElevenLabs API key requerida. Configura ELEVENLABS_API_KEY en .env")

        client = ElevenLabs(api_key=self._el_key)

        voice_id   = self.EL_VOICE_IDS.get(niche, "pNInz6obpgDQGcFmaJgB")   # Adam por defecto
        voice_name = self.EL_VOICE_NAMES.get(niche, "Adam")

        out.mkdir(parents=True, exist_ok=True)

        segments = [("hook", 0, script_data["hook"])]
        for s in script_data["sections"]:
            text = (s.get("re_hook", "") or "") + " " + s["narration"]
            segments.append(("section", s["section_id"], text.strip()))
        segments.append(("outro", 999, script_data["outro"]))

        sections_audio: list[SectionAudio] = []
        audio_files: list[str] = []

        for seg_type, seg_id, text in segments:
            fname = "hook.mp3" if seg_type == "hook" else "outro.mp3" if seg_type == "outro" else f"section_{seg_id}.mp3"
            fpath = str(out / fname)

            # ElevenLabs SDK v2: text_to_speech.convert() devuelve un generador de bytes
            audio_iter = client.text_to_speech.convert(
                voice_id=voice_id,
                text=text,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128",
            )
            with open(fpath, "wb") as f:
                for chunk in audio_iter:
                    if chunk:
                        f.write(chunk)

            duration = self._get_duration(fpath)
            timestamps = self._estimate_timestamps(text, duration)
            sections_audio.append(SectionAudio(
                section_id=seg_id,
                audio_file=fpath,
                duration_seconds=duration,
                word_timestamps=timestamps,
            ))
            audio_files.append(fpath)

        full_audio = str(out / "full_audio.mp3")
        self._concat_mp3(audio_files, full_audio)
        total = self._get_duration(full_audio)

        full_text = "\n\n".join(t for _, _, t in segments)
        return VoiceOutput(
            provider="elevenlabs",
            voice_name=voice_name,
            language=language,
            niche=niche,
            full_audio_file=full_audio,
            total_duration_seconds=total,
            sections=sections_audio,
            narration_text=full_text,
        )

    # ── Utilidades ───────────────────────────────────────────────────────────

    def _estimate_timestamps(self, text: str, duration: float) -> list[WordTimestamp]:
        """Estima timestamps uniformes cuando el proveedor no los da."""
        words = text.split()
        if not words:
            return []
        step = duration / len(words)
        return [
            WordTimestamp(word=w, start=round(i * step, 3), end=round((i + 1) * step, 3))
            for i, w in enumerate(words)
        ]

    def _get_duration(self, mp3_file: str) -> float:
        """Obtiene duración en segundos usando mutagen (puro Python, sin ffprobe)."""
        try:
            from mutagen.mp3 import MP3
            return MP3(mp3_file).info.length
        except Exception:
            return 0.0

    def _concat_mp3(self, files: list[str], output: str) -> None:
        """Concatena varios MP3 en uno usando FFmpeg concat demuxer."""
        list_file = Path(output).parent / "_concat_list.txt"
        with open(list_file, "w", encoding="utf-8", newline="\n") as f:
            for fp in files:
                fwd = Path(fp).resolve().as_posix()
                f.write(f"file '{fwd}'\n")
        subprocess.run(
            [FFMPEG, "-y", "-f", "concat", "-safe", "0",
             "-i", str(list_file), "-b:a", "192k", output],
            capture_output=True, timeout=120,
        )
        list_file.unlink(missing_ok=True)

    # ── Helpers de inspección ────────────────────────────────────────────────

    @staticmethod
    def list_voices(language_filter: str = "es") -> list[str]:
        """Lista voces Edge TTS disponibles para el idioma dado."""
        import edge_tts

        async def _list():
            voices = await edge_tts.list_voices()
            return [v["ShortName"] for v in voices if v["Locale"].startswith(language_filter)]

        return asyncio.run(_list())
