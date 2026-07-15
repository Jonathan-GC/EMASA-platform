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
│   └── test_ws.py
│
│── docker-compose.yml         # Mongo + MQTT broker + Redis + this service
│── Dockerfile                 # Microservice build
│── requirements.txt           # Python dependencies         
└── README.md                  # This file
```

## 📊 Existing Endpoints

| Endpoint            | Purpose                | Receives                  | Usage              |
| ------------------- | ---------------------- | ------------------------- | ------------------ |
| `/ws`               | General/Legacy         | MQTT data + tenant        | General monitoring |
| `/ws/tenant/{id}`   | Tenant dashboard       | All tenant devices        | Specific dashboard |
| `/ws/device/{id}`   | Device monitoring      | Only that device          | Specific device    |

## 🧪 Testing

### 1. Start the server
```bash
docker-compose up --build -d
```
