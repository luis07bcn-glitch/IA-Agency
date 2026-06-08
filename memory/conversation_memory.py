import json
from pathlib import Path
from datetime import datetime

_MEMORY_DIR = Path(__file__).resolve().parent


class ConversationMemory:
    """Persistent conversation memory backed by a JSON file."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._path = _MEMORY_DIR / f"{session_id}.json"
        self.messages: list[dict] = self._load()

    def _load(self) -> list[dict]:
        if self._path.exists():
            return json.loads(self._path.read_text(encoding="utf-8"))
        return []

    def add(self, role: str, content: str) -> None:
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        self._save()

    def _save(self) -> None:
        self._path.write_text(
            json.dumps(self.messages, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get_history(self) -> list[dict]:
        return [{"role": m["role"], "content": m["content"]} for m in self.messages]

    def clear(self) -> None:
        self.messages.clear()
        if self._path.exists():
            self._path.unlink()
