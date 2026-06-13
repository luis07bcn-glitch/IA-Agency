"""
PublishAgent — sube el video final a YouTube y/o TikTok.

YouTube: usa la YouTube Data API v3 con OAuth2.
TikTok:  usa la TikTok Content Posting API v2.

Requisitos previos:
  YouTube:
    1. Crear proyecto en Google Cloud Console
    2. Activar YouTube Data API v3
    3. Crear credenciales OAuth2 (Desktop app) → descargar client_secrets.json
    4. Primera vez: el agente abre el navegador para autorizar

  TikTok:
    1. Cuenta de desarrollador en developers.tiktok.com
    2. Crear app → obtener client_key + client_secret
    3. Autorizar con OAuth2 → access_token
"""

import json
import os
import subprocess
import webbrowser
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


@dataclass
class PublishResult:
    platform: str
    success: bool
    video_id: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PublishOutput:
    video_file: str
    results: list[PublishResult]

    def to_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        lines = []
        for r in self.results:
            status = "OK" if r.success else "FAIL"
            detail = r.url if r.url else r.error or ""
            lines.append(f"  [{status}] {r.platform}: {detail}")
        return "\n".join(lines)


class PublishAgent:
    name = "PublishAgent"
    description = "Sube el video a YouTube y/o TikTok usando sus APIs oficiales"

    def __init__(
        self,
        youtube_secrets_file: str = "",
        youtube_token_file: str = "youtube_token.json",
        tiktok_access_token: str = "",
    ):
        self.yt_secrets   = youtube_secrets_file
        self.yt_token     = youtube_token_file
        self.tt_token     = tiktok_access_token

    # ── API pública ──────────────────────────────────────────────────────────

    def run(
        self,
        video_file: str,
        script_data: dict,
        platforms: list[str],          # ["youtube", "tiktok"] o cualquiera
        schedule_time: Optional[str] = None,  # ISO8601, ej: "2025-06-15T18:00:00Z"
        youtube_privacy: str = "private",      # private | unlisted | public
        tiktok_privacy: str = "SELF_ONLY",     # SELF_ONLY | MUTUAL_FOLLOW_FRIENDS | PUBLIC_TO_EVERYONE
    ) -> PublishOutput:
        results: list[PublishResult] = []

        for platform in platforms:
            if platform == "youtube":
                r = self._publish_youtube(video_file, script_data, youtube_privacy, schedule_time)
            elif platform == "tiktok":
                r = self._publish_tiktok(video_file, script_data, tiktok_privacy)
            else:
                r = PublishResult(platform=platform, success=False, error=f"Plataforma desconocida: {platform}")
            results.append(r)

        return PublishOutput(video_file=video_file, results=results)

    def run_from_files(
        self,
        video_file: str,
        script_json: str,
        **kwargs,
    ) -> PublishOutput:
        with open(script_json, encoding="utf-8") as f:
            script_data = json.load(f)
        return self.run(video_file, script_data, **kwargs)

    # ── YouTube ──────────────────────────────────────────────────────────────

    def _publish_youtube(
        self,
        video_file: str,
        script: dict,
        privacy: str,
        schedule_time: Optional[str],
    ) -> PublishResult:
        try:
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
        except ImportError:
            return PublishResult(
                platform="youtube", success=False,
                error="Instala: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2"
            )

        SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

        # Cargar o refrescar credenciales
        creds = None
        token_path = Path(self.yt_token)
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.yt_secrets or not Path(self.yt_secrets).exists():
                    return PublishResult(
                        platform="youtube", success=False,
                        error="Necesitas client_secrets.json de Google Cloud. Ver README del PublishAgent."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(self.yt_secrets, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, "w") as f:
                f.write(creds.to_json())

        youtube = build("youtube", "v3", credentials=creds)

        # Metadata del video
        title       = script.get("youtube_title", "Video")[:100]
        description = script.get("youtube_description", "")[:5000]
        tags        = script.get("youtube_tags", [])[:500]
        category_id = "22"   # 22 = People & Blogs (bueno para biohacking/motivación)

        body = {
            "snippet": {
                "title":       title,
                "description": description,
                "tags":        tags,
                "categoryId":  category_id,
                "defaultLanguage": "es",
            },
            "status": {
                "privacyStatus":           privacy,
                "selfDeclaredMadeForKids": False,
                "madeForKids":             False,
            },
        }

        # Programar si se especificó hora
        if schedule_time and privacy != "public":
            body["status"]["privacyStatus"]  = "private"
            body["status"]["publishAt"]      = schedule_time

        media = MediaFileUpload(
            video_file,
            mimetype="video/mp4",
            resumable=True,
            chunksize=10 * 1024 * 1024,  # 10 MB chunks
        )

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = None
        while response is None:
            status, response = request.next_chunk()

        video_id = response.get("id", "")
        url = f"https://youtu.be/{video_id}" if video_id else ""

        return PublishResult(
            platform="youtube",
            success=bool(video_id),
            video_id=video_id,
            url=url,
        )

    # ── TikTok ───────────────────────────────────────────────────────────────

    def _publish_tiktok(
        self,
        video_file: str,
        script: dict,
        privacy: str,
    ) -> PublishResult:
        """Sube a TikTok via Content Posting API v2 (file upload)."""
        try:
            import urllib.request
            import urllib.parse
        except ImportError:
            pass  # stdlib

        if not self.tt_token:
            return PublishResult(
                platform="tiktok", success=False,
                error="Necesitas un access_token de TikTok. Ver README del PublishAgent."
            )

        caption  = script.get("tiktok_caption", "")[:2200]
        video_path = Path(video_file).resolve()
        file_size  = video_path.stat().st_size

        headers = {
            "Authorization": f"Bearer {self.tt_token}",
            "Content-Type":  "application/json; charset=UTF-8",
        }

        # 1. Iniciar la subida (Direct Post)
        init_body = json.dumps({
            "post_info": {
                "title":          caption,
                "privacy_level":  privacy,
                "disable_duet":   False,
                "disable_comment": False,
                "disable_stitch": False,
                "video_cover_timestamp_ms": 1000,
            },
            "source_info": {
                "source":          "FILE_UPLOAD",
                "video_size":      file_size,
                "chunk_size":      file_size,
                "total_chunk_count": 1,
            },
        }).encode("utf-8")

        init_req = urllib.request.Request(
            "https://open.tiktokapis.com/v2/post/publish/video/init/",
            data=init_body,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(init_req, timeout=30) as resp:
                init_data = json.loads(resp.read())
        except Exception as e:
            return PublishResult(platform="tiktok", success=False, error=f"Init error: {e}")

        if init_data.get("error", {}).get("code") != "ok":
            return PublishResult(
                platform="tiktok", success=False,
                error=f"TikTok init error: {init_data.get('error')}"
            )

        publish_id  = init_data["data"]["publish_id"]
        upload_url  = init_data["data"]["upload_url"]

        # 2. Subir el archivo
        with open(video_path, "rb") as vf:
            video_data = vf.read()

        upload_headers = {
            "Content-Type":  "video/mp4",
            "Content-Range": f"bytes 0-{file_size-1}/{file_size}",
            "Content-Length": str(file_size),
        }
        upload_req = urllib.request.Request(
            upload_url,
            data=video_data,
            headers=upload_headers,
            method="PUT",
        )
        try:
            with urllib.request.urlopen(upload_req, timeout=300) as resp:
                if resp.status not in (200, 201, 204):
                    return PublishResult(platform="tiktok", success=False, error=f"Upload HTTP {resp.status}")
        except Exception as e:
            return PublishResult(platform="tiktok", success=False, error=f"Upload error: {e}")

        return PublishResult(
            platform="tiktok",
            success=True,
            video_id=publish_id,
            url=f"https://www.tiktok.com/upload (publish_id: {publish_id})",
        )
