"""
SubtitleAgent — genera subtítulos karaoke word-by-word y los quema en el video.

Pipeline:
  1. Transcribe el audio con faster-whisper (timestamps exactos por palabra)
  2. Agrupa palabras en líneas cortas (máx 4 palabras)
  3. Genera un archivo .ASS con efecto karaoke (palabra activa en amarillo)
  4. Quema los subtítulos en el video con FFmpeg
"""

import json
import re
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

_MPT_FFMPEG = Path(r"C:\MPT\MoneyPrinterTurbo-Portable-Windows-1.2.6\lib\ffmpeg\ffmpeg-7.0-essentials_build\ffmpeg.exe")
FFMPEG = str(_MPT_FFMPEG) if _MPT_FFMPEG.exists() else "ffmpeg"

# ── Estilo de subtítulos ─────────────────────────────────────────────────────

ASS_STYLE = {
    "Name":            "Karaoke",
    "Fontname":        "Arial",
    "Fontsize":        "22",        # se escala sobre resolución de referencia
    "PrimaryColour":   "&H00FFFFFF",  # blanco
    "SecondaryColour": "&H0000FFFF",  # amarillo (color de karaoke activo)
    "OutlineColour":   "&H00000000",  # negro
    "BackColour":      "&H80000000",  # semi-transparente
    "Bold":            "1",
    "Italic":          "0",
    "BorderStyle":     "1",
    "Outline":         "3",
    "Shadow":          "1",
    "Alignment":       "2",          # centrado inferior
    "MarginL":         "50",
    "MarginR":         "50",
    "MarginV":         "80",
    "Encoding":        "1",
}

WORDS_PER_LINE   = 4    # máx palabras por línea
WHISPER_MODEL    = "small"   # tiny/base/small/medium — small es el mejor balance calidad/velocidad


@dataclass
class WordEntry:
    word: str
    start: float   # segundos
    end: float


@dataclass
class SubtitleOutput:
    ass_file: str
    video_with_subs: str
    total_words: int
    duration_seconds: float
    model_used: str
    language_detected: str

    def to_dict(self) -> dict:
        return asdict(self)


# ── Agente ───────────────────────────────────────────────────────────────────

