extends Control

enum GamePhase { WAITING, WAIT_LOBBY, SELECTION, ANSWERING, GUESSING, REVELATION, SELECTION_WAITING, SUMMARY }

# ── 顏色常數 ──────────────────────────────────────────────────────────────────
const COLOR_BTN_NORMAL   := Color(0.815686, 0.505882, 0.235294, 1)  # 溫暖橘色
const COLOR_BTN_HOVER    := Color(0.890196, 0.580392, 0.313726, 1)  # 亮橘色
const COLOR_HIGHLIGHT    := Color(0.980, 0.820, 0.200, 1)           # 高亮：金黃
const COLOR_MATCHED      := Color(0.350, 0.620, 0.380, 1)           # 已配對：溫暖綠
const COLOR_PARTICIPANT  := Color(0.42,  0.30,  0.18,  1)           # 參與者預設：溫暖中棕
const COLOR_AUTO_PAIRED  := Color(0.45, 0.45, 0.45, 1)              # 自己的答案：灰色
const COLOR_CORRECT      := Color(0.350, 0.620, 0.380, 1)           # 結算：正確（綠）
const COLOR_WRONG        := Color(0.750, 0.280, 0.280, 1)           # 結算：錯誤（紅）
const COLOR_BTN_DISABLED := Color(0.40, 0.35, 0.30, 1)              # 按鈕停用：暗灰

const PAIR_COLORS = [
	Color(0.35, 0.62, 0.38, 1), # 溫暖綠
	Color(0.24, 0.44, 0.66, 1), # 寧靜藍
	Color(0.56, 0.35, 0.62, 1), # 羅蘭紫
	Color(0.75, 0.42, 0.28, 1), # 鐵鏽紅
	Color(0.22, 0.58, 0.58, 1), # 深青色
	Color(0.66, 0.58, 0.24, 1), # 芥末黃
]

# ── 節點引用 ──────────────────────────────────────────────────────────────────
@onready var phase_nodes: Dictionary = {
	GamePhase.WAITING:    $Phases/Phase0_Lobby,
	GamePhase.WAIT_LOBBY: $Phases/Phase0_WaitLobby,
	GamePhase.SELECTION:  $Phases/Phase1_Selection,
	GamePhase.ANSWERING:  $Phases/Phase2_Answering,
	GamePhase.GUESSING:   $Phases/Phase3_Guessing,
	GamePhase.REVELATION: $Phases/Phase4_Revelation,
	GamePhase.SELECTION_WAITING: $Phases/Phase1_Waiting,
	GamePhase.SUMMARY:    $Phases/Phase5_Summary,
}

# ── Mock Data ─────────────────────────────────────────────────────────────────
var mock_players := ["小明", "阿美", "大偉", "小花"]
var mock_self_name := "我"

var mock_answer_pools := {
	1: [
		"蛋餅加蘿蔔糕", "深夜貓頭鷹", "先洗頭", "LINE",
		"芋頭不行", "滑手機看新聞", "黑色", "安靜的郊區",
		"外觀質感", "游泳", "半糖少冰", "一個月一次",
		"跟著走的人", "累積破百不管", "比較喜歡冬天"
	],
	2: [
		"日本京都", "想回家休息", "星際效應", "獨立完成專案",
		"宮崎駿", "難忘的體驗", "鹹酥雞", "鋼琴",
		"遲到的人", "在家追劇", "柴犬", "外婆的手錶",
		"自己的直覺", "YouTube"
	],
	3: [
		"冷戰沉默型", "互補比較重要", "高中那時候",
		"媽媽", "背後說壞話", "曾經對外表沒自信",
		"具體行動", "第一份打工", "有過好幾次",
		"爸爸的固執", "甜蜜", "家人的期待", "一個人看電影"
	],
	4: [
		"害怕被所有人遺忘", "有說過善意的謊",
		"會咬吸管", "想對爸爸說", "太在意別人看法",
		"裝作很外向", "大學時翹課去環島",
		"不太容易信任人", "想當漫畫家",
		"上個月加班到崩潰", "有搶過朋友的功勞"
	],
	5: [
		"放棄安全感", "不會動手", "不會拿",
		"選擇不知道", "不願意", "要看情況",
		"不存在了吧", "會選擇留下", "願意",
		"為了保護家人", "還是會", "人群中沒人懂更可怕"
	]
}

# ── 遊戲狀態 ──────────────────────────────────────────────────────────────────
var current_phase: GamePhase = GamePhase.WAITING
var question_bank: Dictionary = {}
var current_question: String = ""
var current_level: int = 0
var current_captain: String = ""
var all_players: Array = []
var joined_players: Array = [] # 實際連線的玩家
var is_host: bool = false      # 是否為房主
var current_room_id: String = ""

# Phase 2 → 3 傳遞
var self_answer: String = ""

# Phase 3 狀態
var selected_answer_btn: Button = null
var answer_buttons: Array[Button] = []
var participant_buttons: Array[Button] = []
var paired_count := 0
var total_pairs  := 0

# 配對追蹤
var round_answers: Dictionary = {}      # { player_name: answer_text }
var correct_map: Dictionary = {}        # { answer_text: player_name }
var player_guesses: Dictionary = {}     # { answer_text: player_name }
var answer_btn_map: Dictionary = {}     # { Button: answer_text }
var participant_btn_map: Dictionary = {} # { Button: player_name }
var partner_map: Dictionary = {}        # { Button: Button } (配對對象)
var partner_color_map: Dictionary = {}  # { Button: Color } (記住配對時用的顏色)
var pending_room_id := ""
var all_room_guesses := {}

# 累計統計（跨輪次）
var cumul_guessed_by_others := 0  # 你的答案被隊友猜中的總次數
var cumul_others_attempts := 0    # 隊友猜你答案的總次數
var cumul_my_correct := 0         # 你猜中隊友答案的總次數
var cumul_my_attempts := 0        # 你猜隊友答案的總次數
var game_history : Array = []     # 存放本局所有問答: [{"question": "...", "answer": "..."}]

# ── 平台感知 Emoji 輔助函數 ──────────────────────────────────────────────────
# Android 的 Godot Label 不支援 Emoji（缺少 Emoji 字型），但 Web 和 PC 可以正常顯示。
# 此函數會在 Android 上回傳 fallback 文字，其他平台回傳原始 Emoji。
func _emoji(emoji_text: String, fallback: String) -> String:
	if OS.get_name() == "Android":
		return fallback
	return emoji_text

# ── Tutorial Slides ─────────────────────────────────────────────────────────────
# 注意：因為 _emoji() 需要在 _ready() 之後才能呼叫，tutorial_slides 改為在 _ready() 中初始化
var tutorial_slides: Array = []
var tutorial_current_slide := 0

