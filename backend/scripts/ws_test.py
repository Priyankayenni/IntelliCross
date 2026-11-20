import asyncio
import websockets

async def main():
    uri = 'ws://localhost:8000/ws/traffic'
    async with websockets.connect(uri) as ws:
        msg = await ws.recv()
        print(msg)

if __name__ == '__main__':
    asyncio.run(main())
