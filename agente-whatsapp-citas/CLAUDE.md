# Convenciones del proyecto (para Claude y para humanos)

Este archivo describe cómo trabajar en este repositorio. `AGENTS.md` es un enlace
a este mismo contenido.

## Reglas de oro

- **pnpm SIEMPRE, nunca npm/npx.** Todos los comandos usan pnpm.
- **Idioma:** código, identificadores y comentarios en **inglés**; el copy de la
  UI y el README, en **español**.
- **Single-tenant:** un despliegue = un centro. Hay UN solo agente (no es
  multi-agente). La config del agente vive en una única fila (`agent_config`).

## Arquitectura

- **Frontend:** Next.js (App Router) + React + Tailwind. Puerto 3000.
- **Backend:** NestJS + TypeORM, con el **agente Mastra EMBEBIDO** en el mismo
  proceso. Prefijo global `/api`. Puerto 3001.
- **BD:** PostgreSQL (Docker solo para la BD en local, puerto host **5433**).
- **Realtime:** SSE en un único endpoint `GET /api/events` + `EventSource` nativo.
- **Storage de Mastra:** `@mastra/pg` en el MISMO Postgres que TypeORM.

## Reglas de implementación (IMPORTANTE)

- **El módulo que importa Mastra (`AgentModule`) va el ÚLTIMO en `app.module.ts`.**
  Mastra puede montar rutas catch-all bajo `/api`, así que debe registrarse
  después del resto de controladores.
- **Lógica de dominio en los servicios Nest; las tools de Mastra son finas**
  (solo envuelven a los servicios). Ver `src/agent/agent.tools.ts`.
- **El modelo del agente se resuelve desde la config guardada** (key + modelo de
  OpenRouter). Las env `OPENROUTER_API_KEY` / `AGENT_MODEL` son solo *fallback*.

## Seguridad (MUY IMPORTANTE)

- **Sin login:** herramienta de admin interna. No exponer a internet sin auth
  delante. Lo único público es el webhook firmado.
- **Los secretos NUNCA salen por la API:** la config se sanitiza (devuelve
  booleanos `has*`, no los valores). Los updates ignoran los campos de secreto
  vacíos para no pisar lo guardado.
- **Webhook fail-closed:** sin `YCLOUD_WEBHOOK_SECRET`, se rechaza con 401. Nunca
  se aceptan peticiones sin firmar.
- `helmet`, rate limiting global (`@nestjs/throttler`), usuarios non-root en
  Docker. **Sin PII ni secretos en logs** (los datos clínicos/personales son
  sensibles).
- **La conexión de WhatsApp/YCloud va por env, NO por la UI.** No crear pantallas
  para YCloud.

## WhatsApp (YCloud)

- Webhook único: `POST /api/webhooks/ycloud` (sin `:agentKey`, hay un solo agente).
- Flujo entrante: verifica firma → responde 200 rápido → upsert paciente por
  teléfono → el agente responde → envía por YCloud → emite eventos SSE.

## Comandos

```
pnpm install        # instalar dependencias
pnpm db:up          # levantar Postgres (Docker) en :5433
pnpm dev:api        # backend en :3001
pnpm dev:web        # frontend en :3000
pnpm build          # construir ambos
```
