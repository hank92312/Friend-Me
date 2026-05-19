from fastapi import WebSocket
import json
import time
from database import AsyncSessionLocal
from sqlalchemy import select, update
import models

class RoomConnectionManager:
    def __init__(self):
        # 結構：{ "room_id": [websocket1, websocket2, ...] }
        self.active_rooms: dict[str, list[WebSocket]] = {}
        # 結構：{ "room_id": [name1, name2, ...] } — 所有已加入（含斷線）的玩家
        self.room_players: dict[str, list[str]] = {}
        # 結構：{ "room_id": { player_name: websocket } } — 僅限目前連線中
        self.room_ws_map: dict[str, dict[str, WebSocket]] = {}
        # 額外儲存房間狀態
        self.room_states: dict[str, dict] = {}
        # 結構：{ "room_id": { "player1": "answer1", ... } }
        self.room_answers: dict[str, dict[str, str]] = {}
        # 結構：{ "room_id": { "player1": { "ans1": "p2", ... }, ... } }
        self.room_guesses: dict[str, dict[str, dict[str, str]]] = {}
        # 結構：{ "room_id": "current_captain_name" }
        self.room_captains: dict[str, str] = {}
        # 斷線玩家快取：{ "room_id": { player_name: { "disconnected_at": float, "phase": str } } }
        self.disconnected_players: dict[str, dict[str, dict]] = {}
        # 等待重連後加入下一輪的玩家：{ "room_id": [player_name, ...] }
        self.waiting_for_next_round: dict[str, list[str]] = {}
        # 準備好進入下一輪的玩家：{ "room_id": set(player_name, ...) }
        self.room_ready_players: dict[str, set[str]] = {}

    def create_room_id(self, room_id: str):
        """預先註冊房間 ID，供 REST API 使用"""
        if room_id not in self.room_states:
            self.room_states[room_id] = {"phase": "WAITING"}

    async def connect(self, websocket: WebSocket, room_id: str, player_name: str):
        await websocket.accept()
        
        # 確保玩家在資料庫中存在
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(models.User).where(models.User.name == player_name))
            user = result.scalars().first()
            if not user:
                user = models.User(name=player_name)
                db.add(user)
                await db.commit()

        if room_id not in self.active_rooms:
            self.active_rooms[room_id] = []
            self.room_players[room_id] = []
            self.room_ws_map[room_id] = {}
            self.room_states[room_id] = {"phase": "WAITING"}
            self.room_answers[room_id] = {}
            self.room_guesses[room_id] = {}
            self.room_captains[room_id] = player_name  # 房主預設是第一個隊長
            self.disconnected_players[room_id] = {}
            self.waiting_for_next_round[room_id] = []
            self.room_ready_players[room_id] = set()
            
            # 同步房間到資料庫
            async with AsyncSessionLocal() as db:
                room = models.Room(id=room_id, captain_name=player_name)
                db.add(room)
                await db.commit()

        self.active_rooms[room_id].append(websocket)
        self.room_ws_map[room_id][player_name] = websocket

        if player_name not in self.room_players[room_id]:
            self.room_players[room_id].append(player_name)

    async def reconnect(self, websocket: WebSocket, room_id: str, player_name: str) -> bool:
        """
        嘗試重連：若玩家曾存在於此房間（斷線快取中），恢復連線。
        遊戲繼續，重連玩家加入 waiting_for_next_round，等待本輪結束後一同參與。
        回傳 True 表示為重連，False 表示為全新加入。
        """
        is_reconnect = (
            room_id in self.disconnected_players and
            player_name in self.disconnected_players[room_id]
        )

        if is_reconnect:
            # 清除斷線快取
            del self.disconnected_players[room_id][player_name]
            # 更新 websocket 對應
            self.active_rooms[room_id].append(websocket)
            self.room_ws_map[room_id][player_name] = websocket
            # 加入「等待下一輪」名單（若遊戲進行中）
            current_phase = self.room_states.get(room_id, {}).get("phase", "WAITING")
            if current_phase not in ("WAITING", "SELECTION"):
                if player_name not in self.waiting_for_next_round.get(room_id, []):
                    self.waiting_for_next_round[room_id].append(player_name)
            return True

        return False

    def get_active_player_count(self, room_id: str) -> int:
        """取得目前連線中的玩家數（不含斷線者）"""
        return len(self.active_rooms.get(room_id, []))

    def get_active_player_names(self, room_id: str) -> list[str]:
        """取得目前連線中的玩家名單"""
        ws_map = self.room_ws_map.get(room_id, {})
        active_ws_set = set(self.active_rooms.get(room_id, []))
        return [name for name, ws in ws_map.items() if ws in active_ws_set]

    async def submit_answer(self, room_id: str, player_name: str, answer: str) -> bool:
        if room_id not in self.room_answers:
            self.room_answers[room_id] = {}

        self.room_answers[room_id][player_name] = answer

        # 只計算目前連線中（且未在等待清單中）的玩家
        active_names = self.get_active_player_names(room_id)
        waiting = self.waiting_for_next_round.get(room_id, [])
        eligible = [n for n in active_names if n not in waiting]

        submitted_count = len(self.room_answers.get(room_id, {}))
        return submitted_count >= len(eligible)

    async def submit_guesses(self, room_id: str, player_name: str, guesses: dict) -> bool:
        if room_id not in self.room_guesses:
            self.room_guesses[room_id] = {}

        self.room_guesses[room_id][player_name] = guesses

        # 只計算目前連線中（且未在等待清單中）的玩家
        active_names = self.get_active_player_names(room_id)
        waiting = self.waiting_for_next_round.get(room_id, [])
        eligible = [n for n in active_names if n not in waiting]

        submitted_count = len(self.room_guesses.get(room_id, {}))
        
        # 如果全員提交，結算並存入資料庫
        if submitted_count >= len(eligible):
            await self._persist_round_results(room_id)
            return True
        return False

    async def _persist_round_results(self, room_id: str):
        """結算本輪並將數據永久化到資料庫"""
        answers = self.room_answers.get(room_id, {})
        guesses = self.room_guesses.get(room_id, {})
        state = self.room_states.get(room_id, {})
        round_id = state.get("current_round_id")
        
        if not round_id:
            return

        async with AsyncSessionLocal() as db:
            # 1. 儲存所有答案
            for player, content in answers.items():
                ans_obj = models.Answer(round_id=round_id, player_name=player, content=content)
                db.add(ans_obj)
                
                # 更新玩家的「被猜測次數」（揭露數）
                await db.execute(
                    update(models.User)
                    .where(models.User.name == player)
                    .values(total_disclosures=models.User.total_disclosures + 1)
                )

            # 2. 儲存所有猜測並計算正確率
            for guesser, guess_map in guesses.items():
                for ans_content, target_name in guess_map.items():
                    # 檢查是否猜對
                    actual_owner = next((p for p, a in answers.items() if a == ans_content), None)
                    is_correct = (actual_owner == target_name)
                    
                    guess_obj = models.Guess(
                        round_id=round_id,
                        guesser_name=guesser,
                        target_name=target_name,
                        is_correct=is_correct
                    )
                    db.add(guess_obj)
                    
                    # 更新猜測者的累計數據
                    await db.execute(
                        update(models.User)
                        .where(models.User.name == guesser)
                        .values(
                            total_guesses=models.User.total_guesses + 1,
                            correct_guesses=models.User.correct_guesses + (1 if is_correct else 0)
                        )
                    )
                    
                    # 如果猜對了，更新被猜中者的「被識別次數」
                    if is_correct:
                        await db.execute(
                            update(models.User)
                            .where(models.User.name == target_name)
                            .values(recognized_disclosures=models.User.recognized_disclosures + 1)
                        )
            
            await db.commit()

    async def create_round(self, room_id: str, question: str, level: int, captain: str):
        """建立新的一輪紀錄"""
        async with AsyncSessionLocal() as db:
            new_round = models.Round(
                room_id=room_id,
                question_text=question,
                level=level,
                captain_name=captain
            )
            db.add(new_round)
            await db.commit()
            await db.refresh(new_round)
            
            if room_id not in self.room_states:
                self.room_states[room_id] = {}
            self.room_states[room_id]["current_round_id"] = new_round.id
            return new_round.id

    def rotate_captain(self, room_id: str) -> str | None:
        if room_id not in self.room_players:
            return None

        # 換隊長：從目前連線玩家中輪替
        active = self.get_active_player_names(room_id)
        if not active:
            return None

        current = self.room_captains.get(room_id)
        try:
            idx = active.index(current)
            new_idx = (idx + 1) % len(active)
            new_captain = active[new_idx]
        except ValueError:
            new_captain = active[0]

        self.room_captains[room_id] = new_captain

        # 等待清單的玩家可以重新加入下一輪
        self.waiting_for_next_round[room_id] = []
        # 重置準備狀態
        self.room_ready_players[room_id] = set()
        # 重置答案與猜測
        self.room_answers[room_id] = {}
        self.room_guesses[room_id] = {}

        return new_captain

    def disconnect(self, websocket: WebSocket, room_id: str, player_name: str):
        if room_id in self.active_rooms:
            if websocket in self.active_rooms[room_id]:
                self.active_rooms[room_id].remove(websocket)
            if room_id in self.room_ws_map and player_name in self.room_ws_map[room_id]:
                del self.room_ws_map[room_id][player_name]

            # 標記斷線（保留在 room_players，快取到 disconnected_players）
            current_phase = self.room_states.get(room_id, {}).get("phase", "WAITING")
            if room_id not in self.disconnected_players:
                self.disconnected_players[room_id] = {}
            self.disconnected_players[room_id][player_name] = {
                "disconnected_at": time.time(),
                "phase": current_phase
            }

            # 若房間已無任何連線（含斷線快取均空），才清除房間
            if not self.active_rooms[room_id] and not self.disconnected_players.get(room_id):
                self._cleanup_room(room_id)

    def _cleanup_room(self, room_id: str):
        # 移除所有內存資料
        for d in [self.active_rooms, self.room_players, self.room_ws_map,
                  self.room_states, self.room_answers, self.room_guesses,
                  self.room_captains, self.disconnected_players, self.waiting_for_next_round,
                  self.room_ready_players]:
            d.pop(room_id, None)
        
        # 啟動非同步任務清除資料庫中的房間數據
        import asyncio
        asyncio.create_task(self._delete_room_data_from_db(room_id))

    async def _delete_room_data_from_db(self, room_id: str):
        """從資料庫刪除指定房間及其所有關聯的回合、答案與猜測"""
        async with AsyncSessionLocal() as db:
            from sqlalchemy import delete
            
            # 1. 找出所有屬於該房間的 round_ids
            res = await db.execute(select(models.Round.id).where(models.Round.room_id == room_id))
            round_ids = res.scalars().all()
            
            if round_ids:
                # 2. 刪除相關的 Guess 與 Answer
                await db.execute(delete(models.Guess).where(models.Guess.round_id.in_(round_ids)))
                await db.execute(delete(models.Answer).where(models.Answer.round_id.in_(round_ids)))
                # 3. 刪除 Round
                await db.execute(delete(models.Round).where(models.Round.id.in_(round_ids)))
            
            # 4. 最後刪除 Room
            await db.execute(delete(models.Room).where(models.Room.id == room_id))
            
            await db.commit()
            print(f"[Database] Room {room_id} and all related data deleted.")

    async def leave_room(self, room_id: str, player_name: str):
        """玩家主動離開房間"""
        if room_id in self.room_ws_map and player_name in self.room_ws_map[room_id]:
            ws = self.room_ws_map[room_id][player_name]
            if room_id in self.active_rooms and ws in self.active_rooms[room_id]:
                self.active_rooms[room_id].remove(ws)
            del self.room_ws_map[room_id][player_name]
        
        if room_id in self.room_players and player_name in self.room_players[room_id]:
            self.room_players[room_id].remove(player_name)
            
        # 如果房間已空，執行清除
        if not self.active_rooms.get(room_id):
            self._cleanup_room(room_id)
        else:
            # 廣播名單更新
            await self.broadcast_to_room(room_id, {
                "event": "player_list_updated",
                "players": self.get_active_player_names(room_id)
            })

    async def broadcast_to_room(self, room_id: str, message: dict):
        if room_id in self.active_rooms:
            for connection in list(self.active_rooms[room_id]):
                try:
                    await connection.send_json(message)
                except Exception:
                    pass  # 斷線中的連線會在 disconnect handler 處理

    async def send_to_player(self, room_id: str, player_name: str, message: dict):
        """單獨向特定玩家發送訊息（用於重連後的狀態恢復）"""
        ws = self.room_ws_map.get(room_id, {}).get(player_name)
        if ws:
            try:
                await ws.send_json(message)
            except Exception:
                pass

manager = RoomConnectionManager()
