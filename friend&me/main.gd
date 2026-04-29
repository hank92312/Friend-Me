extends Control

enum GamePhase { WAITING, SELECTION, ANSWERING, GUESSING, REVELATION }

# ── 顏色常數 ──────────────────────────────────────────────────────────────────
const COLOR_BTN_NORMAL   := Color(0.815686, 0.505882, 0.235294, 1)  # 溫暖橘色
const COLOR_BTN_HOVER    := Color(0.890196, 0.580392, 0.313726, 1)  # 亮橘色
const COLOR_HIGHLIGHT    := Color(0.980, 0.820, 0.200, 1)           # 高亮：金黃
const COLOR_MATCHED      := Color(0.350, 0.620, 0.380, 1)           # 已配對：溫暖綠
const COLOR_PARTICIPANT  := Color(0.42,  0.30,  0.18,  1)           # 參與者預設：溫暖中棕

# ── 節點引用 ──────────────────────────────────────────────────────────────────
@onready var phase_nodes: Dictionary = {
	GamePhase.WAITING:    $Phases/Phase0_Lobby,
	GamePhase.SELECTION:  $Phases/Phase1_Selection,
	GamePhase.ANSWERING:  $Phases/Phase2_Answering,
	GamePhase.GUESSING:   $Phases/Phase3_Guessing,
	GamePhase.REVELATION: $Phases/Phase4_Revelation
}

# Phase 3 狀態
var selected_answer_btn: Button = null   # 目前高亮的答案按鈕
var answer_buttons: Array[Button] = []   # 所有答案按鈕
var participant_buttons: Array[Button] = []  # 所有參與者按鈕
var paired_count := 0
var total_pairs  := 0

# 題庫資料
var question_bank: Dictionary = {}
var current_question: String = ""

var current_phase: GamePhase = GamePhase.WAITING

# ── 初始化 ────────────────────────────────────────────────────────────────────
func _ready() -> void:
	# 載入題庫
	_load_question_bank()

	# Phase 0
	$Phases/Phase0_Lobby/VBoxContainer/BtnCreate.pressed.connect(_on_btn_create_pressed)

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

	# Phase 3 ── 蒐集所有答案與參與者按鈕
	var flow_ans := $Phases/Phase3_Guessing/OuterVBox/AnswerPanel/InnerVBox/FlowAnswers
	var flow_par := $Phases/Phase3_Guessing/OuterVBox/ParticipantPanel/InnerVBox/FlowParticipants
	for child in flow_ans.get_children():
		if child is Button:
			answer_buttons.append(child)
			child.pressed.connect(_on_answer_btn_pressed.bind(child))
	for child in flow_par.get_children():
		if child is Button:
			participant_buttons.append(child)
			child.pressed.connect(_on_participant_btn_pressed.bind(child))
	total_pairs = answer_buttons.size()
	$Phases/Phase3_Guessing/BtnSubmitMatch.pressed.connect(_on_btn_submit_match)

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

# ── 通用切換畫面 ──────────────────────────────────────────────────────────────
func switch_phase(new_phase: GamePhase) -> void:
	current_phase = new_phase
	for key in phase_nodes:
		phase_nodes[key].visible = (key == current_phase)
	print("Switched to phase: ", GamePhase.keys()[current_phase])

	# 切換到 Phase 3 時重置配對狀態
	if new_phase == GamePhase.GUESSING:
		_reset_guessing_state()

# ── Phase 0 ───────────────────────────────────────────────────────────────────
func _on_btn_create_pressed() -> void:
	switch_phase(GamePhase.SELECTION)

# ── Phase 1 ───────────────────────────────────────────────────────────────────
func _on_btn_level_pressed(level: int) -> void:
	var actual_level: int = level
	if level == 0:
		actual_level = (randi() % 5) + 1
	print("Selected Level: ", actual_level, (" (Random)" if level == 0 else ""))

	# 從題庫抽題並顯示在 Phase 2
	current_question = _get_random_question(actual_level)
	$Phases/Phase2_Answering/VBox/QuestionCard/Label.text = current_question

	# 清空上一輪的輸入
	($Phases/Phase2_Answering/VBox/AnswerArea/LineEdit as LineEdit).text = ""

	switch_phase(GamePhase.ANSWERING)

func _on_btn_back_pressed() -> void:
	switch_phase(GamePhase.WAITING)

# ── Phase 2 ───────────────────────────────────────────────────────────────────
func _on_btn_submit_answer() -> void:
	var line_edit := $Phases/Phase2_Answering/VBox/AnswerArea/LineEdit as LineEdit
	var answer: String = line_edit.text.strip_edges()
	print("Answer submitted: ", answer if answer != "" else "(empty)")
	switch_phase(GamePhase.GUESSING)

func _on_btn_no_answer() -> void:
	print("Player chose: No Answer")
	switch_phase(GamePhase.GUESSING)

# ── Phase 3：點擊配對邏輯 ─────────────────────────────────────────────────────
func _reset_guessing_state() -> void:
	selected_answer_btn = null
	paired_count = 0
	$Phases/Phase3_Guessing/BtnSubmitMatch.visible = false

	for btn in answer_buttons:
		btn.disabled = false
		_set_btn_bg_color(btn, COLOR_BTN_NORMAL)

	for btn in participant_buttons:
		btn.disabled = false
		_set_btn_bg_color(btn, COLOR_PARTICIPANT)

func _on_answer_btn_pressed(btn: Button) -> void:
	if btn.disabled:
		return
	# 取消前一個高亮（若非已配對）
	if selected_answer_btn != null and selected_answer_btn != btn:
		_set_btn_bg_color(selected_answer_btn, COLOR_BTN_NORMAL)

	selected_answer_btn = btn
	_set_btn_bg_color(btn, COLOR_HIGHLIGHT)
	print("Answer selected: ", btn.text)

func _on_participant_btn_pressed(btn: Button) -> void:
	if btn.disabled or selected_answer_btn == null:
		return

	# 配對完成：兩者變綠，停用
	_set_btn_bg_color(selected_answer_btn, COLOR_MATCHED)
	_set_btn_bg_color(btn, COLOR_MATCHED)
	selected_answer_btn.disabled = true
	btn.disabled = true
	print("Paired: [", selected_answer_btn.text, "] <-> [", btn.text, "]")

	selected_answer_btn = null
	paired_count += 1

	# 全部配對完成才顯示送出按鈕
	if paired_count >= total_pairs:
		$Phases/Phase3_Guessing/BtnSubmitMatch.visible = true
		print("All pairs matched! Submit button shown.")

# 用 StyleBoxFlat 改變 Button 的背景色（create_stylebox_flat 動態產生）
func _set_btn_bg_color(btn: Button, color: Color) -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = color
	sb.corner_radius_top_left    = 16
	sb.corner_radius_top_right   = 16
	sb.corner_radius_bottom_right = 16
	sb.corner_radius_bottom_left  = 16
	sb.content_margin_top    = 16.0
	sb.content_margin_bottom = 16.0
	sb.content_margin_left   = 16.0
	sb.content_margin_right  = 16.0
	btn.add_theme_stylebox_override("normal",  sb)
	btn.add_theme_stylebox_override("hover",   sb)
	btn.add_theme_stylebox_override("pressed", sb)
	btn.add_theme_stylebox_override("disabled", sb)

# ── Phase 3：送出配對 ──────────────────────────────────────────────────────────
func _on_btn_submit_match() -> void:
	print("Guesses submitted -> Phase 4")
	switch_phase(GamePhase.REVELATION)