# ── 初始化 ────────────────────────────────────────────────────────────────────
func _ready() -> void:
	_load_question_bank()
	
	# 初始化 Tutorial Slides（需要在 _ready 中才能呼叫 _emoji()）
	var bullet = _emoji("🔹", "▸")
	tutorial_slides = [
		"【如何創立房間】\n\n1. 點擊「創立圈圈」按鈕。\n2. 輸入一個朋友認得的暱稱。\n3. 系統會產生一組「6 位數房間碼」，將它分享給朋友！",
		"【如何加入房間】\n\n1. 點擊「加入圈圈」按鈕。\n2. 輸入朋友給你的「6 位數房間碼」。\n3. 輸入你的專屬暱稱即可進入大廳，等待房主開始遊戲。",
		"【遊戲流程說明】\n\n" + bullet + " Step 1：房主選擇本次「話題深度」 (LV1~LV5)。\n" + bullet + " Step 2：每人根據題目輸入答案，或選擇「不回答」。\n" + bullet + " Step 3：配對階段！點擊上方答案，再點擊下方朋友名字，猜出誰寫了什麼。\n" + bullet + " Step 4：結果揭曉，看看誰才是最懂你的人！"
	]
	
	# 為了解決名字重複問題，隨機產生一個名字 (MVP 測試用)
	mock_self_name = "玩家_" + str(randi() % 1000)
	NetworkManager.my_player_name = mock_self_name
	
	all_players = [mock_self_name] + mock_players
	current_captain = mock_self_name # 第一場預設我是隊長

	# Phase 0
	$Phases/Phase0_Lobby/VBoxContainer/BtnCreate.pressed.connect(_on_btn_create_pressed)
	$Phases/Phase0_Lobby/VBoxContainer/BtnJoin.pressed.connect(_on_btn_join_pressed)
	$Phases/Phase0_Lobby/VBoxContainer/BtnInstructions.pressed.connect(_on_btn_instructions_pressed)
	$Phases/Phase0_Lobby/VBoxContainer/BtnOptions.pressed.connect(_on_btn_options_pressed)
	$Phases/Phase0_Lobby/JoinPanel/VBox/HBox/BtnCancelJoin.pressed.connect(_on_btn_cancel_join_pressed)
	$Phases/Phase0_Lobby/JoinPanel/VBox/HBox/BtnConfirmJoin.pressed.connect(_on_btn_confirm_join)
	$Phases/Phase0_Lobby/NamePanel/VBox/HBox/BtnCancelName.pressed.connect(_on_btn_cancel_name_pressed)
	$Phases/Phase0_Lobby/NamePanel/VBox/HBox/BtnConfirmName.pressed.connect(_on_btn_confirm_name)

	# --- 網路單例訊號連接 ---
	NetworkManager.room_created.connect(_on_network_room_created)
	NetworkManager.join_failed.connect(_on_network_join_failed)
	NetworkManager.room_checked.connect(_on_network_room_checked)
	NetworkManager.next_round_status.connect(_on_network_next_round_status)
	NetworkManager.player_list_updated.connect(_on_network_player_list_updated)
	NetworkManager.phase_sync_requested.connect(_on_network_phase_sync)
	NetworkManager.reconnect_status_received.connect(_on_reconnect_status)

	# Phase 1
	var p1 := $Phases/Phase1_Selection/VBoxContainer
	p1.get_node("BtnLevel1").pressed.connect(_on_btn_level_pressed.bind(1))
	p1.get_node("BtnLevel2").pressed.connect(_on_btn_level_pressed.bind(2))
	p1.get_node("BtnLevel3").pressed.connect(_on_btn_level_pressed.bind(3))
	p1.get_node("BtnLevel4").pressed.connect(_on_btn_level_pressed.bind(4))
	p1.get_node("BtnLevel5").pressed.connect(_on_btn_level_pressed.bind(5))
	p1.get_node("BtnRandom").pressed.connect(_on_btn_level_pressed.bind(0))
	$Phases/Phase1_Selection/BtnBack.pressed.connect(_on_btn_back_pressed)

	# Phase 2
	$Phases/Phase2_Answering/VBox/AnswerArea/BtnSubmit.pressed.connect(_on_btn_submit_answer)
	$Phases/Phase2_Answering/VBox/BtnNoAnswer.pressed.connect(_on_btn_no_answer)
	($Phases/Phase2_Answering/VBox/AnswerArea/LineEdit as LineEdit).text_changed.connect(_on_answer_text_changed)

	# Phase 3 ── 送出配對（pill 會動態建立）
	$Phases/Phase3_Guessing/BtnSubmitMatch.pressed.connect(_on_btn_submit_match)

	# Phase 0 Lobby Wait
	$Phases/Phase0_WaitLobby/VBox/BtnStartGame.pressed.connect(_on_btn_start_game)
	$Phases/Phase0_WaitLobby/VBox/RoomIDHBox/BtnCopyID.pressed.connect(_on_btn_copy_id)

	# Phase 4 ── 再玩一輪 & 離開
	$Phases/Phase4_Revelation/VBox/BtnNextRound.pressed.connect(_on_btn_next_round)
	$Phases/Phase4_Revelation/BtnLeaveCircle.pressed.connect(_on_btn_leave_circle_pressed)

	# Phase 5 ── 確定離開
	$Phases/Phase5_Summary/VBox/BtnFinalLeave.pressed.connect(_on_btn_final_leave_pressed)

	# ── 創建動態放射漸層背景 ──
	var grad := Gradient.new()
	grad.colors = PackedColorArray([
		Color(0.16, 0.14, 0.13, 1), # 中心稍微亮一點的溫暖深灰色
		Color(0.08, 0.07, 0.07, 1)  # 邊緣極深色
	])
	grad.offsets = PackedFloat32Array([0.0, 1.0])
	
	var grad_tex := GradientTexture2D.new()
	grad_tex.gradient = grad
	grad_tex.fill = GradientTexture2D.FILL_RADIAL
	grad_tex.fill_from = Vector2(0.5, 0.5)
	grad_tex.fill_to = Vector2(0.85, 0.85)
	
	var bg_rect := TextureRect.new()
	bg_rect.name = "GradientBG"
	bg_rect.texture = grad_tex
	bg_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	bg_rect.stretch_mode = TextureRect.STRETCH_SCALE
	bg_rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	$Background.add_child(bg_rect)

	# ── 面板與卡片樣式美化 (追加陰影與邊框) ──
	var card_sb: StyleBoxFlat = $Phases/Phase2_Answering/VBox/QuestionCard.get_theme_stylebox("panel")
	if card_sb:
		card_sb.border_width_left = 2
		card_sb.border_width_top = 2
		card_sb.border_width_right = 2
		card_sb.border_width_bottom = 2
		card_sb.border_color = Color(0.815, 0.505, 0.235, 0.16)
		card_sb.shadow_color = Color(0, 0, 0, 0.45)
		card_sb.shadow_size = 20
		card_sb.shadow_offset = Vector2(0, 12)
		card_sb.corner_radius_top_left = 24
		card_sb.corner_radius_top_right = 24
		card_sb.corner_radius_bottom_right = 24
		card_sb.corner_radius_bottom_left = 24
	
	var section_sb: StyleBoxFlat = $Phases/Phase0_Lobby/JoinPanel.get_theme_stylebox("panel")
	if section_sb:
		section_sb.border_width_left = 2
		section_sb.border_width_top = 2
		section_sb.border_width_right = 2
		section_sb.border_width_bottom = 2
		section_sb.border_color = Color(0.815, 0.505, 0.235, 0.12)
		section_sb.shadow_color = Color(0, 0, 0, 0.35)
		section_sb.shadow_size = 16
		section_sb.shadow_offset = Vector2(0, 8)
		section_sb.corner_radius_top_left = 32
		section_sb.corner_radius_top_right = 32
		section_sb.corner_radius_bottom_right = 32
		section_sb.corner_radius_bottom_left = 32

	# ── 套用輸入框美化 ──
	_style_line_edit($Phases/Phase0_Lobby/JoinPanel/VBox/RoomIDInput)
	_style_line_edit($Phases/Phase0_Lobby/NamePanel/VBox/PlayerNameInput)
	_style_line_edit($Phases/Phase2_Answering/VBox/AnswerArea/LineEdit)

	# ── 註冊全域按鈕動畫 ──
	_register_button_animations(self)

	switch_phase(GamePhase.WAITING)

# ── 題庫載入 ──────────────────────────────────────────────────────────────────
func _load_question_bank() -> void:
	var file := FileAccess.open("res://data/question_bank.json", FileAccess.READ)
	if file == null:
		print("WARNING: question_bank.json not found!")
		return
	var json_text: String = file.get_as_text()
	file.close()
	var json := JSON.new()
	var err := json.parse(json_text)
	if err != OK:
		print("WARNING: Failed to parse question_bank.json: ", json.get_error_message())
		return
	question_bank = json.data.get("levels", {})
	print("Question bank loaded: ", question_bank.size(), " levels")

func _get_random_question(level: int) -> String:
	var lv_key: String = str(level)
	if not question_bank.has(lv_key):
		return "(題庫載入失敗)"
	var questions: Array = question_bank[lv_key]["questions"]
	var idx: int = randi() % questions.size()
	var q: Dictionary = questions[idx]
	return q["text"]

# ── 通用切換畫面（含縮放與淡入淡出轉場） ───────────────────────────────────────
func switch_phase(new_phase: GamePhase) -> void:
	var old_node = phase_nodes.get(current_phase)
	current_phase = new_phase
	var new_node = phase_nodes.get(new_phase)
	print("Switched to phase: ", GamePhase.keys()[current_phase])

	if new_phase == GamePhase.GUESSING:
		_generate_phase3_ui()
	elif new_phase == GamePhase.REVELATION:
		_generate_phase4_ui()
	elif new_phase == GamePhase.SUMMARY:
		_generate_phase5_ui()

	if old_node == null or old_node == new_node:
		for key in phase_nodes:
			phase_nodes[key].visible = (key == current_phase)
		return

	# 計算中心點，確保以中央為基準進行縮放
	var viewport_size = get_viewport_rect().size
	old_node.pivot_offset = old_node.size / 2.0 if old_node.size != Vector2.ZERO else viewport_size / 2.0
	new_node.pivot_offset = new_node.size / 2.0 if new_node.size != Vector2.ZERO else viewport_size / 2.0

	# 準備新畫面：透明度為 0、輕微縮小
	new_node.modulate.a = 0.0
	new_node.scale = Vector2(0.97, 0.97)
	new_node.visible = true

	# 平行播放淡入淡出與縮放
	var tween := create_tween().set_parallel(true).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	
	# 舊畫面：淡出並縮小至 0.97
	tween.tween_property(old_node, "modulate:a", 0.0, 0.18)
	tween.tween_property(old_node, "scale", Vector2(0.97, 0.97), 0.18)
	
	# 隱藏舊畫面並還原狀態
	var chain_tw := create_tween()
	chain_tw.tween_interval(0.18)
	chain_tw.tween_callback(func():
		old_node.visible = false
		old_node.modulate.a = 1.0
		old_node.scale = Vector2(1.0, 1.0)
	)

	# 新畫面：淡入與放大至 1.0
	tween.tween_property(new_node, "modulate:a", 1.0, 0.22)
	tween.tween_property(new_node, "scale", Vector2(1.0, 1.0), 0.22)

func _on_reconnect_status(data: Dictionary) -> void:
	var phase_str = data.get("current_phase", "")
	print("[重連] 目前房間階段：", phase_str, "，等待本輪結束後一起加入下一輪。")
	# 顯示重連提示（若目前在大廳畫面則直接等待）
	if current_phase == GamePhase.WAIT_LOBBY:
		var hint := $Phases/Phase0_WaitLobby/VBox/WaitingHint
		hint.text = "重連成功！等待本輪結束後加入..."  
		hint.visible = true
# ── Phase 0 ───────────────────────────────────────────────────────────────────
func _on_btn_create_pressed() -> void:
	AudioManager.play_tap()
	is_host = true
	pending_room_id = ""
	$Phases/Phase0_Lobby/NamePanel.visible = true
	$Phases/Phase0_Lobby/NamePanel/VBox/PlayerNameInput.grab_focus()

func _on_btn_join_pressed() -> void:
	AudioManager.play_tap()
	is_host = false
	$Phases/Phase0_Lobby/JoinPanel.visible = true
	$Phases/Phase0_Lobby/JoinPanel/VBox/RoomIDInput.text = ""
	$Phases/Phase0_Lobby/JoinPanel/VBox/RoomIDInput.grab_focus()
	
	# 重置 JoinPanel 狀態
	var error_label = $Phases/Phase0_Lobby/JoinPanel/VBox.get_node_or_null("ErrorLabel")
	if error_label:
		error_label.text = ""
	var btn = $Phases/Phase0_Lobby/JoinPanel/VBox/HBox/BtnConfirmJoin
	btn.disabled = false
	btn.text = "確認加入"
	_set_btn_color(btn, COLOR_BTN_NORMAL)

func _on_btn_cancel_join_pressed() -> void:
	AudioManager.play_cancel()
	$Phases/Phase0_Lobby/JoinPanel.visible = false

