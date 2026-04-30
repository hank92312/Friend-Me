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

    async def connect(self, websocket: WebSocket, room_id: str, player_name: str):
        await websocket.accept()
        if room_id not in self.active_rooms:
            self.active_rooms[room_id] = []
            self.room_players[room_id] = []
            self.room_states[room_id] = {"phase": "WAITING"}
        
        self.active_rooms[room_id].append(websocket)
        self.room_players[room_id].append(player_name)

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

    async def broadcast_to_room(self, room_id: str, message: dict):
        if room_id in self.active_rooms:
            # 將訊息轉為 JSON 字串發送
            for connection in self.active_rooms[room_id]:
                await connection.send_json(message)

manager = RoomConnectionManager()
