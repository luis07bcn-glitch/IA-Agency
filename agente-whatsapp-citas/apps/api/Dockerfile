# ---- Build stage ----
FROM node:22-alpine AS build
WORKDIR /app
RUN corepack enable
COPY package.json ./
COPY tsconfig.json nest-cli.json ./
RUN pnpm install
COPY src ./src
RUN pnpm build

# ---- Runtime stage ----
FROM node:22-alpine AS runtime
WORKDIR /app
RUN corepack enable
ENV NODE_ENV=production

# Non-root user (security).
RUN addgroup -S app && adduser -S app -G app

COPY package.json ./
RUN pnpm install --prod
COPY --from=build /app/dist ./dist

USER app
EXPOSE 3001
CMD ["node", "dist/main.js"]
