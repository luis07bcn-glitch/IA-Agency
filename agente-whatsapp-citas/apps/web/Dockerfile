# ---- Build stage ----
FROM node:22-alpine AS build
WORKDIR /app
RUN corepack enable

# NEXT_PUBLIC_* must be present at build time (it is baked into the bundle).
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

COPY package.json ./
RUN pnpm install
COPY . .
RUN pnpm build

# ---- Runtime stage ----
FROM node:22-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production

RUN addgroup -S app && adduser -S app -G app

# Next.js standalone output bundles only what is needed.
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
COPY --from=build /app/public ./public

USER app
EXPOSE 3000
CMD ["node", "server.js"]
