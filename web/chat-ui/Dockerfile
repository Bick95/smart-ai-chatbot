# Stage 1: build Vite/React assets. Stage 2: serve static files with nginx (ci.sh --build smoke hits GET /).

FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# Final image: only nginx + dist/ (no Node at runtime).
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
