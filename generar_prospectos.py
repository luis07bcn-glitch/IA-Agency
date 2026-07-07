# -*- coding: utf-8 -*-
"""
Genera una lista REAL de ~40 prospectos (clinicas dentales/estetica en Barcelona)
via Google Places API (New). Calcula un score de oportunidad determinista y
exporta JSON + CSV en outputs/prospector/.

Score de oportunidad (0-100): mayor = mejor prospecto para la agencia.
Heuristica: penaliza reputacion ya fuerte y premia senales de dolor digital
(sin web, pocas resenas, rating mejorable) -> mas margen para que la IA aporte.
"""
import os
import csv
import json
import time
import requests
from pathlib import Path

ROOT = Path(__file__).parent
OUT_DIR = ROOT / "outputs" / "prospector"
OUT_DIR.mkdir(parents=True, exist_ok=True)
PLACES = "https://places.googleapis.com/v1"

# Ciudad foco: las que esten aqui van primero en el ranking
CIUDAD_FOCO = "Vilanova i la Geltr"  # sin tilde final para casar variantes


def load_key():
    env = ROOT / ".env"
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("GOOGLE_PLACES_API_KEY"):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("No GOOGLE_PLACES_API_KEY en .env")


KEY = load_key()


def search(query, limite=40):
    url = f"{PLACES}/places:searchText"
    headers = {
        "X-Goog-Api-Key": KEY,
        "X-Goog-FieldMask": ",".join([
            "places.id", "places.displayName", "places.formattedAddress",
            "places.rating", "places.userRatingCount",
            "places.nationalPhoneNumber", "places.websiteUri",
            "places.googleMapsUri", "places.businessStatus",
            "nextPageToken",
        ]),
        "Content-Type": "application/json",
    }
    body = {"textQuery": query, "languageCode": "es", "regionCode": "ES",
            "pageSize": 20}
    out = []
    for _ in range(3):  # hasta 3 paginas (60 max)
        r = requests.post(url, headers=headers, json=body, timeout=20)
        d = r.json()
        if r.status_code != 200:
            err = d.get("error", {})
            raise RuntimeError(f"Places error {err.get('status', r.status_code)}: "
                               f"{err.get('message', '')}")
        for p in d.get("places", []):
            out.append(p)
        tok = d.get("nextPageToken")
        if not tok or len(out) >= limite:
            break
        body["pageToken"] = tok
        time.sleep(2)  # el token tarda un momento en activarse
    return out


def score_oportunidad(p):
    """0-100. Mas alto = mas dolor digital = mejor prospecto."""
    s = 50
    motivos = []
    web = p.get("websiteUri")
    rating = p.get("rating")
    n = p.get("userRatingCount", 0) or 0

    if not web:
        s += 25; motivos.append("Sin web propia")
    if not p.get("nationalPhoneNumber"):
        s += 5; motivos.append("Sin telefono visible")
    if rating is None:
        s += 10; motivos.append("Sin valoraciones")
    else:
        if rating < 4.0:
            s += 18; motivos.append(f"Rating bajo ({rating})")
        elif rating < 4.5:
            s += 10; motivos.append(f"Rating mejorable ({rating})")
        else:
            s -= 5
    if n == 0:
        s += 10; motivos.append("0 resenas")
    elif n < 30:
        s += 12; motivos.append(f"Pocas resenas ({n})")
    elif n < 100:
        s += 5; motivos.append(f"Resenas moderadas ({n})")
    else:
        s -= 5  # ya tiene presencia fuerte
    s = max(0, min(100, s))
    if not motivos:
        motivos.append("Presencia digital solida; entrar por eficiencia/automatizacion")
    return s, "; ".join(motivos)


def normaliza(p):
    dn = p.get("displayName", {})
    nombre = dn.get("text", "") if isinstance(dn, dict) else str(dn)
    direccion = p.get("formattedAddress", "")
    s, motivos = score_oportunidad(p)
    return {
        "place_id": p.get("id", ""),
        "nombre": nombre,
        "direccion": direccion,
        "telefono": p.get("nationalPhoneNumber", ""),
        "web": p.get("websiteUri", ""),
        "rating": p.get("rating"),
        "resenas": p.get("userRatingCount", 0),
        "maps": p.get("googleMapsUri", ""),
        "estado": p.get("businessStatus", "OPERATIONAL"),
        "score_oportunidad": s,
        "motivos": motivos,
        "en_foco": CIUDAD_FOCO.lower() in direccion.lower(),
    }


def main():
    queries = [
        # Vilanova i la Geltru primero (ciudad foco)
        "clinica dental en Vilanova i la Geltru",
        "clinica de medicina estetica en Vilanova i la Geltru",
        "clinica estetica en Vilanova i la Geltru",
        # Comarca del Garraf y alrededores para completar hasta 40
        "clinica dental en Sant Pere de Ribes",
        "clinica dental en Sitges",
        "clinica dental en Cubelles",
        "clinica dental en Canyelles",
        "clinica dental en Vilafranca del Penedes",
    ]
    vistos = set()
    prospectos = []
    for q in queries:
        try:
            res = search(q, limite=40)
        except Exception as e:
            print(f"  ! query fallida '{q}': {e}")
            continue
        for p in res:
            pid = p.get("id")
            if pid in vistos:
                continue
            est = p.get("businessStatus", "OPERATIONAL")
            if est not in ("OPERATIONAL", None):
                continue
            vistos.add(pid)
            prospectos.append(normaliza(p))
        print(f"  query '{q}': {len(res)} resultados; acumulado {len(prospectos)}")
        if len(prospectos) >= 60:
            break

    # Vilanova primero; dentro de cada grupo, oportunidad desc y resenas asc
    prospectos.sort(key=lambda x: (not x["en_foco"], -x["score_oportunidad"], x["resenas"]))
    prospectos = prospectos[:40]

    (OUT_DIR / "prospectos_dental_vng.json").write_text(
        json.dumps(prospectos, ensure_ascii=False, indent=2), encoding="utf-8")

    with (OUT_DIR / "prospectos_dental_vng.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["#", "Nombre", "Telefono", "Web", "Rating", "Resenas",
                    "Score", "En Vilanova", "Senales de oportunidad", "Direccion", "Maps"])
        for i, p in enumerate(prospectos, 1):
            w.writerow([i, p["nombre"], p["telefono"], p["web"] or "SIN WEB",
                        p["rating"] if p["rating"] is not None else "-",
                        p["resenas"], p["score_oportunidad"],
                        "Si" if p["en_foco"] else "No (Garraf)",
                        p["motivos"], p["direccion"], p["maps"]])

    sin_web = sum(1 for p in prospectos if not p["web"])
    en_foco = sum(1 for p in prospectos if p["en_foco"])
    print(f"\nOK: {len(prospectos)} prospectos -> {OUT_DIR}")
    print(f"   En Vilanova i la Geltru: {en_foco} | Resto Garraf: {len(prospectos)-en_foco}")
    print(f"   Sin web: {sin_web} | Rating<4.5: "
          f"{sum(1 for p in prospectos if p['rating'] and p['rating']<4.5)}")


if __name__ == "__main__":
    main()