class SubtitleAgent:
    name = "SubtitleAgent"
    description = "Transcribe audio con Whisper, genera karaoke ASS y quema subtítulos en el video"

    def __init__(self, whisper_model: str = WHISPER_MODEL):
        self.model_name = whisper_model
        self._model = None   # lazy load

    # ── API pública ──────────────────────────────────────────────────────────

    def run(
        self,
        video_file: str,
        audio_file: str,
        output_dir: str,
        language: str = "es",
        words_per_line: int = WORDS_PER_LINE,
        font_size: int = 22,
        style: str = "tiktok",   # "tiktok" | "youtube"
    ) -> SubtitleOutput:
        """Genera subtítulos karaoke y los quema en el video.

        Args:
            video_file:    MP4 a subtitular (sin subtítulos)
            audio_file:    MP3 del audio narrado (para transcribir)
            output_dir:    carpeta de salida
            language:      idioma para Whisper ("es", "en", etc.)
            words_per_line: palabras por línea de subtítulo
            font_size:     tamaño de fuente (22 = TikTok, 18 = YouTube)
            style:         "tiktok" (grande, centrado) | "youtube" (más discreto)
        """
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        video_path = Path(video_file).resolve()
        audio_path = Path(audio_file).resolve()

        # Validar entradas antes de gastar 15 min en Whisper
        if not video_path.exists():
            raise FileNotFoundError(f"El video a subtitular no existe: {video_path}")
        if not audio_path.exists():
            raise FileNotFoundError(f"El audio a transcribir no existe: {audio_path}")

        # ── 1. Transcribir con Whisper ───────────────────────────────────────
        words, lang_detected = self._transcribe(str(audio_path), language)

        # ── 2. Generar ASS ──────────────────────────────────────────────────
        width, height = self._get_resolution(str(video_path))
        ass_file = str(out / "subtitles.ass")
        self._write_ass(words, ass_file, words_per_line, font_size, width, height, style)

        # ── 3. Quemar subtítulos ─────────────────────────────────────────────
        stem = video_path.stem
        output_video = str(out / f"{stem}_subtitled.mp4")
        self._burn_subtitles(str(video_path), ass_file, output_video)

        if not Path(output_video).exists() or Path(output_video).stat().st_size < 100_000:
            raise RuntimeError(f"El quemado de subtítulos falló: no se creó {output_video}")

        duration = self._get_duration(output_video)

        return SubtitleOutput(
            ass_file=ass_file,
            video_with_subs=output_video,
            total_words=len(words),
            duration_seconds=duration,
            model_used=self.model_name,
            language_detected=lang_detected,
        )

    def run_from_files(
        self,
        editor_output_json: str,
        voice_output_json: str,
        output_dir: str,
        **kwargs,
    ) -> SubtitleOutput:
        """Carga las rutas desde los JSONs de EditorAgent y VoiceAgent."""
        with open(editor_output_json, encoding="utf-8") as f:
            editor = json.load(f)
        with open(voice_output_json, encoding="utf-8") as f:
            voice = json.load(f)

        video_file = editor["video_file"]
        audio_file = voice["full_audio_file"]

        # Resolver rutas relativas
        for attr, val in [("video", video_file), ("audio", audio_file)]:
            p = Path(val)
            if not p.is_absolute():
                p = Path.cwd() / p
            if attr == "video":
                video_file = str(p)
            else:
                audio_file = str(p)

        return self.run(video_file, audio_file, output_dir, **kwargs)

    # ── Transcripción ────────────────────────────────────────────────────────

    def _transcribe(self, audio_file: str, language: str) -> tuple[list[WordEntry], str]:
        """Transcribe el audio y devuelve lista de WordEntry con timestamps exactos."""
        from faster_whisper import WhisperModel
        import warnings
        warnings.filterwarnings("ignore")

        if self._model is None:
            self._model = WhisperModel(
                self.model_name,
                device="cpu",
                compute_type="int8",
            )

        segments, info = self._model.transcribe(
            audio_file,
            language=language,
            word_timestamps=True,
            vad_filter=True,           # ignora silencios
            vad_parameters={"min_silence_duration_ms": 300},
        )

        words: list[WordEntry] = []
        for segment in segments:
            if segment.words:
                for w in segment.words:
                    clean = w.word.strip()
                    if clean:
                        words.append(WordEntry(
                            word=clean,
                            start=round(w.start, 3),
                            end=round(w.end, 3),
                        ))

        return words, info.language

    # ── Generación de ASS ────────────────────────────────────────────────────

    def _write_ass(
        self,
        words: list[WordEntry],
        output_file: str,
        words_per_line: int,
        font_size: int,
        width: int,
        height: int,
        style: str,
    ) -> None:
        """Genera el archivo ASS con efecto karaoke."""

        # Escalar font_size a la resolución del video
        # Referencia: 22pt sobre 1080px ancho → escalar
        ref_dim = min(width, height)
        scaled_size = max(16, int(font_size * ref_dim / 1080))

        style_cfg = dict(ASS_STYLE)
        style_cfg["Fontsize"] = str(scaled_size)
        if style == "youtube":
            style_cfg["Alignment"] = "2"
            style_cfg["MarginV"]   = "40"
            style_cfg["Fontsize"]  = str(max(14, scaled_size - 4))

        lines: list[str] = []

        # Header
        lines.append("[Script Info]")
        lines.append("ScriptType: v4.00+")
        lines.append(f"PlayResX: {width}")
        lines.append(f"PlayResY: {height}")
        lines.append("ScaledBorderAndShadow: yes")
        lines.append("")
        lines.append("[V4+ Styles]")
        lines.append("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding")
        style_line = (
            f"Style: {style_cfg['Name']},{style_cfg['Fontname']},{style_cfg['Fontsize']},"
            f"{style_cfg['PrimaryColour']},{style_cfg['SecondaryColour']},"
            f"{style_cfg['OutlineColour']},{style_cfg['BackColour']},"
            f"{style_cfg['Bold']},{style_cfg['Italic']},{style_cfg['BorderStyle']},"
            f"{style_cfg['Outline']},{style_cfg['Shadow']},{style_cfg['Alignment']},"
            f"{style_cfg['MarginL']},{style_cfg['MarginR']},{style_cfg['MarginV']},"
            f"{style_cfg['Encoding']}"
        )
        lines.append(style_line)
        lines.append("")
        lines.append("[Events]")
        lines.append("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text")

        # Agrupar palabras en líneas de N palabras
        groups = self._group_words(words, words_per_line)

        for group in groups:
            if not group:
                continue
            line_start = group[0].start
            line_end   = group[-1].end
            start_str  = self._fmt_time(line_start)
            end_str    = self._fmt_time(line_end)

            # Construir texto karaoke: {\kN}palabra
            # N = duración en centisegundos
            text_parts = []
            for w in group:
                dur_cs = max(1, int((w.end - w.start) * 100))
                # \kf = karaoke fill (el color secundario rellena de izq a der)
                text_parts.append(f"{{\\kf{dur_cs}}}{w.word}")

            text = " ".join(text_parts)
            lines.append(f"Dialogue: 0,{start_str},{end_str},Karaoke,,0,0,0,,{text}")

        with open(output_file, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines))

    def _group_words(self, words: list[WordEntry], n: int) -> list[list[WordEntry]]:
        """Agrupa palabras en bloques de n, respetando pausas largas."""
        groups = []
        current = []
        for i, w in enumerate(words):
            current.append(w)
            # Cortar si: alcanzamos n palabras, o hay pausa > 0.5s antes de la siguiente
            pause = (words[i+1].start - w.end) if i+1 < len(words) else 999
            if len(current) >= n or pause > 0.5:
                groups.append(current)
                current = []
        if current:
            groups.append(current)
        return groups

    @staticmethod
    def _fmt_time(seconds: float) -> str:
        """Convierte segundos a formato ASS H:MM:SS.cc"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        cs = int((seconds % 1) * 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    # ── Quemado de subtítulos ────────────────────────────────────────────────

    def _burn_subtitles(self, video: str, ass_file: str, output: str) -> None:
        """Quema el ASS en el video con FFmpeg.

        Ejecuta FFmpeg con cwd=directorio del ASS para evitar el problema
        de escapado de rutas Windows en el filtro ass=.
        """
        ass_path   = Path(ass_file).resolve()
        video_abs  = str(Path(video).resolve())
        output_abs = str(Path(output).resolve())
        cwd        = str(ass_path.parent)
        ass_name   = ass_path.name   # solo el nombre, sin ruta

        cmd = [
            FFMPEG, "-y",
            "-i", video_abs,
            "-vf", f"ass={ass_name}",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "28",            # menor tamaño, calidad suficiente para móvil
            "-c:a", "aac",
            "-ac", "2",              # estéreo — requerido por YouTube
            "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            output_abs,
        ]
        subprocess.run(cmd, capture_output=True, timeout=1800, cwd=cwd)  # 30 min máx

    # ── Utilidades ───────────────────────────────────────────────────────────

    def _get_resolution(self, video: str) -> tuple[int, int]:
        """Obtiene resolución usando ffmpeg -i (funciona sin ffprobe)."""
        try:
            result = subprocess.run(
                [FFMPEG, "-i", video],
                capture_output=True, text=True, timeout=10,
            )
            # La info va a stderr: "Stream #0:0: Video: h264, ..., 1080x1920"
            for line in result.stderr.splitlines():
                if "Video:" in line and "x" in line:
                    import re
                    m = re.search(r"(\d{3,5})x(\d{3,5})", line)
                    if m:
                        return int(m.group(1)), int(m.group(2))
        except Exception:
            pass
        return 1080, 1920  # fallback portrait

    def _get_duration(self, video: str) -> float:
        try:
            from mutagen.mp4 import MP4
            return MP4(video).info.length
        except Exception:
            return 0.0
