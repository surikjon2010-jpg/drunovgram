from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from typing import List

app = FastAPI()
ADMIN_ID = 123456789
connections: List[WebSocket] = []

html = """
<!DOCTYPE html>
<html>
<head>
    <title>Drunogram</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial; background: #17212b; color: white; margin: 0; padding: 10px; }
        #chat { height: 80vh; overflow-y: scroll; border: 1px solid #2b5278; padding: 10px; margin-bottom: 10px; }
        .msg { background: #2b5278; padding: 5px 10px; border-radius: 10px; margin-bottom: 5px; width: fit-content; }
        input { width: 70%; padding: 10px; border-radius: 5px; border: none; }
        button { padding: 10px; border-radius: 5px; border: none; background: #2b5278; color: white; }
    </style>
</head>
<body>
    <h2>Drunogram</h2>
    <div id="chat"></div>
    <input id="msg" type="text" placeholder="Сообщение..." autocomplete="off">
    <button onclick="send()">Отправить</button>
    <script>
        var ws = new WebSocket("wss://" + window.location.host + "/ws");
        ws.onmessage = function(event) {
            var chat = document.getElementById("chat");
            var div = document.createElement("div");
            div.className = "msg";
            div.textContent = event.data;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        };
        function send() {
            var input = document.getElementById("msg");
            if (input.value) {
                ws.send(input.value);
                input.value = "";
            }
        }
        document.getElementById("msg").addEventListener("keyup", function(e) {
            if (e.key === "Enter") send();
        });
    </script>
</body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)

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
