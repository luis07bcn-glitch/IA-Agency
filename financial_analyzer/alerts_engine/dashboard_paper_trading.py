"""
Dashboard Streamlit para Paper Trading Simulator.
Ejecutar: streamlit run financial_analyzer/alerts_engine/dashboard_paper_trading.py --server.port 8505
"""
import sys
import json
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from financial_analyzer.alerts_engine.paper_runner import (
    load_portfolio, save_portfolio, PORTFOLIO_FILE,
    ENTRY_THRESHOLD, EXIT_SCORE_THRESHOLD, SECTOR_MAP, _load_regime,
)
from financial_analyzer.alerts_engine.paper_trading import OperationStatus
from financial_analyzer.alerts.notifier import send_telegram


def run_analysis(progress_callback=None) -> tuple[list[dict], object]:
    """
    Escanea toda la watchlist con régimen macro real.
    Retorna (resultados_ordenados, regime_score).
    """
    from financial_analyzer.fundamentals.scorer import score_ticker, WATCHLIST
    from financial_analyzer.alerts_engine.polygon_fetcher import get_technical_features
    from financial_analyzer.alerts_engine.scorer import compute_unified_score

    regime = _load_regime()

    results = []
    items = list(WATCHLIST.items())
    total = len(items)

    for i, (ticker, company) in enumerate(items):
        if progress_callback:
            progress_callback(i, total, ticker)
        try:
            tech = get_technical_features(ticker)
            if tech is None:
                continue
            fund = score_ticker(ticker, company)
            unified = compute_unified_score(ticker, regime, fund, tech)
            results.append({
                "ticker":    ticker,
                "company":   company,
                "sector":    SECTOR_MAP.get(ticker, "otros"),
                "score":     unified.total,
                "price":     tech.get("price"),
                "macro_pts": unified.macro_pts,
                "fund_pts":  unified.fund_pts,
                "tech_pts":  unified.tech_pts,
                "rsi":       tech.get("rsi"),
                "vs200":     tech.get("vs_sma200_pct"),
                "regime":    unified.regime,
            })
        except Exception:
            continue

    results.sort(key=lambda x: x["score"], reverse=True)
    return results, regime


def enter_position_manually(ticker: str, price: float, score: float, sector: str = "otros"):
    """Abre una posición desde el dashboard respetando todos los límites."""
    portfolio = load_portfolio()

    ok, reason = portfolio.can_enter(ticker, sector)
    if not ok:
        return False, reason

    trade = portfolio.enter_position(ticker, price, score, sector)
    if trade is None:
        return False, "Capital insuficiente o cantidad calculada = 0"

    save_portfolio(portfolio)

    pos_pct = (trade.quantity * price / portfolio.initial_capital) * 100
    risk = trade.quantity * price * abs(portfolio.stop_loss_pct)
    msg = (
        f"🟢 <b>NUEVA POSICIÓN — {ticker}</b>\n\n"
        f"Entrada: <b>${price:.2f}</b> x {trade.quantity} acciones ({pos_pct:.1f}% capital)\n"
        f"Sector: {sector} | Score: <b>{score:.1f}/100</b>\n"
        f"Stop: ${price * (1 + portfolio.stop_loss_pct):.2f}  "
        f"Target: ${price * (1 + portfolio.take_profit_pct):.2f}\n"
        f"Riesgo: ${risk:.2f}\n"
        f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )
    send_telegram(msg)

    return True, trade


def close_position_manually(ticker: str, current_price: float):
    """Cierra manualmente una posición abierta al precio actual."""
    portfolio = load_portfolio()
    trade = next((t for t in portfolio.open_positions if t.ticker == ticker), None)
    if not trade:
        return False, "Posición no encontrada"

    trade.exit_price = current_price
    trade.exit_date = datetime.now()
    trade.exit_reason = "manual"
    trade.pnl_usd = (current_price - trade.entry_price) * trade.quantity
    trade.pnl_pct = ((current_price / trade.entry_price) - 1) * 100
    trade.status = OperationStatus.CLOSED_PROFIT if trade.pnl_usd >= 0 else OperationStatus.CLOSED_LOSS

    save_portfolio(portfolio)

    icon = "✅" if trade.pnl_usd >= 0 else "🔴"
    msg = (
        f"{icon} <b>CIERRE MANUAL — {ticker}</b>\n\n"
        f"Entrada: <b>${trade.entry_price:.2f}</b> → Salida: <b>${current_price:.2f}</b>\n"
        f"Cantidad: {trade.quantity} acciones\n"
        f"P&L: <b>${trade.pnl_usd:+.2f} ({trade.pnl_pct:+.2f}%)</b>\n"
        f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )
    send_telegram(msg)

    return True, trade.pnl_usd

