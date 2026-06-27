"""
Paper Trading Runner — simula operaciones basadas en scoring.

Uso:
  venv\\Scripts\\python.exe financial_analyzer/alerts_engine/paper_runner.py
  venv\\Scripts\\python.exe financial_analyzer/alerts_engine/paper_runner.py --reset
  venv\\Scripts\\python.exe financial_analyzer/alerts_engine/paper_runner.py --report
"""
import os
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env", override=False)

from financial_analyzer.fundamentals.scorer import score_ticker, WATCHLIST
from financial_analyzer.alerts_engine.polygon_fetcher import get_technical_features
from financial_analyzer.alerts_engine.scorer import compute_unified_score
from financial_analyzer.alerts_engine.paper_trading import Portfolio, OperationStatus, Trade

PORTFOLIO_FILE = ROOT / "financial_analyzer" / "data" / "paper_portfolio.json"
DB_PATH = str(ROOT / "financial_analyzer" / "data" / "financial_data.duckdb")

ENTRY_THRESHOLD = 70
EXIT_SCORE_THRESHOLD = 50

# Mapa de sectores para toda la watchlist
SECTOR_MAP: dict[str, str] = {
    # IBEX / EuroStoxx
    "SAN.MC": "financiero",  "BBVA.MC": "financiero",
    "TEF.MC": "telecom",     "IBE.MC": "utilities",
    "ITX.MC": "consumo",     "REP.MC": "energia",
    "AMS.MC": "tecnologia",  "FER.MC": "infraestructura",
    "SAP.DE": "tecnologia",  "ASML.AS": "semiconductores",
    "MC.PA":  "consumo",     "SIE.DE": "industrial",
    "AIR.PA": "defensa",     "SU.PA":  "industrial",
    # Semiconductores
    "NVDA": "semiconductores", "AMD":  "semiconductores",
    "TSM":  "semiconductores", "QCOM": "semiconductores",
    "INTC": "semiconductores", "MU":   "semiconductores",
    "AMAT": "semiconductores", "LRCX": "semiconductores",
    "KLAC": "semiconductores", "AVGO": "semiconductores",
    "ON":   "semiconductores", "MRVL": "semiconductores",
    "ARM":  "semiconductores",
    # IA / Software / Nube
    "AAPL":  "tecnologia", "MSFT":  "tecnologia",
    "GOOGL": "tecnologia", "META":  "tecnologia",
    "AMZN":  "tecnologia", "PLTR":  "tecnologia",
    "CRM":   "tecnologia", "SNOW":  "tecnologia",
    "DDOG":  "tecnologia", "NET":   "tecnologia",
    # Uranio / Nuclear
    "CCJ":  "energia",  "UEC":  "energia",
    "NXE":  "energia",  "DNN":  "energia",
    "UUUU": "energia",  "URA":  "energia",
    "SMR":  "energia",  "CEG":  "utilities",
    "VST":  "utilities",
    # Energía tradicional
    "XOM": "energia", "CVX": "energia",
    "SLB": "energia", "OXY": "energia",
    # Metales / Minería
    "FCX":  "materias_primas", "SCCO": "materias_primas",
    "NEM":  "materias_primas", "GOLD": "materias_primas",
    "MP":   "materias_primas", "ALB":  "materias_primas",
    "SQM":  "materias_primas",
    # Defensa
    "LMT":  "defensa", "NOC":  "defensa",
    "RTX":  "defensa", "GD":   "defensa",
    "HII":  "defensa", "LDOS": "defensa",
    # Salud / Biofarma
    "LLY":  "salud", "ABBV": "salud",
    "NVO":  "salud", "MRNA": "salud",
    "REGN": "salud", "JNJ":  "salud",
    # Financiero
    "JPM":  "financiero", "GS":   "financiero",
    "V":    "financiero", "MA":   "financiero",
    "COIN": "financiero",
    # Infraestructura / Utilities
    "AMT":  "infraestructura", "EQIX": "infraestructura",
    "NEE":  "utilities",
    # Defensivas
    "PG":  "consumo", "KO":  "consumo", "WMT": "consumo",
}


def _load_regime():
    """Carga el RegimeScore real desde la DB. Retorna None si no disponible."""
    db = Path(DB_PATH)
    if not db.exists():
        return None
    try:
        from financial_analyzer.engine.regime_engine import build_inputs_from_db, compute_regime_score
        inputs = build_inputs_from_db(DB_PATH)
        return compute_regime_score(inputs) if inputs else None
    except Exception:
        return None


