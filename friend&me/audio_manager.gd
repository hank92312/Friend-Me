extends Node

## AudioManager — 全域音效管理 Autoload
## 依據 SFX_Design_Brief.md 規範，統一管理所有 UI 短音效的播放。
## 暫時跳過的音效：sfx_pill_select / sfx_reveal_card / sfx_reconnect_ok
## 尚未製作的音效：sfx_pill_unmatch / sfx_result_correct / sfx_result_wrong

# ── 音效播放器池 ──────────────────────────────────────────────────────────────
var _players: Array[AudioStreamPlayer] = []

# ── 音效資源 preload ─────────────────────────────────────────────────────────
var sfx_btn_tap:        AudioStream = preload("res://audio/sfx/sfx_btn_tap.ogg")
var sfx_btn_cancel:     AudioStream = preload("res://audio/sfx/sfx_btn_cancel.ogg")
var sfx_room_created:   AudioStream = preload("res://audio/sfx/sfx_room_created.ogg")
var sfx_player_join:    AudioStream = preload("res://audio/sfx/sfx_player_join.ogg")
var sfx_copy_id:        AudioStream = preload("res://audio/sfx/sfx_copy_id.ogg")
var sfx_game_start:     AudioStream = preload("res://audio/sfx/sfx_game_start.ogg")
var sfx_level_select:   AudioStream = preload("res://audio/sfx/sfx_level_select.ogg")
var sfx_submit_answer:  AudioStream = preload("res://audio/sfx/sfx_submit_answer.ogg")
var sfx_no_answer:      AudioStream = preload("res://audio/sfx/sfx_no_answer.ogg")
var sfx_pill_match:     AudioStream = preload("res://audio/sfx/sfx_pill_match.ogg")
var sfx_pill_unmatch:   AudioStream = preload("res://audio/sfx/sfx_pill_unmatch.ogg")
var sfx_result_correct: AudioStream = preload("res://audio/sfx/sfx_result_correct.ogg")
var sfx_result_wrong:   AudioStream = preload("res://audio/sfx/sfx_result_wrong.ogg")
var sfx_next_round:     AudioStream = preload("res://audio/sfx/sfx_next_round.ogg")

# ── 暫時停用（經測試會稍微打亂遊玩節奏，先暫時不使用） ─────────────
# var sfx_pill_select:     AudioStream  # 暫時跳過
# var sfx_reveal_card:     AudioStream  # 暫時跳過
# var sfx_reconnect_ok:    AudioStream  # 暫時跳過

# ── 靜音控制 ────────────────────────────────────────────────────────────────
var is_muted: bool = false

func _ready() -> void:
	# 預建 8 個播放器，因應連續快速觸發（如 Phase 4 stagger 揭幕）
	for i in range(8):
		var p := AudioStreamPlayer.new()
		p.bus = "Master"
		add_child(p)
		_players.append(p)

func _get_available_player() -> AudioStreamPlayer:
	for p in _players:
		if not p.playing:
			return p
	# 全部忙碌時回傳最早的（強制覆蓋）
	return _players[0]

## 通用底層播放
func play_sfx(stream: AudioStream, pitch: float = 1.0, volume_db: float = 0.0) -> void:
	if stream == null or is_muted:
		return
	var p := _get_available_player()
	p.stream = stream
	p.pitch_scale = pitch
	p.volume_db = volume_db
	p.play()

# ══════════════════════════════════════════════════════════════════════════════
# 各觸發事件的專屬播放方法
# ══════════════════════════════════════════════════════════════════════════════

## 1. 一般按鈕點擊（創立房間/加入房間/確認名字/確認房間碼）
func play_tap() -> void:
	play_sfx(sfx_btn_tap)

## 2. 取消 / 返回按鈕（BtnCancelJoin / BtnCancelName / BtnBack）
##    Brief: 比 btn_tap 略低沉，pitch 降低 3-4 個半音
func play_cancel() -> void:
	play_sfx(sfx_btn_cancel, 0.8)

## 3. 房間建立成功
func play_room_created() -> void:
	play_sfx(sfx_room_created)

## 4. 玩家加入大廳
func play_player_join() -> void:
	play_sfx(sfx_player_join)

## 5. 複製房間碼
func play_copy_id() -> void:
	play_sfx(sfx_copy_id)

## 6. 開始遊戲（房主按下）
func play_game_start() -> void:
	play_sfx(sfx_game_start)

## 7. 選擇難度等級 — 讓同一音效在不同等級聽起來截然不同
##    透過 pitch（音高）+ 延遲疊加（模擬殘響/厚度）
##    對應遊戲社交深度：LV1 輕快日常 → LV5 深沉靈魂拷問
##    音量已經過正規化統一，這裡只調 pitch 與回音
func play_level_select(level: int) -> void:
	var pitch := 1.0
	var echo_count := 0      # 疊加回音層數（營造厚度）
	var echo_pitch_offset := 0.0
	var echo_delay := 0.0

	match level:
		1:  # 日話家常 — 輕快、明亮、乾淨
			pitch = 1.25
		2:  # 下午茶閒聊 — 稍高、舒適
			pitch = 1.12
		3:  # 居酒屋微醺 — 中性、穩定
			pitch = 1.0
		4:  # 深夜真心話 — 下沉、帶一層迴響
			pitch = 0.85
			echo_count = 1
			echo_pitch_offset = -0.08
			echo_delay = 0.06
		5:  # 靈魂拷問 — 最低沉、雙層迴響，莊重儀式感
			pitch = 0.72
			echo_count = 2
			echo_pitch_offset = -0.06
			echo_delay = 0.07
		_:  # Random — 隨機抽取一個等級的風格
			var random_lv := (randi() % 5) + 1
			play_level_select(random_lv)
			return

	# 主音
	play_sfx(sfx_level_select, pitch)

	# 延遲回音層（營造 LV4/5 的厚重感與殘響感）
	for i in range(echo_count):
		var delay_time := echo_delay * (i + 1)
		var echo_pitch := pitch + echo_pitch_offset * (i + 1)
		var echo_vol := -6.0 * (i + 1)  # 每層遞減 6dB
		get_tree().create_timer(delay_time).timeout.connect(
			func(): play_sfx(sfx_level_select, echo_pitch, echo_vol)
		)

## 8. 送出答案
func play_submit_answer() -> void:
	play_sfx(sfx_submit_answer)

## 9. 選擇「不回答」
func play_no_answer() -> void:
	play_sfx(sfx_no_answer)

## 10. sfx_pill_select — 暫時跳過，不播放
# func play_pill_select() -> void:
#     play_sfx(sfx_pill_select)

## 11. 配對成功（兩 pill 連線）
func play_pill_match() -> void:
	play_sfx(sfx_pill_match)

## 12. 解除配對
func play_pill_unmatch() -> void:
	play_sfx(sfx_pill_unmatch)

## 13. sfx_reveal_card — 暫時跳過
# func play_reveal_card() -> void:
#     play_sfx(sfx_reveal_card, randf_range(0.95, 1.05))

## 14. 猜對結果
func play_result_correct() -> void:
	play_sfx(sfx_result_correct)

## 15. 猜錯結果
func play_result_wrong() -> void:
	play_sfx(sfx_result_wrong)

## 16. 再玩一輪
func play_next_round() -> void:
	play_sfx(sfx_next_round)

## 17. sfx_reconnect_ok — 暫時跳過
# func play_reconnect_ok() -> void:
#     play_sfx(sfx_reconnect_ok)
