from fastapi import WebSocket
import json

class RoomConnectionManager:
    def __init__(self):
        # 結構：{ "room_id": [websocket1, websocket2, ...] }
        self.active_rooms: dict[str, list[WebSocket]] = {}
        # 結構：{ "room_id": [name1, name2, ...] }
        self.room_players: dict[str, list[str]] = {}
        # 額外儲存房間狀態
        self.room_states: dict[str, dict] = {}
        # 結構：{ "room_id": { "player1": "answer1", ... } }
        self.room_answers: dict[str, dict[str, str]] = {}
        # 結構：{ "room_id": { "player1": { "ans1": "p2", ... }, ... } }
        self.room_guesses: dict[str, dict[str, dict[str, str]]] = {}
        # 結構：{ "room_id": "current_captain_name" }
        self.room_captains: dict[str, str] = {}

    async def connect(self, websocket: WebSocket, room_id: str, player_name: str):
        await websocket.accept()
        if room_id not in self.active_rooms:
            self.active_rooms[room_id] = []
            self.room_players[room_id] = []
            self.room_states[room_id] = {"phase": "WAITING"}
            self.room_answers[room_id] = {}
            self.room_guesses[room_id] = {}
            self.room_captains[room_id] = player_name # 房主預設是第一個隊長
        
        self.active_rooms[room_id].append(websocket)
        self.room_players[room_id].append(player_name)

    async def submit_answer(self, room_id: str, player_name: str, answer: str):
        if room_id not in self.room_answers:
            self.room_answers[room_id] = {}
        
        self.room_answers[room_id][player_name] = answer
        
        # 檢查是否全員到齊
        total_players = len(self.room_players.get(room_id, []))
        submitted_count = len(self.room_answers.get(room_id, {}))
        
        return submitted_count >= total_players

    async def submit_guesses(self, room_id: str, player_name: str, guesses: dict):
        if room_id not in self.room_guesses:
            self.room_guesses[room_id] = {}
        
        self.room_guesses[room_id][player_name] = guesses
        
        total_players = len(self.room_players.get(room_id, []))
        submitted_count = len(self.room_guesses.get(room_id, {}))
        
        return submitted_count >= total_players

    def rotate_captain(self, room_id: str):
        if room_id not in self.room_players:
            return None
        
        players = self.room_players[room_id]
        current = self.room_captains.get(room_id)
        
        try:
            idx = players.index(current)
            new_idx = (idx + 1) % len(players)
            new_captain = players[new_idx]
            self.room_captains[room_id] = new_captain
            return new_captain
        except:
            if players:
                self.room_captains[room_id] = players[0]
                return players[0]
            return None

    def disconnect(self, websocket: WebSocket, room_id: str, player_name: str):
        if room_id in self.active_rooms:
            if websocket in self.active_rooms[room_id]:
                self.active_rooms[room_id].remove(websocket)
            if player_name in self.room_players[room_id]:
                self.room_players[room_id].remove(player_name)
                
            if not self.active_rooms[room_id]:
                del self.active_rooms[room_id]
                del self.room_players[room_id]
                del self.room_states[room_id]
                if room_id in self.room_answers:
                    del self.room_answers[room_id]
                if room_id in self.room_guesses:
                    del self.room_guesses[room_id]
                if room_id in self.room_captains:
                    del self.room_captains[room_id]

    async def broadcast_to_room(self, room_id: str, message: dict):
        if room_id in self.active_rooms:
            # 將訊息轉為 JSON 字串發送
            for connection in self.active_rooms[room_id]:
                await connection.send_json(message)

manager = RoomConnectionManager()