st.set_page_config(
    page_title="Paper Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📈 Paper Trading Simulator")
st.markdown("---")

# Cargar portfolio
portfolio = load_portfolio()

# ─── SIDEBAR ──────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuración")

    # Equity real: necesitamos precios actuales de posiciones abiertas
    _sidebar_prices = {}
    if portfolio.open_positions:
        try:
            import yfinance as yf
            for t in portfolio.open_positions:
                info = yf.Ticker(t.ticker).info or {}
                p = info.get("currentPrice") or info.get("regularMarketPrice")
                if p:
                    _sidebar_prices[t.ticker] = float(p)
        except Exception:
            pass

    _equity = portfolio.equity(_sidebar_prices or None)
    _unrealized = portfolio.unrealized_pnl(_sidebar_prices) if _sidebar_prices else 0.0
    _total_pnl = portfolio.total_pnl_combined(_sidebar_prices) if _sidebar_prices else portfolio.total_pnl

    st.metric("Capital Inicial", f"${portfolio.initial_capital:,.0f}")
    st.metric("Equity Total", f"${_equity:,.0f}",
              f"{((_equity / portfolio.initial_capital) - 1) * 100:+.2f}% vs inicial")
    st.metric("P&L Realizado", f"${portfolio.total_pnl:+,.2f}")
    if _sidebar_prices:
        st.metric("P&L Latente", f"${_unrealized:+,.2f}", "posiciones abiertas")
        st.metric("P&L Total", f"${_total_pnl:+,.2f}", "realizado + latente")
    else:
        st.metric("P&L Realizado Total", f"${portfolio.total_pnl:+,.2f}",
                  f"{portfolio.total_pnl_pct:+.2f}%")

    st.divider()
    st.subheader("Parámetros")
    st.text(f"Risk per Trade:  {portfolio.risk_per_trade*100:.0f}%")
    st.text(f"Max por posición:{portfolio.max_position_pct*100:.0f}%")
    st.text(f"Stop Loss:       {portfolio.stop_loss_pct*100:.0f}%")
    st.text(f"Take Profit:     {portfolio.take_profit_pct*100:.0f}%")
    st.text(f"Max posiciones:  {portfolio.max_open_positions}")
    st.text(f"Max por sector:  {portfolio.max_sector_positions}")
    st.text(f"Cooldown stop:   {portfolio.cooldown_days}d")
    st.text(f"Max Hold:        {portfolio.max_hold_days}d")

# ─── MAIN TABS ────────────────────────────────────────────
tab_analisis, tab1, tab2, tab3, tab4 = st.tabs(
    ["🔍 Análisis", "📊 Resumen", "📂 Posiciones Abiertas", "✅ Trades Cerrados", "📈 Estadísticas"]
)

