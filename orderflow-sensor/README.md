# orderflow-sensor — Fase 0: ¿el order flow de Kraken predice algo cobrable?

Proyecto derivado del análisis del 2026-07-18 (artículos de unespeculador sobre
volume profile / market profile / order flow). Antes de plantearse un bot de
order flow, este sensor responde con datos la única pregunta que importa:

> ¿Las features de order flow (imbalance del libro, OFI, delta, distancia al
> VPOC) predicen el retorno de BTC/EUR a 10s–15min con magnitud suficiente
> para pagar los costes reales de Kraken?

**Regla inquebrantable heredada de polymarket-bot y funding-bot: nada pasa a
la siguiente fase sin datos y sin gate escrito de antemano.**

## Gate de la Fase 0 (escrito ANTES de mirar los datos, 2026-07-18)

Con ≥7 días de datos recogidos (y ≥5 días de cobertura efectiva), evaluando
horizontes de 10s a 15min:

1. **Gate duro (bot direccional taker):** alguna feature con |IC de Spearman|
   ≥ 0.03 (p < 0.001) **y** |spread D10−D1 de retorno forward| > coste ida y
   vuelta taker (2 × 0.40% + spread mediano). → pasa directo a diseño de paper
   trading. (Expectativa honesta: no va a pasar.)
2. **Gate blando (justifica Fase 1, simulación maker):** alguna feature con
   |IC| ≥ 0.03 (p < 0.001) **y** |spread D10−D1| ≥ 10 bps en algún horizonte.
   → justifica invertir en una simulación maker con modelado de cola
   (reutilizando lo aprendido en `polymarket-bot/maker_sim*.py`).
3. **Ninguno de los dos** → se descarta el bot de order flow sin apego y el
   sensor se apaga. Los artículos se quedan como formación discrecional.

## Uso

```powershell
# prueba local de 90 segundos
venv\Scripts\python.exe orderflow-sensor\collector.py --duration 90

# recolección indefinida (para VPS/systemd)
venv\Scripts\python.exe orderflow-sensor\collector.py

# análisis del poder predictivo + veredicto del gate
venv\Scripts\python.exe orderflow-sensor\analyze.py

# deploy al VPS (mismo patrón que funding-bot; corre 24/7 como systemd)
.\orderflow-sensor\deploy\deploy_to_vps.ps1 -ServerIp 93.93.112.48

# traer la BD del VPS para analizar en local
scp -i $env:USERPROFILE\.ssh\ionos_merakia root@93.93.112.48:/opt/merakia/orderflow-sensor/orderflow.db orderflow-sensor\orderflow.db
```

## Diseño

- `collector.py` — websocket v2 de Kraken (`book` depth 25 + `trade`,
  BTC/EUR). Mantiene el libro L2 en memoria validado con el checksum CRC32
  oficial (si el checksum fallara sistemáticamente por un cambio de formato,
  se desactiva solo y queda la comprobación de libro cruzado). Cada segundo
  escribe un snapshot de features en `orderflow.db` (SQLite WAL, git-ignored);
  los trades se guardan crudos con dedup por `trade_id`. Reconexión con
  backoff; los huecos se detectan por segundos ausentes, nunca se rellenan.
- `analyze.py` — offline. Reconstruye la serie de mid a 1s, calcula retornos
  forward a 10s/30s/1m/5m/15m y mide por feature: IC de Spearman, p-valor y
  spread D10−D1 en bps. Compara contra costes y emite el veredicto del gate.

### Features por snapshot (1s)

| Feature | Qué mide |
|---|---|
| `obi1/obi5/obi10` | Imbalance del libro a 1/5/10 niveles: (bidQty−askQty)/(bidQty+askQty) |
| `ofi` | Order Flow Imbalance (Cont–Kukanov–Stoikov) al mejor nivel, acumulado en el segundo |
| `buy_vol/sell_vol/delta` | Volumen agresor comprador/vendedor y delta del segundo (tape) |
| `cvd_day` | Delta acumulado desde medianoche UTC (reconstruido al arrancar) |
| `vpoc/dist_vpoc` | VPOC intradía (histograma volumen×precio, buckets de 10 EUR) y distancia del mid |
| `spread`, `bid_qty*`, `ask_qty*` | Contexto de liquidez |

## Aproximaciones asumidas (honestidad ante todo)

1. **El lado del trade es el del agresor según Kraken** (`side` = lado taker).
   Es la clasificación correcta para delta/CVD, sin heurística de tick rule.
2. **OFI solo al mejor nivel** y a resolución de mensaje, no de evento
   individual. Es la variante estándar de la literatura; suficiente para
   decidir si hay señal.
3. **El gate blando es OPTIMISTA a propósito**: 10 bps de spread de deciles no
   garantizan estrategia maker rentable (selección adversa y posición en cola
   sin medir — eso es exactamente la Fase 1). Si ni así pasa, el descarte es
   firme y barato.
4. **Fees tier base de Kraken Pro** (maker 0.25%, taker 0.40%), configurables
   en `analyze.py`. Con volumen bajan (0.16%/0.26%), pero el gate no debe
   asumir un tier que no tenemos (cicatriz de polymarket-bot).
5. La BD crece ~15-20 MB/día. Dos semanas de sensor ≈ 300 MB: sin problema en
   el VPS, y OneDrive no la cubre (mismo criterio que la BD del bot: `scp`
   manual cuando toque analizar).

## Fases siguientes (solo si el gate correspondiente pasa)

1. **Fase 1 (gate blando):** simulación maker offline con cola FIFO sobre el
   tape guardado, midiendo selección adversa real de la señal ganadora.
2. **Fase 2 (solo si Fase 1 da edge neto):** paper trading en el VPS con la
   misma política de riesgo y barrido diseñada en polymarket-bot.
