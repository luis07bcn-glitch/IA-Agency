# -*- coding: utf-8 -*-
"""
Genera una lista REAL de ~40 prospectos (gestorias / asesorias fiscales y
laborales en Vilanova i la Geltru + Garraf/Penedes) via Google Places API (New).
Exporta JSON + CSV en outputs/prospector/.

OJO: el scoring es DISTINTO al de clinicas (generar_prospectos.py).
Alli el buen prospecto era el que tenia dolor digital visible (sin web, mala
reputacion) porque vendemos marketing. Aqui vendemos automatizacion de
back-office (IDP facturas/DNI, seguimiento de expedientes): el dolor
(saturacion interna) NO se ve desde Google. El buen prospecto es el despacho
ESTABLECIDO (tiene clientela = volumen de papeles) y CONTACTABLE (web para
localizar email y personalizar, telefono para llamar).

Uso:
  - CLI:    venv\\Scripts\\python.exe generar_prospectos_gestorias.py
  - App:    from generar_prospectos_gestorias import recopilar, guardar,
            DEFAULT_QUERIES, CIUDAD_FOCO
"""
import csv
import json
import time
import requests
from pathlib import Path

ROOT = Path(__file__).parent
OUT_DIR = ROOT / "outputs" / "prospector"
PLACES = "https://places.googleapis.com/v1"

# Ciudad foco por defecto: las que esten aqui van primero en el ranking
CIUDAD_FOCO = "Vilanova i la Geltr"  # sin tilde final para casar variantes

DEFAULT_QUERIES = [
    # Vilanova i la Geltru primero (ciudad foco)
    "gestoria en Vilanova i la Geltru",
    "asesoria fiscal en Vilanova i la Geltru",
    "asesoria laboral en Vilanova i la Geltru",
    "gestor administrativo en Vilanova i la Geltru",
    # Garraf y Penedes para completar hasta 40
    "gestoria en Sant Pere de Ribes",
    "gestoria en Sitges",
    "asesoria fiscal en Sitges",
    "gestoria en Cubelles",
    "gestoria en Vilafranca del Penedes",
    "asesoria fiscal en Vilafranca del Penedes",
]


