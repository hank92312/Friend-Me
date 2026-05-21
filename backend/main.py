from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from room_manager import manager
import uuid
from database import AsyncSessionLocal, init_db
from sqlalchemy import select
import models
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動時：自動建表
    await init_db()
    yield
    # 關閉時：可以在此處清理資源

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REST API: 處理房間建立與加入 ---

@app.post("/create_room")
async def create_room(player_name: str):
    # 隨機產生一個 6 位數房間 ID
    room_id = str(uuid.uuid4())[:6].upper()
    # 在 manager 預註冊房間（防止加入者在房主連線前被擋掉）
    manager.create_room_id(room_id)
    return {
        "status": "success",
        "room_id": room_id,
        "message": f"Room {room_id} created by {player_name}"
    }

@app.post("/join_room")
async def join_room(room_id: str, player_name: str):
    if room_id not in manager.room_states:
        return {
            "status": "error",
            "message": "房間不存在，請確認房號是否正確。"
        }
    
    return {
        "status": "success",
        "room_id": room_id,
        "player_name": player_name
    }

@app.get("/check_room/{room_id}")
async def check_room(room_id: str):
    if room_id not in manager.room_states:
        return {"exists": False}
    return {"exists": True}

@app.get("/player/{player_name}/stats")
async def get_player_stats(player_name: str):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(models.User).where(models.User.name == player_name))
        user = result.scalars().first()
        
        if not user:
            return {"status": "error", "message": "Player not found"}
            
        return {
            "status": "success",
            "name": user.name,
            "total_guesses": user.total_guesses,
            "correct_guesses": user.correct_guesses,
            "total_disclosures": user.total_disclosures,
            "recognized_disclosures": user.recognized_disclosures
        }

# --- WebSocket: 處理房間內的即時互動 ---

@app.websocket("/ws/{room_id}/{player_name}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, player_name: str):
    # 嘗試重連（若為斷線重連，回傳 True）
    is_reconnect = await manager.reconnect(websocket, room_id, player_name)

    if not is_reconnect:
        # 全新加入
        await manager.connect(websocket, room_id, player_name)

    # 廣播更新後的完整玩家清單（全員可見）
    all_names = manager.room_players.get(room_id, [])
    active_names = manager.get_active_player_names(room_id)
    await manager.broadcast_to_room(room_id, {
        "event": "player_list_updated",
        "players": active_names  # 只顯示連線中的玩家
    })

    if is_reconnect:
        # 告知重連玩家目前的房間狀態
        current_phase = manager.room_states.get(room_id, {}).get("phase", "WAITING")
        captain = manager.room_captains.get(room_id, "")
        await manager.send_to_player(room_id, player_name, {
            "event": "reconnect_status",
            "current_phase": current_phase,
            "captain": captain,
            "message": "重連成功！等待本輪結束後一起加入下一輪。"
        })

    try:
        while True:
            data = await websocket.receive_json()

            # 房主開始遊戲
            if data.get("event") == "start_game":
                captain = manager.room_captains.get(room_id)
                manager.room_states[room_id]["phase"] = "SELECTION"
                await manager.broadcast_to_room(room_id, {
                    "event": "phase_changed",
                    "new_phase": "SELECTION",
                    "captain": captain
                })

            # 隊長選題
            elif data.get("event") == "topic_selected":
                if room_id in manager.room_answers:
                    manager.room_answers[room_id] = {}
                if room_id in manager.room_guesses:
                    manager.room_guesses[room_id] = {}
                
                # 在資料庫建立這一輪
                question = data.get("question", "")
                level = data.get("level", 1)
                captain = manager.room_captains.get(room_id)
                await manager.create_round(room_id, question, level, captain)

                manager.room_states[room_id]["phase"] = "ANSWERING"
                await manager.broadcast_to_room(room_id, {
                    "event": "phase_changed",
                    "new_phase": "ANSWERING",
                    "level": level,
                    "question": question
                })

            # 提交答案
            elif data.get("event") == "answer_submitted":
                answer = data.get("answer", "")
                all_done = await manager.submit_answer(room_id, player_name, answer)

                # 廣播提交狀態
                active_names = manager.get_active_player_names(room_id)
                waiting = manager.waiting_for_next_round.get(room_id, [])
                eligible_count = len([n for n in active_names if n not in waiting])
                await manager.broadcast_to_room(room_id, {
                    "event": "player_submitted_status",
                    "player": player_name,
                    "submitted": len(manager.room_answers.get(room_id, {})),
                    "total": eligible_count
                })

                if all_done:
                    manager.room_states[room_id]["phase"] = "GUESSING"
                    await manager.broadcast_to_room(room_id, {
                        "event": "phase_changed",
                        "new_phase": "GUESSING",
                        "answers": manager.room_answers[room_id]
                    })

            # 提交猜測結果
            elif data.get("event") == "guesses_submitted":
                guesses = data.get("guesses", {})
                all_done = await manager.submit_guesses(room_id, player_name, guesses)

                if all_done:
                    manager.room_states[room_id]["phase"] = "REVELATION"
                    
                    # 抓取目前連線中所有玩家的最新累計數據
                    active_players = manager.get_active_player_names(room_id)
                    all_stats = {}
                    async with AsyncSessionLocal() as db:
                        for name in active_players:
                            res = await db.execute(select(models.User).where(models.User.name == name))
                            u = res.scalars().first()
                            if u:
                                all_stats[name] = {
                                    "total_guesses": u.total_guesses,
                                    "correct_guesses": u.correct_guesses,
                                    "total_disclosures": u.total_disclosures,
                                    "recognized_disclosures": u.recognized_disclosures
                                }

                    await manager.broadcast_to_room(room_id, {
                        "event": "phase_changed",
                        "new_phase": "REVELATION",
                        "all_guesses": manager.room_guesses[room_id],
                        "all_answers": manager.room_answers[room_id],
                        "player_stats": all_stats
                    })

            # 準備接續下一輪
            elif data.get("event") == "ready_for_next_round":
                if room_id not in manager.room_ready_players:
                    manager.room_ready_players[room_id] = set()
                manager.room_ready_players[room_id].add(player_name)
                
                active_names = manager.get_active_player_names(room_id)
                ready_count = len(manager.room_ready_players[room_id])
                total_count = len(active_names)
                
                await manager.broadcast_to_room(room_id, {
                    "event": "next_round_status",
                    "ready": ready_count,
                    "total": total_count
                })
                
                if ready_count >= total_count and total_count > 0:
                    # 所有人準備完畢，進入下一輪
                    new_captain = manager.rotate_captain(room_id)
                    manager.room_states[room_id]["phase"] = "SELECTION"
                    active_names = manager.get_active_player_names(room_id)
                    await manager.broadcast_to_room(room_id, {
                        "event": "phase_changed",
                        "new_phase": "SELECTION",
                        "captain": new_captain,
                        "players": active_names
                    })

            # 再玩一輪（換隊長，舊版保留相容性或可移除，但為了安全先保留）
            elif data.get("event") == "next_round":
                new_captain = manager.rotate_captain(room_id)
                manager.room_states[room_id]["phase"] = "SELECTION"
                active_names = manager.get_active_player_names(room_id)
                await manager.broadcast_to_room(room_id, {
                    "event": "phase_changed",
                    "new_phase": "SELECTION",
                    "captain": new_captain,
                    "players": active_names
                })

            # 離開房間
            elif data.get("event") == "leave_room":
                await manager.leave_room(room_id, player_name)
                # 斷開 WebSocket
                break

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id, player_name)
        active_names = manager.get_active_player_names(room_id)
        await manager.broadcast_to_room(room_id, {
            "event": "player_list_updated",
            "players": active_names
        })
        # 若該玩家是等待提交的一員，檢查是否可以繼續推進階段
        await _check_phase_progress_after_disconnect(room_id)