# ── 遊戲說明 (Tutorial) 邏輯 ──
func _on_btn_instructions_pressed() -> void:
	AudioManager.play_tap()
	var lobby := $Phases/Phase0_Lobby
	var panel = lobby.get_node_or_null("TutorialPanel")
	if not panel:
		# 建立半透明暗底覆蓋層
		panel = Control.new()
		panel.name = "TutorialPanel"
		panel.set_anchors_preset(Control.PRESET_FULL_RECT)
		
		var bg_overlay := ColorRect.new()
		bg_overlay.name = "BgOverlay"
		bg_overlay.color = Color(0.05, 0.04, 0.04, 0.82)
		bg_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
		panel.add_child(bg_overlay)
		
		# 建立中央漂浮卡片
		var card := PanelContainer.new()
		card.name = "DialogCard"
		card.custom_minimum_size = Vector2(880, 1100)
		card.set_anchors_preset(Control.PRESET_CENTER)
		card.pivot_offset = Vector2(440, 550)
		
		var style := StyleBoxFlat.new()
		style.bg_color = Color(0.16, 0.14, 0.13, 1)
		style.corner_radius_top_left = 32
		style.corner_radius_top_right = 32
		style.corner_radius_bottom_right = 32
		style.corner_radius_bottom_left = 32
		style.border_width_left = 2
		style.border_width_top = 2
		style.border_width_right = 2
		style.border_width_bottom = 2
		style.border_color = Color(0.815, 0.505, 0.235, 0.18)
		style.shadow_color = Color(0, 0, 0, 0.5)
		style.shadow_size = 24
		style.shadow_offset = Vector2(0, 16)
		card.add_theme_stylebox_override("panel", style)
		panel.add_child(card)
		
		var margin := MarginContainer.new()
		margin.name = "MarginContainer"
		margin.add_theme_constant_override("margin_left", 60)
		margin.add_theme_constant_override("margin_right", 60)
		margin.add_theme_constant_override("margin_top", 80)
		margin.add_theme_constant_override("margin_bottom", 80)
		card.add_child(margin)
		
		var vbox := VBoxContainer.new()
		vbox.name = "VBoxContainer"
		vbox.alignment = BoxContainer.ALIGNMENT_CENTER
		vbox.add_theme_constant_override("separation", 45)
		margin.add_child(vbox)
		
		var title := Label.new()
		title.text = "遊戲說明"
		title.add_theme_font_size_override("font_size", 52)
		title.add_theme_color_override("font_color", COLOR_HIGHLIGHT)
		title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		vbox.add_child(title)
		
		var content := Label.new()
		content.name = "ContentLabel"
		content.text = tutorial_slides[0]
		content.add_theme_font_size_override("font_size", 36)
		content.autowrap_mode = TextServer.AUTOWRAP_WORD
		content.custom_minimum_size = Vector2(400, 360)
		vbox.add_child(content)
		
		var hbox := HBoxContainer.new()
		hbox.name = "HBoxContainer"
		hbox.alignment = BoxContainer.ALIGNMENT_CENTER
		hbox.add_theme_constant_override("separation", 30)
		vbox.add_child(hbox)
		
		var btn_prev := Button.new()
		btn_prev.name = "BtnPrev"
		btn_prev.text = "上一頁"
		btn_prev.custom_minimum_size = Vector2(220, 80)
		btn_prev.add_theme_font_size_override("font_size", 32)
		_set_btn_color(btn_prev, COLOR_BTN_NORMAL)
		btn_prev.pressed.connect(_on_tutorial_prev)
		hbox.add_child(btn_prev)
		
		var btn_next := Button.new()
		btn_next.name = "BtnNext"
		btn_next.text = "下一頁"
		btn_next.custom_minimum_size = Vector2(220, 80)
		btn_next.add_theme_font_size_override("font_size", 32)
		_set_btn_color(btn_next, COLOR_BTN_NORMAL)
		btn_next.pressed.connect(_on_tutorial_next)
		hbox.add_child(btn_next)
		
		var btn_close := Button.new()
		btn_close.text = "關閉說明"
		btn_close.custom_minimum_size = Vector2(470, 80)
		btn_close.add_theme_font_size_override("font_size", 32)
		_set_btn_color(btn_close, COLOR_BTN_DISABLED)
		btn_close.pressed.connect(_on_tutorial_close)
		
		var spacer := Control.new()
		spacer.custom_minimum_size = Vector2(0, 30)
		vbox.add_child(spacer)
		vbox.add_child(btn_close)
		
		lobby.add_child(panel)
		_register_button_animations(card)
	
	tutorial_current_slide = 0
	_update_tutorial_ui()
	
	# 播放開場動畫
	panel.visible = true
	var card_node = panel.get_node("DialogCard")
	card_node.scale = Vector2(0.9, 0.9)
	card_node.modulate.a = 0.0
	var tw := create_tween().set_parallel(true).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_property(card_node, "scale", Vector2(1.0, 1.0), 0.22)
	tw.tween_property(card_node, "modulate:a", 1.0, 0.22)

func _on_tutorial_prev() -> void:
	AudioManager.play_tap()
	if tutorial_current_slide > 0:
		tutorial_current_slide -= 1
		_update_tutorial_ui()

func _on_tutorial_next() -> void:
	AudioManager.play_tap()
	if tutorial_current_slide < tutorial_slides.size() - 1:
		tutorial_current_slide += 1
		_update_tutorial_ui()

func _on_tutorial_close() -> void:
	AudioManager.play_cancel()
	var panel = $Phases/Phase0_Lobby.get_node_or_null("TutorialPanel")
	if panel:
		var card_node = panel.get_node("DialogCard")
		var tw := create_tween().set_parallel(true).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_IN)
		tw.tween_property(card_node, "scale", Vector2(0.9, 0.9), 0.18)
		tw.tween_property(card_node, "modulate:a", 0.0, 0.18)
		tw.chain().tween_callback(func():
			panel.visible = false
		)

func _update_tutorial_ui() -> void:
	var panel = $Phases/Phase0_Lobby.get_node_or_null("TutorialPanel")
	if not panel: return
	
	var content: Label = panel.get_node("DialogCard/MarginContainer/VBoxContainer/ContentLabel")
	content.text = tutorial_slides[tutorial_current_slide]
	
	var btn_prev: Button = panel.get_node("DialogCard/MarginContainer/VBoxContainer/HBoxContainer/BtnPrev")
	var btn_next: Button = panel.get_node("DialogCard/MarginContainer/VBoxContainer/HBoxContainer/BtnNext")
	
	btn_prev.disabled = (tutorial_current_slide == 0)
	btn_next.disabled = (tutorial_current_slide == tutorial_slides.size() - 1)
	
	_set_btn_color(btn_prev, COLOR_BTN_NORMAL if not btn_prev.disabled else COLOR_BTN_DISABLED)
	_set_btn_color(btn_next, COLOR_BTN_NORMAL if not btn_next.disabled else COLOR_BTN_DISABLED)

# ── 選項 (Options) 邏輯 ──
func _on_btn_options_pressed() -> void:
	AudioManager.play_tap()
	var lobby := $Phases/Phase0_Lobby
	var panel = lobby.get_node_or_null("OptionsPanel")
	if not panel:
		# 建立半透明暗底覆蓋層
		panel = Control.new()
		panel.name = "OptionsPanel"
		panel.set_anchors_preset(Control.PRESET_FULL_RECT)
		
		var bg_overlay := ColorRect.new()
		bg_overlay.name = "BgOverlay"
		bg_overlay.color = Color(0.05, 0.04, 0.04, 0.82)
		bg_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
		panel.add_child(bg_overlay)
		
		# 建立中央漂浮卡片
		var card := PanelContainer.new()
		card.name = "DialogCard"
		card.custom_minimum_size = Vector2(880, 1000)
		card.set_anchors_preset(Control.PRESET_CENTER)
		card.pivot_offset = Vector2(440, 500)
		
		var style := StyleBoxFlat.new()
		style.bg_color = Color(0.16, 0.14, 0.13, 1)
		style.corner_radius_top_left = 32
		style.corner_radius_top_right = 32
		style.corner_radius_bottom_right = 32
		style.corner_radius_bottom_left = 32
		style.border_width_left = 2
		style.border_width_top = 2
		style.border_width_right = 2
		style.border_width_bottom = 2
		style.border_color = Color(0.815, 0.505, 0.235, 0.18)
		style.shadow_color = Color(0, 0, 0, 0.5)
		style.shadow_size = 24
		style.shadow_offset = Vector2(0, 16)
		card.add_theme_stylebox_override("panel", style)
		panel.add_child(card)
		
		var margin := MarginContainer.new()
		margin.name = "MarginContainer"
		margin.add_theme_constant_override("margin_left", 60)
		margin.add_theme_constant_override("margin_right", 60)
		margin.add_theme_constant_override("margin_top", 80)
		margin.add_theme_constant_override("margin_bottom", 80)
		card.add_child(margin)
		
		var vbox := VBoxContainer.new()
		vbox.name = "VBoxContainer"
		vbox.alignment = BoxContainer.ALIGNMENT_CENTER
		vbox.add_theme_constant_override("separation", 45)
		margin.add_child(vbox)
		
		var title := Label.new()
		title.text = "設定選項"
		title.add_theme_font_size_override("font_size", 52)
		title.add_theme_color_override("font_color", COLOR_HIGHLIGHT)
		title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		vbox.add_child(title)
		
		var btn_audio := Button.new()
		btn_audio.name = "BtnAudio"
		btn_audio.text = "音效：開啟" if not AudioManager.is_muted else "音效：關閉"
		btn_audio.custom_minimum_size = Vector2(450, 90)
		btn_audio.add_theme_font_size_override("font_size", 34)
		_set_btn_color(btn_audio, COLOR_BTN_NORMAL)
		btn_audio.pressed.connect(_on_options_audio_toggled)
		vbox.add_child(btn_audio)
		
		var btn_feedback := Button.new()
		btn_feedback.name = "BtnFeedback"
		btn_feedback.text = "問題回饋 / 聯絡製作人\nhank92312@gmail.com (點擊複製)"
		btn_feedback.custom_minimum_size = Vector2(450, 120)
		btn_feedback.add_theme_font_size_override("font_size", 30)
		_set_btn_color(btn_feedback, COLOR_BTN_NORMAL)
		btn_feedback.pressed.connect(_on_options_feedback_pressed)
		vbox.add_child(btn_feedback)
		
		var spacer := Control.new()
		spacer.custom_minimum_size = Vector2(0, 30)
		vbox.add_child(spacer)
		
		var btn_close := Button.new()
		btn_close.text = "關閉設定"
		btn_close.custom_minimum_size = Vector2(450, 80)
		btn_close.add_theme_font_size_override("font_size", 32)
		_set_btn_color(btn_close, COLOR_BTN_DISABLED)
		btn_close.pressed.connect(_on_options_close)
		vbox.add_child(btn_close)
		
		lobby.add_child(panel)
		_register_button_animations(card)
	
	# 每次開啟時更新按鈕文字（防止在其他地方修改了靜音）
	var btn_audio: Button = panel.get_node("DialogCard/MarginContainer/VBoxContainer/BtnAudio")
	if btn_audio:
		btn_audio.text = "音效：關閉" if AudioManager.is_muted else "音效：開啟"
	
	var btn_feedback: Button = panel.get_node("DialogCard/MarginContainer/VBoxContainer/BtnFeedback")
	if btn_feedback:
		btn_feedback.text = "問題回饋 / 聯絡製作人\nhank92312@gmail.com (點擊複製)"
	
	# 播放開場動畫
	panel.visible = true
	var card_node = panel.get_node("DialogCard")
	card_node.scale = Vector2(0.9, 0.9)
	card_node.modulate.a = 0.0
	var tw := create_tween().set_parallel(true).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_property(card_node, "scale", Vector2(1.0, 1.0), 0.22)
	tw.tween_property(card_node, "modulate:a", 1.0, 0.22)

