#!/bin/bash

# Entrypoint script for Monitor Hermes FastAPI application
# Handles both WS (unsecured) and WSS (secure) WebSocket protocols

# Base uvicorn command parts as array to prevent injection
UVICORN_CMD=(uvicorn app.main:app --host 0.0.0.0 --port 5000)

# Add SSL parameters if SSL certificates are configured
if [ -n "$SSL_KEYFILE" ] && [ -n "$SSL_CERTFILE" ]; then
    if [ -f "$SSL_KEYFILE" ] && [ -f "$SSL_CERTFILE" ]; then
        echo "🔒 SSL certificates detected - Starting with WSS (WebSocket Secure) support"
        echo "   - SSL Key: $SSL_KEYFILE"
        echo "   - SSL Cert: $SSL_CERTFILE"
        UVICORN_CMD+=(--ssl-keyfile="$SSL_KEYFILE" --ssl-certfile="$SSL_CERTFILE")
    else
        echo "⚠️  SSL paths configured but files not found. Starting without SSL."
        echo "   - SSL Key: $SSL_KEYFILE (exists: $([ -f "$SSL_KEYFILE" ] && echo 'yes' || echo 'no'))"
        echo "   - SSL Cert: $SSL_CERTFILE (exists: $([ -f "$SSL_CERTFILE" ] && echo 'yes' || echo 'no'))"
    fi
else
    echo "📡 Starting with WS (unsecured WebSocket) support"
    echo "   To enable WSS, set SSL_KEYFILE and SSL_CERTFILE environment variables"
fi

# Execute uvicorn with the constructed command array
exec "${UVICORN_CMD[@]}"

