"""
Test script to verify WSS (WebSocket Secure) connectivity.

This script tests both WS and WSS connections to Monitor Hermes.
For WSS testing, valid SSL certificates must be configured on the server.

Usage:
    python test_wss_connection.py [--wss] [--token YOUR_JWT_TOKEN]

Options:
    --wss           Test WSS (secure) connection instead of WS
    --token         JWT token for authentication (required)
    --host          Host address (default: localhost)
    --port          Port number (default: 5000)
    --skip-verify   Skip SSL certificate verification (for self-signed certs)
"""

import asyncio
import websockets
import ssl
import argparse
import json
import loguru


async def test_websocket_connection(
    host: str,
    port: int,
    token: str,
    use_wss: bool = False,
    skip_verify: bool = False,
):
    """Test WebSocket connection to Monitor Hermes."""

    # Construct the WebSocket URL
    protocol = "wss" if use_wss else "ws"
    url = f"{protocol}://{host}:{port}/ws/notifications?token={token}"

    loguru.logger.info(f"Testing {protocol.upper()} connection to {url}")

    # Configure SSL context if using WSS
    ssl_context = None
    if use_wss:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        if skip_verify:
            loguru.logger.warning(
                "⚠️  SSL verification disabled (only for development/testing)"
            )
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        else:
            ssl_context.check_hostname = True
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            ssl_context.load_default_certs()

    try:
        # Connect to WebSocket
        async with websockets.connect(url, ssl=ssl_context) as websocket:
            loguru.logger.success(
                f"✅ Successfully connected to {protocol.upper()} endpoint"
            )

            # Send a ping
            ping_message = json.dumps({"action": "ping"})
            await websocket.send(ping_message)
            loguru.logger.debug(f"Sent: {ping_message}")

            # Wait for response (with timeout)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                loguru.logger.success(f"Received: {data}")

                if data.get("action") == "pong":
                    loguru.logger.success("✅ Ping/Pong test successful")
                else:
                    loguru.logger.info(f"📨 Received message: {data}")

            except asyncio.TimeoutError:
                loguru.logger.warning("⏱️  Timeout waiting for response")
                loguru.logger.info(
                    "Connection is established but no immediate response received"
                )
                loguru.logger.info("This is expected if no notifications are pending")

            # Keep connection open for a few more seconds to receive any notifications
            loguru.logger.info("Listening for notifications for 10 seconds...")
            try:
                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(message)
                    loguru.logger.info(f"📬 Notification received: {data}")
            except asyncio.TimeoutError:
                loguru.logger.info("No notifications received in 10 seconds")

    except websockets.exceptions.InvalidStatusCode as e:
        loguru.logger.error(f"❌ Connection failed with status code: {e.status_code}")
        if e.status_code == 1008:
            loguru.logger.error(
                "Authentication failed. Check your JWT token and ensure it's valid."
            )
    except websockets.exceptions.WebSocketException as e:
        loguru.logger.error(f"❌ WebSocket error: {e}")
    except ssl.SSLError as e:
        loguru.logger.error(f"❌ SSL/TLS error: {e}")
        loguru.logger.error(
            "This might be due to invalid or self-signed certificates."
        )
        loguru.logger.error(
            "For self-signed certificates, use --skip-verify flag (development only)"
        )
    except Exception as e:
        loguru.logger.exception(f"❌ Unexpected error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Test WebSocket (WS/WSS) connection to Monitor Hermes"
    )
    parser.add_argument(
        "--wss",
        action="store_true",
        help="Use WSS (secure) protocol instead of WS",
    )
    parser.add_argument(
        "--token",
        type=str,
        required=True,
        help="JWT token for authentication",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host address (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port number (default: 5000)",
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip SSL certificate verification (for self-signed certs)",
    )

    args = parser.parse_args()

    # Run the test
    asyncio.run(
        test_websocket_connection(
            host=args.host,
            port=args.port,
            token=args.token,
            use_wss=args.wss,
            skip_verify=args.skip_verify,
        )
    )


if __name__ == "__main__":
    main()
