# Monitor Hermes 🪽

Microservice with MQTT and WebSockets (WS/WSS)

## 🔐 WebSocket Security

Monitor Hermes supports both:
- **WS** (WebSocket) - Unsecured connection for development
- **WSS** (WebSocket Secure) - Encrypted connection for production

For WSS configuration, SSL certificates, and production deployment, see **[WSS Configuration Guide](docs/WSS_CONFIGURATION.md)**.

## Architecture

```bash
Monitor_Hermes/
│── app/
│   ├── main.py                # FastAPI entry point
│   ├── settings.py            # Configuration (env vars, secrets, URLs, etc.)
│
│   ├── mqtt/                  # Everything related to MQTT ingestion
│   │   ├── __init__.py
│   │   ├── client.py          # MQTT connection and callbacks
│   │   └── handlers.py        # Payload processing (parse, enrich)
│
│   ├── ws/                    # WebSockets
│   │   ├── routes.py          # WS endpoints (`/ws`)
│   │   ├── manager.py         # Connection manager (handles connected clients)
│   │   └── filters.py         # Message filtering by tenant/role
│
│   ├── persistence/           # MongoDB persistence
│   │   ├── mongo.py           # Mongo client and CRUD functions
│   │   └── models.py          # Document models (pydantic + pymongo)
│
│   ├── auth/                  # JWT and permissions
│   │   ├── jwt.py             # Token validation, claims extraction
│   │   └── deps.py            # Security dependencies for WS
│
│   ├── redis/                 # Redis caching
│   │   ├── redis.py           # Redis client
│   │   └── cache.py           # Cache functions
│
│   ├── schemas/               # Pydantic schemas
│   │   ├── payloads.py        # Processed IoT payloads
│   │   └── ws.py              # WS messages
│
│   ├── workers/               # Background workers
│   │   └── redis_worker.py    # Redis worker tasks
│
│   └── utils/                 # Generic utilities
│       └── logs.py            # Logging configuration
│
│── docs/                      # Documentation
│   └── NOTIFICATIONS.md
│
│── tests/                     # Unit tests
│   ├── test_notifications_ws.py
│   ├── test_send_notification.py
│   └── test_ws.py
│
│── docker-compose.yml         # Mongo + MQTT broker + Redis + this service
│── Dockerfile                 # Microservice build
│── requirements.txt           # Python dependencies         
└── README.md                  # This file
```

# 🔔 Notifications via WS

## 🎨 Message Format

### Received notification (server → client)
```json
{
    "channel": "notifications",
    "title": "Sensor alert",
    "message": "Sensor ABC exceeded threshold",
    "type": "warning"
}
```

### Available types
- `info` 📘 - General information
- `success` ✅ - Successful action
- `warning` ⚠️ - Warning
- `error` ❌ - Error or problem

---

## 📊 Existing Endpoints

| Endpoint            | Purpose                | Receives                  | Usage              |
| ------------------- | ---------------------- | ------------------------- | ------------------ |
| `/ws/notifications` | Personal notifications | Only user's notifications | Alerts, messages   |
| `/ws`               | General/Legacy         | MQTT data + tenant        | General monitoring |
| `/ws/tenant/{id}`   | Tenant dashboard       | All tenant devices        | Specific dashboard |
| `/ws/device/{id}`   | Device monitoring      | Only that device          | Specific device    |

---

## 💡 Quick Usage

### Backend (Send notification)
```python
import requests

requests.post("http://localhost:5000/notify", json={
    "user_id": "123",
    "title": "New alert",
    "message": "Sensor disconnected",
    "type": "error"
})
```

### Frontend (Receive notifications)
```javascript
import NotificationClient from './notification-client.js';

const client = new NotificationClient('ws://localhost:5000', jwt_token);

client.on('notification', (notif) => {
    showToast(notif.title, notif.message, notif.type);
});

client.connect();
```
## 🧪 Testing

### 1. Start the server
```bash
docker-compose up --build -d
```

### 2. Connect WebSocket client
```bash
# Terminal 1
python tests/test_notifications_ws.py
```

### 3. Send test notifications
```bash
# Terminal 2
python tests/test_send_notification.py
```

### 4. Or use the web interface
```bash
open docs/test-notifications.html
```

## 📚 Documentation

- **Complete guide**: `docs/NOTIFICATIONS_WEBSOCKET.md`
- **Implementation guide**: `docs/README_NOTIFICATIONS.md`
- **JavaScript client**: `docs/notification-client.js`
- **Tests**: `tests/test_notifications_ws.py` and `tests/test_send_notification.py`

---
