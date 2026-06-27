# AGENTS.md

Las convenciones de este proyecto están en [CLAUDE.md](./CLAUDE.md).

Resumen rápido:
- **pnpm SIEMPRE, nunca npm/npx.**
- Código en inglés; UI y README en español.
- El módulo que importa **Mastra va el ÚLTIMO** en `app.module.ts`.
- Lógica de dominio en servicios Nest; tools de Mastra finas.
- Secretos nunca salen por la API; webhook fail-closed; sin PII en logs.
- WhatsApp/YCloud se configura por variables de entorno, no por la UI.
