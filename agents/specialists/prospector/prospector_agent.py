"""
ProspectorAgent — orquesta todo el pipeline de prospección:
  1. Buscar negocios (Google Places)
  2. Enriquecer con detalles (web, teléfono, reseñas)
  3. Analizar web (checklist)
  4. Minar reseñas (categorías de dolor)
  5. Detectar pains (IA prioriza por impacto)
  6. Generar outreach (email / WhatsApp / script)
  7. Guardar en CRM
"""
from typing import List, Callable, Optional
import anthropic

from agents.base_agent import BaseAgent
from config.settings import settings
from .models import Business, ProspectorResult
from .scraper import GooglePlacesScraper
from .web_analyzer import WebAnalyzer
from .review_miner import ReviewMiner
from .pain_detector import PainDetector
from .offer_generator import OfferGenerator
from .pricing import PricingCalculator
from .scorecard import construir_scorecard, calcular_win_probability, aplicar_benchmark
from .competitive import aplicar_competitivo
from .pagespeed import PageSpeedAnalyzer
from .crm import CRM


class ProspectorAgent(BaseAgent):
    def __init__(self, nombre_agencia: str = "MerakIA"):
        super().__init__(
            name="ProspectorIA",
            description="Encuentra negocios locales, analiza sus dolores y genera ofertas irresistibles",
        )
        self.nombre_agencia = nombre_agencia
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._review_miner = ReviewMiner(self._client)
        self._pain_detector = PainDetector(self._client)
        self._web_analyzer = WebAnalyzer()
        self._offer_gen = OfferGenerator(self._client, nombre_agencia)
        self._pricing = PricingCalculator()
        self._crm = CRM()

    # ── Entrypoint del BaseAgent ───────────────────────────────────────────────

    def run(self, task: str, **kwargs):
        """Interfaz genérica — usa los métodos específicos desde la UI."""
        return f"ProspectorAgent listo. Usa buscar_negocios() y analizar_negocio() desde la UI."

    # ── Pipeline principal ─────────────────────────────────────────────────────

    def buscar_negocios(
        self,
        tipo: str,
        ciudad: str,
        limite: int = 20,
        google_api_key: Optional[str] = None,
    ) -> List[Business]:
        """Paso 1: buscar negocios en Google Places sin enriquecer todavía."""
        key = google_api_key or settings.google_places_api_key
        if not key:
            raise ValueError("Falta GOOGLE_PLACES_API_KEY en el .env")
        scraper = GooglePlacesScraper(key)
        return scraper.buscar_negocios(tipo, ciudad, limite)

    def analizar_negocio(
        self,
        negocio: Business,
        generar_outreach: bool = True,
        google_api_key: Optional[str] = None,
        progress_cb: Optional[Callable[[str], None]] = None,
    ) -> ProspectorResult:
        """
        Análisis completo de un negocio: web + reseñas + dolor + outreach.
        progress_cb recibe mensajes de estado para mostrar en la UI.
        """
        def log(msg: str):
            if progress_cb:
                progress_cb(msg)

        result = ProspectorResult(business=negocio)
        key = google_api_key or settings.google_places_api_key

        # 1. Enriquecer con detalles de Google Places (web, teléfono, reseñas)
        if key:
            log(f"Obteniendo detalles de Google Places para {negocio.nombre}...")
            scraper = GooglePlacesScraper(key)
            negocio, resenas_raw = scraper.enriquecer_negocio(negocio)
        else:
            resenas_raw = []

        # 2. Analizar web
        if negocio.tiene_web:
            log(f"Analizando web: {negocio.web}...")
            checklist, tiempo, propietario, tech_stack = self._web_analyzer.analizar(negocio.web)
            result.web_checklist = checklist
            result.tiempo_carga = tiempo
            result.tech_stack = tech_stack or None
            if propietario and not negocio.nombre_propietario:
                negocio.nombre_propietario = propietario
        else:
            log(f"⚠️ {negocio.nombre} no tiene web — lead Tier 1")

        # 3. Minar reseñas
        log("Clasificando reseñas...")
        result.resenas = self._review_miner.procesar(resenas_raw)

        # 4. Detectar pains
        log("Detectando dolores del negocio con IA...")
        pains, score, resumen = self._pain_detector.detectar(
            negocio, result.web_checklist, result.resenas
        )
        result.pains = pains
        result.score_oportunidad = score
        result.resumen_oportunidad = resumen

        # 4b. Scorecard de madurez digital + win probability (determinista, gratis)
        log("Calculando scorecard de madurez digital...")
        sc = construir_scorecard(
            negocio, result.web_checklist, result.resenas, result.tiempo_carga
        )
        result.scorecard = sc.to_dict()
        result.win_probability = calcular_win_probability(result, sc).to_dict()

        # 5. Generar outreach
        if generar_outreach and pains:
            negativas = [r for r in result.resenas if r.rating <= 3 and r.texto]
            nombre_dest = negocio.nombre_propietario

            log("Generando email personalizado...")
            asunto, cuerpo = self._offer_gen.generar_email(
                negocio, pains, negativas, nombre_dest
            )
            result.email_asunto = asunto
            result.email_cuerpo = cuerpo

            log("Generando mensaje WhatsApp...")
            result.whatsapp_mensaje = self._offer_gen.generar_whatsapp(
                negocio, pains, negativas
            )

        # 6. Guardar en CRM
        log("Guardando en CRM...")
        self._crm.guardar(result)

        return result

    def analizar_lote(
        self,
        negocios: List[Business],
        generar_outreach: bool = False,
        google_api_key: Optional[str] = None,
        progress_cb: Optional[Callable[[int, int, str], None]] = None,
    ) -> List[ProspectorResult]:
        """
        Analiza una lista de negocios en batch.
        progress_cb(i, total, nombre) para actualizar barra de progreso.
        generar_outreach=False en el batch para no gastar tokens innecesariamente.
        """
        results = []
        for i, negocio in enumerate(negocios):
            if progress_cb:
                progress_cb(i, len(negocios), negocio.nombre)
            try:
                result = self.analizar_negocio(
                    negocio,
                    generar_outreach=generar_outreach,
                    google_api_key=google_api_key,
                )
                results.append(result)
            except Exception as e:
                # No parar el lote si un negocio falla
                result = ProspectorResult(business=negocio, resumen_oportunidad=f"Error: {e}")
                results.append(result)

        # Benchmark de nicho + recálculo de win probability
        self.finalizar_lote(results)

        # Ordenar por score descendente
        results.sort(key=lambda r: r.score_oportunidad, reverse=True)
        return results

    @staticmethod
    def finalizar_lote(results: List[ProspectorResult]) -> None:
        """
        Tras analizar un lote del mismo nicho: calcula el percentil de cada
        negocio vs el promedio y recalcula la win probability con esa posición.
        Llamar desde la UI cuando el análisis se hace negocio a negocio.
        """
        aplicar_benchmark(results)
        for r in results:
            if not r.scorecard:
                continue
            sc = construir_scorecard(
                r.business, r.web_checklist, r.resenas, r.tiempo_carga
            )
            sc.percentil_nicho = r.scorecard.get("percentil_nicho")
            sc.score_medio_nicho = r.scorecard.get("score_medio_nicho")
            sc.tamano_muestra_nicho = r.scorecard.get("tamano_muestra_nicho")
            r.win_probability = calcular_win_probability(r, sc).to_dict()
        # Análisis competitivo: cada negocio vs sus competidores del lote
        aplicar_competitivo(results)

    def generar_outreach_completo(
        self,
        result: ProspectorResult,
    ) -> ProspectorResult:
        """Genera email + WhatsApp + script de llamada para un resultado ya analizado."""
        negativas = [r for r in result.resenas if r.rating <= 3 and r.texto]
        nombre_dest = result.business.nombre_propietario

        asunto, cuerpo = self._offer_gen.generar_email(
            result.business, result.pains, negativas, nombre_dest
        )
        result.email_asunto = asunto
        result.email_cuerpo = cuerpo

        result.whatsapp_mensaje = self._offer_gen.generar_whatsapp(
            result.business, result.pains, negativas
        )

        result.script_llamada = self._offer_gen.generar_script_llamada(
            result.business, result.pains, negativas
        )

        self._crm.guardar(result)
        return result

    def analizar_pagespeed(
        self,
        result: ProspectorResult,
        estrategia: str = "mobile",
        google_api_key: Optional[str] = None,
    ) -> ProspectorResult:
        """
        Ejecuta PageSpeed Insights real (Lighthouse) sobre la web del negocio.
        Bajo demanda porque tarda ~5-15s. Guarda result.pagespeed y persiste.
        """
        b = result.business
        if not b.tiene_web or not b.web:
            return result
        key = google_api_key or settings.google_places_api_key
        ps = PageSpeedAnalyzer(api_key=key)
        psr = ps.analizar(b.web, estrategia=estrategia)
        if psr:
            result.pagespeed = psr.to_dict()
            try:
                self._crm.guardar(result)
            except Exception:
                pass
        return result

    @property
    def crm(self) -> CRM:
        return self._crm

    @property
    def offer_gen(self) -> OfferGenerator:
        return self._offer_gen

    @property
    def pricing(self) -> PricingCalculator:
        return self._pricing
