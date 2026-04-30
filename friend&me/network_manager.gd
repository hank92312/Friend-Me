extends Node

# 訊號：讓 main.gd 知道發生了什麼事
signal room_created(room_id: String)
signal player_list_updated(players: Array)
signal phase_sync_requested(new_phase: String, data: Dictionary)
signal connection_established
signal connection_closed

# 設定後端網址 (測試時使用 127.0.0.1，部署後改為伺服器 IP)
const BASE_URL = "http://127.0.0.1:8000"
const WS_URL = "ws://127.0.0.1:8000/ws"

var socket = WebSocketPeer.new()
var http_client: HTTPRequest
var current_room_id := ""
var my_player_name := "我"

func _ready():
	# 建立 HTTPRequest 節點
	http_client = HTTPRequest.new()
	add_child(http_client)
	http_client.request_completed.connect(_on_request_completed)

var last_state = WebSocketPeer.STATE_CLOSED

func _process(_delta):
	socket.poll()
	var state = socket.get_ready_state()
	
	if state != last_state:
		if state == WebSocketPeer.STATE_OPEN:
			connection_established.emit()
			print("WebSocket Connected!")
		elif state == WebSocketPeer.STATE_CLOSED:
			connection_closed.emit()
			print("WebSocket Disconnected!")
		last_state = state
	
	if state == WebSocketPeer.STATE_OPEN:
		while socket.get_available_packet_count():
			var packet = socket.get_packet()
			var message = JSON.parse_string(packet.get_string_from_utf8())
			if message:
				_handle_ws_message(message)
	elif state == WebSocketPeer.STATE_CLOSED:
		# 如果之前是連線狀態現在斷了，發送訊號
		pass

# --- API 呼叫 ---

func create_room(player_name: String):
	my_player_name = player_name
	var url = BASE_URL + "/create_room?player_name=" + player_name.uri_encode()
	http_client.request(url, [], HTTPClient.METHOD_POST)

func join_room(room_id: String, player_name: String):
	my_player_name = player_name
	current_room_id = room_id
	var url = BASE_URL + "/join_room?room_id=" + room_id + "&player_name=" + player_name.uri_encode()
	http_client.request(url, [], HTTPClient.METHOD_POST)

# --- WebSocket 控制 ---

func connect_to_room_ws(room_id: String, player_name: String):
	var url = WS_URL + "/" + room_id + "/" + player_name.uri_encode()
	var err = socket.connect_to_url(url)
	if err != OK:
		print("WebSocket connection failed!")
	else:
		print("Connecting to WebSocket: ", url)

func send_game_event(event_name: String, data: Dictionary):
	if socket.get_ready_state() == WebSocketPeer.STATE_OPEN:
		data["event"] = event_name
		socket.send_text(JSON.stringify(data))

# --- 回傳處理 ---

func _on_request_completed(_result, response_code, _headers, body):
	if response_code == 200:
		var json = JSON.parse_string(body.get_string_from_utf8())
		if json.has("room_id"):
			current_room_id = json.room_id
			room_created.emit(current_room_id)
			# 建立成功後自動連上 WebSocket
			connect_to_room_ws(current_room_id, my_player_name)
	else:
		print("HTTP Request failed with code: ", response_code)

func _handle_ws_message(message: Dictionary):
	print("WS Message received: ", message)
	var event = message.get("event", "")
	
	match event:
		"player_list_updated":
			player_list_updated.emit(message.players)
		"phase_changed":
			phase_sync_requested.emit(message.new_phase, message)
