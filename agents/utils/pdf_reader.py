"""Extrae texto de un PDF para usarlo como material de referencia en ScriptAgent."""

from pathlib import Path


def extract_pdf_text(path: str, max_chars: int = 5000) -> str:
    """Devuelve el texto extraído de un PDF, truncado a max_chars.

    Usa pypdf (ya instalado). Si el PDF es solo imágenes escaneadas devuelve cadena vacía.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF no encontrado: {path}")

    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        pages_text = []
        for page in reader.pages:
            text = page.extract_text() or ""
            pages_text.append(text)
        full_text = "\n".join(pages_text).strip()
        return full_text[:max_chars]
    except ImportError:
        raise ImportError("pypdf no instalado. Ejecuta: pip install pypdf")
    except Exception as e:
        raise RuntimeError(f"Error leyendo PDF '{path}': {e}")
