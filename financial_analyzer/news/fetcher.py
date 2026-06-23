"""
Agregador de noticias financieras vía RSS gratuito.
Fuentes: Reuters, CNBC, MarketWatch, Yahoo Finance, FT, Bloomberg (limitado).
Filtra por relevancia para mercados usando keywords categorizadas.
"""
import feedparser
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

# ── Fuentes RSS ────────────────────────────────────────────────
RSS_FEEDS = {
    "Reuters Business":   "https://feeds.reuters.com/reuters/businessNews",
    "Reuters Markets":    "https://feeds.reuters.com/reuters/companyNews",
    "CNBC Top News":      "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "CNBC Economy":       "https://www.cnbc.com/id/20910258/device/rss/rss.html",
    "MarketWatch Top":    "https://feeds.marketwatch.com/marketwatch/topstories",
    "MarketWatch Economy":"https://feeds.marketwatch.com/marketwatch/economy-politics",
    "Yahoo Finance":      "https://finance.yahoo.com/rss/topstories",
    "Investing.com":      "https://www.investing.com/rss/news_25.rss",
    "FT Markets":         "https://www.ft.com/rss/home/uk",
}

# ── Keywords por categoría ─────────────────────────────────────
CATEGORIES = {
    "Geopolitica": [
        "war", "guerra", "sanctions", "sanciones", "iran", "russia", "china", "taiwan",
        "nato", "otan", "conflict", "conflicto", "ceasefire", "alto el fuego", "attack",
        "ataque", "trump", "tariff", "arancel", "trade war", "guerra comercial",
        "north korea", "middle east", "ukraine", "israel", "hamas", "hezbollah",
        "embargo", "nuclear", "missile", "drones",
    ],
    "Banco Central / Fed": [
        "fed", "federal reserve", "fomc", "interest rate", "tipo de interes",
        "rate hike", "rate cut", "subida tipos", "bajada tipos", "powell",
        "ecb", "bce", "lagarde", "boe", "bank of england", "quantitative",
        "qe", "qt", "taper", "inflation", "inflacion", "pivot", "pause",
        "dot plot", "balance sheet",
    ],
    "Macro EEUU": [
        "gdp", "pib", "recession", "recesion", "jobs", "employment", "unemployment",
        "nonfarm", "cpi", "pce", "retail sales", "consumer", "housing", "deficit",
        "debt ceiling", "fiscal", "treasury", "yield curve", "inverted",
        "earnings", "s&p 500", "nasdaq", "dow jones",
    ],
    "Credito & Liquidez": [
        "credit", "credito", "default", "impago", "bankruptcy", "quiebra",
        "high yield", "spread", "repo", "liquidity", "liquidez", "svb",
        "bank failure", "bank run", "financial crisis", "contagion",
        "hedge fund", "margin call", "leverage", "apalancamiento",
    ],
    "Energia & Materias Primas": [
        "oil", "petroleo", "opec", "gas", "lng", "crude", "brent", "wti",
        "gold", "oro", "copper", "cobre", "wheat", "wheat", "food prices",
        "commodity", "materias primas", "energy crisis",
    ],
    "Tecnologia & IA": [
        "ai", "artificial intelligence", "inteligencia artificial", "nvidia",
        "semiconductor", "chip", "tech", "apple", "microsoft", "google",
        "amazon", "meta", "openai", "regulation", "regulacion", "antitrust",
        "big tech", "cyber", "hack",
    ],
    "Salud & Crisis": [
        "virus", "pandemic", "pandemia", "outbreak", "covid", "mpox",
        "bird flu", "epidemic", "who", "oms", "health crisis",
        "earthquake", "natural disaster",
    ],
}

# Impacto estimado por categoría para el mercado
CATEGORY_IMPACT = {
    "Geopolitica":          "⚠️ Alto",
    "Banco Central / Fed":  "🔴 Critico",
    "Macro EEUU":           "🟠 Alto",
    "Credito & Liquidez":   "🔴 Critico",
    "Energia & Materias Primas": "🟡 Medio",
    "Tecnologia & IA":      "🟡 Medio",
    "Salud & Crisis":       "⚠️ Alto",
}


def _parse_date(entry) -> datetime:
    """Intenta extraer la fecha de publicacion de una entrada RSS."""
    for attr in ("published", "updated"):
        val = getattr(entry, attr, None)
        if val:
            try:
                return parsedate_to_datetime(val).replace(tzinfo=None)
            except Exception:
                pass
    return datetime.utcnow()


def _classify(text: str) -> list[str]:
    """Devuelve las categorias relevantes para un texto."""
    text_lower = text.lower()
    found = []
    for cat, keywords in CATEGORIES.items():
        if any(kw in text_lower for kw in keywords):
            found.append(cat)
    return found


def fetch_news(max_per_feed: int = 8, timeout: int = 6) -> list[dict]:
    """
    Descarga y agrega noticias de todas las fuentes RSS.
    Devuelve lista de dicts ordenada por fecha descendente, solo las relevantes para mercados.
    """
    articles = []

    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url, request_headers={"User-Agent": "Mozilla/5.0"})
            for entry in feed.entries[:max_per_feed]:
                title   = getattr(entry, "title", "")
                summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
                link    = getattr(entry, "link", "")
                date    = _parse_date(entry)

                combined = f"{title} {summary}"
                cats = _classify(combined)
                if not cats:
                    continue  # solo noticias relevantes para mercados

                articles.append({
                    "source":     source,
                    "title":      title,
                    "summary":    summary[:280].strip(),
                    "link":       link,
                    "date":       date,
                    "categories": cats,
                    "impact":     CATEGORY_IMPACT.get(cats[0], "🟡 Medio"),
                })
        except Exception:
            continue

    # Ordenar por fecha descendente y deduplicar por titulo
    seen = set()
    unique = []
    for a in sorted(articles, key=lambda x: x["date"], reverse=True):
        key = a["title"][:60].lower()
        if key not in seen:
            seen.add(key)
            unique.append(a)

    return unique


def get_macro_calendar() -> list[dict]:
    """
    Eventos macro clave de la semana actual (hardcoded por relevancia).
    En produccion esto podria venir de un calendario economico API.
    """
    from datetime import timedelta
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())

    # Eventos fijos de alta relevancia por dia de la semana (patron tipico EEUU)
    weekly_pattern = [
        {"day": 1, "time": "14:30",  "event": "JOLTS Job Openings",          "impact": "🟠 Alto",    "source": "BLS"},
        {"day": 2, "time": "14:30",  "event": "ADP Employment",               "impact": "🟠 Alto",    "source": "ADP"},
        {"day": 3, "time": "14:30",  "event": "Initial Jobless Claims",        "impact": "🟡 Medio",   "source": "DOL"},
        {"day": 4, "time": "14:30",  "event": "Nonfarm Payrolls (primer viernes mes)", "impact": "🔴 Critico", "source": "BLS"},
        {"day": 4, "time": "15:00",  "event": "ISM Manufacturing / Services", "impact": "🟠 Alto",    "source": "ISM"},
    ]

    return [
        {**e, "date": (week_start + timedelta(days=e["day"])).strftime("%d/%m/%Y")}
        for e in weekly_pattern
    ]
