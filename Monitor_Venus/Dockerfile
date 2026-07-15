
FROM node:22-alpine AS builder

WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

# Accept build arguments
ARG VITE_WEBSOCKET_URL
ARG VITE_API_URL
ARG VITE_WS_NOTIFY_URL

# Set environment variables for build
ENV VITE_WEBSOCKET_URL=$VITE_WEBSOCKET_URL
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_WS_NOTIFY_URL=$VITE_WS_NOTIFY_URL

# Copy package files
COPY package*.json pnpm-lock.yaml pnpm-workspace.yaml ./

# Install dependencies and ensure build scripts (like esbuild) are allowed to run
RUN pnpm config set ignore-scripts false && \
    pnpm install --frozen-lockfile

# Copy source code
COPY . .

# Build for production
RUN pnpm run build

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