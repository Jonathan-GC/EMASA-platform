# WebSocket Secure (WSS) Configuration Guide

## Overview

Monitor Hermes supports both **WS** (unsecured WebSocket) and **WSS** (WebSocket Secure) protocols. WSS provides encrypted communication between clients and the server using TLS/SSL, which is essential for production environments.

## Current WebSocket Endpoints

All endpoints support both WS and WSS protocols:

- `/ws/notifications` - Personal notifications channel
- `/ws` - General/Legacy WebSocket endpoint
- `/ws/tenant/{id}` - Tenant-specific dashboard
- `/ws/device/{id}` - Device-specific monitoring

## WSS Configuration

### Prerequisites

1. **SSL Certificate**: A valid SSL certificate (`.crt` or `.pem` file)
2. **SSL Private Key**: The corresponding private key file (`.key` or `.pem` file)

### Environment Variables

Add the following environment variables to your `.env` file:

```bash
# SSL/TLS Configuration for WSS
SSL_KEYFILE=/path/to/your/private.key
SSL_CERTFILE=/path/to/your/certificate.crt
```

**Note**: If these variables are not set or the files don't exist, the server will start with standard WS (unsecured) protocol.

### Docker Configuration

#### Option 1: Mount SSL Certificates as Volumes

Add volume mounts to your `docker-compose.yml`:

```yaml
services:
  fastapi:
    build: .
    container_name: fastapi_app
    restart: always
    env_file: .env
    volumes:
      - ./app:/app/app
      - ./certs:/app/certs:ro  # Mount certificates directory (read-only)
    ports:
      - "5000:5000"
    environment:
      - SSL_KEYFILE=/app/certs/server.key
      - SSL_CERTFILE=/app/certs/server.crt
    depends_on:
      - mongo
      - redis-hermes
    networks:
      - chirp-django-net
```

#### Option 2: Build Certificates into Image

Copy certificates during build (not recommended for security):

```dockerfile
# In Dockerfile, before CMD
COPY ./certs /app/certs
```

### Local Development

For local development, you can generate self-signed certificates:

```bash
# Generate self-signed certificate (valid for 365 days)
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout server.key \
  -out server.crt \
  -days 365 \
  -subj "/CN=localhost"

# Create certs directory
mkdir -p Monitor_Hermes/certs

# Move certificates
mv server.key server.crt Monitor_Hermes/certs/
```

Then update your `.env`:

```bash
SSL_KEYFILE=/app/certs/server.key
SSL_CERTFILE=/app/certs/server.crt
```

## Client Connection Examples

### WSS Connection (Secure)

**Python:**
```python
import asyncio
import websockets
import ssl

async def connect_wss():
    # For production with valid certificates
    uri = "wss://your-domain.com/ws/notifications?token=YOUR_JWT_TOKEN"
    async with websockets.connect(uri) as websocket:
        message = await websocket.recv()
        print(f"Received: {message}")

    # For self-signed certificates (development only)
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    uri = "wss://localhost:5000/ws/notifications?token=YOUR_JWT_TOKEN"
    async with websockets.connect(uri, ssl=ssl_context) as websocket:
        message = await websocket.recv()
        print(f"Received: {message}")

asyncio.run(connect_wss())
```

**JavaScript:**
```javascript
// Browser automatically handles WSS certificates
const ws = new WebSocket('wss://your-domain.com/ws/notifications?token=' + jwt_token);

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};

ws.onopen = () => {
    console.log('Connected to WSS');
};

ws.onerror = (error) => {
    console.error('WSS Error:', error);
};
```

**Node.js:**
```javascript
const WebSocket = require('ws');
const fs = require('fs');

// For self-signed certificates (development)
const ws = new WebSocket('wss://localhost:5000/ws/notifications?token=' + jwt_token, {
    rejectUnauthorized: false  // Only for development!
});

// For production with valid certificates
const ws = new WebSocket('wss://your-domain.com/ws/notifications?token=' + jwt_token);

ws.on('message', (data) => {
    console.log('Received:', JSON.parse(data));
});
```

### WS Connection (Unsecured)

