extends Node

# ── AdManager — 廣告管理單例 ──────────────────────────────────────────────────
# 負責初始化 AdMob SDK、預載入 Interstitial 廣告、控制廣告播放。
# 非 Android 平台自動跳過廣告，廣告載入失敗時不卡住玩家。

signal ad_finished  # 廣告播放完成（或跳過）後發出

# ── AdMob ID ─────────────────────────────────────────────────────────────────
# 開發測試時使用 Google 官方測試 ID，正式發布前替換為真實 ID
const USE_TEST_ADS := false

# 正式 ID
const REAL_AD_UNIT_ID := "ca-app-pub-XXXXXXXXXXXXXXXX/XXXXXXXXXX"
# Google 官方測試 Interstitial ID
const TEST_AD_UNIT_ID := "ca-app-pub-3940256099942544/1033173712"

var _ad_unit_id: String:
	get:
		return TEST_AD_UNIT_ID if USE_TEST_ADS else REAL_AD_UNIT_ID

# ── 狀態 ─────────────────────────────────────────────────────────────────────
var _is_initialized := false
var _interstitial_ad: InterstitialAd = null
var _is_ad_loading := false
var _is_showing_ad := false

# ── 防止 GC 回收：將廣告物件與回呼保留為類別變數 ─────────────────────────────
var _current_showing_ad = null               # 正在播放的廣告物件
var _current_full_screen_callback = null      # 正在使用的回呼物件
var _safety_timer: Timer = null               # 安全計時器（防止永遠卡住）
var _web_ad_callback = null                  # Web 平台 JavaScript 回呼物件

func _ready() -> void:
	# 建立安全計時器（30 秒後如果廣告還沒回應，強制放行）
	_safety_timer = Timer.new()
	_safety_timer.one_shot = true
	_safety_timer.wait_time = 30.0
	_safety_timer.timeout.connect(_on_safety_timeout)
	add_child(_safety_timer)
	
	if OS.get_name() == "Android":
		_initialize_admob()
	elif OS.has_feature("web"):
		_initialize_web_ads()
	else:
		print("[AdManager] Non-Android/Web platform — AdMob/Web Ads disabled.")

# ── 初始化 AdMob SDK ─────────────────────────────────────────────────────────
func _initialize_admob() -> void:
	var listener := OnInitializationCompleteListener.new()
	listener.on_initialization_complete = func(_status: InitializationStatus) -> void:
		_is_initialized = true
		print("[AdManager] AdMob SDK initialized successfully.")
		# SDK 初始化完成後立即預載入第一支廣告
		_load_interstitial()
	MobileAds.initialize(listener)
	print("[AdManager] Initializing AdMob SDK...")

# ── 初始化 Web 廣告 ──────────────────────────────────────────────────────────
func _initialize_web_ads() -> void:
	print("[AdManager] Initializing Web Ad callbacks...")
	_web_ad_callback = JavaScriptBridge.create_callback(_on_web_ad_finished)
	var window = JavaScriptBridge.get_interface("window")
	if window:
		window.godot_on_web_ad_finished = _web_ad_callback
		_is_initialized = true
		print("[AdManager] Web Ad callbacks registered successfully on window.")

func _on_web_ad_finished(_args) -> void:
	print("[AdManager] Web ad finished callback received from JS.")
	_finish_ad()

# ── 預載入 Interstitial 廣告 ─────────────────────────────────────────────────
func _load_interstitial() -> void:
	if _is_ad_loading:
		return
	_is_ad_loading = true
	_interstitial_ad = null

	var loader := InterstitialAdLoader.new()
	var callback := InterstitialAdLoadCallback.new()

	callback.on_ad_loaded = func(ad: InterstitialAd) -> void:
		_interstitial_ad = ad
		_is_ad_loading = false
		print("[AdManager] Interstitial ad loaded and ready.")

	callback.on_ad_failed_to_load = func(error: LoadAdError) -> void:
		_interstitial_ad = null
		_is_ad_loading = false
		print("[AdManager] Interstitial ad failed to load: ", error)

	loader.load(_ad_unit_id, AdRequest.new(), callback)
	print("[AdManager] Loading interstitial ad...")

# ── 顯示廣告 ─────────────────────────────────────────────────────────────────
# 呼叫後等待 `ad_finished` 信號即可繼續遊戲流程
func show_interstitial() -> void:
	# Web 平台 → 呼叫 JavaScript 播放廣告
	if OS.has_feature("web"):
		_is_showing_ad = true
		_safety_timer.start()
		var window = JavaScriptBridge.get_interface("window")
		if window and window.showWebAd != null:
			print("[AdManager] Requesting Web Ad via JS...")
			window.showWebAd()
		else:
			print("[AdManager] showWebAd JS function not found or is null! Skipping ad.")
			_finish_ad()
		return

	# 非 Android 平台 → 直接跳過
	if OS.get_name() != "Android":
		print("[AdManager] Skipping ad (non-Android/Web).")
		ad_finished.emit.call_deferred()
		return

	# SDK 尚未初始化或廣告還沒載好 → 直接放行不卡住玩家
	if not _is_initialized or _interstitial_ad == null:
		print("[AdManager] No ad ready — skipping.")
		ad_finished.emit.call_deferred()
		# 嘗試重新載入，下次就有了
		if _is_initialized and not _is_ad_loading:
			_load_interstitial()
		return

	# ── 關鍵修正：將廣告與回呼存為類別變數，防止 GC 回收 ──
	_is_showing_ad = true
	_current_showing_ad = _interstitial_ad
	_interstitial_ad = null  # 用完即清，防止重複播放

	_current_full_screen_callback = FullScreenContentCallback.new()
	
	_current_full_screen_callback.on_ad_dismissed_full_screen_content = func() -> void:
		print("[AdManager] Ad dismissed — continuing game.")
		_finish_ad()

	_current_full_screen_callback.on_ad_failed_to_show_full_screen_content = func(error: AdError) -> void:
		print("[AdManager] Ad failed to show: ", error, " — skipping.")
		_finish_ad()

	_current_showing_ad.full_screen_content_callback = _current_full_screen_callback
	_current_showing_ad.show()
	
	# 啟動安全計時器
	_safety_timer.start()
	print("[AdManager] Showing interstitial ad... (safety timer started)")

# ── 統一的廣告結束處理 ───────────────────────────────────────────────────────
func _finish_ad() -> void:
	# 防止重複觸發
	if not _is_showing_ad:
		return
	_is_showing_ad = false
	
	# 停止安全計時器
	_safety_timer.stop()
	
	# 清除引用（現在可以安全釋放了）
	_current_showing_ad = null
	_current_full_screen_callback = null
	
	print("[AdManager] _finish_ad() — emitting ad_finished via call_deferred")
	ad_finished.emit.call_deferred()
	
	# 預載下一支廣告
	_load_interstitial()

# ── 安全計時器觸發（防止永遠卡住） ───────────────────────────────────────────
func _on_safety_timeout() -> void:
	if _is_showing_ad:
		print("[AdManager] WARNING: Safety timeout reached (30s) — force finishing ad.")
		_finish_ad()

