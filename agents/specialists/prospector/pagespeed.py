"""
Cliente de Google PageSpeed Insights (API v5, gratuita).

Da datos DUROS de rendimiento web (Lighthouse): performance score real,
Core Web Vitals (LCP, CLS, FCP, TBT) y hasta un screenshot de la web.
Esto convierte "tu web va lenta" (opinión) en "tu web tarda 4,2s y Google
penaliza por encima de 2,5s" (evidencia con la que se cierran ventas).

Estrategia 'mobile' por defecto: el 70% del tráfico local es móvil y es lo
que más penaliza Google. Funciona sin API key (con límite de cuota); si se
pasa key (puede reutilizarse la de Places si el proyecto tiene habilitada
"PageSpeed Insights API"), sube el límite.
"""
import requests
from dataclasses import dataclass, field
from typing import Optional

PSI_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


def _verdict(score: int) -> str:
    if score >= 90:
        return "bueno"
    if score >= 50:
        return "mejorable"
    return "malo"


@dataclass
class PageSpeedResult:
    estrategia: str                       # mobile / desktop
    performance_score: int                # 0-100 (Lighthouse)
    verdict: str                          # bueno / mejorable / malo
    lcp_s: Optional[float] = None         # Largest Contentful Paint (s)
    cls: Optional[float] = None           # Cumulative Layout Shift
    fcp_s: Optional[float] = None         # First Contentful Paint (s)
    tbt_ms: Optional[float] = None        # Total Blocking Time (ms)
    speed_index_s: Optional[float] = None
    screenshot: Optional[str] = None      # data URI base64 (jpeg)
    # Datos de campo reales (CrUX) si están disponibles
    field_lcp_cat: Optional[str] = None   # FAST / AVERAGE / SLOW
    field_cls_cat: Optional[str] = None

    def to_dict(self) -> dict:
        return self.__dict__.copy()


class PageSpeedAnalyzer:
    def __init__(self, api_key: Optional[str] = None, timeout: int = 60):
        self.api_key = api_key
        self.timeout = timeout

    def analizar(self, url: str, estrategia: str = "mobile") -> Optional[PageSpeedResult]:
        """
        Llama a PageSpeed Insights. Devuelve None si falla (web caída, sin
        respuesta, cuota agotada). Tarda ~5-15s por web — usar bajo demanda.
        """
        if not url:
            return None
        if not url.startswith("http"):
            url = "https://" + url

        params = {
            "url": url,
            "strategy": estrategia,
            "category": "performance",
        }
        if self.api_key:
            params["key"] = self.api_key

        try:
            resp = requests.get(PSI_URL, params=params, timeout=self.timeout)
            if resp.status_code != 200 and self.api_key:
                # La key puede estar restringida a otra API: reintentar sin key
                params.pop("key", None)
                resp = requests.get(PSI_URL, params=params, timeout=self.timeout)
            if resp.status_code != 200:
                import streamlit as st
                try:
                    err = resp.json().get("error", {})
                    st.warning(f"PageSpeed API error {resp.status_code}: {err.get('message', resp.text[:200])}")
                except Exception:
                    st.warning(f"PageSpeed error {resp.status_code}: {resp.text[:200]}")
                return None
            data = resp.json()
        except requests.exceptions.Timeout:
            import streamlit as st
            st.warning("PageSpeed: tiempo de espera agotado (la web tardó más de 60s). Inténtalo de nuevo.")
            return None
        except Exception as e:
            import streamlit as st
            st.warning(f"PageSpeed: error de conexión — {e}")
            return None

        lh = data.get("lighthouseResult", {})
        cats = lh.get("categories", {})
        audits = lh.get("audits", {})

        perf = cats.get("performance", {}).get("score")
        if perf is None:
            return None
        score = round(perf * 100)

        def _num(audit_key: str, divisor: float = 1.0) -> Optional[float]:
            a = audits.get(audit_key, {})
            v = a.get("numericValue")
            return round(v / divisor, 2) if v is not None else None

        # Screenshot final (data URI base64)
        screenshot = None
        shot = audits.get("final-screenshot", {}).get("details", {})
        if shot.get("data", "").startswith("data:image"):
            screenshot = shot["data"]

        # Datos de campo reales (CrUX)
        field_lcp = field_cls = None
        le = data.get("loadingExperience", {}).get("metrics", {})
        if le:
            field_lcp = le.get("LARGEST_CONTENTFUL_PAINT_MS", {}).get("category")
            field_cls = le.get("CUMULATIVE_LAYOUT_SHIFT_SCORE", {}).get("category")

        return PageSpeedResult(
            estrategia=estrategia,
            performance_score=score,
            verdict=_verdict(score),
            lcp_s=_num("largest-contentful-paint", 1000),
            cls=_num("cumulative-layout-shift"),
            fcp_s=_num("first-contentful-paint", 1000),
            tbt_ms=_num("total-blocking-time"),
            speed_index_s=_num("speed-index", 1000),
            screenshot=screenshot,
            field_lcp_cat=field_lcp,
            field_cls_cat=field_cls,
        )