For development or testing without SSL:

```python
import asyncio
import websockets

async def connect_ws():
    uri = "ws://localhost:5000/ws/notifications?token=YOUR_JWT_TOKEN"
    async with websockets.connect(uri) as websocket:
        message = await websocket.recv()
        print(f"Received: {message}")

asyncio.run(connect_ws())
```

## Production Deployment

### Using Reverse Proxy (Recommended)

In production, it's common to use a reverse proxy (like Nginx or Traefik) to handle SSL/TLS termination:

**Nginx Configuration:**
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/certs/your-cert.crt;
    ssl_certificate_key /etc/ssl/private/your-key.key;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

With this setup:
- Nginx handles SSL/TLS (clients connect via `wss://`)
- Backend service runs without SSL (using `ws://`)
- No need to configure `SSL_KEYFILE` and `SSL_CERTFILE` in the application

### Direct SSL/TLS in Application

If you're not using a reverse proxy, configure SSL directly in the application:

1. Set environment variables in `.env`
2. Mount certificates in Docker
3. Clients connect directly to `wss://your-domain.com:5000`

## Security Best Practices

1. **Never commit certificates to version control**
   - Add `*.key`, `*.crt`, `*.pem` to `.gitignore`
   - Use environment variables or secrets management

2. **Use valid certificates in production**
   - Obtain certificates from Let's Encrypt (free) or a trusted CA
   - Avoid self-signed certificates in production

3. **Rotate certificates regularly**
   - Set up automatic renewal (e.g., with Certbot for Let's Encrypt)
   - Monitor certificate expiration dates

4. **Restrict certificate file permissions**
   ```bash
   chmod 600 /path/to/server.key
   chmod 644 /path/to/server.crt
   ```

5. **Use environment-specific configurations**
   - Development: Self-signed certificates or no SSL
   - Staging/Production: Valid certificates from trusted CA

## Troubleshooting

### Connection Refused

**Problem:** Client cannot connect to WSS endpoint

**Solutions:**
1. Verify SSL certificates are valid and not expired
2. Check firewall rules allow HTTPS traffic (port 443 or your custom port)
3. Ensure `SSL_KEYFILE` and `SSL_CERTFILE` paths are correct
4. Check server logs for SSL initialization errors

### Certificate Errors

**Problem:** "SSL certificate verification failed" or similar errors

**Solutions:**
1. For self-signed certificates in development, disable certificate verification in client
2. For production, ensure certificate is issued by a trusted CA
3. Check certificate chain includes intermediate certificates
4. Verify certificate matches the domain/hostname

### Mixed Content Warnings (Browser)

**Problem:** Browser blocks WSS connection from HTTPS page

**Solutions:**
1. Ensure your web page is served over HTTPS
2. Use `wss://` (not `ws://`) for WebSocket connections from HTTPS pages
3. Check browser console for specific error messages

## Verification

### Check SSL Configuration

When the service starts with SSL configured, you should see:

```
🔒 SSL certificates detected - Starting with WSS (WebSocket Secure) support
   - SSL Key: /app/certs/server.key
   - SSL Cert: /app/certs/server.crt
```

Without SSL:

```
📡 Starting with WS (unsecured WebSocket) support
   To enable WSS, set SSL_KEYFILE and SSL_CERTFILE environment variables
```

### Test WSS Connection

```bash
# Using wscat (install with: npm install -g wscat)
wscat -c "wss://localhost:5000/ws/notifications?token=YOUR_JWT_TOKEN" --no-check

# Using curl (test HTTPS endpoint)
curl -k https://localhost:5000/messages/last?dev_eui=TEST&limit=1
```

## Summary

Monitor Hermes is **ready for WSS protocols** with the changes implemented in this configuration. The application:

- ✅ Supports both WS and WSS protocols
- ✅ Automatically enables WSS when SSL certificates are provided
- ✅ Falls back to WS when certificates are not configured
- ✅ Works with reverse proxy SSL termination (recommended for production)
- ✅ Supports direct SSL/TLS configuration in the application

Choose the deployment approach that best fits your infrastructure and security requirements.
