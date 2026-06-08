from pathlib import Path

_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"


def save_to_file(filename: str, content: str) -> dict:
    _OUTPUT_DIR.mkdir(exist_ok=True)
    safe_name = Path(filename).name  # prevent path traversal
    path = _OUTPUT_DIR / safe_name
    path.write_text(content, encoding="utf-8")
    return {"saved": str(path), "bytes": len(content.encode())}


def read_from_file(filename: str) -> dict:
    safe_name = Path(filename).name
    path = _OUTPUT_DIR / safe_name
    if not path.exists():
        return {"error": f"Archivo '{safe_name}' no encontrado en outputs/"}
    return {"filename": safe_name, "content": path.read_text(encoding="utf-8")}
