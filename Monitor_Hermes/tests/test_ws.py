import websockets, asyncio, loguru

ACCESS_TOKEN = "your_jwt_access_token_here"
URL = f"ws://localhost:5000/ws?token={ACCESS_TOKEN}"


async def test():
    """Test WebSocket connection and message exchange."""
    async with websockets.connect(URL) as websocket:
        loguru.logger.info("WebSocket connected")
        await websocket.send("Hello WebSocket!")
        response = await websocket.recv()
        loguru.logger.info(f"Received: {response}")


asyncio.run(test())
