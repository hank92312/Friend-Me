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
                if room_id in manager.room_answers: manager.room_answers[room_id] = {}
                if room_id in manager.room_guesses: manager.room_guesses[room_id] = {}
                await manager.broadcast_to_room(room_id, {
                    "event": "phase_changed",
                    "new_phase": "ANSWERING",
                    "level": data.get("level"),
                    "question": data.get("question")
                })
            
            # 範例：房主開始遊戲
            elif data.get("event") == "start_game":
                captain = manager.room_captains.get(room_id)
                await manager.broadcast_to_room(room_id, {
                    "event": "phase_changed",
                    "new_phase": "SELECTION",
                    "captain": captain
                })
            
            # 實作：提交答案事件
            elif data.get("event") == "answer_submitted":
                answer = data.get("answer", "")
                all_done = await manager.submit_answer(room_id, player_name, answer)
                
                # 廣播「某人已提交」
                await manager.broadcast_to_room(room_id, {
                    "event": "player_submitted_status",
                    "player": player_name,
                    "count": len(manager.room_answers.get(room_id, {}))
                })

                if all_done:
                    await manager.broadcast_to_room(room_id, {
                        "event": "phase_changed",
                        "new_phase": "GUESSING",
                        "answers": manager.room_answers[room_id]
                    })
            
            # 實作：提交猜測結果
            elif data.get("event") == "guesses_submitted":
                guesses = data.get("guesses", {})
                all_done = await manager.submit_guesses(room_id, player_name, guesses)
                
                if all_done:
                    # 全員完成配對，廣播進入揭曉階段
                    await manager.broadcast_to_room(room_id, {
                        "event": "phase_changed",
                        "new_phase": "REVELATION",
                        "all_guesses": manager.room_guesses[room_id],
                        "all_answers": manager.room_answers[room_id]
                    })
            
            # 實作：再玩一輪（換隊長）
            elif data.get("event") == "next_round":
                new_captain = manager.rotate_captain(room_id)
                await manager.broadcast_to_room(room_id, {
                    "event": "phase_changed",
                    "new_phase": "SELECTION",
                    "captain": new_captain
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id, player_name)
        await manager.broadcast_to_room(room_id, {
            "event": "player_list_updated",
            "players": manager.room_players.get(room_id, [])
        })
