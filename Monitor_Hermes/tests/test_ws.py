import websockets, asyncio, loguru, json

ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU3MzYzNDM1LCJpYXQiOjE3NTczNTk4MzUsImp0aSI6IjRjY2YxZjFhNTY3MzQ3YTRiMDM0OTg3MTk4YzY3YmQ0IiwidXNlcl9pZCI6MSwidXNlcm5hbWUiOiJ3ZWVkbyIsImlzX2dsb2JhbCI6ZmFsc2UsImNzX3RlbmFudF9pZCI6bnVsbCwiaXNfc3VwZXJ1c2VyIjp0cnVlfQ.Q4RuVfRQrnIVxOWRitasfcSC4FQz2YsuJnJYR7E80-U"
URL = f"ws://localhost:5000/ws?token={ACCESS_TOKEN}"


async def test():
    """Test WebSocket connection and message exchange."""
    async with websockets.connect(URL) as websocket:
        loguru.logger.info("WebSocket connected")
        while True:
            msg = await websocket.recv()
            data = json.loads(msg)
            loguru.logger.info(f"Received message: {data}")


asyncio.run(test())