# ══════════════════════════════════════════════════════════
# TAB: ANÁLISIS  —  escanea la watchlist y permite entrar
# ══════════════════════════════════════════════════════════
with tab_analisis:
    st.subheader("Análisis de la Watchlist")
    st.caption(
        f"Escanea todos los tickers (macro + fundamental + técnico con Claude). "
        f"Umbral de entrada: **score ≥ {ENTRY_THRESHOLD}**. "
        f"El sistema sugiere oportunidades; tú decides si entras."
    )

    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        run_clicked = st.button("🔍 Ejecutar Análisis", type="primary", use_container_width=True)
    with col_info:
        last = st.session_state.get("analysis_timestamp")
        if last:
            st.caption(f"Último análisis: **{last}**")
        else:
            st.caption("Aún no se ha ejecutado ningún análisis en esta sesión.")

    if run_clicked:
        progress_bar = st.progress(0, text="Cargando régimen macro...")

        def _update(i, total, ticker):
            progress_bar.progress(
                min((i + 1) / total, 1.0),
                text=f"Analizando {ticker}  ({i + 1}/{total})",
            )

        results, regime = run_analysis(progress_callback=_update)
        progress_bar.empty()

        st.session_state["analysis_results"] = results
        st.session_state["analysis_regime"] = regime
        st.session_state["analysis_timestamp"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        st.success(f"✓ Análisis completado — {len(results)} tickers con datos válidos")

    results = st.session_state.get("analysis_results")
    regime = st.session_state.get("analysis_regime")

    if results:
        open_tickers = {t.ticker for t in portfolio.open_positions}
        opportunities = [r for r in results if r["score"] >= ENTRY_THRESHOLD]

        st.divider()

        # ─── Régimen macro ───
        if regime:
            REGIME_COLOR = {"RISK-ON": "🟢", "NEUTRAL": "🟡", "RISK-OFF": "🔴"}
            icon = REGIME_COLOR.get(regime.regime, "⚪")
            rc1, rc2, rc3, rc4 = st.columns(4)
            with rc1:
                st.metric("Régimen Macro", f"{icon} {regime.regime}", f"Score: {regime.total:.0f}/100")
            with rc2:
                st.metric("Liquidez", f"{regime.liquidity:.0f}/28")
            with rc3:
                st.metric("Apetito Riesgo", f"{regime.risk_appetite:.0f}/25")
            with rc4:
                st.metric("Momentum", f"{regime.momentum:.0f}/15")
            if regime.warnings:
                for w in regime.warnings:
                    st.warning(f"⚠️ {w}")
            st.caption(f"_{regime.action}_")
        else:
            st.warning("⚠️ Régimen macro no disponible (DB no encontrada) — usando NEUTRAL por defecto")

        st.divider()

        # ─── Oportunidades destacadas ───
        st.markdown(f"### 🎯 Oportunidades de entrada ({len(opportunities)})")
        if not opportunities:
            st.info(f"Ningún ticker supera el umbral de {ENTRY_THRESHOLD}/100 ahora mismo.")
        else:
            for r in opportunities:
                with st.container(border=True):
                    c1, c2, c3, c4, c5 = st.columns([2, 1.2, 1.2, 1.4, 1.2])
                    with c1:
                        st.metric(r["ticker"], f"{r['score']:.1f}/100", r["company"][:22])
                    with c2:
                        price = r["price"]
                        st.metric("Precio", f"${price:.2f}" if price else "—")
                    with c3:
                        st.metric("RSI", f"{r['rsi']:.0f}" if r["rsi"] is not None else "—")
                    with c4:
                        st.caption("Desglose")
                        st.text(f"Mac {r['macro_pts']:.0f} · Fun {r['fund_pts']:.0f} · Téc {r['tech_pts']:.0f}")
                    with c5:
                        st.write("")
                        if r["ticker"] in open_tickers:
                            st.success("✓ En cartera")
                        elif not r["price"]:
                            st.caption("sin precio")
                        else:
                            can_ok, can_reason = portfolio.can_enter(r["ticker"], r["sector"])
                            if not can_ok:
                                st.caption(f"⊘ {can_reason[:30]}")
                            elif st.button("➕ Entrar", key=f"enter_{r['ticker']}", use_container_width=True):
                                ok, res = enter_position_manually(r["ticker"], r["price"], r["score"], r["sector"])
                                if ok:
                                    st.success(f"Entrada en {r['ticker']} · {res.quantity} x ${r['price']:.2f}")
                                    st.rerun()
                                else:
                                    st.warning(res)

        st.divider()

        # ─── Tabla completa ───
        st.markdown("### 📋 Watchlist completa (ordenada por score)")
        table = []
        for r in results:
            if r["score"] >= ENTRY_THRESHOLD:
                estado = "🎯 Oportunidad"
            elif r["score"] < EXIT_SCORE_THRESHOLD:
                estado = "🔴 Débil"
            else:
                estado = "⚪ Neutral"
            if r["ticker"] in open_tickers:
                estado = "📂 En cartera"
            table.append({
                "Ticker":  r["ticker"],
                "Empresa": r["company"],
                "Sector":  r["sector"],
                "Score":   round(r["score"], 1),
                "Precio":  f"${r['price']:.2f}" if r["price"] else "—",
                "RSI":     f"{r['rsi']:.0f}" if r["rsi"] is not None else "—",
                "vs200":   f"{r['vs200']:+.1f}%" if r.get("vs200") is not None else "—",
                "Macro":   round(r["macro_pts"], 0),
                "Fund":    round(r["fund_pts"], 0),
                "Téc":     round(r["tech_pts"], 0),
                "Estado":  estado,
            })
        st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)
    else:
        st.info("Pulsa **🔍 Ejecutar Análisis** para escanear la watchlist y ver las oportunidades.")

