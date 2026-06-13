import json
import time
import urllib.request
import urllib.parse
import urllib.error
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from config import settings

PEXELS_VIDEO_API = "https://api.pexels.com/videos/search"
PEXELS_PHOTO_API = "https://api.pexels.com/v1/search"

# Resolución mínima aceptable para un clip
MIN_WIDTH = 1080
MIN_DURATION = 3   # segundos
MAX_DURATION = 30  # segundos por clip individual


# ── Modelos de datos ─────────────────────────────────────────────────────────

@dataclass
class ClipInfo:
    section_id: int
    keyword: str
    file: str           # ruta local descargada
    duration: float     # segundos
    width: int
    height: int
    source_url: str
    pexels_id: int


@dataclass
class SectionMedia:
    section_id: int
    target_duration: float      # segundos de audio que debe cubrir
    clips: list[ClipInfo]
    total_clip_duration: float  # suma de clips descargados


@dataclass
class MediaOutput:
    total_sections: int
    output_dir: str
    sections: list[SectionMedia]

    def to_dict(self) -> dict:
        return asdict(self)

    def coverage_report(self) -> str:
        lines = []
        for s in self.sections:
            label = "hook" if s.section_id == 0 else "outro" if s.section_id == 999 else f"sección {s.section_id}"
            pct = (s.total_clip_duration / s.target_duration * 100) if s.target_duration else 0
            lines.append(f"  {label}: {s.total_clip_duration:.0f}s / {s.target_duration:.0f}s ({pct:.0f}%)")
        return "\n".join(lines)


# ── Agente ───────────────────────────────────────────────────────────────────

