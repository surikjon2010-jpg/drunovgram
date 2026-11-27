from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import List, Dict
import json

app = FastAPI()

# Твой ник (админ)
ADMIN_NICK = "sabhail"
# Список активных подключений: {websocket: username}
active_connections: Dict[WebSocket, str] = {}

html = """
<!DOCTYPE html>
<html>
<head>
    <title>Drunogram</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        body { font-family: -apple-system, sans-serif; background: #0e1621; color: white; margin: 0; padding: 0; display: flex; height: 100vh; overflow: hidden; }
        /* Сайдбар (список чатов) */
        #sidebar { width: 30%; background: #17212b; border-right: 1px solid #101921; display: flex; flex-direction: column; }
        #user-profile { padding: 15px; border-bottom: 1px solid #101921; font-weight: bold; color: #5eb5f7; }
        #chat-list { flex: 1; overflow-y: auto; }
        .chat-item { padding: 15px; border-bottom: 1px solid #101921; cursor: pointer; }
        .chat-item:hover { background: #202b36; }
        .chat-item.active { background: #2b5278; }
        /* Основной чат */
        #main { flex: 1; display: flex; flex-direction: column; background: #0e1621; }
        #header { padding: 15px; background: #17212b; border-bottom: 1px solid #101921; font-weight: bold; }
        #chat { flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; }
        .msg-container { display: flex; flex-direction: column; margin-bottom: 8px; max-width: 80%; }
        .my-msg-container { align-self: flex-end; }
        .other-msg-container { align-self: flex-start; }
        .msg { padding: 8px 12px; border-radius: 12px; font-size: 15px; word-wrap: break-word; }
        .my-msg { background: #2b5278; border-bottom-right-radius: 4px; }
        .other-msg { background: #182533; border-bottom-left-radius: 4px; }
        .nft-msg { background: #3e2723; border: 1px solid #ffd700; color: #ffd700; text-align: center; font-weight: bold; padding: 15px; border-radius: 8px; margin: 10px 0; }
        .name { font-size: 12px; color: #5eb5f7; margin-bottom: 2px; font-weight: 500; }
        #input-area { padding: 10px; background: #17212b; display: flex; gap: 10px; align-items: center; }
        #msg { flex: 1; padding: 12px 16px; border-radius: 20px; border: none; background: #242f3d; color: white; font-size: 16px; outline: none; }
        button { background: none; border: none; color: #5eb5f7; font-size: 24px; font-weight: bold; padding: 0 8px; cursor: pointer; }
        
        @media (max-width: 600px) {
            #sidebar { display: none; } /* На телефоне скрываем сайдбар, показываем только чат */
        }
    </style>
</head>
<body>
    <div id="sidebar">
        <div id="user-profile">Загрузка...</div>
        <div id="chat-list">
            <div class="chat-item active" onclick="switchChat('global')">🌍 Общий чат</div>
            <div class="chat-item" onclick="switchChat('admin')">👑 Админ (Только для тебя)</div>
        </div>
    </div>
    
    <div id="main">
        <div id="header">🌍 Общий чат</div>
        <div id="chat"></div>
        <div id="input-area">
            <input id="msg" type="text" placeholder="Message" autocomplete="off">
            <button onclick="send()">➤</button>
        </div>
    </div>

    <script>
        var myName = prompt("Enter your name:", "User");
        if (!myName) myName = "User";
        document.getElementById("user-profile").textContent = "👤 " + myName;
        
        var currentChat = "global";
        var ws = new WebSocket("wss://" + window.location.host + "/ws?username=" + myName);
        
        ws.onmessage = function(event) {
            var data = JSON.parse(event.data);
            
            // Если сообщение для другого чата - игнорируем
            if (data.chat !== currentChat) return;
            
            var chatDiv = document.getElementById("chat");
            var container = document.createElement("div");
            
            // NFT рендер
            if (data.type === "nft") {
                container.className = "nft-msg";
                container.innerHTML = "🎁 NFT: " + data.text + "<br><span style='font-size:12px;color:#fff'>От: " + data.user + "</span>";
                chatDiv.appendChild(container);
                chatDiv.scrollTop = chatDiv.scrollHeight;
                return;
            }
            
            container.className = "msg-container " + (data.user === myName ? "my-msg-container" : "other-msg-container");
            var msgDiv = document.createElement("div");
            msgDiv.className = "msg " + (data.user === myName ? "my-msg" : "other-msg");
            
            if (data.user !== myName) {
                var nameSpan = document.createElement("div");
                nameSpan.className = "name";
                nameSpan.textContent = data.user;
                msgDiv.appendChild(nameSpan);
            }
            
            var textSpan = document.createElement("div");
            textSpan.textContent = data.text;
            msgDiv.appendChild(textSpan);
            container.appendChild(msgDiv);
            
            chatDiv.appendChild(container);
            chatDiv.scrollTop = chatDiv.scrollHeight;
        };

        function switchChat(chatName) {
            currentChat = chatName;
            document.getElementById("header").textContent = chatName === 'global' ? "🌍 Общий чат" : "👑 Админ";
            document.getElementById("chat").innerHTML = ""; // Очищаем экран
            ws.send(JSON.stringify({ action: "get_history", chat: currentChat }));
        }

        function send() {
            var input = document.getElementById("msg");
            var text = input.value;
            if (!text) return;

            var payload = { user: myName, text: text, chat: currentChat, type: "text" };
            
            // Если админ пишет /nft
            if (myName === "sabhail" && text.startsWith("/nft")) {
                payload.text = text.replace("/nft ", "");
                payload.type = "nft";
            }
            
            if (ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify(payload));
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

# База данных в памяти (для теста)
chat_history = {"global": [], "admin": []}

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await websocket.accept()
    active_connections[websocket] = username
    
    try:
        while True:
            data = await websocket.receive_text()
            parsed = json.loads(data)
            
            # Если клиент запросил историю
            if parsed.get("action") == "get_history":
                chat_name = parsed.get("chat", "global")
                for msg in chat_history[chat_name]:
                    await websocket.send_json(msg)
                continue
            
            # Если это новое сообщение
            chat_name = parsed.get("chat", "global")
            message = {
                "user": parsed["user"],
                "text": parsed["text"],
                "type": parsed.get("type", "text"),
                "chat": chat_name
            }
            
            # Сохраняем в историю
            chat_history[chat_name].append(message)
            
            # Рассылаем всем
            for conn in active_connections.keys():
                try:
                    await conn.send_json(message)
                except:
                    pass
    except WebSocketDisconnect:
        if websocket in active_connections:
            del active_connections[websocket]х
