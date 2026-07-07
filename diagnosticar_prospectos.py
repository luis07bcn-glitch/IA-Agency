# -*- coding: utf-8 -*-
"""
Ejecuta el pipeline completo de ProspectorIA sobre los primeros N prospectos de
outputs/prospector/prospectos_dental_vng.json y guarda los diagnosticos en
outputs/prospector/diagnosticos_top.json (scorecard, perdida en EUR/mes,
servicios recomendados y textos personalizados: WhatsApp, email y guion).

Uso:  python diagnosticar_prospectos.py [N]   (N por defecto = 10)
"""
import os
import sys
import json
import traceback
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from agents.specialists.prospector.prospector_agent import ProspectorAgent
from agents.specialists.prospector.models import Business

IN = ROOT / "outputs" / "prospector" / "prospectos_dental_vng.json"
OUT = ROOT / "outputs" / "prospector" / "diagnosticos_top.json"

# Supuestos de partida conservadores (ajustables en la reunion con cada clinica)
LEADS_MES = 120
CONVERSION = 25.0

ESTETICA_HINTS = ("estetic", "estét", "laser", "láser", "medicina est", "belle",
                  "dermat", "cema", "vithas", "medic")


def tipo_de(nombre: str) -> str:
    n = nombre.lower()
    if any(h in n for h in ESTETICA_HINTS):
        return "clínica estética"
    return "clínica dental"


def biz_from(p: dict) -> Business:
    return Business(
        place_id=p.get("place_id", ""),
        nombre=p["nombre"],
        tipo=tipo_de(p["nombre"]),
        ciudad="Vilanova i la Geltrú",
        direccion=p.get("direccion", ""),
        telefono=p.get("telefono") or None,
        web=p.get("web") or None,
        rating=p.get("rating"),
        total_resenas=p.get("resenas", 0),
        tiene_web=bool(p.get("web")),
    )


def serializa(r, agent) -> dict:
    b = r.business
    return {
        "nombre": b.nombre,
        "tipo": b.tipo,
        "telefono": b.telefono,
        "web": b.web,
        "direccion": b.direccion,
        "rating": b.rating,
        "total_resenas": b.total_resenas,
        "ticket": r.ticket_promedio,
        "scorecard": r.scorecard,
        "win_probability": r.win_probability,
        "resumen_oportunidad": r.resumen_oportunidad,
        "pains": [{"categoria": p.categoria, "descripcion": p.descripcion,
                   "urgencia": p.urgencia, "servicio": p.servicio} for p in r.pains],
        "perdida_total_mes": r.perdida_total_mes,
        "perdidas": r.perdidas,
        "servicios_recomendados": r.servicios_recomendados,
        "email_asunto": r.email_asunto,
        "email_cuerpo": r.email_cuerpo,
        "whatsapp_mensaje": r.whatsapp_mensaje,
        "script_llamada": r.script_llamada,
    }


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    prospectos = json.loads(IN.read_text(encoding="utf-8"))[:n]
    agent = ProspectorAgent(nombre_agencia="MerakIA")

    results = []
    diag = []
    for i, p in enumerate(prospectos, 1):
        b = biz_from(p)
        print(f"[{i}/{len(prospectos)}] {b.nombre[:45]} ({b.tipo})...", flush=True)
        try:
            r = agent.analizar_negocio(b, generar_outreach=True)
            # guion de llamada
            negativas = [x for x in r.resenas if x.rating <= 3 and x.texto]
            try:
                r.script_llamada = agent.offer_gen.generar_script_llamada(
                    r.business, r.pains, negativas)
            except Exception as e:
                r.script_llamada = f"(no generado: {e})"
            # pricing: ticket, servicios, perdidas
            ticket = agent.pricing.ticket_sugerido(r.business.tipo)
            r.ticket_promedio = ticket
            servicios = agent.pricing.recomendar(r, ticket)
            r.servicios_recomendados = [{
                "nombre": s.servicio.nombre,
                "setup": s.setup,
                "mensual": s.mensual,
                "motivo": s.motivo,
                "impacto": s.impacto_especifico,
            } for s in servicios[:4]]
            perdidas = agent.pricing.calcular_perdidas(r, ticket, LEADS_MES, CONVERSION)
            r.perdidas = [pp.to_dict() for pp in perdidas]
            r.perdida_total_mes = agent.pricing.total_perdidas(perdidas)
            results.append(r)
            print(f"    OK · score {r.score_oportunidad} · pérdida ~{r.perdida_total_mes}€/mes "
                  f"· {len(r.servicios_recomendados)} servicios", flush=True)
        except Exception as e:
            print(f"    ERROR: {e}", flush=True)
            traceback.print_exc()

    # benchmark de nicho (percentil + win recalculado)
    try:
        agent.finalizar_lote(results)
    except Exception as e:
        print(f"finalizar_lote error: {e}", flush=True)

    for r in results:
        diag.append(serializa(r, agent))

    OUT.write_text(json.dumps(diag, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nOK -> {OUT}  ({len(diag)} diagnósticos)", flush=True)


if __name__ == "__main__":
    main()
