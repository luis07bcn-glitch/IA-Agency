"""
EditorAgent — ensambla audio narrado + clips de video en un MP4 final.

Pipeline por sección:
  1. Divide la duración del audio de la sección entre los clips disponibles
  2. Recorta cada clip a su ventana asignada (trim)
  3. Escala y crop al aspect ratio objetivo (portrait 1080x1920 / landscape 1920x1080)
  4. Concatena los clips de la sección con crossfade
  5. Une todas las secciones en el video final
  6. Mezcla el audio narrado + música de fondo (BGM a -18dB)
"""

import json
import os
import random
import subprocess
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

_MPT_FFMPEG = Path(r"C:\MPT\MoneyPrinterTurbo-Portable-Windows-1.2.6\lib\ffmpeg\ffmpeg-7.0-essentials_build\ffmpeg.exe")
_MPT_BGM_DIR = Path(r"C:\MPT\MoneyPrinterTurbo-Portable-Windows-1.2.6\MoneyPrinterTurbo\resource\songs")

FFMPEG = str(_MPT_FFMPEG) if _MPT_FFMPEG.exists() else "ffmpeg"

RESOLUTIONS = {
    "portrait":  (1080, 1920),
    "landscape": (1920, 1080),
    "square":    (1080, 1080),
}

CROSSFADE_DURATION = 0.5   # segundos entre clips
BGM_VOLUME = 0.08          # 8% del volumen original (~-22dB subjetivo)
VIDEO_FPS = 30
VIDEO_CRF = 23             # calidad H.264 (18=alta, 28=baja)


@dataclass
class EditorOutput:
    video_file: str
    duration_seconds: float
    width: int
    height: int
    file_size_mb: float
    sections_processed: int

    def to_dict(self) -> dict:
        return asdict(self)


