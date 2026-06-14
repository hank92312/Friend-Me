from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from room_manager import manager
import uuid
import asyncio
import time
import json as json_module
import random
import os
from database import AsyncSessionLocal, init_db
from sqlalchemy import select
import models
from contextlib import asynccontextmanager

countdown_tasks: dict[str, asyncio.Task] = {}
phase_timeout_tasks: dict[str, asyncio.Task] = {}

# 載入題庫供超時自動選題用
question_bank = {}
def load_question_bank():
    global question_bank
    # 嘗試從多個可能的路徑載入
    paths = [
        os.path.join(os.path.dirname(__file__), "data", "question_bank.json"),
        os.path.join(os.path.dirname(__file__), "..", "FriendAndMe", "data", "question_bank.json"),
        os.path.join(os.path.dirname(__file__), "..", "friendAndme", "data", "question_bank.json"),
    ]
    for path in paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json_module.load(f)
                question_bank = data.get("levels", {})
                print(f"[QuestionBank] Loaded {len(question_bank)} levels from {path}")
                return
    print("[QuestionBank] WARNING: question_bank.json not found!")

def get_random_question_from_bank():
    """從題庫隨機選一個 level 和問題"""
    if not question_bank:
        return 1, "(自動選題 - 題庫未載入)"
    level_key = random.choice(list(question_bank.keys()))
    level = int(level_key)
    questions = question_bank[level_key].get("questions", [])
    if not questions:
        return level, "(自動選題 - 無題目)"
    q = random.choice(questions)
    return level, q.get("text", "(自動選題)")

def start_phase_timeout(room_id: str, phase: str, seconds: int = 60):
    """啟動一個階段超時任務，超時後自動推進"""
    cancel_phase_timeout(room_id)
    task = asyncio.create_task(run_phase_timeout(room_id, phase, seconds))
    phase_timeout_tasks[room_id] = task

def cancel_phase_timeout(room_id: str):
    """取消該房間的超時任務"""
    task = phase_timeout_tasks.pop(room_id, None)
    if task and not task.done():
        task.cancel()

async def run_phase_timeout(room_id: str, phase: str, seconds: int):
    """等待 seconds 秒後，根據 phase 自動推進"""
    try:
        await asyncio.sleep(seconds)
        current_phase = manager.room_states.get(room_id, {}).get("phase", "")
        if current_phase != phase:
            return  # 階段已被手動推進，不再處理

        print(f"[PhaseTimeout] Room {room_id} phase {phase} timed out after {seconds}s. Auto-advancing...")

        if phase == "SELECTION":
            # 自動選題
            level, question = get_random_question_from_bank()
            captain = manager.room_captains.get(room_id, "")
            if room_id in manager.room_answers:
                manager.room_answers[room_id] = {}
            if room_id in manager.room_guesses:
                manager.room_guesses[room_id] = {}
            await manager.create_round(room_id, question, level, captain)
            manager.room_states[room_id]["phase"] = "ANSWERING"
            manager.room_states[room_id]["started_at"] = time.time()
            await manager.broadcast_to_room(room_id, {
                "event": "phase_changed",
                "new_phase": "ANSWERING",
                "level": level,
                "question": question,
                "remaining_seconds": 120
            })
            start_phase_timeout(room_id, "ANSWERING", 120)

        elif phase == "ANSWERING":
            # 自動提交空答案
            active_names = manager.get_active_player_names(room_id)
            waiting = manager.waiting_for_next_round.get(room_id, [])
            eligible = [n for n in active_names if n not in waiting]
            submitted = manager.room_answers.get(room_id, {})
            for name in eligible:
                if name not in submitted:
                    # 時間到未作答者，視同選擇「不回答」（可正確翻譯並作為配對干擾項）
                    await manager.submit_answer(room_id, name, "不回答")
            manager.room_states[room_id]["phase"] = "GUESSING"
            manager.room_states[room_id]["started_at"] = time.time()
            await manager.broadcast_to_room(room_id, {
                "event": "phase_changed",
                "new_phase": "GUESSING",
                "answers": manager.room_answers[room_id],
                "remaining_seconds": 60
            })
            start_phase_timeout(room_id, "GUESSING", 60)

        elif phase == "GUESSING":
            # 自動提交空配對
            active_names = manager.get_active_player_names(room_id)
            waiting = manager.waiting_for_next_round.get(room_id, [])
            eligible = [n for n in active_names if n not in waiting]
            submitted = manager.room_guesses.get(room_id, {})
            for name in eligible:
                if name not in submitted:
                    await manager.submit_guesses(room_id, name, {})
            manager.room_states[room_id]["phase"] = "REVELATION"
            manager.room_states[room_id]["started_at"] = time.time()
            
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
                "all_guesses": manager.room_guesses.get(room_id, {}),
                "all_answers": manager.room_answers.get(room_id, {}),
                "player_stats": all_stats,
                "remaining_seconds": 120
            })
            start_phase_timeout(room_id, "REVELATION", 120)

        elif phase == "REVELATION":
            # 強制進入下一輪
            if room_id in countdown_tasks:
                countdown_tasks[room_id].cancel()
                countdown_tasks.pop(room_id, None)
            new_captain = manager.rotate_captain(room_id)
            manager.room_states[room_id]["phase"] = "SELECTION"
            manager.room_states[room_id]["started_at"] = time.time()
            active_names = manager.get_active_player_names(room_id)
            manager.room_ready_players[room_id] = set()
            await manager.broadcast_to_room(room_id, {
                "event": "phase_changed",
                "new_phase": "SELECTION",
                "captain": new_captain,
                "players": active_names,
                "remaining_seconds": 60
            })
            start_phase_timeout(room_id, "SELECTION", 60)

    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"[PhaseTimeout] Error in room {room_id} phase {phase}: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動時：自動建表
    await init_db()
    load_question_bank()
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

