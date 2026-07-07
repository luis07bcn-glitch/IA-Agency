# Roadmap de mejora — Bot Polymarket BTC Up/Down

Origen: propuesta de Luis (2026-07-07) + anotaciones técnicas de la revisión.
Documento vivo. Regla inquebrantable: **nada pasa a producción sin autopsia
previa y un solo cambio por iteración.** Este roadmap ordena QUÉ analizar y
CUÁNDO hay muestra suficiente para decidirlo.

## Diagnóstico compartido (confirmado por los datos)

- Brier del modelo (0.2157) no supera al del mercado (0.2141) con n=84: el
  modelo Gauss + vol 2h + distancia a apertura captura solo una fracción de lo
  que mueve una ventana de 5 min.
- Lo que falta y el mercado sí ve: microestructura (imbalance, flujo), colas
  gordas y jumps, reversiones rápidas, y el ruido Chainlink vs nuestras
  fuentes (~4% de ventanas).
- Por eso el edge real vive en una banda estrecha (0.08–0.12). **La palanca
  principal de rentabilidad es mejorar p_modelo, no tocar riesgo.**

## P0 — HECHO (2026-07-07) — instrumentación; NO cambió la estrategia

Los datos que no se capturan hoy no existen mañana. Todo el bloque ML (P2)
depende de este histórico.

1. ✅ **Tabla `window_snapshots`**: una foto por tick y ventana con features
   de microestructura (imbalance top-1 y top-3, spread, tamaños del libro),
   precio reciente (ret_30s propio, ret 1/3/5 min, aceleración, vol de alta
   frecuencia, cruces de signo), sigma/mu del modelo y las probabilidades
   cruda y final. Implementado en `clob.top_of_book` (profundidad),
   `btc.market_state` (features de precio) y `Runner.evaluate` (captura).
2. ✅ **Dataset a nivel de VENTANA**: la foto se guarda SIEMPRE que la
   ventana tiene open capturado, se opere o no; el JOIN con
   `windows.outcome` etiqueta cada fila (~20-40 fotos/ventana, miles de
   muestras/semana). Entrenar sobre ventanas adelanta meses el "hay data
   suficiente para ML".
3. ✅ **Autopsia con slippage**: PnL global recalculado asumiendo ejecución
   1 céntimo peor que el ask visto, con veredicto explícito
   (sobrevive / NO sobrevive). Pendiente de P0 ampliado: latencia simulada
   en contrafactuales (posible cuando haya snapshots acumulados, que
   permiten reconstruir el libro unos segundos después de cada señal).

## P1 — Al completar la muestra de v2.3 (30-50 trades)

- **v2.4 candidata ya aprobada por Luis: conciencia de régimen/tendencia.**
  Como FILTRO DE EXCLUSIÓN (p. ej. no operar contra 3+ cierres de ventana
  consecutivos en la misma dirección), no como opinión direccional dentro de
  la probabilidad. Decidir con los contrafactuales (¿cuánto habría ahorrado
  en la racha de 8?).
- **Student-t / cuantiles empíricos en vez de Gauss**: validable OFFLINE
  contra el histórico de ventanas (comparar Brier) sin tocar el bot. Solo
  pasa a producción si gana offline.
- **Patrones horarios / de régimen de vol**: analizables ya con las ventanas
  acumuladas; si alguna franja tiene edge estructural, es un filtro barato.

## P2 — Con 300-500+ trades y miles de ventanas etiquetadas

- **Modelo ML ligero** (logistic regression primero, LightGBM después),
  entrenado walk-forward con purga estricta sobre el dataset de ventanas.
  Criterio de despliegue: Brier out-of-sample < Brier del mercado de forma
  sostenida en varias semanas distintas. Nada de desplegar por PnL de
  backtest bonito.
- **Calibración post-modelo** (isotonic / Platt) sobre las probabilidades
  crudas.
- **Parámetros adaptativos** — solo cuando exista un modelo que gane al
  mercado a veces; adaptar antes = ajustar ruido (es la Fase C ya aplazada):
  - `min_edge`/`max_edge` dependientes de régimen de volatilidad.
  - `market_prior_weight` según Brier rodante de las últimas 50-100
    operaciones (modelo gana → menos prior; pierde → más prior).
  - Filtro de calidad de señal por incertidumbre (anchura del intervalo de
    la probabilidad).
- **Ensemble** (estadístico + ML): operar solo con acuerdo o ponderar por
  confianza.
- Subida prudente de riesgo (`kelly_fraction` 0.30-0.35, `max_stake_pct`
  2.5%) SOLO tras consistencia demostrada.
- **Vigilancia de concept drift**: re-evaluar el modelo por tramos; BTC
  cambia de régimen y lo de hace 3 semanas caduca.

## P3 — Camino a real (tras criterios: ≥500 trades, PnL+ tras slippage, calibración)

- Capital muy pequeño + wallet dedicada (Polygon/USDC, `py-clob-client`,
  revisar restricciones jurisdiccionales).
- Medir slippage REAL las primeras 2 semanas (el asesino silencioso) y
  recalibrar min_edge con él.
- Feeds de pago / fuentes más rápidas solo si la latencia demostrablemente
  se come el edge.
- Límites diarios: tope de pérdida diaria sí (gestión de riesgo); tope de
  ganancia, si se quiere por tranquilidad, como trailing desde el máximo del
  día, no cifra fija (nota pendiente ya registrada).

## Vetos y cicatrices (no repetir errores ya pagados)

- **Drift 30 min con peso 0.5** (v2/v2.1): sesgo sistemático a "Up", −$154.
  Cualquier reintroducción de tendencia: como filtro de exclusión o peso
  bajo, y validada offline primero.
- **Edges > 0.12**: selección adversa demostrada (perdedores netos). El
  mercado sabe algo; no son gangas.
- **Banda 0.05-0.08**: perdedora demostrada (autopsia n=84).
- **Adaptatividad con muestra pequeña**: distinguir 55% de 50% requiere
  ~400 trades; antes de eso, los "ajustes" persiguen ruido.