def load_portfolio() -> Portfolio:
    """Carga el portfolio desde archivo o crea uno nuevo."""
    if not PORTFOLIO_FILE.exists():
        return Portfolio()

    try:
        with open(PORTFOLIO_FILE) as f:
            data = json.load(f)

        portfolio = Portfolio(
            initial_capital=data.get("initial_capital", 10000),
            risk_per_trade=data.get("risk_per_trade", 0.02),
            max_position_pct=data.get("max_position_pct", 0.15),
            max_open_positions=data.get("max_open_positions", 8),
            stop_loss_pct=data.get("stop_loss_pct", -0.08),
            take_profit_pct=data.get("take_profit_pct", 0.15),
            max_hold_days=data.get("max_hold_days", 30),
            cooldown_days=data.get("cooldown_days", 3),
            max_sector_positions=data.get("max_sector_positions", 2),
        )

        for t_data in data.get("trades", []):
            trade = Trade(
                ticker=t_data["ticker"],
                entry_price=t_data["entry_price"],
                entry_score=t_data["entry_score"],
                entry_date=datetime.fromisoformat(t_data["entry_date"]),
                quantity=t_data["quantity"],
                sector=t_data.get("sector", SECTOR_MAP.get(t_data["ticker"], "otros")),
            )
            if t_data.get("exit_date"):
                trade.exit_price = t_data["exit_price"]
                trade.exit_date = datetime.fromisoformat(t_data["exit_date"])
                trade.exit_reason = t_data["exit_reason"]
                trade.status = OperationStatus(t_data["status"])
                trade.pnl_usd = t_data["pnl_usd"]
                trade.pnl_pct = t_data["pnl_pct"]
            portfolio.trades.append(trade)

        # Recalcular capital
        portfolio.current_capital = portfolio.initial_capital
        for trade in portfolio.trades:
            if trade.is_open:
                portfolio.current_capital -= trade.quantity * trade.entry_price
            else:
                portfolio.current_capital += trade.exit_price * trade.quantity

        return portfolio

    except Exception as e:
        print(f"  Error cargando portfolio: {e}")
        return Portfolio()


def save_portfolio(portfolio: Portfolio):
    """Guarda el portfolio en JSON."""
    data = {
        "initial_capital":      portfolio.initial_capital,
        "risk_per_trade":       portfolio.risk_per_trade,
        "max_position_pct":     portfolio.max_position_pct,
        "max_open_positions":   portfolio.max_open_positions,
        "stop_loss_pct":        portfolio.stop_loss_pct,
        "take_profit_pct":      portfolio.take_profit_pct,
        "max_hold_days":        portfolio.max_hold_days,
        "cooldown_days":        portfolio.cooldown_days,
        "max_sector_positions": portfolio.max_sector_positions,
        "trades": [t.to_dict() for t in portfolio.trades],
    }
    PORTFOLIO_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(data, f, indent=2)


