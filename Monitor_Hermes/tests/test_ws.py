import websockets, asyncio, loguru

ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU3MTA5MzQ5LCJpYXQiOjE3NTcxMDU3NDksImp0aSI6IjgyYmMzOTMxYmM3NjRjZjI4MjNjYjZlYzQwOGMzNmQ4IiwidXNlcl9pZCI6MSwidXNlcm5hbWUiOiJ3ZWVkbyIsImlzX2dsb2JhbCI6ZmFsc2UsImNzX3RlbmFudF9pZCI6bnVsbCwiaXNfc3VwZXJ1c2VyIjp0cnVlfQ.SdDUHQykeQpZ1DRNreFI4QT4eZmnjgdfzg4G9TYEKhk"
URL = f"ws://localhost:5000/ws?token={ACCESS_TOKEN}"


async def test():
    """Test WebSocket connection and message exchange."""
    async with websockets.connect(URL) as websocket:
        loguru.logger.info("WebSocket connected")
        await websocket.send("Hello WebSocket!")
        response = await websocket.recv()
        loguru.logger.info(f"Received: {response}")


asyncio.run(test())