func _on_options_audio_toggled() -> void:
	AudioManager.is_muted = not AudioManager.is_muted
	AudioManager.play_tap() # 若開啟音效，就會播放一聲作為回饋
	var panel = $Phases/Phase0_Lobby.get_node_or_null("OptionsPanel")
	if panel:
		var btn_audio: Button = panel.get_node("DialogCard/MarginContainer/VBoxContainer/BtnAudio")
		btn_audio.text = "音效：關閉" if AudioManager.is_muted else "音效：開啟"

func _on_options_feedback_pressed() -> void:
	AudioManager.play_copy_id()
	DisplayServer.clipboard_set("hank92312@gmail.com")
	var panel = $Phases/Phase0_Lobby.get_node_or_null("OptionsPanel")
	if panel:
		var btn_feedback: Button = panel.get_node("DialogCard/MarginContainer/VBoxContainer/BtnFeedback")
		btn_feedback.text = "已複製信箱！"
		await get_tree().create_timer(1.5).timeout
		if btn_feedback and is_instance_valid(btn_feedback):
			btn_feedback.text = "問題回饋 / 聯絡製作人\nhank92312@gmail.com (點擊複製)"

func _on_options_close() -> void:
	AudioManager.play_cancel()
	var panel = $Phases/Phase0_Lobby.get_node_or_null("OptionsPanel")
	if panel:
		var card_node = panel.get_node("DialogCard")
		var tw := create_tween().set_parallel(true).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_IN)
		tw.tween_property(card_node, "scale", Vector2(0.9, 0.9), 0.18)
		tw.tween_property(card_node, "modulate:a", 0.0, 0.18)
		tw.chain().tween_callback(func():
			panel.visible = false
		)

func _show_join_error(msg: String) -> void:
	var vbox = $Phases/Phase0_Lobby/JoinPanel/VBox
	var error_label = vbox.get_node_or_null("ErrorLabel")
	if not error_label:
		error_label = Label.new()
		error_label.name = "ErrorLabel"
		error_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		error_label.add_theme_font_size_override("font_size", 40)
		error_label.add_theme_color_override("font_color", Color(1, 0.3, 0.3, 1))
		error_label.autowrap_mode = TextServer.AUTOWRAP_WORD
		vbox.add_child(error_label)
		vbox.move_child(error_label, 1) # 放在標題下方
	error_label.text = "錯誤：" + msg
	error_label.visible = true
	
	var btn = $Phases/Phase0_Lobby/JoinPanel/VBox/HBox/BtnConfirmJoin
	btn.disabled = false
	btn.text = "確認加入"
	_set_btn_color(btn, COLOR_BTN_NORMAL)

func _on_btn_confirm_join() -> void:
	var room_id = $Phases/Phase0_Lobby/JoinPanel/VBox/RoomIDInput.text.strip_edges().to_upper()
	if room_id.length() != 6:
		AudioManager.play_cancel()
		_show_join_error("房號必須為 6 碼 (包含英數)")
		return
		
	AudioManager.play_tap()
	
	# 先鎖定按鈕，顯示檢查中
	var btn = $Phases/Phase0_Lobby/JoinPanel/VBox/HBox/BtnConfirmJoin
	btn.disabled = true
	btn.text = "檢查中..."
	_set_btn_color(btn, COLOR_BTN_DISABLED)
	
	pending_room_id = room_id
	NetworkManager.check_room(room_id)

func _on_network_room_checked(exists: bool, _room_id: String) -> void:
	if exists:
		# 房間存在，進入下一個流程 (輸入名字)
		$Phases/Phase0_Lobby/JoinPanel.visible = false
		$Phases/Phase0_Lobby/NamePanel.visible = true
		$Phases/Phase0_Lobby/NamePanel/VBox/PlayerNameInput.grab_focus()
	else:
		AudioManager.play_cancel()
		_show_join_error("房間不存在，請確認房號是否正確。")

func _on_btn_cancel_name_pressed() -> void:
	AudioManager.play_cancel()
	$Phases/Phase0_Lobby/NamePanel.visible = false

func _on_btn_confirm_name() -> void:
	var player_name = $Phases/Phase0_Lobby/NamePanel/VBox/PlayerNameInput.text.strip_edges()
	if player_name == "":
		return
	AudioManager.play_tap()
	
	mock_self_name = player_name
	NetworkManager.my_player_name = player_name
	
	$Phases/Phase0_Lobby/NamePanel.visible = false
	
	# 斷線重連豁免：跳過廣告流程
	if NetworkManager._is_reconnecting:
		_proceed_to_room()
		return
	
	# 正常流程：先顯示廣告警語面板
	_show_ad_disclaimer()

func _proceed_to_room() -> void:
	if is_host:
		print("Requesting room creation for: ", mock_self_name)
		NetworkManager.create_room(mock_self_name)
	else:
		print("Attempting to join room ", pending_room_id, " as: ", mock_self_name)
		NetworkManager.join_room(pending_room_id, mock_self_name)

# ── 廣告友善警語面板 ─────────────────────────────────────────────────────────
func _show_ad_disclaimer() -> void:
	var lobby := $Phases/Phase0_Lobby
	var panel = lobby.get_node_or_null("AdDisclaimerPanel")
	if not panel:
		# 建立半透明暗底覆蓋層
		panel = Control.new()
		panel.name = "AdDisclaimerPanel"
		panel.set_anchors_preset(Control.PRESET_FULL_RECT)
		
		var bg_overlay := ColorRect.new()
		bg_overlay.name = "BgOverlay"
		bg_overlay.color = Color(0.05, 0.04, 0.04, 0.82)
		bg_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
		panel.add_child(bg_overlay)
		
		# 建立中央漂浮卡片
		var card := PanelContainer.new()
		card.name = "DialogCard"
		card.custom_minimum_size = Vector2(880, 1000)
		card.set_anchors_preset(Control.PRESET_CENTER)
		card.pivot_offset = Vector2(440, 500)
		
		var style := StyleBoxFlat.new()
		style.bg_color = Color(0.16, 0.14, 0.13, 1)
		style.corner_radius_top_left = 32
		style.corner_radius_top_right = 32
		style.corner_radius_bottom_right = 32
		style.corner_radius_bottom_left = 32
		style.border_width_left = 2
		style.border_width_top = 2
		style.border_width_right = 2
		style.border_width_bottom = 2
		style.border_color = Color(0.815, 0.505, 0.235, 0.18)
		style.shadow_color = Color(0, 0, 0, 0.5)
		style.shadow_size = 24
		style.shadow_offset = Vector2(0, 16)
		card.add_theme_stylebox_override("panel", style)
		panel.add_child(card)
		
		var margin := MarginContainer.new()
		margin.name = "MarginContainer"
		margin.add_theme_constant_override("margin_left", 60)
		margin.add_theme_constant_override("margin_right", 60)
		margin.add_theme_constant_override("margin_top", 100)
		margin.add_theme_constant_override("margin_bottom", 100)
		card.add_child(margin)
		
		var vbox := VBoxContainer.new()
		vbox.name = "VBoxContainer"
		vbox.alignment = BoxContainer.ALIGNMENT_CENTER
		vbox.add_theme_constant_override("separation", 40)
		margin.add_child(vbox)
		
		var icon_label := Label.new()
		icon_label.text = _emoji("📢", "-- 廣告通知 --")
		icon_label.add_theme_font_size_override("font_size", 72 if OS.get_name() != "Android" else 36)
		if OS.get_name() == "Android":
			icon_label.add_theme_color_override("font_color", Color(0.7, 0.6, 0.5, 0.8))
		icon_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		vbox.add_child(icon_label)
		
		var title := Label.new()
		title.text = "即將播放一則短廣告"
		title.add_theme_font_size_override("font_size", 56)
		title.add_theme_color_override("font_color", COLOR_HIGHLIGHT)
		title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		vbox.add_child(title)
		
		var desc := Label.new()
		desc.text = "您的每次觀看，都是對我們\n維持伺服器運作的支持。\n\n感謝您的體諒與陪伴 " + _emoji("❤️", "")
		desc.add_theme_font_size_override("font_size", 44)
		desc.add_theme_color_override("font_color", Color(1, 0.95, 0.8, 0.9))
		desc.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		desc.autowrap_mode = TextServer.AUTOWRAP_WORD
		vbox.add_child(desc)
		
		var spacer := Control.new()
		spacer.custom_minimum_size = Vector2(0, 20)
		vbox.add_child(spacer)
		
		var btn_continue := Button.new()
		btn_continue.name = "BtnContinue"
		btn_continue.text = "繼續"
		btn_continue.custom_minimum_size = Vector2(340, 100)
		btn_continue.add_theme_font_size_override("font_size", 48)
		_set_btn_color(btn_continue, COLOR_BTN_NORMAL)
		btn_continue.pressed.connect(_on_ad_disclaimer_continue)
		vbox.add_child(btn_continue)
		
		lobby.add_child(panel)
	
	panel.visible = true
	
	# 確保每次顯示時按鈕狀態是正確的（防止上一輪殘留的「載入中」狀態）
	var btn = panel.get_node_or_null("MarginContainer/VBoxContainer/BtnContinue")
	if btn:
		btn.text = "繼續"
		btn.disabled = false
		_set_btn_color(btn, COLOR_BTN_NORMAL)
	
	# 清除錯誤訊息
	var error_label = panel.get_node_or_null("MarginContainer/VBoxContainer/ErrorLabel")
	if error_label:
		error_label.text = ""

