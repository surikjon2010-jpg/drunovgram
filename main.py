from fastapi import FastAPI, WebSocket
from typing import List

app = FastAPI()

ADMIN_ID = 123456789
connections: List[WebSocket] = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            for connection in connections:
                await connection.send_text(data)
    except:
        connections.remove(websocket)

@app.get("/")
def read_root():
    return {"status": "Server is running"}
