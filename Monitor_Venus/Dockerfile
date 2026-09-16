
FROM node:22-alpine AS builder

WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

# Accept build arguments
ARG VITE_WEBSOCKET_URL
ARG VITE_API_URL
ARG VITE_WS_NOTIFY_URL
ARG VITE_HEALTH_MONITOR_URL
ARG VITE_BUILD_VERSION
ARG GIT_SHA
ARG GIT_BRANCH
ARG VITE_GOOGLE_CLIENT_ID
ARG VITE_FIREBASE_API_KEY
ARG VITE_FIREBASE_AUTH_DOMAIN
ARG VITE_FIREBASE_PROJECT_ID
ARG VITE_FIREBASE_STORAGE_BUCKET
ARG VITE_FIREBASE_MESSAGING_SENDER_ID
ARG VITE_FIREBASE_APP_ID
ARG VITE_FIREBASE_MEASUREMENT_ID
ARG VITE_FIREBASE_VAPID_KEY

# Set environment variables for build
ENV VITE_WEBSOCKET_URL=$VITE_WEBSOCKET_URL
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_WS_NOTIFY_URL=$VITE_WS_NOTIFY_URL
ENV VITE_HEALTH_MONITOR_URL=$VITE_HEALTH_MONITOR_URL
ENV VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID
ENV VITE_FIREBASE_API_KEY=$VITE_FIREBASE_API_KEY
ENV VITE_FIREBASE_AUTH_DOMAIN=$VITE_FIREBASE_AUTH_DOMAIN
ENV VITE_FIREBASE_PROJECT_ID=$VITE_FIREBASE_PROJECT_ID
ENV VITE_FIREBASE_STORAGE_BUCKET=$VITE_FIREBASE_STORAGE_BUCKET
ENV VITE_FIREBASE_MESSAGING_SENDER_ID=$VITE_FIREBASE_MESSAGING_SENDER_ID
ENV VITE_FIREBASE_APP_ID=$VITE_FIREBASE_APP_ID
ENV VITE_FIREBASE_MEASUREMENT_ID=$VITE_FIREBASE_MEASUREMENT_ID
ENV VITE_FIREBASE_VAPID_KEY=$VITE_FIREBASE_VAPID_KEY

# Copy package files
COPY package*.json pnpm-lock.yaml pnpm-workspace.yaml ./

# Install dependencies and ensure build scripts (like esbuild) are allowed to run
# CI=1 lets pnpm auto-confirm purging/reinstalling node_modules without a TTY,
# avoiding ERR_PNPM_ABORTED_REMOVE_MODULES_DIR_NO_TTY in Docker builds
ENV CI=1
RUN pnpm config set ignore-scripts false && \
    pnpm install --frozen-lockfile

# Copy source code
COPY . .

# Build for production
RUN pnpm run build

# Bake health metadata into dist/ (served by nginx at /health)
# ARG vars are available as env in RUN; Vite copies public/health.json first.
RUN node -e "const fs=require('fs'); \
const build={version:process.env.VITE_BUILD_VERSION||'dev',commit:process.env.GIT_SHA||'unknown',branch:process.env.GIT_BRANCH||'unknown',built_at:new Date().toISOString(),environment:'production'}; \
const config={api_url:process.env.VITE_API_URL||null,ws_url:process.env.VITE_WEBSOCKET_URL||null,firebase_configured:!!process.env.VITE_FIREBASE_API_KEY,capacitor_app_id:'com.mtr.online'}; \
const payload={status:'healthy',service:'Monitor_Venus',type:'spa_frontend',version:process.env.VITE_BUILD_VERSION||'dev',build:build,config:config}; \
fs.writeFileSync('/app/dist/health.json',JSON.stringify(payload,null,2)+'\n')"

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