func _on_ad_disclaimer_continue() -> void:
	AudioManager.play_tap()
	
	# 不要立即隱藏警語面板，等到廣告真的結束再隱藏
	# 但可以更新按鈕狀態讓玩家知道有在動
	var panel = $Phases/Phase0_Lobby.get_node_or_null("AdDisclaimerPanel")
	if not panel: return
	
	var btn = panel.get_node_or_null("MarginContainer/VBoxContainer/BtnContinue")
	if btn:
		btn.text = "載入中..."
		btn.disabled = true
		_set_btn_color(btn, COLOR_BTN_DISABLED)
	
	# 播放廣告 → 等待 ad_finished 信號 → 進入房間
	if AdManager.ad_finished.is_connected(_on_ad_finished_proceed):
		AdManager.ad_finished.disconnect(_on_ad_finished_proceed)
	
	AdManager.ad_finished.connect(_on_ad_finished_proceed, CONNECT_ONE_SHOT)
	print("[Main] Calling AdManager.show_interstitial()...")
	AdManager.show_interstitial()

func _on_ad_finished_proceed() -> void:
	print("[Main] Ad finished — proceeding to room.")
	_proceed_to_room()

func _on_network_join_failed(reason: String) -> void:
	print("[Main] Join failed UI Trigger: ", reason)
	
	# 優先尋找警語面板中的 ErrorLabel
	var panel = $Phases/Phase0_Lobby.get_node_or_null("AdDisclaimerPanel")
	if panel:
		var btn = panel.get_node_or_null("MarginContainer/VBoxContainer/BtnContinue")
		if btn:
			btn.text = "重試"
			btn.disabled = false
			_set_btn_color(btn, COLOR_BTN_NORMAL)
		
		var vbox = panel.get_node("MarginContainer/VBoxContainer")
		if vbox:
			var error_label = vbox.get_node_or_null("ErrorLabel")
			if not error_label:
				error_label = Label.new()
				error_label.name = "ErrorLabel"
				error_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
				error_label.add_theme_font_size_override("font_size", 40)
				error_label.add_theme_color_override("font_color", Color(1, 0.3, 0.3, 1))
				error_label.autowrap_mode = TextServer.AUTOWRAP_WORD
				vbox.add_child(error_label)
				vbox.move_child(error_label, 1) # 置於標題下方
			
			error_label.text = "錯誤：" + reason
			error_label.visible = true
	else:
		# 如果沒在警語面板，就直接彈窗（保險起見）
		OS.alert(reason, "連線失敗")

func _on_network_room_created(room_id: String) -> void:
	print("Room joined/created successfully: ", room_id)
	AudioManager.play_room_created()
	$Phases/Phase0_Lobby/JoinPanel.visible = false
	current_room_id = room_id
	
	# 更新大廳 UI
	$Phases/Phase0_WaitLobby/VBox/RoomIDHBox/RoomIDLabel.text = "房間碼: " + room_id
	$Phases/Phase0_WaitLobby/VBox/BtnStartGame.visible = is_host
	$Phases/Phase0_WaitLobby/VBox/WaitingHint.visible = !is_host
	
	# 初始化玩家清單
	joined_players = [mock_self_name]
	_update_player_list_ui()
	
	switch_phase(GamePhase.WAIT_LOBBY)

func _on_btn_start_game() -> void:
	AudioManager.play_game_start()
	print("Host starting game...")
	NetworkManager.send_game_event("start_game", {})

func _on_btn_copy_id() -> void:
	if current_room_id != "":
		AudioManager.play_copy_id()
		DisplayServer.clipboard_set(current_room_id)
		# 簡單的視覺回饋
		$Phases/Phase0_WaitLobby/VBox/RoomIDHBox/BtnCopyID.text = "已複製"
		await get_tree().create_timer(1.5).timeout
		$Phases/Phase0_WaitLobby/VBox/RoomIDHBox/BtnCopyID.text = "複製"

func _update_player_list_ui() -> void:
	var text = "已加入玩家:\n"
	for p in joined_players:
		text += "- " + p + "\n"
	$Phases/Phase0_WaitLobby/VBox/PlayerListLabel.text = text

func _on_network_player_list_updated(players: Array) -> void:
	print("Room player list updated: ", players)
	# 只在有新玩家加入時播放音效（排除初始化與玩家離開）
	if players.size() > joined_players.size():
		AudioManager.play_player_join()
	joined_players = players
	_update_player_list_ui()

func _on_network_phase_sync(new_phase: String, data: Dictionary) -> void:
	print("Network Sync: Switching to ", new_phase)
	
	if new_phase == "SELECTION":
		# 接收伺服器指定的隊長
		current_captain = data.get("captain", "")
		print("New Captain: ", current_captain)
		
		# 重置一下按鈕狀態（以防是上一輪留下的殘留）
		$Phases/Phase3_Guessing/BtnSubmitMatch.disabled = false
		$Phases/Phase3_Guessing/BtnSubmitMatch.text = "送出配對結果"
		
		if current_captain == mock_self_name:
			# 通知：輪到你當隊長
			NotifManager.notify_captain()
			switch_phase(GamePhase.SELECTION)
		else:
			$Phases/Phase1_Waiting/VBox/CaptainInfoLabel.text = "目前隊長：" + current_captain
			switch_phase(GamePhase.SELECTION_WAITING)
			
	elif new_phase == "ANSWERING":
		current_level = data.get("level", 1)
		current_question = data.get("question", "")
		var q_card := $Phases/Phase2_Answering/VBox/QuestionCard
		q_card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var q_label := $Phases/Phase2_Answering/VBox/QuestionCard/Label
		q_label.text = current_question
		q_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		q_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		q_label.custom_minimum_size = Vector2(100, 0)
		($Phases/Phase2_Answering/VBox/AnswerArea/LineEdit as LineEdit).text = ""
		
		# 重置送出按鈕
		var submit_btn := $Phases/Phase2_Answering/VBox/AnswerArea/BtnSubmit
		submit_btn.disabled = true
		submit_btn.text = "送出答案"
		_set_btn_color(submit_btn, COLOR_BTN_DISABLED)
		
		# 通知：新題目來了
		NotifManager.notify_answering()
		switch_phase(GamePhase.ANSWERING)

	elif new_phase == "GUESSING":
		var remote_answers = data.get("answers", {})
		_setup_real_round(remote_answers)
		# 通知：配對階段開始
		NotifManager.notify_guessing()
		switch_phase(GamePhase.GUESSING)

	elif new_phase == "REVELATION":
		all_room_guesses = data.get("all_guesses", {})
		# 同步一下答案，確保揭曉時數據一致
		var remote_answers = data.get("all_answers", {})
		if remote_answers.size() > 0:
			round_answers = remote_answers
		# 通知：結果揭曉
		NotifManager.notify_revelation()
		switch_phase(GamePhase.REVELATION)

# ── Phase 1 ───────────────────────────────────────────────────────────────────
func _on_btn_level_pressed(level: int) -> void:
	# 只有隊長可以選題（MVP 測試階段先不做強硬限制，但邏輯上應由隊長觸發）
	var actual_level: int = level
	if level == 0:
		actual_level = (randi() % 5) + 1
	AudioManager.play_level_select(actual_level)
	
	var selected_q = _get_random_question(actual_level)
	
	print("Captain selected Level ", actual_level, ". Sending to server...")
	
	# 發送給伺服器，讓伺服器告訴所有人「進入回答階段」
	NetworkManager.send_game_event("topic_selected", {
		"level": actual_level,
		"question": selected_q
	})
	
	# 注意：這裡我們「不」直接呼叫 switch_phase，而是等待伺服器廣播回來
	# 這樣能確保所有人（包括隊長自己）都在同一秒進入下一關。

func _on_btn_back_pressed() -> void:
	AudioManager.play_cancel()
	switch_phase(GamePhase.WAITING)

# ── Phase 2 ───────────────────────────────────────────────────────────────────
func _on_answer_text_changed(new_text: String) -> void:
	var submit_btn := $Phases/Phase2_Answering/VBox/AnswerArea/BtnSubmit
	if new_text.strip_edges() == "":
		submit_btn.disabled = true
		_set_btn_color(submit_btn, COLOR_BTN_DISABLED)
	else:
		submit_btn.disabled = false
		_set_btn_color(submit_btn, COLOR_BTN_NORMAL)

func _set_btn_color(btn: Button, color: Color) -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = color
	sb.corner_radius_top_left = 16
	sb.corner_radius_top_right = 16
	sb.corner_radius_bottom_right = 16
	sb.corner_radius_bottom_left = 16
	sb.content_margin_top = 24.0
	sb.content_margin_bottom = 24.0
	sb.shadow_color = Color(0, 0, 0, 0.15)
	sb.shadow_size = 6
	sb.shadow_offset = Vector2(0, 4)
	btn.add_theme_stylebox_override("normal", sb)
	btn.add_theme_stylebox_override("hover", sb)
	btn.add_theme_stylebox_override("pressed", sb)
	btn.add_theme_stylebox_override("disabled", sb)

func _on_btn_submit_answer() -> void:
	var line_edit := $Phases/Phase2_Answering/VBox/AnswerArea/LineEdit as LineEdit
	self_answer = line_edit.text.strip_edges()
	if self_answer == "":
		self_answer = "(空白)"
	AudioManager.play_submit_answer()
	
	print("Submitting real answer: ", self_answer)
	NetworkManager.send_game_event("answer_submitted", {"answer": self_answer})
	
	# 視覺回饋：進入等待狀態
	var submit_btn := $Phases/Phase2_Answering/VBox/AnswerArea/BtnSubmit
	submit_btn.disabled = true
	submit_btn.text = "已提交，等待其他玩家..."
	_set_btn_color(submit_btn, COLOR_BTN_DISABLED)
	game_history.append({"question": current_question, "answer": self_answer})

