"""
Orquestador del sistema de alertas IA.
Analiza la watchlist, puntúa cada ticker (macro + fundamental + técnico)
y envía alertas por Telegram cuando el score supera el umbral.

Uso:
  venv\\Scripts\\python.exe financial_analyzer/alerts_engine/runner.py
  venv\\Scripts\\python.exe financial_analyzer/alerts_engine/runner.py --dry-run
  venv\\Scripts\\python.exe financial_analyzer/alerts_engine/runner.py --ticker NVDA
  venv\\Scripts\\python.exe financial_analyzer/alerts_engine/runner.py --ticker NVDA --dry-run
"""
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env", override=False)

from financial_analyzer.fundamentals.scorer import score_ticker, WATCHLIST
from financial_analyzer.alerts_engine.technical import get_technical_features
from financial_analyzer.alerts_engine.scorer import compute_unified_score
from financial_analyzer.alerts_engine.llm_agent import generate_analysis
from financial_analyzer.alerts.notifier import send_telegram

# ── Configuración ────────────────────────────────────────────────
SCORE_THRESHOLD = int(os.getenv("ALERT_SCORE_THRESHOLD", "68"))
DB_PATH = str(ROOT / "financial_analyzer" / "data" / "financial_data.duckdb")

SESGO_ICON  = {"ALCISTA": "📈", "BAJISTA": "📉", "NEUTRO": "➡️"}
REGIME_ICON = {"RISK-ON": "🟢", "NEUTRAL": "🟡", "RISK-OFF": "🔴"}


def _load_regime():
    """Carga el RegimeScore desde la DB. Retorna None si la DB aún no existe."""
    db = Path(DB_PATH)
    if not db.exists():
        print("  AVISO: DB no encontrada. Ejecuta update_data.py primero. Usando régimen NEUTRAL.")
        return None
    try:
        from financial_analyzer.engine.regime_engine import build_inputs_from_db, compute_regime_score
        inputs = build_inputs_from_db(DB_PATH)
        return compute_regime_score(inputs) if inputs else None
    except Exception as e:
        print(f"  AVISO: No se pudo cargar régimen ({e}). Usando NEUTRAL.")
        return None


def _format_alert(ticker: str, company: str, unified, llm_result: dict) -> str:
    """Formatea el mensaje de Telegram en HTML."""
    sesgo = llm_result.get("sesgo", "NEUTRO")
    icon = SESGO_ICON.get(sesgo, "➡️")
    r_icon = REGIME_ICON.get(unified.regime, "⚪")

    price    = unified.tech_features.get("price", "?")
    rsi      = unified.tech_features.get("rsi", "?")
    vs200    = unified.tech_features.get("vs_sma200_pct")
    vs200_str = f"{vs200:+.1f}%" if vs200 is not None else "N/A"
    vol_ratio = unified.tech_features.get("volume_ratio", "?")

    catalizadores = llm_result.get("catalizadores", [])
    riesgos       = llm_result.get("riesgos", [])
    niveles       = llm_result.get("niveles", {})

    entrada   = niveles.get("entrada") or "—"
    stop      = niveles.get("stop") or "—"
    target    = niveles.get("target1") or "—"
    horizonte = niveles.get("horizonte") or "—"
    confianza = llm_result.get("confianza_llm", 0)

    ts = datetime.now().strftime("%d/%m/%Y %H:%M")

    parts = [
        f"{icon} <b>ALERTA IA — {ticker}</b>",
    ]
    if company:
        parts.append(f"<i>{company}</i>")

    parts += [
        "",
        f"<b>Score: {unified.total}/100</b>  |  {r_icon} {unified.regime}",
        f"Macro {unified.macro_pts:.0f}/25 · Fund {unified.fund_pts:.0f}/40 · Técnico {unified.tech_pts:.0f}/35",
        "",
        f"<b>Técnico:</b>  Precio {price}  |  RSI {rsi}  |  SMA200 {vs200_str}  |  Vol {vol_ratio}x",
        "",
        f"<b>Análisis:</b>",
        llm_result.get("analisis", ""),
        "",
    ]

    if catalizadores:
        parts.append("<b>Catalizadores:</b>")
        parts += [f"  • {c}" for c in catalizadores[:3]]
        parts.append("")

    if riesgos:
        parts.append("<b>Riesgos:</b>")
        parts += [f"  • {r}" for r in riesgos[:2]]
        parts.append("")

    parts += [
        f"<b>Niveles:</b>  Entrada {entrada}  |  Stop {stop}  |  Target {target}",
        f"Horizonte: {horizonte}",
        "",
        f"<i>Confianza LLM: {confianza}/100  ·  {ts}</i>",
        f"<i>⚠️ Solo informativo. No es asesoramiento financiero.</i>",
    ]

    return "\n".join(parts)


