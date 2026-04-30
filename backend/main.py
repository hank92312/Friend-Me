from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from room_manager import manager
import uuid

app = FastAPI()

# --- REST API: 處理房間建立與加入 ---

@app.post("/create_room")
async def create_room(player_name: str):
    # 隨機產生一個 6 位數房間 ID (簡化版)
    room_id = str(uuid.uuid4())[:6].upper()
    return {
        "status": "success",
        "room_id": room_id,
        "message": f"Room {room_id} created by {player_name}"
    }

@app.post("/join_room")
async def join_room(room_id: str, player_name: str):
    # 實際開發時這裡會檢查房間是否存在於資料庫或 Redis
    return {
        "status": "success",
        "room_id": room_id,
        "player_name": player_name
    }

# --- WebSocket: 處理房間內的即時互動 ---

@app.websocket("/ws/{room_id}/{player_name}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, player_name: str):
    await manager.connect(websocket, room_id, player_name)
    
    # 廣播更新後的完整玩家清單
    await manager.broadcast_to_room(room_id, {
        "event": "player_list_updated",
        "players": manager.room_players.get(room_id, [])
    })
    
    try:
        while True:
            # 接收來自 Godot 的訊息
            data = await websocket.receive_json()
            
            # 範例：轉發隊長選題事件
            if data.get("event") == "topic_selected":
                await manager.broadcast_to_room(room_id, {
                    "event": "phase_changed",
                    "new_phase": "ANSWERING",
                    "level": data.get("level"),
                    "question": data.get("question")
                })
            
            # 範例：房主開始遊戲
            elif data.get("event") == "start_game":
                await manager.broadcast_to_room(room_id, {
                    "event": "phase_changed",
                    "new_phase": "SELECTION"
                })
            
            # 範例：轉發提交答案事件
            elif data.get("event") == "answer_submitted":
                await manager.broadcast_to_room(room_id, {
                    "event": "update_status",
                    "player": player_name,
                    "action": "submitted"
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id, player_name)
        await manager.broadcast_to_room(room_id, {
            "event": "player_list_updated",
            "players": manager.room_players.get(room_id, [])
        })
