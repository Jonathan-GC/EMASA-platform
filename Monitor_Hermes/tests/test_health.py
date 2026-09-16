import os

# Set dummy env vars before importing app
os.environ.setdefault("JWT_SECRET_KEY", "dummy_secret_key_for_testing")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("BROKER_URL", "localhost")
os.environ.setdefault("BROKER_PORT", "1883")
os.environ.setdefault("MONGO_HOST", "localhost")
os.environ.setdefault("MONGO_PORT", "27017")
os.environ.setdefault("MONGO_INITDB_ROOT_USERNAME", "admin")
os.environ.setdefault("MONGO_INITDB_ROOT_PASSWORD", "password")
os.environ.setdefault("MONGO_URI", "mongodb://admin:password@localhost:27017/hermes")
os.environ.setdefault("MONGO_DB", "hermes")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_PASSWORD", "secret")
os.environ.setdefault("WS_SECRET", "dummy_ws_secret_32_bytes_long!!")
os.environ.setdefault("SERVICE_API_KEY", "test_service_key")

import pytest
from unittest.mock import AsyncMock, patch
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_hermes_healthcheck_endpoint_all_healthy():
    with (
        patch("app.main.check_mongo_health", new_callable=AsyncMock) as mock_mongo,
        patch("app.main.check_redis_health", new_callable=AsyncMock) as mock_redis,
        patch("app.main.is_mqtt_connected", return_value=True),
        patch("app.main.manager.get_stats", return_value={
            "status": "healthy",
            "active_tenants": 2,
            "tenant_connections": 5,
            "global_connections": 1,
            "super_connections": 0,
            "total_connections": 6,
            "device_subscriptions": 3,
        }),
    ):
        mock_mongo.return_value = {"status": "healthy", "latency_ms": 1.25, "database": "hermes"}
        mock_redis.return_value = {"status": "healthy", "latency_ms": 0.85}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "Monitor_Hermes"
            assert "timestamp" in data
            assert data["components"]["database"]["status"] == "healthy"
            assert data["components"]["redis"]["status"] == "healthy"
            assert data["components"]["websockets"]["total_connections"] == 6
            assert data["components"]["mqtt"]["status"] == "connected"


@pytest.mark.anyio
async def test_hermes_healthcheck_endpoint_degraded():
    with (
        patch("app.main.check_mongo_health", new_callable=AsyncMock) as mock_mongo,
        patch("app.main.check_redis_health", new_callable=AsyncMock) as mock_redis,
        patch("app.main.is_mqtt_connected", return_value=False),
        patch("app.main.manager.get_stats", return_value={"status": "healthy", "total_connections": 0}),
    ):
        mock_mongo.return_value = {"status": "healthy", "latency_ms": 1.5}
        mock_redis.return_value = {"status": "unhealthy", "error": "Connection refused"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["components"]["database"]["status"] == "healthy"
            assert data["components"]["redis"]["status"] == "unhealthy"


@pytest.mark.anyio
async def test_hermes_healthcheck_alias():
    with (
        patch("app.main.check_mongo_health", new_callable=AsyncMock) as mock_mongo,
        patch("app.main.check_redis_health", new_callable=AsyncMock) as mock_redis,
        patch("app.main.is_mqtt_connected", return_value=True),
        patch("app.main.manager.get_stats", return_value={"status": "healthy", "total_connections": 0}),
    ):
        mock_mongo.return_value = {"status": "healthy", "latency_ms": 1.0}
        mock_redis.return_value = {"status": "healthy", "latency_ms": 1.0}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/healthcheck")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