func _on_btn_no_answer() -> void:
	self_answer = "不回答"
	AudioManager.play_no_answer()
	print("Submitting No Answer")
	NetworkManager.send_game_event("answer_submitted", {"answer": self_answer})
	
	# 視覺回饋
	var submit_btn_no := $Phases/Phase2_Answering/VBox/AnswerArea/BtnSubmit
	submit_btn_no.disabled = true
	submit_btn_no.text = "已提交，等待其他玩家..."
	_set_btn_color(submit_btn_no, COLOR_BTN_DISABLED)
	game_history.append({"question": current_question, "answer": self_answer})

# ── 實體數據同步 ────────────────────────────────────────────────────────────
func _setup_real_round(remote_answers: Dictionary) -> void:
	round_answers = remote_answers
	correct_map.clear()
	player_guesses.clear()

	# 建立正確對應表
	for player_name in round_answers:
		var ans: String = round_answers[player_name]
		correct_map[ans] = player_name

	print("=== Real Round Setup ===")
	for player_name in round_answers:
		print("  ", player_name, ": ", round_answers[player_name])

# ── Mock Data 準備 (保留作為測試或 fallback) ──────────────────────────────────
func _setup_mock_round() -> void:
	round_answers.clear()
	correct_map.clear()
	player_guesses.clear()

	# 自己的答案
	round_answers[mock_self_name] = self_answer

	# Mock 玩家的答案
	var pool: Array = mock_answer_pools.get(current_level, mock_answer_pools[1]).duplicate()
	pool.shuffle()

	# 隨機讓 1 位 Mock 玩家選「不回答」
	var no_answer_idx := randi() % mock_players.size()

	for i in range(mock_players.size()):
		var player_name: String = mock_players[i]
		if i == no_answer_idx:
			round_answers[player_name] = "不回答"
		else:
			if pool.size() > 0:
				round_answers[player_name] = pool.pop_back()
			else:
				round_answers[player_name] = "(沒有更多答案)"

	# 建立正確對應表
	for player_name in round_answers:
		var ans: String = round_answers[player_name]
		correct_map[ans] = player_name

	print("=== Mock Round Setup ===")
	for player_name in round_answers:
		print("  ", player_name, ": ", round_answers[player_name])

# ── Phase 3：動態生成 UI ──────────────────────────────────────────────────────
func _generate_phase3_ui() -> void:
	selected_answer_btn = null
	paired_count = 0
	answer_buttons.clear()
	participant_buttons.clear()
	answer_btn_map.clear()
	participant_btn_map.clear()
	partner_map.clear()
	partner_color_map.clear()
	player_guesses.clear()
	$Phases/Phase3_Guessing/BtnSubmitMatch.visible = true
	$Phases/Phase3_Guessing/BtnSubmitMatch.disabled = false
	$Phases/Phase3_Guessing/BtnSubmitMatch.text = "提交配對"
	
	# 自適應排版修正：確保按鈕不會被擠出畫面或被覆蓋
	var submit_match_btn := $Phases/Phase3_Guessing/BtnSubmitMatch
	submit_match_btn.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	submit_match_btn.offset_left = 40
	submit_match_btn.offset_right = -40
	submit_match_btn.offset_bottom = -40
	submit_match_btn.offset_top = -140
	
	# 讓 OuterVBox 底部留出空間，才不會蓋住按鈕
	var outer_vbox := $Phases/Phase3_Guessing/OuterVBox
	outer_vbox.set_anchors_preset(Control.PRESET_FULL_RECT)
	outer_vbox.offset_bottom = -160

	# 在頂部顯示題目
	var q_label: Label = outer_vbox.get_node_or_null("QuestionLabel")
	if q_label == null:
		q_label = Label.new()
		q_label.name = "QuestionLabel"
		q_label.add_theme_font_size_override("font_size", 32)
		q_label.add_theme_color_override("font_color", Color(1, 0.95, 0.8, 1))
		q_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		q_label.autowrap_mode = TextServer.AUTOWRAP_WORD
		q_label.custom_minimum_size = Vector2(100, 0) # 確保它能夠換行
		outer_vbox.add_child(q_label)
		outer_vbox.move_child(q_label, 0)
	q_label.text = "「" + current_question + "」"

	var flow_ans := $Phases/Phase3_Guessing/OuterVBox/AnswerPanel/InnerVBox/ScrollAnswers/FlowAnswers
	var flow_par := $Phases/Phase3_Guessing/OuterVBox/ParticipantPanel/InnerVBox/ScrollParticipants/FlowParticipants

	# 清除舊的動態按鈕
	for child in flow_ans.get_children():
		child.queue_free()
	for child in flow_par.get_children():
		child.queue_free()

	# 收集所有答案並打亂
	var all_answers: Array = []
	for player_name in round_answers:
		all_answers.append(round_answers[player_name])
	all_answers.shuffle()

	# 收集所有參與者並打亂
	var all_participants: Array = round_answers.keys()
	all_participants.shuffle()

	var self_ans: String = round_answers[mock_self_name]
	total_pairs = all_answers.size() - 1  # 減去自己的（自動配對）

	# ── 自適應調整：根據人數調整按鈕大小與字體 ──
	var player_count := all_participants.size()
	var pill_font_size := 34
	var pill_min_height := 80
	if player_count <= 3:
		pill_font_size = 46
		pill_min_height = 120
	elif player_count <= 5:
		pill_font_size = 38
		pill_min_height = 90

	var self_paired := false
	# 生成答案 pill
	for ans_text in all_answers:
		var btn := Button.new()
		btn.text = ans_text
		btn.custom_minimum_size = Vector2(0, pill_min_height)
		btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL # 讓它佔滿寬度
		btn.add_theme_font_size_override("font_size", pill_font_size)

		if ans_text == self_ans and not self_paired:
			_set_pill_style(btn, COLOR_AUTO_PAIRED)
			btn.disabled = true
			self_paired = true
		else:
			_set_pill_style(btn, COLOR_BTN_NORMAL)
			btn.pressed.connect(_on_answer_btn_pressed.bind(btn))

		flow_ans.add_child(btn)
		answer_buttons.append(btn)
		answer_btn_map[btn] = ans_text

	# 生成參與者 pill
	for p_name in all_participants:
		var btn := Button.new()
		btn.text = p_name
		btn.custom_minimum_size = Vector2(0, pill_min_height)
		btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL # 讓它佔滿寬度
		btn.add_theme_font_size_override("font_size", pill_font_size)

		if p_name == mock_self_name:
			_set_pill_style(btn, COLOR_AUTO_PAIRED)
			btn.disabled = true
		else:
			_set_pill_style(btn, COLOR_PARTICIPANT)
			btn.pressed.connect(_on_participant_btn_pressed.bind(btn))

		flow_par.add_child(btn)
		participant_buttons.append(btn)
		participant_btn_map[btn] = p_name

	print("Phase 3 UI generated: ", all_answers.size(), " answers, ", all_participants.size(), " participants")

# ── Phase 3：點擊配對邏輯 ─────────────────────────────────────────────────────
func _on_answer_btn_pressed(btn: Button) -> void:
	if partner_map.has(btn):
		_unmatch_pair(btn)
		return

	if selected_answer_btn != null and selected_answer_btn != btn:
		if not partner_map.has(selected_answer_btn):
			_set_pill_style(selected_answer_btn, COLOR_BTN_NORMAL)
			_anim_pill_deselect(selected_answer_btn)

	selected_answer_btn = btn
	_set_pill_style(btn, COLOR_HIGHLIGHT)
	_anim_pill_select(btn)
	print("Answer selected: ", btn.text)

func _anim_pill_select(btn: Button) -> void:
	var tw := create_tween().set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	btn.scale = Vector2(0.92, 0.92)
	btn.pivot_offset = btn.size / 2.0
	tw.tween_property(btn, "scale", Vector2(1.06, 1.06), 0.12)
	tw.tween_property(btn, "scale", Vector2(1.0, 1.0), 0.10)

func _anim_pill_deselect(btn: Button) -> void:
	var tw := create_tween().set_trans(Tween.TRANS_SINE)
	tw.tween_property(btn, "scale", Vector2(1.0, 1.0), 0.10)

func _on_participant_btn_pressed(btn: Button) -> void:
	if partner_map.has(btn):
		_unmatch_pair(btn)
		return

	if selected_answer_btn == null:
		return

	var ans_text: String = answer_btn_map[selected_answer_btn]
	var p_name: String = participant_btn_map[btn]
	player_guesses[p_name] = ans_text

	var pair_color = PAIR_COLORS[paired_count % PAIR_COLORS.size()]
	_set_pill_style(selected_answer_btn, pair_color)
	_set_pill_style(btn, pair_color)
	# 配對成功 bounce 動畫 + 音效
	AudioManager.play_pill_match()
	_anim_pill_match(selected_answer_btn)
	_anim_pill_match(btn)

	partner_map[selected_answer_btn] = btn
	partner_map[btn] = selected_answer_btn
	partner_color_map[selected_answer_btn] = pair_color
	partner_color_map[btn] = pair_color

	print("Paired: [", ans_text, "] <-> [", p_name, "] with color ", pair_color)

	selected_answer_btn = null
	paired_count += 1
	
	# 原本是全員配對才顯示，現在改為一直顯示，但可以做視覺提示
	var submit_btn := $Phases/Phase3_Guessing/BtnSubmitMatch
	if paired_count >= total_pairs:
		submit_btn.text = "完成配對！送出"
	else:
		submit_btn.text = "提交目前的配對"

func _anim_pill_match(btn: Button) -> void:
	btn.pivot_offset = btn.size / 2.0
	var tw := create_tween().set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)
	tw.tween_property(btn, "scale", Vector2(1.12, 1.12), 0.10)
	tw.tween_property(btn, "scale", Vector2(1.0, 1.0), 0.25)

