"""
Sistema de alertas multicanal.
Punto 4 incorporado: Telegram Bot como canal principal (más rápido que email, 10 líneas de código).
Canales disponibles: Telegram, Email (SMTP), consola.
"""
import os
import smtplib
import requests
from email.mime.text import MIMEText
from datetime import datetime

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
ALERT_EMAIL_TO   = os.getenv("ALERT_EMAIL_TO", "")
SMTP_HOST        = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT        = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER        = os.getenv("SMTP_USER", "")
SMTP_PASS        = os.getenv("SMTP_PASS", "")


def send_telegram(message: str) -> bool:
    """Envía mensaje via Telegram Bot. Setup: @BotFather → token + chat_id."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("  AVISO: TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID no configurados")
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        resp = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
        }, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"  ERROR Telegram: {e}")
        return False


def send_email(subject: str, body: str) -> bool:
    """Envía email via SMTP."""
    if not SMTP_USER or not ALERT_EMAIL_TO:
        return False
    try:
        msg = MIMEText(body, "html")
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = ALERT_EMAIL_TO
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, ALERT_EMAIL_TO, msg.as_string())
        return True
    except Exception as e:
        print(f"  ERROR Email: {e}")
        return False


def format_regime_alert(regime: str, score: float, prev_regime: str = None) -> str:
    icons = {"RISK-ON": "🟢", "NEUTRAL": "🟡", "RISK-OFF": "🔴"}
    icon = icons.get(regime, "⚪")
    ts = datetime.now().strftime("%d/%m/%Y %H:%M")

    msg = f"{icon} <b>CAMBIO DE RÉGIMEN</b> | {ts}\n\n"
    if prev_regime:
        prev_icon = icons.get(prev_regime, "⚪")
        msg += f"{prev_icon} <s>{prev_regime}</s> → {icon} <b>{regime}</b>\n"
    else:
        msg += f"Régimen actual: {icon} <b>{regime}</b>\n"
    msg += f"Score total: <b>{score}/100</b>"
    return msg


def format_stale_data_alert(stale_series: list[dict]) -> str:
    """Alerta de datos obsoletos — punto 3."""
    if not stale_series:
        return ""
    ts = datetime.now().strftime("%d/%m/%Y %H:%M")
    msg = f"⚠️ <b>DATOS OBSOLETOS</b> | {ts}\n\n"
    msg += "Las siguientes series tienen datos más antiguos de lo esperado:\n\n"
    for s in stale_series[:8]:
        msg += f"• <b>{s.get('series_name', '?')}</b>: último dato {s.get('last_data_date', '?')} "
        msg += f"(lag esperado: {s.get('data_lag_days', '?')} días)\n"
    msg += "\n⚡ Revisa las fuentes de datos antes de tomar decisiones."
    return msg


def format_dip_alert(ticker: str, drop_pct: float, regime: str, fund_score: float = None) -> str:
    """Alerta de dip en régimen favorable."""
    icon = "🟢" if regime == "RISK-ON" else "🟡"
    msg = f"📉 <b>DIP OPPORTUNITY</b>\n\n"
    msg += f"<b>{ticker}</b> ha caído <b>{abs(drop_pct):.1f}%</b>\n"
    msg += f"Régimen actual: {icon} <b>{regime}</b>\n"
    if fund_score is not None:
        msg += f"Fundamental Score: <b>{fund_score:.0f}/100</b>\n"
    msg += "\n⚡ Considera entrada escalonada si el régimen se mantiene."
    return msg


def notify(message: str, channels: list[str] = None):
    """
    Envía una notificación por los canales especificados.
    channels: ['telegram', 'email', 'console'] — default: todos los configurados
    """
    if channels is None:
        channels = ["telegram", "email", "console"]

    results = {}
    if "console" in channels:
        print(f"\n{'='*50}\nALERTA: {message}\n{'='*50}")
        results["console"] = True

    if "telegram" in channels:
        results["telegram"] = send_telegram(message)

    if "email" in channels:
        subject = f"[FinancialAnalyzer] Alerta {datetime.now().strftime('%d/%m %H:%M')}"
        results["email"] = send_email(subject, message.replace("\n", "<br>"))

    return results
