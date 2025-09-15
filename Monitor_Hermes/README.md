# Hermes

Microservice with MQTT and WebSockets 

```bash
Monitor_Hermes/
│── app/
│   ├── main.py                # Punto de entrada FastAPI
│   ├── config.py              # Configuración (env vars, secrets, URLs, etc.)
│   ├── deps.py                # Dependencias comunes (ej: JWT validation, DB sessions)
│
│   ├── mqtt/                  # Todo lo relacionado con ingestión MQTT
│   │   ├── client.py          # Conexión y callbacks MQTT
│   │   ├── handlers.py        # Procesamiento de payloads (parse, enrich)
│   │   └── __init__.py
│
│   ├── ws/                    # WebSockets
│   │   ├── routes.py          # Endpoints WS (`/ws`)
│   │   ├── manager.py         # Connection manager (maneja clientes conectados)
│   │   └── filters.py         # Filtrado de mensajes por tenant/rol
│
│   ├── persistence/           # Persistencia en Mongo
│   │   ├── mongo.py           # Cliente Mongo y funciones CRUD
│   │   └── models.py          # Modelos de documentos (pydantic + pymongo)
│
│   ├── auth/                  # JWT y permisos
│   │   ├── jwt.py             # Validación de tokens, extracción de claims
│   │   └── deps.py            # Dependencias de seguridad para WS
│
│   ├── schemas/               # Pydantic schemas
│   │   ├── payloads.py        # Payloads IoT procesados
│   │   └── ws.py              # Mensajes WS
│
│   └── utils/                 # Utilidades genéricas (logging, helpers, etc.)
│
│── tests/                     # Tests unitarios
│── requirements.txt           # Dependencias Python
│── docker-compose.yml         # Mongo + MQTT broker + este servicio
│── Dockerfile                 # Build del microservicio
```
