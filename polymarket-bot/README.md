# Polymarket BTC Up/Down Bot — Paper Trading

Bot que opera los mercados de 5 minutos "Bitcoin Up or Down" de Polymarket,
inspirado en la estrategia del bot viral (+$288k): detectar pequeños errores de
pricing en ventanas muy cortas y repetirlo a escala.

**Arranca en modo paper trading con datos 100% reales** (orderbook CLOB en vivo,
precios BTC en vivo). Ni un dólar real en riesgo hasta que los datos demuestren
que hay edge.

## Cómo funciona

1. **Descubrimiento** — Los mercados de 5 min usan slugs deterministas
   (`btc-updown-5m-<epoch>`), así que el bot localiza la ventana activa sin buscar.
2. **Open** — Al empezar cada ventana captura el precio de apertura de BTC
   (mediana de Binance, Coinbase y Kraken, como proxy del stream Chainlink que
   usa Polymarket para resolver).
3. **Modelo** — Estima P(cierre ≥ open) con la volatilidad realizada de 1 min:
   `P = Φ( ln(spot/open) / (σ₁ₘ·√min_restantes) )`.
4. **Señal** — Compara esa probabilidad con el mejor ask del orderbook de cada
   lado (Up/Down). Si `p_modelo − ask ≥ min_edge` (5 céntimos por defecto) y hay
   liquidez suficiente, compra (en paper).
5. **Sizing** — Kelly fraccionado (25%) con tope del 2% del bankroll por operación.
6. **Resolución** — Espera la liquidación oficial de Polymarket vía API Gamma;
   si tarda >15 min, resuelve con el precio proxy. Todo queda en SQLite.

## Uso

```powershell
# Diagnóstico (una pasada, sin operar): mercado, orderbook, modelo, edges
venv\Scripts\python.exe polymarket-bot\run_bot.py --diagnose

# Correr el bot (paper). Ctrl+C para parar; el estado persiste en SQLite
venv\Scripts\python.exe polymarket-bot\run_bot.py

# Correr 2 horas con edge mínimo más exigente
venv\Scripts\python.exe polymarket-bot\run_bot.py --minutes 120 --min-edge 0.07

# Dashboard (puerto 8507)
venv\Scripts\streamlit.exe run polymarket-bot\dashboard\app.py --server.port 8507

# Autopsia: calibración, sesgos y propuestas (solo propone con n>=30 y |z|>=2)
venv\Scripts\python.exe polymarket-bot\autopsy.py
venv\Scripts\python.exe polymarket-bot\autopsy.py --since <ts_unix>   # solo desde una versión
```

El bot registra en la tabla `signals` **todas** las señales evaluadas (operadas
o rechazadas y por qué). Como cada ventana acaba teniendo resultado, la autopsia
puede medir contrafactuales: qué habría pasado con otra banda de edge, si la
bandera roja ahorra o cuesta dinero, etc. Las propuestas nunca se auto-aplican:
el protocolo sigue siendo un cambio por iteración, decidido por un humano.

Además, la tabla `window_snapshots` guarda una foto por tick de CADA ventana
con open capturado (se opere o no): microestructura del orderbook (imbalance,
spread, tamaños), precio reciente (retornos a 30s/1m/3m/5m, aceleración, vol
HF, cruces) y las probabilidades del modelo. Cada ventana resuelta etiqueta
sus fotos vía `windows.outcome`: es el dataset de entrenamiento para los
modelos futuros (ver ROADMAP.md). La autopsia reporta también el PnL tras
slippage (1 céntimo por share) — el listón real para plantear dinero real.

## Parámetros clave (`bot/config.py`)

| Parámetro | Default | Qué controla |
|---|---|---|
| `min_edge` | 0.05 | Ventaja mínima modelo−ask para operar |
| `max_stake_pct` | 0.02 | Máximo % del bankroll por operación |
| `kelly_fraction` | 0.25 | Fracción de Kelly (conservador) |
| `min_book_size` | 50 | Liquidez mínima en el ask |
| `no_trade_last_sec` | 45 | No abrir al final de la ventana |

## Criterio para pasar a real (no antes)

Deja el bot en paper **mínimo 2 semanas** y exige TODO esto:

- ≥500 operaciones resueltas (significancia estadística mínima)
- PnL positivo **después** de asumir slippage (resta ~1 céntimo por trade)
- Winrate realizado coherente con el `model_p` medio (calibración del modelo)
- Edge estable por tramos temporales (no concentrado en un día raro)

Para operar en real harían falta: wallet en Polygon con USDC, clave privada,
`py-clob-client`, y revisar restricciones jurisdiccionales de Polymarket
(estos mercados aparecen como `restricted` en su API). Eso es una fase 2
deliberadamente separada.

## Advertencias honestas

- Los números del tuit (+$288k, 56% winrate) **no son verificables** en lo que
  importa: que el edge exista hoy y sea capturable por ti. En estos mercados
  compites contra bots con latencia de milisegundos; el taker que llega tarde
  compra los precios que los rápidos ya no quieren.
- 56% de winrate con precios medios de ~0.50 es rentable; con slippage de 1-2
  céntimos por lado puede no serlo. El paper trading de este bot compra al ask
  real, que ya captura parte de ese coste, pero no el impacto de mercado.
- El precio de resolución oficial es el stream Chainlink BTC/USD; nuestro proxy
  (mediana de 3 exchanges) puede diferir unos dólares. En ventanas donde BTC se
  mueve poco, esa diferencia decide el resultado — otra razón para `min_edge` alto.
