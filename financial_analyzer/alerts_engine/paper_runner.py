"""
Paper Trading Runner — simula operaciones basadas en scoring.

Uso:
  venv\\Scripts\\python.exe financial_analyzer/alerts_engine/paper_runner.py
  venv\\Scripts\\python.exe financial_analyzer/alerts_engine/paper_runner.py --reset  (borra histórico)
  venv\\Scripts\\python.exe financial_analyzer/alerts_engine/paper_runner.py --report  (muestra resumen)
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
from financial_analyzer.alerts_engine.paper_trading import Portfolio, OperationStatus

# Configuración
PORTFOLIO_FILE = ROOT / "financial_analyzer" / "data" / "paper_portfolio.json"
ENTRY_THRESHOLD = 70
EXIT_SCORE_THRESHOLD = 50


def load_portfolio() -> Portfolio:
    """Carga el portfolio desde archivo, o crea uno nuevo."""
    if PORTFOLIO_FILE.exists():
        try:
            with open(PORTFOLIO_FILE) as f:
                data = json.load(f)

            portfolio = Portfolio(
                initial_capital=data.get("initial_capital", 10000),
                risk_per_trade=data.get("risk_per_trade", 0.02),
                stop_loss_pct=data.get("stop_loss_pct", -0.03),
                take_profit_pct=data.get("take_profit_pct", 0.05),
                max_hold_days=data.get("max_hold_days", 30),
            )

            # Restaurar trades
            for t_data in data.get("trades", []):
                from financial_analyzer.alerts_engine.paper_trading import Trade

                trade = Trade(
                    ticker=t_data["ticker"],
                    entry_price=t_data["entry_price"],
                    entry_score=t_data["entry_score"],
                    entry_date=datetime.fromisoformat(t_data["entry_date"]),
                    quantity=t_data["quantity"],
                )
                if t_data["exit_date"]:
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
                elif trade.status != OperationStatus.OPEN:
                    portfolio.current_capital += trade.exit_price * trade.quantity

            return portfolio

        except Exception as e:
            print(f"  Error cargando portfolio: {e}")
            return Portfolio()
    else:
        return Portfolio()


def save_portfolio(portfolio: Portfolio):
    """Guarda el portfolio en JSON."""
    data = {
        "initial_capital": portfolio.initial_capital,
        "risk_per_trade": portfolio.risk_per_trade,
        "stop_loss_pct": portfolio.stop_loss_pct,
        "take_profit_pct": portfolio.take_profit_pct,
        "max_hold_days": portfolio.max_hold_days,
        "trades": [t.to_dict() for t in portfolio.trades],
    }

    PORTFOLIO_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(data, f, indent=2)


def run_paper_trading(tickers_dict: dict | None = None, verbose: bool = True):
    """
    Analiza la watchlist y simula operaciones.
    1. Carga portfolio actual
    2. Revisa posiciones abiertas (cierra si se cumplen condiciones)
    3. Busca nuevas oportunidades (score > 70) → abre posiciones
    4. Guarda portfolio
    """
    if tickers_dict is None:
        tickers_dict = WATCHLIST

    portfolio = load_portfolio()

    if verbose:
        print(f"\n{'='*60}")
        print(f"  Paper Trading Simulator  —  {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print(f"  Capital: ${portfolio.initial_capital:,.0f} | P&L: ${portfolio.total_pnl:,.2f} ({portfolio.total_pnl_pct:.2f}%)")
        print(f"  Posiciones abiertas: {len(portfolio.open_positions)} | Trades cerrados: {len(portfolio.closed_trades)}")
        print(f"{'='*60}\n")

    # Paso 1: Analizar todos los tickers para obtener precios y scores
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
        regime = None  # En una versión completa, cargaríamos el régimen
        unified = compute_unified_score(ticker, regime, fund, tech)

        current_prices[ticker] = tech.get("price")
        current_scores[ticker] = unified.total

        if verbose:
            status = "✓" if unified.total >= ENTRY_THRESHOLD else " "
            print(f"score={unified.total:5.1f}/100 {status}")

        if unified.total >= ENTRY_THRESHOLD:
            opportunities.append((ticker, company, unified.total, tech.get("price")))

    # Paso 2: Cerrar posiciones que cumplen condiciones
    if verbose and portfolio.open_positions:
        print(f"\n  Revisando {len(portfolio.open_positions)} posiciones abiertas...")

    portfolio.check_and_close_positions(current_prices, current_scores)

    closed_this_run = [t for t in portfolio.closed_trades if
                       t.exit_date and
                       t.exit_date.timestamp() > (datetime.now().timestamp() - 3600)]  # últimas 2h

    if closed_this_run and verbose:
        print(f"\n  Posiciones cerradas:")
        for t in closed_this_run:
            icon = "✓" if t.pnl_usd > 0 else "✗"
            print(f"    {icon} {t.ticker:8s} | Entrada: ${t.entry_price:.2f} → Salida: ${t.exit_price:.2f} | "
                  f"P&L: ${t.pnl_usd:+.2f} ({t.pnl_pct:+.2f}%) | {t.exit_reason}")

    # Paso 3: Abrir nuevas posiciones
    if opportunities and verbose:
        print(f"\n  Oportunidades de entrada ({len(opportunities)}):")

    entered = 0
    for ticker, company, score, price in opportunities:
        # No entrar si ya hay posición abierta en este ticker
        if any(t.ticker == ticker for t in portfolio.open_positions):
            if verbose:
                print(f"    ⊘ {ticker:8s} | Ya hay posición abierta")
            continue

        trade = portfolio.enter_position(ticker, price, score)
        if trade:
            entered += 1
            if verbose:
                qty = trade.quantity
                risk = qty * price * abs(portfolio.stop_loss_pct)
                print(f"    → {ticker:8s} | Entrada: ${price:.2f} x {qty} | Score: {score:.1f}/100 | Risk: ${risk:.2f}")

    if verbose:
        print(f"\n  Resumen del simulador:")
        summary = portfolio.get_portfolio_summary()
        for key, val in summary.items():
            if "pct" in key or "ratio" in key:
                print(f"    {key:25s}: {val:.2f}")
            elif "capital" in key or "pnl" in key or "drawdown" in key:
                print(f"    {key:25s}: ${val:,.2f}")
            else:
                print(f"    {key:25s}: {val}")

    # Guardar portfolio
    save_portfolio(portfolio)

    if verbose:
        print(f"\n  Portfolio guardado en: {PORTFOLIO_FILE}")

    return portfolio


def main():
    parser = argparse.ArgumentParser(description="Paper Trading Simulator")
    parser.add_argument("--reset", action="store_true",
                        help="Borra el histórico de trades y reinicia con capital inicial")
    parser.add_argument("--report", action="store_true",
                        help="Muestra el resumen del portfolio sin simular nuevas operaciones")
    args = parser.parse_args()

    if args.reset:
        if PORTFOLIO_FILE.exists():
            PORTFOLIO_FILE.unlink()
            print("✓ Portfolio resetado")
        return

    if args.report:
        portfolio = load_portfolio()
        print(f"\n{'='*60}")
        print(f"  PAPER TRADING REPORT")
        print(f"{'='*60}\n")
        summary = portfolio.get_portfolio_summary()
        for key, val in summary.items():
            if "pct" in key or "ratio" in key:
                print(f"  {key:25s}: {val:.2f}")
            elif "capital" in key or "pnl" in key or "drawdown" in key:
                print(f"  {key:25s}: ${val:,.2f}")
            else:
                print(f"  {key:25s}: {val}")

        if portfolio.closed_trades:
            print(f"\n  Últimos 5 trades cerrados:")
            for t in portfolio.closed_trades[-5:]:
                icon = "✓" if t.pnl_usd > 0 else "✗"
                print(f"    {icon} {t.ticker:8s} | {t.entry_date.strftime('%d/%m')} → {t.exit_date.strftime('%d/%m') if t.exit_date else '?'} | "
                      f"P&L: ${t.pnl_usd:+.2f} ({t.pnl_pct:+.2f}%)")
        return

    run_paper_trading()


if __name__ == "__main__":
    main()