class MediaAgent:
    name = "MediaAgent"
    description = "Descarga clips de video de Pexels para cada sección del guión según las visual_keywords"

    def __init__(self, pexels_api_key: str = ""):
        self._key = pexels_api_key or settings.pexels_api_key
        if not self._key:
            raise ValueError("Pexels API key requerida. Configura PEXELS_API_KEY en .env o pásala en __init__.")

    # ── API pública ──────────────────────────────────────────────────────────

    def run(
        self,
        script_data: dict,
        voice_data: dict,
        output_dir: str,
        orientation: str = "portrait",   # "portrait" (9:16 TikTok) | "landscape" (16:9 YT)
        clips_per_section: int = 4,      # cuántos clips distintos buscar por sección
    ) -> MediaOutput:
        """Descarga clips de Pexels para cada sección del video.

        Args:
            script_data:      dict del VideoScript (script_agent)
            voice_data:       dict del VoiceOutput (voice_agent) — para saber duración real
            output_dir:       carpeta raíz donde guardar los clips
            orientation:      "portrait" (9:16) o "landscape" (16:9)
            clips_per_section: clips distintos a descargar por sección
        """
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        # Mapa section_id → duración real del audio
        duration_map = self._build_duration_map(voice_data)

        sections_media: list[SectionMedia] = []

        # Hook
        hook_dir = out / "hook"
        hook_clips = self._fetch_section(
            section_id=0,
            keywords=["productivity success morning", "sunrise motivation"],
            target_duration=duration_map.get(0, 20),
            out_dir=hook_dir,
            orientation=orientation,
            clips_per_section=2,
        )
        sections_media.append(SectionMedia(
            section_id=0,
            target_duration=duration_map.get(0, 20),
            clips=hook_clips,
            total_clip_duration=sum(c.duration for c in hook_clips),
        ))

        # Secciones principales
        for section in script_data["sections"]:
            sid = section["section_id"]
            keywords = section.get("visual_keywords", [])
            target = duration_map.get(sid, section.get("duration_seconds", 120))
            sec_dir = out / f"section_{sid}"

            clips = self._fetch_section(
                section_id=sid,
                keywords=keywords,
                target_duration=target,
                out_dir=sec_dir,
                orientation=orientation,
                clips_per_section=clips_per_section,
            )
            sections_media.append(SectionMedia(
                section_id=sid,
                target_duration=target,
                clips=clips,
                total_clip_duration=sum(c.duration for c in clips),
            ))

        # Outro
        outro_dir = out / "outro"
        outro_clips = self._fetch_section(
            section_id=999,
            keywords=["subscribe button, like notification bell", "success celebration"],
            target_duration=duration_map.get(999, 45),
            out_dir=outro_dir,
            orientation=orientation,
            clips_per_section=2,
        )
        sections_media.append(SectionMedia(
            section_id=999,
            target_duration=duration_map.get(999, 45),
            clips=outro_clips,
            total_clip_duration=sum(c.duration for c in outro_clips),
        ))

        return MediaOutput(
            total_sections=len(sections_media),
            output_dir=str(out),
            sections=sections_media,
        )

    def run_from_files(
        self,
        script_json: str,
        voice_json: str,
        output_dir: str,
        **kwargs,
    ) -> MediaOutput:
        with open(script_json, encoding="utf-8") as f:
            script_data = json.load(f)
        with open(voice_json, encoding="utf-8") as f:
            voice_data = json.load(f)
        return self.run(script_data, voice_data, output_dir, **kwargs)

    # ── Lógica de búsqueda y descarga ────────────────────────────────────────

    def _fetch_section(
        self,
        section_id: int,
        keywords: list[str],
        target_duration: float,
        out_dir: Path,
        orientation: str,
        clips_per_section: int,
    ) -> list[ClipInfo]:
        """Busca y descarga clips hasta cubrir target_duration segundos."""
        out_dir.mkdir(parents=True, exist_ok=True)
        clips: list[ClipInfo] = []
        accumulated = 0.0
        used_ids: set[int] = set()

        # Intenta cada keyword hasta tener suficiente material
        for keyword in keywords:
            if accumulated >= target_duration * 1.2:
                break

            results = self._search_videos(keyword, orientation, per_page=10)
            for video in results:
                if accumulated >= target_duration * 1.2:
                    break
                if video["id"] in used_ids:
                    continue
                if len(clips) >= clips_per_section * len(keywords):
                    break

                file_url, width, height, clip_dur = self._best_file(video, orientation)
                if not file_url:
                    continue

                fname = out_dir / f"{section_id}_{video['id']}.mp4"
                if self._download(file_url, fname):
                    clips.append(ClipInfo(
                        section_id=section_id,
                        keyword=keyword,
                        file=str(fname),
                        duration=clip_dur,
                        width=width,
                        height=height,
                        source_url=video.get("url", ""),
                        pexels_id=video["id"],
                    ))
                    used_ids.add(video["id"])
                    accumulated += clip_dur
                    time.sleep(0.15)   # respetar rate limit de Pexels

        return clips

    def _search_videos(self, query: str, orientation: str, per_page: int = 10) -> list[dict]:
        """Llama a la API de Pexels Videos y devuelve la lista de videos."""
        params = urllib.parse.urlencode({
            "query": query,
            "orientation": orientation,
            "size": "medium",
            "per_page": per_page,
        })
        url = f"{PEXELS_VIDEO_API}?{params}"
        req = urllib.request.Request(url, headers={"Authorization": self._key, "User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
                return data.get("videos", [])
        except Exception:
            return []

    def _best_file(self, video: dict, orientation: str) -> tuple[Optional[str], int, int, float]:
        """Selecciona el archivo de mayor resolución adecuada para la orientación."""
        files = video.get("video_files", [])
        clip_dur = video.get("duration", 0)

        if clip_dur < MIN_DURATION or clip_dur > MAX_DURATION:
            return None, 0, 0, 0

        # Filtrar por orientación y resolución mínima
        if orientation == "portrait":
            candidates = [f for f in files if f.get("height", 0) >= MIN_WIDTH and f.get("width", 0) < f.get("height", 1)]
        else:
            candidates = [f for f in files if f.get("width", 0) >= MIN_WIDTH and f.get("width", 0) > f.get("height", 0)]

        if not candidates:
            # Fallback: cualquier archivo HD disponible
            candidates = [f for f in files if f.get("width", 0) >= 720]

        if not candidates:
            return None, 0, 0, 0

        # El de mayor resolución
        best = max(candidates, key=lambda f: f.get("width", 0) * f.get("height", 0))
        return best.get("link"), best.get("width", 0), best.get("height", 0), float(clip_dur)

    def _download(self, url: str, dest: Path) -> bool:
        """Descarga un archivo de video."""
        if dest.exists() and dest.stat().st_size > 10_000:
            return True
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MerakIA-VideoAgent/1.0"})
            with urllib.request.urlopen(req, timeout=60) as resp, open(dest, "wb") as f:
                while chunk := resp.read(1024 * 256):
                    f.write(chunk)
            return dest.stat().st_size > 10_000
        except Exception:
            if dest.exists():
                dest.unlink(missing_ok=True)
            return False

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _build_duration_map(self, voice_data: dict) -> dict[int, float]:
        """Construye un mapa section_id → duración real del audio."""
        result = {}
        for s in voice_data.get("sections", []):
            result[s["section_id"]] = s["duration_seconds"]
        return result