async def _check_phase_progress_after_disconnect(room_id: str):
    """
    玩家斷線後，重新檢查目前階段是否可以因人數減少而推進。
    避免「某玩家斷線後，其他玩家全都卡在等待」的情況。
    """
    current_phase = manager.room_states.get(room_id, {}).get("phase", "WAITING")

    if current_phase == "ANSWERING":
        # 重新檢查是否全員已提交答案
        active_names = manager.get_active_player_names(room_id)
        waiting = manager.waiting_for_next_round.get(room_id, [])
        eligible = [n for n in active_names if n not in waiting]
        submitted = manager.room_answers.get(room_id, {})
        if eligible and all(n in submitted for n in eligible):
            manager.room_states[room_id]["phase"] = "GUESSING"
            await manager.broadcast_to_room(room_id, {
                "event": "phase_changed",
                "new_phase": "GUESSING",
                "answers": manager.room_answers[room_id]
            })

    elif current_phase == "GUESSING":
        active_names = manager.get_active_player_names(room_id)
        waiting = manager.waiting_for_next_round.get(room_id, [])
        eligible = [n for n in active_names if n not in waiting]
        submitted = manager.room_guesses.get(room_id, {})
        if eligible and all(n in submitted for n in eligible):
            manager.room_states[room_id]["phase"] = "REVELATION"
            
            # 同樣需要抓取累計數據
            all_stats = {}
            async with AsyncSessionLocal() as db:
                for name in active_names:
                    res = await db.execute(select(models.User).where(models.User.name == name))
                    u = res.scalars().first()
                    if u:
                        all_stats[name] = {
                            "total_guesses": u.total_guesses,
                            "correct_guesses": u.correct_guesses,
                            "total_disclosures": u.total_disclosures,
                            "recognized_disclosures": u.recognized_disclosures
                        }

            await manager.broadcast_to_room(room_id, {
                "event": "phase_changed",
                "new_phase": "REVELATION",
                "all_guesses": manager.room_guesses[room_id],
                "all_answers": manager.room_answers[room_id],
                "player_stats": all_stats
            })

    elif current_phase == "REVELATION":
        # 檢查是否剩下的人都已經 ready
        active_names = manager.get_active_player_names(room_id)
        # 移除斷線玩家的 ready 狀態
        ready_players = manager.room_ready_players.get(room_id, set())
        ready_players = {p for p in ready_players if p in active_names}
        manager.room_ready_players[room_id] = ready_players
        
        ready_count = len(ready_players)
        total_count = len(active_names)
        
        if total_count > 0:
            await manager.broadcast_to_room(room_id, {
                "event": "next_round_status",
                "ready": ready_count,
                "total": total_count
            })
            
            if ready_count >= total_count:
                new_captain = manager.rotate_captain(room_id)
                manager.room_states[room_id]["phase"] = "SELECTION"
                active_names = manager.get_active_player_names(room_id)
                await manager.broadcast_to_room(room_id, {
                    "event": "phase_changed",
                    "new_phase": "SELECTION",
                    "captain": new_captain,
                    "players": active_names
                })
