from fastapi import WebSocket
import json
import time

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

    async def connect(self, websocket: WebSocket, room_id: str, player_name: str):
        await websocket.accept()
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
        return submitted_count >= len(eligible)

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
        for d in [self.active_rooms, self.room_players, self.room_ws_map,
                  self.room_states, self.room_answers, self.room_guesses,
                  self.room_captains, self.disconnected_players, self.waiting_for_next_round]:
            d.pop(room_id, None)

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
