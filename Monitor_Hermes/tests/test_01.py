import websockets, asyncio


async def test():
    """Test WebSocket connection and message exchange."""

    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        await websocket.send("Hello WebSocket")
        print(await websocket.recv())


asyncio.run(test())