func _unmatch_pair(btn: Button) -> void:
	var partner: Button = partner_map.get(btn)
	if partner == null: return
	
	AudioManager.play_pill_unmatch()
	# 找出誰是答案按鈕，誰是參與者按鈕
	var ans_btn: Button = btn if answer_btn_map.has(btn) else partner
	var par_btn: Button = partner if answer_btn_map.has(btn) else btn
	
	# 從猜測紀錄移除
	var par_name = participant_btn_map[par_btn]
	var ans_text = answer_btn_map[ans_btn]
	player_guesses.erase(par_name)
	
	# 復原樣式
	_set_pill_style(ans_btn, COLOR_BTN_NORMAL)
	_set_pill_style(par_btn, COLOR_PARTICIPANT)
	
	# 移除配對資訊
	partner_map.erase(ans_btn)
	partner_map.erase(par_btn)
	partner_color_map.erase(ans_btn)
	partner_color_map.erase(par_btn)
	
	paired_count -= 1
	
	var submit_btn := $Phases/Phase3_Guessing/BtnSubmitMatch
	if paired_count < total_pairs:
		submit_btn.text = "提交目前的配對"
	
	print("Unmatched pair: ", ans_text)

func _set_pill_style(btn: Button, color: Color) -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = color
	sb.corner_radius_top_left    = 80
	sb.corner_radius_top_right   = 80
	sb.corner_radius_bottom_right = 80
	sb.corner_radius_bottom_left  = 80
	sb.content_margin_left   = 40.0
	sb.content_margin_right  = 40.0
	sb.content_margin_top    = 22.0
	sb.content_margin_bottom = 22.0
	sb.shadow_color = Color(0, 0, 0, 0.12)
	sb.shadow_size = 5
	sb.shadow_offset = Vector2(0, 3)
	btn.add_theme_stylebox_override("normal",  sb)
	btn.add_theme_stylebox_override("hover",   sb)
	btn.add_theme_stylebox_override("pressed", sb)
	btn.add_theme_stylebox_override("disabled", sb)

# ── Phase 3：送出配對 ──────────────────────────────────────────────────────────
func _on_btn_submit_match() -> void:
	AudioManager.play_tap()
	var self_ans: String = round_answers[mock_self_name]
	player_guesses[self_ans] = mock_self_name
	
	print("Sending guesses to server...")
	NetworkManager.send_game_event("guesses_submitted", {"guesses": player_guesses})
	
	# 視覺回饋：等待中
	$Phases/Phase3_Guessing/BtnSubmitMatch.disabled = true
	$Phases/Phase3_Guessing/BtnSubmitMatch.text = "等待其他玩家..."

# ── Phase 4：戲劇性結果揭曉與計分 ────────────────────────────────────────────
func _generate_phase4_ui() -> void:
	# 進入 Phase 4 時，重置接續下一輪按鈕
	var btn_next = $Phases/Phase4_Revelation/VBox/BtnNextRound
	btn_next.disabled = false
	btn_next.text = "接續下一輪"
	_set_btn_color(btn_next, COLOR_BTN_NORMAL)
	
	# ── 調整字體大小 ──
	var q_label := $Phases/Phase4_Revelation/VBox/QuestionLabel
	q_label.text = "「" + current_question + "」"
	q_label.add_theme_font_size_override("font_size", 33) # 題目加大 1 單位 (原本 32)
	q_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	q_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	q_label.custom_minimum_size = Vector2(100, 0) # 確保它能夠換行
	q_label.modulate.a = 0.0
	var title_tw := create_tween().set_trans(Tween.TRANS_SINE)
	title_tw.tween_property(q_label, "modulate:a", 1.0, 0.4)

	var results_vbox := $Phases/Phase4_Revelation/VBox/ScrollContainer/ResultsVBox
	for child in results_vbox.get_children():
		child.queue_free()

	# ── 計算本輪「你猜中幾個隊友」──
	var correct_count := 0
	var guess_total := 0

	# ── 自適應調整：根據結果數量調整字體 ──
	var result_count := guess_total
	var font_size_ans := 34 # 加大 2 單位 (原本 32)
	var font_size_res := 30 # 加大 2 單位 (原本 28)
	if result_count <= 3:
		font_size_ans = 46 # 加大 2 單位 (原本 44)
		font_size_res = 38 # 加大 2 單位 (原本 36)
	elif result_count <= 5:
		font_size_ans = 38 # 加大 2 單位 (原本 36)
		font_size_res = 32 # 加大 2 單位 (原本 30)

	var stagger_delay := 0.0
	
	# 建立我們所有的猜測清單
	var unused_guesses := player_guesses.duplicate() # {participant: ans_text}
	
	# 預先找出所有「猜對」的玩家，因為有多個相同答案時，必須優先結算對的
	var correct_evals = {}
	for player_name in round_answers:
		if player_name == mock_self_name: continue
		var actual_ans: String = round_answers[player_name]
		if unused_guesses.get(player_name) == actual_ans:
			correct_evals[player_name] = true
			unused_guesses.erase(player_name) # 標記為已使用
			
	for player_name in round_answers:
		if player_name == mock_self_name:
			continue
		var ans_text: String = round_answers[player_name]
		var is_correct: bool = correct_evals.has(player_name)
		var guessed_player: String = "?"
		
		if is_correct:
			guessed_player = player_name
		else:
			# 從剩下的錯誤猜測中，找一個「答案文字」符合 ans_text 的來顯示
			for p_name in unused_guesses.keys():
				if unused_guesses[p_name] == ans_text:
					guessed_player = p_name
					unused_guesses.erase(p_name)
					break
			# 防呆：如果數量對不上，至少隨便顯示一個
			if guessed_player == "?":
				for p_name in unused_guesses.keys():
					guessed_player = p_name
					unused_guesses.erase(p_name)
					break

		guess_total += 1
		if is_correct:
			correct_count += 1

		var row := _create_result_row(ans_text, player_name, guessed_player, is_correct, font_size_ans, font_size_res)
		results_vbox.add_child(row)
		# 飛入動畫：從右側滑入 + 淡入（錯開時間）
		row.modulate.a = 0.0
		row.position.x += 80.0
		var d := stagger_delay
		var stagger_tw := create_tween().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
		stagger_tw.tween_interval(d)
		stagger_tw.tween_callback(func():
			if is_correct:
				AudioManager.play_result_correct()
			else:
				AudioManager.play_result_wrong()
		)
		stagger_tw.tween_property(row, "modulate:a", 1.0, 0.35)
		var row_ref := row
		stagger_tw.parallel().tween_property(row_ref, "position:x", row_ref.position.x - 80.0, 0.35)
		stagger_delay += 0.18

	# ── 計算「你的答案被幾個隊友猜中」（真實數據同步）──
	var round_guessed_by := 0
	var round_others_count := 0
	
	var self_ans_text: String = round_answers.get(mock_self_name, "")
	
	# 遍歷所有人的猜測，看看有誰猜中了我的答案
	for other_name in all_room_guesses:
		if other_name == mock_self_name:
			continue
		
		round_others_count += 1
		var other_guesses: Dictionary = all_room_guesses[other_name]
		# 如果那位隊友猜測「我的答案」屬於「我」
		# 這裡的 other_guesses 結構是 {participant_name: ans_text}
		if other_guesses.get(mock_self_name) == self_ans_text:
			round_guessed_by += 1

	# ── 累計統計 ──
	cumul_my_correct += correct_count
	cumul_my_attempts += guess_total
	cumul_guessed_by_others += round_guessed_by
	cumul_others_attempts += round_others_count

	# ── 計算百分比 ──
	var my_accuracy_pct := 0.0
	if cumul_my_attempts > 0:
		my_accuracy_pct = float(cumul_my_correct) / float(cumul_my_attempts) * 100.0
	var guessed_by_pct := 0.0
	if cumul_others_attempts > 0:
		guessed_by_pct = float(cumul_guessed_by_others) / float(cumul_others_attempts) * 100.0

	# ── 更新 UI ──
	var score_label := $Phases/Phase4_Revelation/VBox/ScoreLabel
	score_label.text = "猜對 " + str(correct_count) + " / " + str(guess_total) + " 題"
	score_label.add_theme_font_size_override("font_size", 50) # 成績加大 2 單位 (原本 48)

	# 累計統計區塊
	var stats_vbox := $Phases/Phase4_Revelation/VBox.get_node_or_null("StatsVBox")
	if stats_vbox == null:
		stats_vbox = VBoxContainer.new()
		stats_vbox.name = "StatsVBox"
		stats_vbox.add_theme_constant_override("separation", 12)
		# 插入在 ScoreLabel 之後、BtnNextRound 之前
		var score_idx: int = $Phases/Phase4_Revelation/VBox/ScoreLabel.get_index()
		$Phases/Phase4_Revelation/VBox.add_child(stats_vbox)
		$Phases/Phase4_Revelation/VBox.move_child(stats_vbox, score_idx + 1)
	else:
		for child in stats_vbox.get_children():
			child.queue_free()

	# 猜中率
	var guess_label := Label.new()
	guess_label.text = "你的猜中率：" + str(cumul_my_correct) + "/" + str(cumul_my_attempts) + "（0.0%）"
	guess_label.add_theme_font_size_override("font_size", 32) # 成績加大 2 單位 (原本 30)
	guess_label.add_theme_color_override("font_color", COLOR_CORRECT)
	guess_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	stats_vbox.add_child(guess_label)
	
	# 計數動畫：你的猜中率
	var guess_tween := create_tween().set_trans(Tween.TRANS_QUART).set_ease(Tween.EASE_OUT)
	guess_tween.tween_interval(0.5) 
	guess_tween.tween_method(func(v: float):
		if is_instance_valid(guess_label):
			guess_label.text = "你的猜中率：" + str(cumul_my_correct) + "/" + str(cumul_my_attempts) + "（" + str(snapped(v, 0.1)) + "%）"
	, 0.0, my_accuracy_pct, 1.2)

	# 被猜中率
	var guessed_label := Label.new()
	guessed_label.text = "被隊友猜中：" + str(cumul_guessed_by_others) + "/" + str(cumul_others_attempts) + "（0.0%）"
	guessed_label.add_theme_font_size_override("font_size", 32) # 成績加大 2 單位 (原本 30)
	guessed_label.add_theme_color_override("font_color", Color(0.98, 0.82, 0.20, 1))
	guessed_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	stats_vbox.add_child(guessed_label)

	# 計數動畫：被隊友猜中率
	var guessed_tween := create_tween().set_trans(Tween.TRANS_QUART).set_ease(Tween.EASE_OUT)
	guessed_tween.tween_interval(0.7)
	guessed_tween.tween_method(func(v: float):
		if is_instance_valid(guessed_label):
			guessed_label.text = "被隊友猜中：" + str(cumul_guessed_by_others) + "/" + str(cumul_others_attempts) + "（" + str(snapped(v, 0.1)) + "%）"
	, 0.0, guessed_by_pct, 1.2)

	print("Phase 4 Score: ", correct_count, "/", guess_total)
	print("Cumulative - 猜中率: ", cumul_my_correct, "/", cumul_my_attempts, " (", snapped(my_accuracy_pct, 0.1), "%)")
	print("Cumulative - 被猜中: ", cumul_guessed_by_others, "/", cumul_others_attempts, " (", snapped(guessed_by_pct, 0.1), "%)")

