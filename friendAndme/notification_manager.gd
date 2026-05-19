extends Node

# ── NotifManager — 本地通知管理單例 ───────────────────────────────────────────
# 負責 Android 本地推播通知：建立通知頻道、請求權限、排程/取消通知。
# 非 Android 平台安靜跳過，不產生任何錯誤。

const CHANNEL_ID := "game_events"
const CHANNEL_NAME := "遊戲事件通知"
const CHANNEL_DESC := "Friends & Me 遊戲階段切換通知"

var _scheduler: NotificationScheduler = null
var _is_initialized := false
var _next_notification_id := 1000  # 通知 ID 起始值
var _is_app_in_foreground := true  # 追蹤 App 是否在前景

func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_IN or what == NOTIFICATION_APPLICATION_RESUMED:
		_is_app_in_foreground = true
		cancel_all() # 回到前景時自動取消所有通知
	elif what == NOTIFICATION_APPLICATION_FOCUS_OUT or what == NOTIFICATION_APPLICATION_PAUSED:
		_is_app_in_foreground = false

func _ready() -> void:
	if OS.get_name() == "Android":
		_setup_scheduler()
	else:
		print("[NotifManager] Non-Android platform — notifications disabled.")

# ── 初始化 NotificationScheduler ─────────────────────────────────────────────
func _setup_scheduler() -> void:
	_scheduler = NotificationScheduler.new()
	_scheduler.name = "NotificationSchedulerNode"
	add_child(_scheduler)

	# 綁定初始化完成回呼
	_scheduler.initialization_completed.connect(_on_init_completed)
	_scheduler.post_notifications_permission_granted.connect(_on_permission_granted)
	_scheduler.post_notifications_permission_denied.connect(_on_permission_denied)

	_scheduler.initialize()
	print("[NotifManager] Initializing NotificationScheduler...")

func _on_init_completed() -> void:
	_is_initialized = true
	print("[NotifManager] NotificationScheduler initialized.")

	# 建立通知頻道 (Android 8+ 必須)
	var channel := NotificationChannel.new()
	channel.set_id(CHANNEL_ID)
	channel.set_name(CHANNEL_NAME)
	channel.set_description(CHANNEL_DESC)
	channel.set_importance(NotificationChannel.Importance.HIGH)
	_scheduler.create_notification_channel(channel)
	print("[NotifManager] Notification channel created: ", CHANNEL_ID)

	# 請求通知權限 (Android 13+ 必須)
	if not _scheduler.has_post_notifications_permission():
		_scheduler.request_post_notifications_permission()
		print("[NotifManager] Requesting POST_NOTIFICATIONS permission...")
	else:
		print("[NotifManager] POST_NOTIFICATIONS permission already granted.")

func _on_permission_granted(_perm: String) -> void:
	print("[NotifManager] Notification permission granted: ", _perm)

func _on_permission_denied(_perm: String) -> void:
	print("[NotifManager] Notification permission denied: ", _perm)
	# 權限被拒絕時不影響遊戲流程，只是無法發送通知

# ── 發送即時本地通知 ──────────────────────────────────────────────────────────
func notify(title: String, content: String) -> void:
	# 只有當 App 在背景 (縮小) 時才發送通知
	if _is_app_in_foreground:
		print("[NotifManager] App is in foreground, skipping notification: ", content)
		return

	if OS.get_name() != "Android" or not _is_initialized or _scheduler == null:
		return

	# 確認有通知權限
	if not _scheduler.has_post_notifications_permission():
		return

	var notification := NotificationData.new()
	notification.set_id(_next_notification_id)
	notification.set_channel_id(CHANNEL_ID)
	notification.set_title(title)
	notification.set_content(content)
	notification.set_small_icon_name("ic_default_notification")
	notification.set_delay(0)  # 立即發送

	_scheduler.schedule(notification)
	print("[NotifManager] Notification scheduled: ", title, " — ", content)

	_next_notification_id += 1

# ── 便捷方法：各遊戲階段通知 ─────────────────────────────────────────────────
func notify_answering() -> void:
	notify("Friends & Me", "新題目來了！快回來作答 ✏️")

func notify_guessing() -> void:
	notify("Friends & Me", "配對階段開始！猜猜誰寫了什麼 🔍")

func notify_revelation() -> void:
	notify("Friends & Me", "結果揭曉！回來看看你猜對了幾個 🎉")

func notify_captain() -> void:
	notify("Friends & Me", "輪到你當隊長！快選一個話題深度 👑")

# ── 取消所有已排程的通知 ──────────────────────────────────────────────────────
func cancel_all() -> void:
	if OS.get_name() != "Android" or not _is_initialized or _scheduler == null:
		return

	# 取消從 1000 到目前 ID 的所有通知
	for id in range(1000, _next_notification_id):
		_scheduler.cancel(id)

	print("[NotifManager] All notifications cancelled.")
