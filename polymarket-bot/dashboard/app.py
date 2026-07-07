"""Dashboard Streamlit del bot Polymarket (paper trading).

Lanzar:
    venv\\Scripts\\streamlit.exe run polymarket-bot/dashboard/app.py --server.port 8507
"""
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

DB = Path(__file__).resolve().parents[1] / "paper_trades.db"

st.set_page_config(page_title="Polymarket Bot — Paper", page_icon="🎲", layout="wide")
st.title("🎲 Polymarket BTC Up/Down — Paper Trading")

if not DB.exists():
    st.warning("Todavía no hay base de datos. Ejecuta primero `python run_bot.py`.")
    st.stop()

conn = sqlite3.connect(DB)
trades = pd.read_sql_query(
    "SELECT * FROM trades ORDER BY ts", conn,
    parse_dates={"ts": {"unit": "s"}, "resolved_ts": {"unit": "s"}},
)
bankroll = conn.execute("SELECT value FROM meta WHERE key='bankroll'").fetchone()[0]
conn.close()

resolved = trades[trades["status"] != "open"]
wins = (resolved["status"] == "won").sum()
total_resolved = len(resolved)
pnl = resolved["pnl"].sum() if total_resolved else 0.0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Bankroll", f"${bankroll:,.2f}")
c2.metric("PnL realizado", f"${pnl:+,.2f}")
c3.metric("Operaciones resueltas", f"{total_resolved}")
c4.metric("Winrate", f"{wins / total_resolved:.1%}" if total_resolved else "—")
c5.metric("Abiertas", f"{(trades['status'] == 'open').sum()}")

if total_resolved:
    st.subheader("Curva de equity (PnL acumulado)")
    curve = resolved.sort_values("resolved_ts").copy()
    curve["equity"] = curve["pnl"].cumsum()
    st.line_chart(curve.set_index("resolved_ts")["equity"])

    st.subheader("Calidad del modelo")
    col1, col2 = st.columns(2)
    with col1:
        st.caption("Edge estimado al abrir vs resultado")
        q = resolved.copy()
        q["acierto"] = (q["status"] == "won").astype(int)
        st.scatter_chart(q, x="edge", y="acierto")
    with col2:
        st.caption("Winrate por lado")
        st.dataframe(
            resolved.groupby("side")
            .agg(n=("id", "count"), winrate=("status", lambda s: (s == "won").mean()),
                 pnl=("pnl", "sum"))
            .round(3)
        )

st.subheader("Operaciones")
show = trades.sort_values("ts", ascending=False).head(200)
st.dataframe(
    show[["ts", "window_start", "side", "price", "stake", "shares",
          "model_p", "edge", "status", "pnl"]],
    width="stretch",
)
