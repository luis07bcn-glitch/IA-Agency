# Agente de Citas — CRM + Agente de WhatsApp

CRM de un solo centro (single-tenant) con **un agente de IA conectable a WhatsApp**
que gestiona las citas de los pacientes conversando: consulta disponibilidad,
reserva, lista y cancela. El ejemplo viene preparado para un **centro de
fisioterapia**, pero la arquitectura es genérica (sirve para cualquier negocio
de citas cambiando los servicios y horarios desde la pantalla «Agente»).

> ⚠️ **Importante (seguridad):** esta herramienta **no tiene login**. Está pensada
> para uso interno. **No la publiques en internet** sin poner una contraseña
> delante (un proxy con autenticación). Lo único que debe ser público es el
> webhook firmado de WhatsApp.

> ⚠️ **Salvaguarda clínica:** el agente **no da diagnósticos ni consejo médico**.
> Si un paciente describe una dolencia, responde con empatía y ofrece reservar una
> «Primera valoración». Su único ámbito es la gestión de citas.

---

## Qué necesitas instalado (una sola vez)

1. **Node.js 20 o superior** — https://nodejs.org (instala la versión "LTS").
2. **pnpm** (gestor de paquetes). En este proyecto se usa **pnpm SIEMPRE, nunca
   npm ni npx**. Para instalarlo, abre una terminal y ejecuta:
   ```
   npm install -g pnpm
   ```
3. **Docker Desktop** — https://www.docker.com/products/docker-desktop (sirve para
   la base de datos en local).

---

## Arrancar en local, paso a paso

### 1. Prepara la configuración
Copia el archivo de ejemplo `.env.example` a un archivo nuevo llamado `.env`:
```
cp .env.example .env
```
Ábrelo con el Bloc de notas. Para probar en local **no necesitas tocar casi nada**:
puedes dejar los valores por defecto. (La conexión de WhatsApp y la API key del
agente se pueden rellenar más tarde.)

### 2. Instala las dependencias
Desde la carpeta del proyecto:
```
pnpm install
```

### 3. Arranca la base de datos
```
pnpm db:up
```
Esto levanta PostgreSQL con Docker en el puerto **5433** de tu ordenador.

### 4. Arranca el backend y el frontend
En **dos terminales** distintas (o usa `pnpm dev` para las dos a la vez):
```
pnpm dev:api     # backend  -> http://localhost:3001/api
```
```
pnpm dev:web     # frontend -> http://localhost:3000
```

### 5. Abre la aplicación
Ve a **http://localhost:3000** en tu navegador. La primera vez se crean datos de
ejemplo (centro «Fisioterapia Bienestar», servicios, horarios, pacientes y
conversaciones). Para empezar con la base vacía, pon `SEED_DEMO_DATA=false` en `.env`.

### 6. Conecta el agente de IA
En la pantalla **«Agente»**:
- Pega tu **API key de OpenRouter** (https://openrouter.ai).
- Elige un **modelo** del desplegable.
- Pulsa **Guardar cambios** y prueba el agente en el **Playground**.

---

## ¿Cómo se conecta WhatsApp? (lo hace una persona técnica una vez)

La conexión de WhatsApp se configura por **variables de entorno** en el `.env`
(no hay pantalla para esto), usando el proveedor **YCloud**:

- `YCLOUD_API_KEY` — para enviar mensajes.
- `YCLOUD_WEBHOOK_SECRET` — para verificar que los mensajes entrantes son
  auténticos. **Sin este secreto, el webhook rechaza todo** (es lo seguro).
- `YCLOUD_WHATSAPP_NUMBER` — tu número de WhatsApp Business.

En el panel de YCloud, configura el webhook entrante apuntando a:
```
https://TU-DOMINIO/api/webhooks/ycloud
```

---

## Desplegar en un servidor (VPS)

Con Docker, todo el sistema (base de datos + backend + frontend) se levanta así:
```
docker compose -f docker-compose.prod.yml up -d --build
```
Antes, rellena el `.env` con tus valores reales y pon un proxy (Caddy/Nginx) con
**HTTPS y autenticación** delante. Recuerda dejar accesible públicamente **solo**
la ruta `/api/webhooks/ycloud`.

---

## Estructura del proyecto

```
agente-whatsapp-citas/
├─ apps/
│  ├─ api/     Backend NestJS + TypeORM + agente Mastra embebido
│  └─ web/     Frontend Next.js (App Router) + Tailwind
├─ docker-compose.yml         Solo PostgreSQL (desarrollo local)
├─ docker-compose.prod.yml    Stack completo (producción)
└─ .env.example               Plantilla de configuración comentada
```

## Pantallas

- **Inicio** — métricas (pacientes, citas hoy, próximas, estado del agente) y
  conversaciones recientes, en tiempo real.
- **Pacientes** — buscar, crear, editar y borrar; la ficha muestra sus citas.
- **Calendario** — vistas de mes y semana; reserva con disponibilidad en vivo.
- **Conversaciones** — bandeja tipo chat (WhatsApp + Playground), en vivo.
- **Agente** — persona del centro, servicios, horarios, modelo de IA y Playground.

> Nota técnica: `pnpm build` del frontend usa el modo *standalone* de Next.js para
> Docker. En **Windows** ese paso puede fallar al crear enlaces simbólicos; no
> afecta al uso en local (`pnpm dev`) ni al despliegue con Docker (corre en Linux).
