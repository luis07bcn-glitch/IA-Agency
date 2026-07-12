# funding-bot — Fase 0: medición del cash-and-carry en Kraken

Proyecto derivado del análisis de mercados del 2026-07-12 (tras congelar el bot
de Polymarket y descubrir el bloqueo DGOJ en España). Estrategia candidata:
**arbitraje de funding rate delta-neutral** — long spot + short perpetuo en
Kraken (única opción clara con licencia MiCA CASP + MiFID II para derivados
retail en la UE desde julio 2026).

**Regla inquebrantable heredada de polymarket-bot: nada pasa a la siguiente
fase sin datos y sin gate escrito de antemano.**

## Gate de la Fase 0 (escrito ANTES de mirar los datos, 2026-07-12)

> Retorno neto anualizado simulado > 8% con drawdown máximo < 3% sobre ≥12
> meses de histórico → pasa a paper trading con precios reales.
> Si no lo supera, se descarta sin apego.

## Uso

```powershell
# histórico completo de funding (idempotente, relanzable a diario)
venv\Scripts\python.exe funding-bot\collector.py --backfill

# backtest con costes conservadores (0.45% por lado, todo taker, tier base)
venv\Scripts\python.exe funding-bot\backtest.py

# snapshot puntual / bucle para VPS
venv\Scripts\python.exe funding-bot\collector.py --once
venv\Scripts\python.exe funding-bot\collector.py --interval 300
```

## Diseño

- `collector.py` — stdlib pura. Backfill del endpoint público
  `v4/historicalfundingrates` (1 entrada/hora, ~1 año de profundidad) +
  snapshots de `v3/tickers` (funding actual, predicción, mark) y spot, en
  `funding.db` (SQLite WAL, git-ignored).
- `backtest.py` — simula notional constante 1.0. Cada hora en posición
  acumula `relative_rate` (si es negativo, se paga). Compara **always-on**
  contra **umbral con histéresis** (media móvil 7d anualizada: entra >5%,
  sale <0%). Costes por defecto: spot taker 0.40% + futuros taker 0.05% por
  lado = 0.90% ida y vuelta.

## Aproximaciones asumidas (honestidad ante todo)

1. **Ignora el mark-to-market de la base perp-spot.** En perpetuos la base es
   pequeña y converge (el funding existe precisamente para anclarla), pero en
   picos de volatilidad puede abrir el drawdown real más que el simulado.
2. **Ignora el coste de oportunidad del margen** del short (colateral que no
   trabaja) y posibles intereses de margen.
3. **Todo taker.** Con órdenes maker los costes bajan (~0.16% spot + 0.02%
   fut), pero el backtest no debe asumir fills de maker que no puede probar
   (cicatriz aprendida en polymarket-bot).
4. Funding de Kraken PF_* es **horario** (verificado empíricamente:
   entradas cada 1h exacta). Anualización = tasa horaria × 24 × 365.
5. Convención de signo verificada: funding positivo → los longs pagan a los
   shorts → el cash-and-carry cobra.

## Fases siguientes (solo si el gate pasa)

1. **Paper** con snapshots reales del collector en el VPS (reutiliza el
   patrón systemd de polymarket-bot), midiendo spread real de entrada.
2. **Real pequeño** en Kraken con la política de barrido del 50% en máximos
   (diseñada en polymarket-bot, encaja mejor aquí: estrategia de rentas).