def load_key():
    """Lee GOOGLE_PLACES_API_KEY del .env. Devuelve None si no la encuentra
    (para que el import no reviente; el llamador decide qué hacer)."""
    env = ROOT / ".env"
    if not env.exists():
        return None
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("GOOGLE_PLACES_API_KEY"):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def search(query, key, limite=40):
    url = f"{PLACES}/places:searchText"
    headers = {
        "X-Goog-Api-Key": key,
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


def score_prospecto(p):
    """0-100. Mas alto = despacho establecido y contactable = mejor prospecto
    para vender automatizacion de back-office."""
    s = 40
    motivos = []
    web = p.get("websiteUri")
    tel = p.get("nationalPhoneNumber")
    rating = p.get("rating")
    n = p.get("userRatingCount", 0) or 0

    if web:
        s += 20; motivos.append("Con web (email localizable, despacho establecido)")
    else:
        s -= 5; motivos.append("Sin web (contactar por telefono/visita)")
    if tel:
        s += 15
    else:
        s -= 10; motivos.append("Sin telefono visible")

    if n >= 20:
        s += 15; motivos.append(f"Muy activo ({n} resenas = clientela amplia)")
    elif n >= 5:
        s += 8; motivos.append(f"Activo ({n} resenas)")
    else:
        motivos.append(f"Poca senal de actividad ({n} resenas)")

    if rating is not None:
        if rating >= 4.5:
            s += 10; motivos.append(f"Buena reputacion ({rating}) = buen cliente potencial")
        elif rating >= 4.0:
            s += 5
        else:
            s -= 5; motivos.append(f"Reputacion floja ({rating})")

    return max(0, min(100, s)), "; ".join(motivos)


def clasifica_tipo(nombre):
    """ICP primario = gestoria/asesoria fiscal-laboral (volumen de facturas y
    tramites). Los despachos puramente juridicos son ICP secundario: el angulo
    IDP-facturas les encaja peor, van mas abajo en el ranking."""
    n = nombre.lower()
    juridico = ("abogado", "advocat", "abogac", "advocac", "law", "legal", "juridic")
    gestoria = ("gestor", "gesti", "assessor", "asesor", "consultor", "fiscal",
                "laboral", "comptable", "contable")
    if any(k in n for k in gestoria):
        return "gestoria/asesoria"
    if any(k in n for k in juridico):
        return "despacho juridico"
    return "otros"


def normaliza(p, ciudad_foco=CIUDAD_FOCO):
    dn = p.get("displayName", {})
    nombre = dn.get("text", "") if isinstance(dn, dict) else str(dn)
    direccion = p.get("formattedAddress", "")
    s, motivos = score_prospecto(p)
    tipo = clasifica_tipo(nombre)
    if tipo == "despacho juridico":
        s = max(0, s - 20)
        motivos = "ICP secundario (juridico puro); " + motivos
    return {
        "place_id": p.get("id", ""),
        "nombre": nombre,
        "tipo": tipo,
        "direccion": direccion,
        "telefono": p.get("nationalPhoneNumber", ""),
        "web": p.get("websiteUri", ""),
        "rating": p.get("rating"),
        "resenas": p.get("userRatingCount", 0),
        "maps": p.get("googleMapsUri", ""),
        "estado": p.get("businessStatus", "OPERATIONAL"),
        "score_prospecto": s,
        "motivos": motivos,
        "en_foco": ciudad_foco.lower() in direccion.lower(),
    }


def recopilar(key=None, queries=None, ciudad_foco=CIUDAD_FOCO, limite=40,
              log=None):
    """Busca, deduplica, puntua y ordena prospectos. Devuelve la lista final
    (max `limite`). `log` es un callable(str) opcional para reportar progreso
    (la app le pasa un st.write; la CLI usa print)."""
    key = key or load_key()
    if not key:
        raise RuntimeError("Falta GOOGLE_PLACES_API_KEY (ni argumento ni .env).")
    queries = queries or DEFAULT_QUERIES

    def _say(msg):
        (log or print)(msg)

    vistos = set()
    prospectos = []
    for q in queries:
        try:
            res = search(q, key, limite=40)
        except Exception as e:
            _say(f"  ! query fallida '{q}': {e}")
            continue
        nuevos = 0
        for p in res:
            pid = p.get("id")
            if pid in vistos:
                continue
            est = p.get("businessStatus", "OPERATIONAL")
            if est not in ("OPERATIONAL", None):
                continue
            vistos.add(pid)
            prospectos.append(normaliza(p, ciudad_foco))
            nuevos += 1
        _say(f"  query '{q}': {len(res)} resultados ({nuevos} nuevos); acumulado {len(prospectos)}")
        if len(prospectos) >= max(limite * 2, 80):
            break

    # Ciudad foco primero; dentro de cada grupo, score desc y mas resenas primero
    # (mas actividad = mas volumen de papeles = mas dolor de saturacion)
    prospectos.sort(key=lambda x: (not x["en_foco"], -x["score_prospecto"], -x["resenas"]))
    return prospectos[:limite]


def guardar(prospectos, out_dir=OUT_DIR):
    """Escribe JSON + CSV y devuelve las rutas (json_path, csv_path)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "prospectos_gestorias_vng.json"
    csv_path = out_dir / "prospectos_gestorias_vng.csv"

    json_path.write_text(
        json.dumps(prospectos, ensure_ascii=False, indent=2), encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["#", "Nombre", "Tipo", "Telefono", "Web", "Rating", "Resenas",
                    "Score", "En Vilanova", "Senales", "Direccion", "Maps"])
        for i, p in enumerate(prospectos, 1):
            w.writerow([i, p["nombre"], p["tipo"], p["telefono"], p["web"] or "SIN WEB",
                        p["rating"] if p["rating"] is not None else "-",
                        p["resenas"], p["score_prospecto"],
                        "Si" if p["en_foco"] else "No (Garraf/Penedes)",
                        p["motivos"], p["direccion"], p["maps"]])
    return json_path, csv_path


def main():
    prospectos = recopilar()
    guardar(prospectos)
    con_web = sum(1 for p in prospectos if p["web"])
    en_foco = sum(1 for p in prospectos if p["en_foco"])
    print(f"\nOK: {len(prospectos)} prospectos -> {OUT_DIR}")
    print(f"   En foco ({CIUDAD_FOCO}): {en_foco} | Resto: {len(prospectos)-en_foco}")
    print(f"   Con web (email localizable): {con_web} | Sin web: {len(prospectos)-con_web}")


if __name__ == "__main__":
    main()
