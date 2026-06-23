"""
Dashboard Streamlit para Paper Trading Simulator.
Ejecutar: streamlit run financial_analyzer/alerts_engine/dashboard_paper_trading.py --server.port 8505
"""
import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from financial_analyzer.alerts_engine.paper_runner import load_portfolio

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
    st.metric("Capital Inicial", f"${portfolio.initial_capital:,.0f}")
    st.metric("Capital Actual", f"${portfolio.current_capital:,.0f}")
    st.metric("P&L Total", f"${portfolio.total_pnl:+,.2f}", f"{portfolio.total_pnl_pct:+.2f}%")

    st.divider()
    st.subheader("Parámetros")
    st.text(f"Risk per Trade: {portfolio.risk_per_trade*100:.1f}%")
    st.text(f"Stop Loss: {portfolio.stop_loss_pct*100:.1f}%")
    st.text(f"Take Profit: {portfolio.take_profit_pct*100:.1f}%")
    st.text(f"Max Hold: {portfolio.max_hold_days} días")

# ─── MAIN TABS ────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📊 Resumen", "📂 Posiciones Abiertas", "✅ Trades Cerrados", "📈 Estadísticas"])

# ══════════════════════════════════════════════════════════
# TAB 1: RESUMEN
# ══════════════════════════════════════════════════════════
with tab1:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total P&L",
            f"${portfolio.total_pnl:,.2f}",
            f"{portfolio.total_pnl_pct:+.2f}%",
            delta_color="normal"
        )

    with col2:
        st.metric(
            "Win Rate",
            f"{portfolio.win_rate:.1f}%",
            f"{len([t for t in portfolio.closed_trades if t.pnl_usd > 0])} de {len(portfolio.closed_trades)}"
        )

    with col3:
        st.metric(
            "Risk/Reward",
            f"{portfolio.risk_reward_ratio:.2f}x",
            "Ratio medio"
        )

    with col4:
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

        for trade in portfolio.open_positions:
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Ticker", trade.ticker, f"Score: {trade.entry_score:.1f}/100")

                with col2:
                    st.metric("Entrada", f"${trade.entry_price:.2f}", f"{trade.quantity} x")

                with col3:
                    risk_usd = trade.quantity * trade.entry_price * abs(portfolio.stop_loss_pct)
                    target_price = trade.entry_price * (1 + portfolio.take_profit_pct)
                    st.metric("Target", f"${target_price:.2f}", f"Risk: ${risk_usd:.2f}")

                with col4:
                    st.metric("Hold", f"{trade.days_held} días", f"Max: {portfolio.max_hold_days}")

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