# ══════════════════════════════════════════════════════════
# TAB 1: RESUMEN
# ══════════════════════════════════════════════════════════
with tab1:
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Equity Total",
            f"${_equity:,.0f}",
            f"{((_equity / portfolio.initial_capital) - 1) * 100:+.2f}%",
            delta_color="normal"
        )

    with col2:
        st.metric(
            "P&L Realizado",
            f"${portfolio.total_pnl:+,.2f}",
            f"{portfolio.total_pnl_pct:+.2f}%",
            delta_color="normal"
        )

    with col3:
        st.metric(
            "Win Rate",
            f"{portfolio.win_rate:.1f}%",
            f"{len([t for t in portfolio.closed_trades if t.pnl_usd > 0])} de {len(portfolio.closed_trades)}"
        )

    with col4:
        st.metric(
            "Risk/Reward",
            f"{portfolio.risk_reward_ratio:.2f}x",
            "Ratio medio"
        )

    with col5:
        st.metric(
            "Max Drawdown",
            f"${portfolio.max_drawdown:,.2f}",
            "Caída máxima"
        )

    st.divider()

    # Resumen de posiciones
    col1, col2, col3 = st.columns(3)

    with col1:
        st.info(f"📂 **Posiciones Abiertas:** {len(portfolio.open_positions)}")

    with col2:
        st.success(f"✅ **Trades Cerrados:** {len(portfolio.closed_trades)}")

    with col3:
        wins = len([t for t in portfolio.closed_trades if t.pnl_usd > 0])
        losses = len([t for t in portfolio.closed_trades if t.pnl_usd < 0])
        st.warning(f"📊 **{wins}W / {losses}L**")

    st.divider()

    # Capital progression
    if portfolio.closed_trades:
        st.subheader("Evolución del Capital")

        cap_history = [portfolio.initial_capital]
        for trade in portfolio.closed_trades:
            cap_history.append(cap_history[-1] + trade.pnl_usd)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            y=cap_history,
            mode='lines+markers',
            name='Capital',
            line=dict(color='#00D9FF', width=2),
            fill='tozeroy',
        ))

        fig.update_layout(
            height=300,
            margin=dict(l=0, r=0, t=30, b=0),
            hovermode='x unified',
            xaxis_title="Trade #",
            yaxis_title="Capital ($)",
        )
        st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════
# TAB 2: POSICIONES ABIERTAS
# ══════════════════════════════════════════════════════════
with tab2:
    if not portfolio.open_positions:
        st.info("✓ Sin posiciones abiertas")
    else:
        st.subheader(f"Posiciones Abiertas ({len(portfolio.open_positions)})")

        # Obtener precios actuales
        import yfinance as yf

        current_prices = {}
        for trade in portfolio.open_positions:
            try:
                ticker_obj = yf.Ticker(trade.ticker)
                current_prices[trade.ticker] = ticker_obj.info.get('currentPrice') or ticker_obj.info.get('regularMarketPrice')
            except:
                current_prices[trade.ticker] = None

        for trade in portfolio.open_positions:
            with st.container(border=True):
                current_price = current_prices.get(trade.ticker)

                if current_price:
                    pnl_usd = (current_price - trade.entry_price) * trade.quantity
                    pnl_pct = ((current_price / trade.entry_price) - 1) * 100

                    stop_price = trade.entry_price * (1 + portfolio.stop_loss_pct)
                    target_price = trade.entry_price * (1 + portfolio.take_profit_pct)

                    dist_to_stop = ((current_price - stop_price) / abs(stop_price)) * 100
                    dist_to_target = ((target_price - current_price) / target_price) * 100

                    # Row 1: Ticker, Entrada, Precio Actual, P&L, Botón cierre
                    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
                    with col1:
                        st.metric("Ticker", trade.ticker, f"Score: {trade.entry_score:.1f}/100")
                    with col2:
                        st.metric("Precio Entrada", f"${trade.entry_price:.2f}", f"{trade.quantity} x")
                    with col3:
                        delta = current_price - trade.entry_price
                        delta_color_actual = "inverse" if delta < 0 else "normal"
                        st.metric("Precio Actual", f"${current_price:.2f}", f"Δ: ${delta:+.2f}", delta_color=delta_color_actual)
                    with col4:
                        dc = "normal" if pnl_pct >= 0 else "inverse"
                        st.metric("P&L", f"${pnl_usd:+.2f}", f"{pnl_pct:+.2f}%", delta_color=dc)
                    with col5:
                        st.write("")
                        st.write("")
                        close_key = f"confirm_{trade.ticker}"
                        if st.session_state.get(close_key):
                            st.error(f"¿Cerrar {trade.ticker} a ${current_price:.2f}?")
                            c1, c2 = st.columns(2)
                            with c1:
                                if st.button("✅ Sí", key=f"yes_{trade.ticker}"):
                                    ok, result = close_position_manually(trade.ticker, current_price)
                                    if ok:
                                        pnl_str = f"${result:+.2f}"
                                        st.success(f"Cerrada · P&L: {pnl_str}")
                                        st.session_state.pop(close_key, None)
                                        st.rerun()
                            with c2:
                                if st.button("❌ No", key=f"no_{trade.ticker}"):
                                    st.session_state.pop(close_key, None)
                                    st.rerun()
                        else:
                            if st.button("🔒 Cerrar", key=f"close_{trade.ticker}", type="primary"):
                                st.session_state[close_key] = True
                                st.rerun()

                    # Row 2: Stop, Target, Risk, Ratio
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Stop Loss", f"${stop_price:.2f}", f"{dist_to_stop:+.2f}% dist")
                    with col2:
                        st.metric("Target (+5%)", f"${target_price:.2f}", f"{dist_to_target:.2f}% restante")
                    with col3:
                        risk_usd = trade.quantity * trade.entry_price * abs(portfolio.stop_loss_pct)
                        st.metric("Risk", f"${risk_usd:.2f}", f"{trade.quantity} x")
                    with col4:
                        ratio = ((target_price - trade.entry_price) / abs(stop_price - trade.entry_price))
                        st.metric("S/T Ratio", f"{ratio:.2f}x", "Riesgo/Ganancia")
                else:
                    st.warning(f"⚠️ {trade.ticker}: No se pudo obtener precio actual")