def run_paper_trading(tickers_dict: dict | None = None, verbose: bool = True):
    """
    Analiza la watchlist y simula operaciones.
    1. Carga régimen macro real
    2. Carga portfolio actual
    3. Revisa posiciones abiertas (cierra si cumplen condiciones)
    4. Busca oportunidades (score > 70) → abre posiciones respetando todos los límites
    5. Guarda portfolio
    """
    if tickers_dict is None:
        tickers_dict = WATCHLIST

    regime = _load_regime()
    regime_str = regime.regime if regime else "NEUTRAL (sin DB)"

    portfolio = load_portfolio()

    if verbose:
        print(f"\n{'='*60}")
        print(f"  Paper Trading Simulator  —  {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print(f"  Régimen macro: {regime_str}")
        print(f"  Capital: ${portfolio.initial_capital:,.0f} | P&L: ${portfolio.total_pnl:,.2f} ({portfolio.total_pnl_pct:.2f}%)")
        print(f"  Posiciones abiertas: {len(portfolio.open_positions)}/{portfolio.max_open_positions} | Cerrados: {len(portfolio.closed_trades)}")
        print(f"{'='*60}\n")

    current_prices = {}
    current_scores = {}
    opportunities = []

    for ticker, company in tickers_dict.items():
        if verbose:
            print(f"  [{ticker:8s}] {company[:25]:25s}", end="  ", flush=True)

        tech = get_technical_features(ticker)
        if tech is None:
            if verbose:
                print("sin datos")
            continue

        fund = score_ticker(ticker, company)
        unified = compute_unified_score(ticker, regime, fund, tech)

        current_prices[ticker] = tech.get("price")
        current_scores[ticker] = unified.total

        if verbose:
            marker = "✓" if unified.total >= ENTRY_THRESHOLD else " "
            print(f"score={unified.total:5.1f}/100  M={unified.macro_pts:.0f} F={unified.fund_pts:.0f} T={unified.tech_pts:.0f} {marker}")

        if unified.total >= ENTRY_THRESHOLD:
            opportunities.append((ticker, company, unified.total, tech.get("price")))

    # Cerrar posiciones que cumplen condiciones
    if verbose and portfolio.open_positions:
        print(f"\n  Revisando {len(portfolio.open_positions)} posiciones abiertas...")
        for trade in portfolio.open_positions:
            curr_p = current_prices.get(trade.ticker)
            if curr_p:
                pnl = ((curr_p / trade.entry_price) - 1) * 100
                print(f"    {trade.ticker}: ${trade.entry_price:.2f} → ${curr_p:.2f} ({pnl:+.2f}%)")

    portfolio.check_and_close_positions(current_prices, current_scores)

    closed_this_run = [
        t for t in portfolio.closed_trades
        if t.exit_date and (datetime.now() - t.exit_date).total_seconds() < 7200
    ]
    if closed_this_run and verbose:
        print(f"\n  Posiciones cerradas:")
        for t in closed_this_run:
            icon = "✓" if t.pnl_usd > 0 else "✗"
            print(f"    {icon} {t.ticker:8s} | ${t.entry_price:.2f}→${t.exit_price:.2f} | "
                  f"P&L: ${t.pnl_usd:+.2f} ({t.pnl_pct:+.2f}%) | {t.exit_reason}")

    # Abrir nuevas posiciones
    if opportunities and verbose:
        print(f"\n  Oportunidades ({len(opportunities)}):")

    for ticker, company, score, price in opportunities:
        sector = SECTOR_MAP.get(ticker, "otros")
        ok, reason = portfolio.can_enter(ticker, sector)

        if not ok:
            if verbose:
                print(f"    ⊘ {ticker:8s} | {reason}")
            continue

        trade = portfolio.enter_position(ticker, price, score, sector)
        if trade and verbose:
            risk = trade.quantity * price * abs(portfolio.stop_loss_pct)
            pos_pct = (trade.quantity * price / portfolio.initial_capital) * 100
            print(f"    → {ticker:8s} | ${price:.2f} x {trade.quantity} ({pos_pct:.1f}% capital) | "
                  f"Score: {score:.1f} | Sector: {sector} | Risk: ${risk:.2f}")

    if verbose:
        print(f"\n  Resumen:")
        for k, v in portfolio.get_portfolio_summary().items():
            if "pct" in k or "ratio" in k:
                print(f"    {k:25s}: {v:.2f}")
            elif any(w in k for w in ["capital", "pnl", "drawdown"]):
                print(f"    {k:25s}: ${v:,.2f}")
            else:
                print(f"    {k:25s}: {v}")

    save_portfolio(portfolio)
    if verbose:
        print(f"\n  Portfolio guardado.")

    return portfolio


def main():
    parser = argparse.ArgumentParser(description="Paper Trading Simulator")
    parser.add_argument("--reset", action="store_true", help="Borra histórico y reinicia")
    parser.add_argument("--report", action="store_true", help="Muestra resumen sin simular")
    args = parser.parse_args()

    if args.reset:
        if PORTFOLIO_FILE.exists():
            PORTFOLIO_FILE.unlink()
            print("✓ Portfolio resetado")
        return

    if args.report:
        portfolio = load_portfolio()
        print(f"\n{'='*60}\n  PAPER TRADING REPORT\n{'='*60}\n")
        for k, v in portfolio.get_portfolio_summary().items():
            if "pct" in k or "ratio" in k:
                print(f"  {k:25s}: {v:.2f}")
            elif any(w in k for w in ["capital", "pnl", "drawdown"]):
                print(f"  {k:25s}: ${v:,.2f}")
            else:
                print(f"  {k:25s}: {v}")

        if portfolio.closed_trades:
            print(f"\n  Últimos 5 trades:")
            for t in portfolio.closed_trades[-5:]:
                icon = "✓" if t.pnl_usd > 0 else "✗"
                print(f"    {icon} {t.ticker:8s} | {t.entry_date.strftime('%d/%m')}→"
                      f"{t.exit_date.strftime('%d/%m') if t.exit_date else '?'} | "
                      f"P&L: ${t.pnl_usd:+.2f} ({t.pnl_pct:+.2f}%)")
        return

    run_paper_trading()


if __name__ == "__main__":
    main()