func _create_result_row(ans_text: String, correct_player: String, guessed_player: String, is_correct: bool, font_ans: int, font_res: int) -> PanelContainer:
	var panel := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.18, 0.16, 0.14, 1)
	sb.corner_radius_top_left = 16
	sb.corner_radius_top_right = 16
	sb.corner_radius_bottom_right = 16
	sb.corner_radius_bottom_left = 16
	sb.content_margin_left = 20.0
	sb.content_margin_right = 20.0
	sb.content_margin_top = 16.0
	sb.content_margin_bottom = 16.0
	panel.add_theme_stylebox_override("panel", sb)

	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 8)
	panel.add_child(vbox)

	# 答案文字
	var ans_label := Label.new()
	ans_label.text = "「" + ans_text + "」"
	ans_label.add_theme_font_size_override("font_size", font_ans)
	ans_label.add_theme_color_override("font_color", Color(1, 0.95, 0.8, 1))
	ans_label.autowrap_mode = TextServer.AUTOWRAP_WORD
	vbox.add_child(ans_label)

	# 配對結果
	var result_label := Label.new()
	if is_correct:
		result_label.text = "✓ 正確！是 " + correct_player + " 的答案"
		result_label.add_theme_color_override("font_color", COLOR_CORRECT)
	else:
		result_label.text = "✗ 你猜 " + guessed_player + "，正確答案是 " + correct_player
		result_label.add_theme_color_override("font_color", COLOR_WRONG)
	result_label.add_theme_font_size_override("font_size", font_res)
	result_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	result_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	vbox.add_child(result_label)

	return panel

# ── Phase 4：再玩一輪（更換隊長邏輯） ──────────────────────────────────────────
func _on_btn_next_round() -> void:
	AudioManager.play_tap()
	var btn = $Phases/Phase4_Revelation/VBox/BtnNextRound
	btn.disabled = true
	btn.text = "已準備，等待中..."
	_set_btn_color(btn, COLOR_BTN_DISABLED)
	
	print("Ready for next round...")
	NetworkManager.send_game_event("ready_for_next_round", {})

func _on_network_next_round_status(ready: int, total: int) -> void:
	var btn = $Phases/Phase4_Revelation/VBox/BtnNextRound
	if btn.disabled:
		btn.text = "等待其他人... (" + str(ready) + "/" + str(total) + ")"

func _on_btn_leave_circle_pressed() -> void:
	AudioManager.play_cancel()
	switch_phase(GamePhase.SUMMARY)

# ── Phase 5：個人結算與確定離開 ──────────────────────────────────────────────
func _generate_phase5_ui() -> void:
	var vbox := $Phases/Phase5_Summary/VBox/PersonalResultPanel/VBox
	vbox.get_node("NameLabel").text = "玩家：" + mock_self_name
	
	# 清除舊的歷史顯示
	var history_vbox := vbox.get_node("HistoryScroll/HistoryVBox")
	for child in history_vbox.get_children():
		child.queue_free()
	
	# 生成所有歷史問答
	for record in game_history:
		var q_label := Label.new()
		q_label.text = "問：" + record["question"]
		q_label.add_theme_font_size_override("font_size", 32)
		q_label.add_theme_color_override("font_color", Color(0.9, 0.9, 0.9, 1))
		q_label.autowrap_mode = TextServer.AUTOWRAP_WORD
		history_vbox.add_child(q_label)
		
		var a_label := Label.new()
		a_label.text = "答：" + record["answer"]
		a_label.add_theme_font_size_override("font_size", 36)
		a_label.add_theme_color_override("font_color", Color(0.98, 0.82, 0.2, 1))
		a_label.autowrap_mode = TextServer.AUTOWRAP_WORD
		history_vbox.add_child(a_label)
		
		# 加入分隔線或間距
		var spacer := Control.new()
		spacer.custom_minimum_size.y = 10
		history_vbox.add_child(spacer)
	
	# 計算累計百分比
	var my_accuracy_pct := 0.0
	if cumul_my_attempts > 0:
		my_accuracy_pct = float(cumul_my_correct) / float(cumul_my_attempts) * 100.0
	
	vbox.get_node("StatsLabel").text = "累計猜中率：" + str(snapped(my_accuracy_pct, 0.1)) + "% (" + str(cumul_my_correct) + "/" + str(cumul_my_attempts) + ")"

func _on_btn_final_leave_pressed() -> void:
	AudioManager.play_cancel() # 播放離開音效
	print("Leaving circle definitively...")
	NetworkManager.send_game_event("leave_room", {})
	
	# 重置本地累計數據與歷史
	cumul_guessed_by_others = 0
	cumul_others_attempts = 0
	cumul_my_correct = 0
	cumul_my_attempts = 0
	game_history = []
	
	# 重置 NetworkManager 狀態
	NetworkManager.current_room_id = ""
	NetworkManager.socket.close()
	
	# 隱藏所有大廳的子彈窗，確保回到乾淨的標題畫面
	$Phases/Phase0_Lobby/JoinPanel.visible = false
	$Phases/Phase0_Lobby/NamePanel.visible = false
	var ad_panel = $Phases/Phase0_Lobby.get_node_or_null("AdDisclaimerPanel")
	if ad_panel:
		ad_panel.visible = false
	
	switch_phase(GamePhase.WAITING)

# ── 全域按鈕與輸入框美化輔助函數 ──────────────────────────────────────────────
func _register_button_animations(node: Node) -> void:
	if node is Button:
		var btn = node as Button
		# 排除 Phase 3 的動態 Pill 按鈕，因為它們有自訂的選擇和配對動畫
		var parent = btn.get_parent()
		var is_p3_pill = parent and (parent.name == "FlowAnswers" or parent.name == "FlowParticipants")
		if not is_p3_pill:
			_setup_button_hover_press_tween(btn)
	for child in node.get_children():
		_register_button_animations(child)

func _setup_button_hover_press_tween(btn: Button) -> void:
	btn.pivot_offset = btn.size / 2.0
	if not btn.resized.is_connected(self._on_btn_resized.bind(btn)):
		btn.resized.connect(self._on_btn_resized.bind(btn))
	
	# 滑鼠移入（放大）
	btn.mouse_entered.connect(func():
		if btn.disabled: return
		var tw := create_tween().set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		tw.tween_property(btn, "scale", Vector2(1.04, 1.04), 0.12)
	)
	
	# 滑鼠移出（還原）
	btn.mouse_exited.connect(func():
		if btn.disabled: return
		var tw := create_tween().set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		tw.tween_property(btn, "scale", Vector2(1.0, 1.0), 0.12)
	)
	
	# 按鈕按下（下壓）
	btn.button_down.connect(func():
		if btn.disabled: return
		var tw := create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
		tw.tween_property(btn, "scale", Vector2(0.94, 0.94), 0.06)
	)
	
	# 按鈕放開（還原或維持 Hover）
	btn.button_up.connect(func():
		if btn.disabled: return
		var target_scale = Vector2(1.04, 1.04) if btn.is_hovered() else Vector2(1.0, 1.0)
		var tw := create_tween().set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		tw.tween_property(btn, "scale", target_scale, 0.12)
	)

func _on_btn_resized(btn: Button) -> void:
	btn.pivot_offset = btn.size / 2.0

func _style_line_edit(line_edit: LineEdit) -> void:
	var sb_normal := StyleBoxFlat.new()
	sb_normal.bg_color = Color(0.08, 0.07, 0.07, 1)
	sb_normal.corner_radius_top_left = 16
	sb_normal.corner_radius_top_right = 16
	sb_normal.corner_radius_bottom_right = 16
	sb_normal.corner_radius_bottom_left = 16
	sb_normal.border_width_left = 2
	sb_normal.border_width_top = 2
	sb_normal.border_width_right = 2
	sb_normal.border_width_bottom = 2
	sb_normal.border_color = Color(0.28, 0.25, 0.22, 1)
	sb_normal.content_margin_left = 24.0
	sb_normal.content_margin_right = 24.0
	sb_normal.content_margin_top = 16.0
	sb_normal.content_margin_bottom = 16.0
	
	var sb_focus := sb_normal.duplicate() as StyleBoxFlat
	sb_focus.border_color = COLOR_BTN_HOVER
	sb_focus.shadow_color = Color(0.815, 0.505, 0.235, 0.15)
	sb_focus.shadow_size = 10
	sb_focus.shadow_offset = Vector2(0, 4)
	
	line_edit.add_theme_stylebox_override("normal", sb_normal)
	line_edit.add_theme_stylebox_override("focus", sb_focus)
	line_edit.add_theme_color_override("font_color", Color(0.98, 0.95, 0.9, 1))
	line_edit.add_theme_color_override("placeholder_color", Color(0.5, 0.45, 0.4, 1))

# ── App 前景/背景偵測 — 取消通知 ─────────────────────────────────────────────
func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_IN:
		# App 回到前景 → 取消所有已排程的通知
		NotifManager.cancel_all()