# ══════════════════════════════════════════════════════════
# TAB 3: TRADES CERRADOS
# ══════════════════════════════════════════════════════════
with tab3:
    if not portfolio.closed_trades:
        st.info("✓ Sin trades cerrados aún")
    else:
        st.subheader(f"Histórico de Trades ({len(portfolio.closed_trades)})")

        # Tabla de trades
        trades_data = []
        for t in portfolio.closed_trades:
            trades_data.append({
                "Ticker": t.ticker,
                "Entrada": f"${t.entry_price:.2f}",
                "Salida": f"${t.exit_price:.2f}",
                "Qty": t.quantity,
                "P&L $": f"${t.pnl_usd:+.2f}",
                "P&L %": f"{t.pnl_pct:+.2f}%",
                "Razón": t.exit_reason,
                "Hold": f"{t.days_held}d",
            })

        df = pd.DataFrame(trades_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.divider()

        # Gráfico P&L por trade
        pnl_values = [t.pnl_usd for t in portfolio.closed_trades]
        tickers = [t.ticker for t in portfolio.closed_trades]

        fig = go.Figure()
        colors = ['#00D9FF' if x > 0 else '#FF6B6B' for x in pnl_values]

        fig.add_trace(go.Bar(
            y=tickers,
            x=pnl_values,
            orientation='h',
            marker=dict(color=colors),
            text=[f"${x:.2f}" for x in pnl_values],
            textposition='auto',
        ))

        fig.update_layout(
            height=max(300, len(portfolio.closed_trades) * 25),
            margin=dict(l=100, r=0, t=30, b=0),
            xaxis_title="P&L ($)",
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════
# TAB 4: ESTADÍSTICAS
# ══════════════════════════════════════════════════════════
with tab4:
    st.subheader("Estadísticas de Desempeño")

    summary = portfolio.get_portfolio_summary()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Capital Inicial", f"${summary['initial_capital']:,.2f}")
        st.metric("Capital Actual", f"${summary['current_capital']:,.2f}")
        st.metric("P&L Total", f"${summary['total_pnl']:+,.2f}")

    with col2:
        st.metric("P&L %", f"{summary['total_pnl_pct']:+.2f}%")
        st.metric("Win Rate", f"{summary['win_rate_pct']:.1f}%")
        st.metric("Risk/Reward", f"{summary['risk_reward_ratio']:.2f}x")

    with col3:
        st.metric("Posiciones Abiertas", summary['num_open_positions'])
        st.metric("Trades Cerrados", summary['num_closed_trades'])
        st.metric("Max Drawdown", f"${summary['max_drawdown']:,.2f}")

    st.divider()

    if portfolio.closed_trades:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Promedio Ganancia", f"${summary['avg_win']:+,.2f}")

        with col2:
            st.metric("Promedio Pérdida", f"${summary['avg_loss']:+,.2f}")

        with col3:
            ratio = portfolio.risk_reward_ratio
            st.metric(
                "Ratio Ganancia/Pérdida",
                f"{ratio:.2f}x",
                "Idealmente > 2.0"
            )

        st.divider()
        st.info(
            f"📊 **Análisis:** "
            f"De {summary['num_closed_trades']} trades cerrados, "
            f"{len([t for t in portfolio.closed_trades if t.pnl_usd > 0])} fueron ganadores ({summary['win_rate_pct']:.1f}%). "
            f"Ratio riesgo/recompensa: {ratio:.2f}x (bueno si > 2.0)"
        )

# Footer
st.divider()
st.caption(
    f"Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | "
    f"Portfolio guardado en: `paper_portfolio.json`"
)