def run_analysis(
    tickers_dict: dict | None = None,
    dry_run: bool = False,
    verbose: bool = True,
    score_threshold: int | None = None,
) -> list[dict]:
    """
    Analiza la watchlist y envía alertas Telegram para los tickers que superen el umbral.
    Retorna lista de resultados con score y estado de cada ticker.
    """
    if tickers_dict is None:
        tickers_dict = WATCHLIST
    threshold = score_threshold if score_threshold is not None else SCORE_THRESHOLD

    if verbose:
        print(f"\n{'='*60}")
        print(f"  Sistema de Alertas IA  —  {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print(f"  Tickers: {len(tickers_dict)}  |  Umbral: {threshold}/100")
        print(f"  Modo: {'DRY-RUN (sin alertas)' if dry_run else 'PRODUCCIÓN'}")
        print(f"{'='*60}\n")

    regime_score = _load_regime()
    regime_label = regime_score.regime if regime_score else "NEUTRAL (sin DB)"
    if verbose:
        icon = REGIME_ICON.get(regime_label.split(" ")[0], "⚪")
        print(f"  Régimen macro: {icon} {regime_label}\n")

    results = []
    alerts_sent = 0

    for ticker, company in tickers_dict.items():
        if verbose:
            print(f"  [{ticker:8s}] {company[:25]:25s}", end="  ", flush=True)

        # 1. Datos técnicos
        tech = get_technical_features(ticker)
        if tech is None:
            if verbose:
                print("sin datos técnicos")
            results.append({"ticker": ticker, "status": "no_data"})
            continue

        # 2. Score fundamental
        fund = score_ticker(ticker, company)

        # 3. Score unificado
        unified = compute_unified_score(ticker, regime_score, fund, tech)

        if verbose:
            print(f"score={unified.total:5.1f}/100", end="")

        status = "below_threshold"

        if unified.total >= threshold:
            if verbose:
                print("  → 🔔 ALERTA", end="")

            llm_result = generate_analysis(unified, regime_score, company)
            msg = _format_alert(ticker, company, unified, llm_result)

            if not dry_run:
                ok = send_telegram(msg)
                status = "alert_sent" if ok else "alert_failed"
                if verbose:
                    print(f" ({'enviada ✓' if ok else 'ERROR ✗'})", end="")
            else:
                status = "dry_run"
                if verbose:
                    print(f" (dry-run)", end="")
                    print(f"\n{'─'*50}\n{msg}\n{'─'*50}")

            alerts_sent += 1
            results.append({
                "ticker": ticker, "company": company,
                "score": unified.total, "regime": unified.regime,
                "status": status, "llm": llm_result,
            })
        else:
            results.append({
                "ticker": ticker, "company": company,
                "score": unified.total, "regime": unified.regime,
                "status": status,
            })

        if verbose:
            print()

    if verbose:
        print(f"\n  Completado: {alerts_sent} alertas / {len(tickers_dict)} tickers analizados")

    # Resumen diario por Telegram
    if not dry_run:
        top = sorted(
            [x for x in results if "score" in x],
            key=lambda x: x["score"], reverse=True
        )[:3]
        top_str = "\n".join(
            f"  • {x['ticker']} ({x.get('company', '')}): {x['score']:.1f}/100"
            for x in top
        ) or "  Ninguno superó el umbral"

        regime_info = (
            f"{REGIME_ICON.get(regime_score.regime, '⚪')} {regime_score.regime} ({regime_score.total:.0f}/100)"
            if regime_score else "Sin datos de régimen"
        )

        summary = (
            f"📊 <b>Resumen diario — {datetime.now().strftime('%d/%m/%Y')}</b>\n\n"
            f"Régimen: {regime_info}\n"
            f"Alertas generadas: <b>{alerts_sent}</b> de {len(tickers_dict)} tickers\n\n"
            f"<b>Top scores del día:</b>\n{top_str}\n\n"
            f"<i>Umbral de alerta: {threshold}/100</i>"
        )
        send_telegram(summary)

    return results


def main():
    parser = argparse.ArgumentParser(description="Sistema de Alertas IA — Financial Analyzer")
    parser.add_argument("--dry-run", action="store_true",
                        help="Muestra alertas por consola sin enviar a Telegram")
    parser.add_argument("--ticker", type=str,
                        help="Analiza solo este ticker (ej: NVDA, AAPL)")
    parser.add_argument("--threshold", type=int, default=None,
                        help=f"Umbral de score para alertas (default: {SCORE_THRESHOLD})")
    args = parser.parse_args()

    threshold = SCORE_THRESHOLD
    if args.threshold:
        threshold = args.threshold

    if args.ticker:
        ticker = args.ticker.upper()
        tickers = {ticker: WATCHLIST.get(ticker, ticker)}
    else:
        tickers = WATCHLIST

    run_analysis(tickers, dry_run=args.dry_run, score_threshold=threshold)


if __name__ == "__main__":
    main()
