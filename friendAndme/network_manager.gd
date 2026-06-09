extends Node

# 訊號：讓 main.gd 知道發生了什麼事
signal join_failed(reason: String)
signal room_checked(exists: bool, room_id: String)
signal room_created(room_id: String)
signal player_list_updated(players: Array)
signal phase_sync_requested(new_phase: String, data: Dictionary)
signal next_round_status(ready: int, total: int)
signal next_round_countdown(seconds: int)
signal connection_established
signal connection_closed
signal reconnect_status_received(data: Dictionary)

# 設定後端網址 (測試時使用 true，準備發布時改為 false)
var USE_LOCAL := false

var BASE_URL = "http://127.0.0.1:8000" if USE_LOCAL else "https://friends-and-me.fly.dev"
var WS_URL   = "ws://127.0.0.1:8000/ws" if USE_LOCAL else "wss://friends-and-me.fly.dev/ws"

func set_use_local(local: bool) -> void:
	USE_LOCAL = local
	BASE_URL = "http://127.0.0.1:8000" if USE_LOCAL else "https://friends-and-me.fly.dev"
	WS_URL   = "ws://127.0.0.1:8000/ws" if USE_LOCAL else "wss://friends-and-me.fly.dev/ws"
	print("[NetworkManager] Server environment set to: ", "LOCAL" if USE_LOCAL else "CLOUD")

var socket = WebSocketPeer.new()
var http_client: HTTPRequest
var http_client_check: HTTPRequest # 用於事前檢查
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
	
	http_client_check = HTTPRequest.new()
	add_child(http_client_check)
	http_client_check.request_completed.connect(_on_check_request_completed)

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

func check_room(room_id: String):
	var url = BASE_URL + "/check_room/" + room_id
	http_client_check.request(url)

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

# 回到前景時主動重連並重新同步狀態。
# 處理網頁/手機背景時 WebSocket 「假死」（狀態仍顯示 OPEN 但實際已斷）的情況——
# 此時 _process 偵測不到 STATE_CLOSED，永遠不會觸發重連，玩家會卡在「等待」畫面。
# 主動丟棄舊 socket 重連，伺服器會回傳 reconnect_status 重新同步階段與倒數。
func resync_on_foreground():
	if current_room_id == "" or my_player_name == "":
		return  # 不在對局中（例如還在主選單/大廳），不需重連
	print("[NetworkManager] Foreground resync: forcing WebSocket reconnect for room: ", current_room_id)
	socket.close()
	socket = WebSocketPeer.new()
	last_state = WebSocketPeer.STATE_CLOSED
	_is_reconnecting = true
	_reconnect_attempts = 0
	_reconnect_timer = 0.0
	connect_to_room_ws(current_room_id, my_player_name)

# ── 訊息處理 ──────────────────────────────────────────────────────────────────

func _on_request_completed(_result, response_code, _headers, body):
	print("[NetworkManager] Request completed. Code: ", response_code)
	if response_code == 200:
		var body_str = body.get_string_from_utf8()
		var json = JSON.parse_string(body_str)
		if not json:
			join_failed.emit("伺服器傳回無效格式")
			return
			
		if json.has("status") and json.status == "error":
			join_failed.emit(json.get("message", "加入失敗"))
			return
			
		if json.has("room_id"):
			current_room_id = json.room_id
			room_created.emit(current_room_id)
			connect_to_room_ws(current_room_id, my_player_name)
	else:
		join_failed.emit("伺服器連線失敗 (Code: %d)" % response_code)
		print("[NetworkManager] HTTP Request failed with code: ", response_code)

func _on_check_request_completed(_result, response_code, _headers, body):
	if response_code == 200:
		var json = JSON.parse_string(body.get_string_from_utf8())
		if json and json.has("exists"):
			# URL format is /check_room/{room_id}, we extract room_id from json if we added it,
			# but we didn't add it in python. So we emit with empty string or the caller knows it.
			# Let's just emit exists. We will change room_checked to just take exists.
			# Actually, room_checked(exists: bool, room_id: String)
			# We can get room_id from the original request but we only have 1 check at a time.
			room_checked.emit(json.exists, "")
		else:
			room_checked.emit(false, "")
	else:
		room_checked.emit(false, "")

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

		"next_round_status":
			next_round_status.emit(message.get("ready", 0), message.get("total", 0))

		"next_round_countdown":
			next_round_countdown.emit(message.get("seconds", 0))
