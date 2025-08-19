# Multi-stage build para producción
FROM node:20-alpine AS builder

WORKDIR /app

# Accept build arguments
ARG VITE_WEBSOCKET_URL=ws://localhost/ws

# Set environment variables for build
ENV VITE_WEBSOCKET_URL=$VITE_WEBSOCKET_URL

# Copy package files
COPY package*.json ./

# Install dependencies (including devDependencies for build)
RUN npm ci

# Copy source code
COPY . .

RUN chmod +x node_modules/.bin/vite

# Build for production
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration for SPA (usar nginx.prod.conf)
COPY ./nginx/nginx.prod.conf /etc/nginx/conf.d/default.conf

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:80 || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
