extends Node

# 訊號：讓 main.gd 知道發生了什麼事
signal room_created(room_id: String)
signal player_list_updated(players: Array)
signal phase_sync_requested(new_phase: String, data: Dictionary)
signal connection_established
signal connection_closed
signal reconnect_status_received(data: Dictionary)

# 設定後端網址 (測試時使用 127.0.0.1，部署後改為伺服器 IP)
const BASE_URL = "http://127.0.0.1:8000"
const WS_URL  = "ws://127.0.0.1:8000/ws"

var socket = WebSocketPeer.new()
var http_client: HTTPRequest
var current_room_id := ""
var my_player_name := "我"

# ── 重連狀態管理 ───────────────────────────────────────────────────────────────
var _is_reconnecting   := false   # 目前是否處於重連模式
var _reconnect_timer   := 0.0     # 計時器（秒）
var _reconnect_interval := 3.0    # 每次嘗試間隔（秒）
var _reconnect_attempts := 0
const MAX_RECONNECT_ATTEMPTS = 8  # 最多嘗試 8 次（共約 24 秒）

var last_state = WebSocketPeer.STATE_CLOSED

func _ready():
	http_client = HTTPRequest.new()
	add_child(http_client)
	http_client.request_completed.connect(_on_request_completed)

func _process(delta):
	socket.poll()
	var state = socket.get_ready_state()

	if state != last_state:
		if state == WebSocketPeer.STATE_OPEN:
			_reconnect_attempts = 0
			_is_reconnecting = false
			_reconnect_timer = 0.0
			connection_established.emit()
			print("[NetworkManager] WebSocket Connected!")

		elif state == WebSocketPeer.STATE_CLOSED:
			connection_closed.emit()
			print("[NetworkManager] WebSocket Disconnected!")
			# 若有房間可重連，啟動靜默重連
			if current_room_id != "" and my_player_name != "" and not _is_reconnecting:
				_start_reconnect()

		last_state = state

	if state == WebSocketPeer.STATE_OPEN:
		while socket.get_available_packet_count():
			var packet = socket.get_packet()
			var message = JSON.parse_string(packet.get_string_from_utf8())
			if message:
				_handle_ws_message(message)

	# ── 重連計時 ──
	elif state == WebSocketPeer.STATE_CLOSED and _is_reconnecting:
		_reconnect_timer += delta
		if _reconnect_timer >= _reconnect_interval:
			_reconnect_timer = 0.0
			_attempt_reconnect()

# ── API 呼叫 ──────────────────────────────────────────────────────────────────

func create_room(player_name: String):
	my_player_name = player_name
	var url = BASE_URL + "/create_room?player_name=" + player_name.uri_encode()
	http_client.request(url, [], HTTPClient.METHOD_POST)

func join_room(room_id: String, player_name: String):
	my_player_name = player_name
	current_room_id = room_id
	var url = BASE_URL + "/join_room?room_id=" + room_id + "&player_name=" + player_name.uri_encode()
	http_client.request(url, [], HTTPClient.METHOD_POST)

# ── WebSocket 控制 ────────────────────────────────────────────────────────────

func connect_to_room_ws(room_id: String, player_name: String):
	var url = WS_URL + "/" + room_id + "/" + player_name.uri_encode()
	var err = socket.connect_to_url(url)
	if err != OK:
		print("[NetworkManager] WebSocket connection failed!")
	else:
		print("[NetworkManager] Connecting to WebSocket: ", url)

func send_game_event(event_name: String, data: Dictionary):
	if socket.get_ready_state() == WebSocketPeer.STATE_OPEN:
		data["event"] = event_name
		socket.send_text(JSON.stringify(data))

# ── 重連邏輯 ──────────────────────────────────────────────────────────────────

func _start_reconnect():
	_is_reconnecting = true
	_reconnect_attempts = 0
	_reconnect_timer = 0.0
	print("[NetworkManager] Starting silent reconnect for room: ", current_room_id)

func _attempt_reconnect():
	_reconnect_attempts += 1
	if _reconnect_attempts > MAX_RECONNECT_ATTEMPTS:
		_is_reconnecting = false
		print("[NetworkManager] Max reconnect attempts reached. Giving up.")
		return

	print("[NetworkManager] Reconnect attempt ", _reconnect_attempts, "/", MAX_RECONNECT_ATTEMPTS, "...")
	# 重新建立 WebSocket — 伺服器端會識別此為重連
	socket = WebSocketPeer.new()
	last_state = WebSocketPeer.STATE_CLOSED
	connect_to_room_ws(current_room_id, my_player_name)

# ── 訊息處理 ──────────────────────────────────────────────────────────────────

func _on_request_completed(_result, response_code, _headers, body):
	if response_code == 200:
		var json = JSON.parse_string(body.get_string_from_utf8())
		if json.has("room_id"):
			current_room_id = json.room_id
			room_created.emit(current_room_id)
			connect_to_room_ws(current_room_id, my_player_name)
	else:
		print("[NetworkManager] HTTP Request failed with code: ", response_code)

func _handle_ws_message(message: Dictionary):
	print("[NetworkManager] WS Message: ", message)
	var event = message.get("event", "")

	match event:
		"player_list_updated":
			player_list_updated.emit(message.players)

		"phase_changed":
			phase_sync_requested.emit(message.new_phase, message)

		"reconnect_status":
			# 重連後告知目前遊戲狀態（等待下一輪）
			reconnect_status_received.emit(message)
			print("[NetworkManager] Reconnected! Current phase: ", message.get("current_phase", "?"))