async def start_next_round_countdown(room_id: str):
    try:
        # 倒數 10 秒
        for seconds_left in range(10, 0, -1):
            await manager.broadcast_to_room(room_id, {
                "event": "next_round_countdown",
                "seconds": seconds_left
            })
            await asyncio.sleep(1)
        
        # 倒數結束，強制進入下一輪
        print(f"[Countdown Force] Room {room_id} next round countdown finished. Forcing next round.")
        new_captain = manager.rotate_captain(room_id)
        manager.room_states[room_id]["phase"] = "SELECTION"
        manager.room_states[room_id]["started_at"] = time.time()
        active_names = manager.get_active_player_names(room_id)
        await manager.broadcast_to_room(room_id, {
            "event": "phase_changed",
            "new_phase": "SELECTION",
            "captain": new_captain,
            "players": active_names,
            "remaining_seconds": 60
        })
        countdown_tasks.pop(room_id, None)
        cancel_phase_timeout(room_id)
        start_phase_timeout(room_id, "SELECTION", 60)
    except asyncio.CancelledError:
        print(f"[Countdown Cancelled] Room {room_id} next round countdown cancelled.")
        pass

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
        
        # 計算剩餘時間
        started_at = manager.room_states.get(room_id, {}).get("started_at", time.time())
        duration = 120 if current_phase in ("REVELATION", "ANSWERING") else 60
        remaining = max(0, duration - int(time.time() - started_at))
            
        await manager.send_to_player(room_id, player_name, {
            "event": "reconnect_status",
            "current_phase": current_phase,
            "captain": captain,
            "remaining_seconds": remaining,
            "message": "重連成功！等待本輪結束後一起加入下一輪。"
        })

    try:
        while True:
            data = await websocket.receive_json()

            # 房主開始遊戲
            if data.get("event") == "start_game":
                captain = manager.room_captains.get(room_id)
                manager.room_states[room_id]["phase"] = "SELECTION"
                manager.room_states[room_id]["started_at"] = time.time()
                await manager.broadcast_to_room(room_id, {
                    "event": "phase_changed",
                    "new_phase": "SELECTION",
                    "captain": captain,
                    "remaining_seconds": 60
                })
                start_phase_timeout(room_id, "SELECTION", 60)

            # 隊長選題
            elif data.get("event") == "topic_selected":
                # 階段守衛：只在 SELECTION 階段接受選題，忽略過期/重複事件
                if manager.room_states.get(room_id, {}).get("phase") != "SELECTION":
                    continue
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
                manager.room_states[room_id]["started_at"] = time.time()
                
                await manager.broadcast_to_room(room_id, {
                    "event": "phase_changed",
                    "new_phase": "ANSWERING",
                    "level": level,
                    "question": question,
                    "remaining_seconds": 120
                })
                cancel_phase_timeout(room_id)  # 取消 SELECTION 超時
                start_phase_timeout(room_id, "ANSWERING", 120)

            # 提交答案
            elif data.get("event") == "answer_submitted":
                # 階段守衛：只在 ANSWERING 階段接受答案。
                # 擋掉背景分頁殘留計時器送來的過期答案，避免階段從
                # REVELATION/GUESSING 被強制退回 GUESSING。
                if manager.room_states.get(room_id, {}).get("phase") != "ANSWERING":
                    continue
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
                    cancel_phase_timeout(room_id)  # 取消 ANSWERING 超時
                    manager.room_states[room_id]["phase"] = "GUESSING"
                    manager.room_states[room_id]["started_at"] = time.time()
                    await manager.broadcast_to_room(room_id, {
                        "event": "phase_changed",
                        "new_phase": "GUESSING",
                        "answers": manager.room_answers[room_id],
                        "remaining_seconds": 60
                    })
                    start_phase_timeout(room_id, "GUESSING", 60)

            # 提交猜測結果
            elif data.get("event") == "guesses_submitted":
                # 階段守衛：只在 GUESSING 階段接受配對。
                # 擋掉過期/重複配對，避免 _persist_round_results 二次寫入
                # 資料庫造成猜對猜錯次數重複計算。
                if manager.room_states.get(room_id, {}).get("phase") != "GUESSING":
                    continue
                guesses = data.get("guesses", {})
                all_done = await manager.submit_guesses(room_id, player_name, guesses)

                if all_done:
                    manager.room_states[room_id]["phase"] = "REVELATION"
                    manager.room_states[room_id]["started_at"] = time.time()
                    
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
                        "player_stats": all_stats,
                        "remaining_seconds": 120
                    })
                    cancel_phase_timeout(room_id)  # 取消 GUESSING 超時
                    start_phase_timeout(room_id, "REVELATION", 120)

            # 準備接續下一輪
            elif data.get("event") == "ready_for_next_round":
                if room_id not in manager.room_ready_players:
                    manager.room_ready_players[room_id] = set()
                manager.room_ready_players[room_id].add(player_name)
                
                active_names = manager.get_active_player_names(room_id)
                waiting = manager.waiting_for_next_round.get(room_id, [])
                eligible = [n for n in active_names if n not in waiting]
                
                # 確保 ready_players 中只有 eligible 玩家
                ready_players = manager.room_ready_players.get(room_id, set())
                ready_players = {p for p in ready_players if p in eligible}
                manager.room_ready_players[room_id] = ready_players
                
                ready_count = len(ready_players)
                total_count = len(eligible)
                
                await manager.broadcast_to_room(room_id, {
                    "event": "next_round_status",
                    "ready": ready_count,
                    "total": total_count
                })
                
                if ready_count >= total_count and total_count > 0:
                    # 所有人準備完畢，立即進入下一輪
                    # 1. 取消可能存在的倒數計時
                    if room_id in countdown_tasks:
                        countdown_tasks[room_id].cancel()
                        countdown_tasks.pop(room_id, None)
                    
                    new_captain = manager.rotate_captain(room_id)
                    manager.room_states[room_id]["phase"] = "SELECTION"
                    manager.room_states[room_id]["started_at"] = time.time()
                    active_names = manager.get_active_player_names(room_id)
                    await manager.broadcast_to_room(room_id, {
                        "event": "phase_changed",
                        "new_phase": "SELECTION",
                        "captain": new_captain,
                        "players": active_names,
                        "remaining_seconds": 60
                    })
                    cancel_phase_timeout(room_id)  # 取消 REVELATION 超時
                    start_phase_timeout(room_id, "SELECTION", 60)
                elif ready_count >= total_count - 1 and total_count > 1:
                    # 剩下最後一個玩家未點擊，啟動 10 秒倒數計時
                    if room_id not in countdown_tasks:
                        print(f"[Countdown Start] Room {room_id} start next round countdown.")
                        task = asyncio.create_task(start_next_round_countdown(room_id))
                        countdown_tasks[room_id] = task

            # 再玩一輪（換隊長，舊版保留相容性或可移除，但為了安全先保留）
            elif data.get("event") == "next_round":
                new_captain = manager.rotate_captain(room_id)
                manager.room_states[room_id]["phase"] = "SELECTION"
                manager.room_states[room_id]["started_at"] = time.time()
                active_names = manager.get_active_player_names(room_id)
                await manager.broadcast_to_room(room_id, {
                    "event": "phase_changed",
                    "new_phase": "SELECTION",
                    "captain": new_captain,
                    "players": active_names,
                    "remaining_seconds": 60
                })
                cancel_phase_timeout(room_id)
                start_phase_timeout(room_id, "SELECTION", 60)

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
            manager.room_states[room_id]["started_at"] = time.time()
            await manager.broadcast_to_room(room_id, {
                "event": "phase_changed",
                "new_phase": "GUESSING",
                "answers": manager.room_answers[room_id],
                "remaining_seconds": 60
            })
            cancel_phase_timeout(room_id)
            start_phase_timeout(room_id, "GUESSING", 60)

    elif current_phase == "GUESSING":
        active_names = manager.get_active_player_names(room_id)
        waiting = manager.waiting_for_next_round.get(room_id, [])
        eligible = [n for n in active_names if n not in waiting]
        submitted = manager.room_guesses.get(room_id, {})
        if eligible and all(n in submitted for n in eligible):
            manager.room_states[room_id]["phase"] = "REVELATION"
            manager.room_states[room_id]["started_at"] = time.time()
            
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
                "player_stats": all_stats,
                "remaining_seconds": 120
            })
            cancel_phase_timeout(room_id)
            start_phase_timeout(room_id, "REVELATION", 120)

    elif current_phase == "REVELATION":
        # 檢查是否剩下的人都已經 ready
        active_names = manager.get_active_player_names(room_id)
        waiting = manager.waiting_for_next_round.get(room_id, [])
        eligible = [n for n in active_names if n not in waiting]
        
        # 移除斷線玩家的 ready 狀態
        ready_players = manager.room_ready_players.get(room_id, set())
        ready_players = {p for p in ready_players if p in eligible}
        manager.room_ready_players[room_id] = ready_players
        
        ready_count = len(ready_players)
        total_count = len(eligible)
        
        if total_count > 0:
            await manager.broadcast_to_room(room_id, {
                "event": "next_round_status",
                "ready": ready_count,
                "total": total_count
            })
            
            if ready_count >= total_count:
                # 所有人準備完畢，立即進入下一輪
                if room_id in countdown_tasks:
                    countdown_tasks[room_id].cancel()
                    countdown_tasks.pop(room_id, None)
                    
                new_captain = manager.rotate_captain(room_id)
                manager.room_states[room_id]["phase"] = "SELECTION"
                manager.room_states[room_id]["started_at"] = time.time()
                active_names = manager.get_active_player_names(room_id)
                await manager.broadcast_to_room(room_id, {
                    "event": "phase_changed",
                    "new_phase": "SELECTION",
                    "captain": new_captain,
                    "players": active_names,
                    "remaining_seconds": 60
                })
                cancel_phase_timeout(room_id)
                start_phase_timeout(room_id, "SELECTION", 60)
            elif ready_count >= total_count - 1 and total_count > 1:
                # 剩最後一個人，啟動倒數計時
                if room_id not in countdown_tasks:
                    print(f"[Countdown Start - Disconnect] Room {room_id} start next round countdown.")
                    task = asyncio.create_task(start_next_round_countdown(room_id))
                    countdown_tasks[room_id] = task