class EditorAgent:
    name = "EditorAgent"
    description = "Ensambla clips de video + audio narrado en un MP4 final con música de fondo"

    def __init__(self):
        if not Path(FFMPEG).exists() and FFMPEG != "ffmpeg":
            raise FileNotFoundError(f"FFmpeg no encontrado en {FFMPEG}")

    # ── API pública ──────────────────────────────────────────────────────────

    def run(
        self,
        script_data: dict,
        voice_data: dict,
        media_data: dict,
        output_dir: str,
        orientation: str = "portrait",
        bgm_file: Optional[str] = None,
        bgm_volume: float = BGM_VOLUME,
    ) -> EditorOutput:
        """Ensambla el video final.

        Args:
            script_data:  dict del ScriptAgent
            voice_data:   dict del VoiceAgent
            media_data:   dict del MediaAgent
            output_dir:   carpeta de salida
            orientation:  portrait | landscape | square
            bgm_file:     ruta a MP3 de música de fondo (None = aleatorio de MPT)
            bgm_volume:   volumen relativo de la música (0.0–1.0)
        """
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        tmp = out / "_tmp"
        tmp.mkdir(exist_ok=True)

        width, height = RESOLUTIONS.get(orientation, RESOLUTIONS["portrait"])

        # Mapas rápidos
        duration_map  = {s["section_id"]: s["duration_seconds"] for s in voice_data["sections"]}
        audio_map     = {s["section_id"]: s["audio_file"]       for s in voice_data["sections"]}
        # Resolver rutas de clips a absolutas
        def _resolve(p: str) -> str:
            path = Path(p)
            if path.is_absolute(): return str(path)
            resolved = Path.cwd() / path
            return str(resolved) if resolved.exists() else p

        raw_clips = {s["section_id"]: s["clips"] for s in media_data["sections"]}
        clips_map = {
            sid: [{**c, "file": _resolve(c["file"])} for c in clips]
            for sid, clips in raw_clips.items()
        }

        # Música de fondo
        bgm = bgm_file or self._pick_bgm()

        # ── 1. Procesar cada sección ─────────────────────────────────────────
        section_videos: list[str] = []

        ordered_ids = sorted(clips_map.keys(), key=lambda x: (x == 999, x))
        for sid in ordered_ids:
            clips   = clips_map.get(sid, [])
            target  = duration_map.get(sid, 30.0)
            if not clips:
                continue

            label = "hook" if sid == 0 else "outro" if sid == 999 else f"s{sid}"
            section_mp4 = str(tmp / f"{label}.mp4")

            self._build_section(
                clips=clips,
                target_duration=target,
                output=section_mp4,
                width=width,
                height=height,
            )
            if Path(section_mp4).exists() and Path(section_mp4).stat().st_size > 1000:
                section_videos.append(section_mp4)

        if not section_videos:
            raise RuntimeError("No se generó ninguna sección de video.")

        # ── 2. Concatenar todas las secciones ────────────────────────────────
        silent_video = str(tmp / "silent_full.mp4")
        self._concat_sections(section_videos, silent_video)

        # ── 3. Obtener audio completo ────────────────────────────────────────
        full_audio = voice_data.get("full_audio_file", "")
        # Resolver ruta relativa desde el directorio del proyecto
        if full_audio:
            full_audio_path = Path(full_audio)
            if not full_audio_path.is_absolute():
                # Buscar relativo al cwd o al directorio del script JSON
                candidates = [full_audio_path, Path.cwd() / full_audio_path]
                full_audio = next((str(p.resolve()) for p in candidates if p.exists()), "")
        if not full_audio or not Path(full_audio).exists():
            # Reconstruir desde secciones
            full_audio = str(tmp / "full_audio.mp3")
            audio_files = [s["audio_file"] for s in voice_data["sections"]]
            audio_files = [str(Path(a).resolve()) if Path(a).exists() else
                           str((Path.cwd() / a).resolve()) for a in audio_files]
            self._concat_audio(audio_files, full_audio)

        # ── 4. Mezclar narración + BGM ───────────────────────────────────────
        mixed_audio = str(tmp / "mixed_audio.mp3")
        video_duration = self._get_duration(silent_video)
        if video_duration <= 0:
            raise RuntimeError(
                f"No se pudo leer la duración de {silent_video} — "
                f"el video concatenado parece corrupto. Temporales en {tmp}."
            )
        self._mix_audio(full_audio, bgm, mixed_audio, video_duration, bgm_volume)

        # ── 5. Combinar video silencioso + audio mezclado ────────────────────
        import unicodedata
        title = script_data.get("youtube_title", "video")[:40]
        # Normalizar a ASCII puro: FFmpeg en Windows falla con acentos/caracteres especiales
        title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
        title = "".join(c if c.isalnum() or c in " _-" else "" for c in title)
        title = title.strip().replace(" ", "_") or "video_final"
        final_mp4 = str(out / f"{title}.mp4")
        self._mux(silent_video, mixed_audio, final_mp4)

        # Validar ANTES de limpiar tmp — si falló el mux conservamos los temporales
        if not Path(final_mp4).exists() or Path(final_mp4).stat().st_size < 100_000:
            raise RuntimeError(
                f"El mux final falló: no se creó {final_mp4}. "
                f"Los archivos temporales se conservan en {tmp} para reintentar."
            )

        # Cleanup tmp
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)

        size_mb = round(Path(final_mp4).stat().st_size / 1_048_576, 1)
        return EditorOutput(
            video_file=final_mp4,
            duration_seconds=video_duration,
            width=width,
            height=height,
            file_size_mb=size_mb,
            sections_processed=len(section_videos),
        )

    def run_from_files(
        self,
        script_json: str,
        voice_json: str,
        media_json: str,
        output_dir: str,
        **kwargs,
    ) -> EditorOutput:
        with open(script_json,  encoding="utf-8") as f: script_data = json.load(f)
        with open(voice_json,   encoding="utf-8") as f: voice_data  = json.load(f)
        with open(media_json,   encoding="utf-8") as f: media_data  = json.load(f)
        return self.run(script_data, voice_data, media_data, output_dir, **kwargs)

    # ── Construcción de sección ──────────────────────────────────────────────

    def _build_section(
        self,
        clips: list[dict],
        target_duration: float,
        output: str,
        width: int,
        height: int,
    ) -> None:
        """Recorta y encadena clips para cubrir exactamente target_duration segundos."""
        tmp_clips: list[str] = []
        tmp_dir = Path(output).parent

        # Distribuir la duración objetivo entre los clips disponibles
        # Ciclar clips si hacen falta más
        files = [c["file"] for c in clips if Path(c["file"]).exists()]
        if not files:
            return

        # Calcular cuántos segundos asignar a cada clip
        assignments = self._assign_durations(files, target_duration)

        for i, (fpath, dur) in enumerate(assignments):
            trimmed = str(tmp_dir / f"_clip_{Path(output).stem}_{i}.mp4")
            self._trim_and_scale(fpath, dur, trimmed, width, height)
            if Path(trimmed).exists() and Path(trimmed).stat().st_size > 500:
                tmp_clips.append(trimmed)

        if not tmp_clips:
            return

        self._concat_video_clips(tmp_clips, output)

        # Limpiar clips temporales
        for f in tmp_clips:
            try: Path(f).unlink()
            except: pass

    def _assign_durations(self, files: list[str], total: float) -> list[tuple[str, float]]:
        """Asigna duración a cada clip ciclando si es necesario."""
        result = []
        accumulated = 0.0
        i = 0
        min_clip = 3.0
        max_clip = 8.0   # máx segundos por clip en el video final

        while accumulated < total:
            fpath = files[i % len(files)]
            remaining = total - accumulated
            dur = min(max_clip, remaining)
            if dur < min_clip and remaining < min_clip:
                dur = remaining
            result.append((fpath, round(dur, 3)))
            accumulated += dur
            i += 1
            if i > len(files) * 4:   # evitar bucle infinito
                break

        return result

    # ── FFmpeg helpers ───────────────────────────────────────────────────────

    def _run_ffmpeg(self, cmd: list, timeout: int, step: str) -> None:
        """Ejecuta FFmpeg y lanza RuntimeError con el stderr si falla."""
        result = subprocess.run(cmd, capture_output=True, timeout=timeout)
        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="replace")[-800:]
            raise RuntimeError(f"FFmpeg falló en '{step}':\n{stderr}")

    def _trim_and_scale(self, src: str, duration: float, output: str, w: int, h: int) -> None:
        """Recorta clip a `duration` segundos y escala/crop al aspect ratio."""
        # Calcular crop para mantener aspect ratio sin barras negras
        # scale2ref + crop centrado
        vf = (
            f"scale={w}:{h}:force_original_aspect_ratio=increase,"
            f"crop={w}:{h},"
            f"setsar=1"
        )
        cmd = [
            FFMPEG, "-y",
            "-ss", "0",
            "-i", src,
            "-t", str(duration),
            "-vf", vf,
            "-r", str(VIDEO_FPS),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", str(VIDEO_CRF),
            "-an",           # sin audio — lo añadimos después
            "-pix_fmt", "yuv420p",
            output,
        ]
        subprocess.run(cmd, capture_output=True, timeout=120)  # fallo tolerable: el clip se omite

    def _write_concat_list(self, paths: list[str], list_file: Path) -> None:
        """Escribe un concat list con forward slashes (requerido por FFmpeg en Windows)."""
        with open(list_file, "w", encoding="utf-8", newline="\n") as f:
            for p in paths:
                # FFmpeg requiere forward slashes incluso en Windows
                fwd = Path(p).resolve().as_posix()
                f.write(f"file '{fwd}'\n")

    def _concat_video_clips(self, clips: list[str], output: str) -> None:
        """Concatena clips sin re-encode usando concat demuxer."""
        list_file = Path(output).parent / f"_list_{Path(output).stem}.txt"
        self._write_concat_list(clips, list_file)
        cmd = [
            FFMPEG, "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            output,
        ]
        subprocess.run(cmd, capture_output=True, timeout=300)
        list_file.unlink(missing_ok=True)

    def _concat_sections(self, section_files: list[str], output: str) -> None:
        """Concatena secciones en el video completo."""
        list_file = Path(output).parent / "_sections_list.txt"
        self._write_concat_list(section_files, list_file)
        cmd = [
            FFMPEG, "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            output,
        ]
        self._run_ffmpeg(cmd, timeout=600, step="concat de secciones")
        list_file.unlink(missing_ok=True)
        if not Path(output).exists() or Path(output).stat().st_size < 100_000:
            raise RuntimeError(f"El concat de secciones no produjo {output}")

    def _concat_audio(self, audio_files: list[str], output: str) -> None:
        valid = [a for a in audio_files if Path(a).exists()]
        list_file = Path(output).parent / "_audio_list.txt"
        self._write_concat_list(valid, list_file)
        cmd = [FFMPEG, "-y", "-f", "concat", "-safe", "0",
               "-i", str(list_file), "-b:a", "192k", output]
        subprocess.run(cmd, capture_output=True, timeout=120)
        list_file.unlink(missing_ok=True)

    def _mix_audio(self, narration: str, bgm: str, output: str, duration: float, bgm_vol: float) -> None:
        """Mezcla narración + BGM. La BGM se loop si es más corta que el video."""
        # Resolver a rutas absolutas para evitar problemas con cwd en subprocess
        narration = str(Path(narration).resolve())
        bgm       = str(Path(bgm).resolve())
        cmd = [
            FFMPEG, "-y",
            "-i", narration,
            "-stream_loop", "-1", "-i", bgm,
            "-filter_complex",
            f"[1:a]volume={bgm_vol},apad[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[out]",
            "-map", "[out]",
            "-t", str(duration),
            "-b:a", "192k",
            output,
        ]
        self._run_ffmpeg(cmd, timeout=300, step="mezcla narración + BGM")

    def _mux(self, video: str, audio: str, output: str) -> None:
        """Combina video silencioso con audio mezclado en estéreo."""
        cmd = [
            FFMPEG, "-y",
            "-i", video,
            "-i", audio,
            "-c:v", "copy",
            "-c:a", "aac",
            "-ac", "2",      # estéreo — requerido por YouTube
            "-b:a", "192k",
            "-shortest",
            output,
        ]
        self._run_ffmpeg(cmd, timeout=300, step="mux video + audio")

    def _get_duration(self, mp4_file: str) -> float:
        from mutagen.mp4 import MP4
        try:
            dur = MP4(mp4_file).info.length
            if dur and dur > 0:
                return dur
        except Exception:
            pass
        # Fallback: parsear "Duration: HH:MM:SS.cc" del stderr de ffmpeg -i
        import re
        try:
            result = subprocess.run([FFMPEG, "-i", str(Path(mp4_file).resolve())],
                                    capture_output=True, text=True, timeout=15)
            m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", result.stderr)
            if m:
                h, mn, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
                return h * 3600 + mn * 60 + s
        except Exception:
            pass
        return 0.0

    def _pick_bgm(self) -> str:
        """Elige una pista de música de fondo aleatoria del directorio de MPT."""
        if _MPT_BGM_DIR.exists():
            songs = list(_MPT_BGM_DIR.glob("*.mp3"))
            if songs:
                return str(random.choice(songs))
        raise FileNotFoundError(f"No se encontró música de fondo en {_MPT_BGM_DIR}")
