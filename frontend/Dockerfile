# --- Agatronic Frontend — Industrial AI Monitoring Platform ---

# Stage 1: build the static Vite bundle
FROM node:20-slim AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
# VITE_API_BASE_URL est injecté au build (les variables VITE_* sont figées
# dans le bundle statique — voir docker-compose.yml / build args)
ARG VITE_API_BASE_URL=http://localhost:8000/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# Stage 2: serve with Nginx
FROM nginx:1.27-alpine AS production
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q --spider http://localhost:80 || exit 1
CMD ["nginx", "-g", "daemon off;"]
