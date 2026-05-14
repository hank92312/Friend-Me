extends Node

# ── AdManager — 廣告管理單例 ──────────────────────────────────────────────────
# 負責初始化 AdMob SDK、預載入 Interstitial 廣告、控制廣告播放。
# 非 Android 平台自動跳過廣告，廣告載入失敗時不卡住玩家。

signal ad_finished  # 廣告播放完成（或跳過）後發出

# ── AdMob ID ─────────────────────────────────────────────────────────────────
# 開發測試時使用 Google 官方測試 ID，正式發布前替換為真實 ID
const USE_TEST_ADS := true

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

func _ready() -> void:
	# 僅在 Android 平台初始化 AdMob
	if OS.get_name() == "Android":
		_initialize_admob()
	else:
		print("[AdManager] Non-Android platform — AdMob disabled.")

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
	# 非 Android 平台 → 直接跳過
	if OS.get_name() != "Android":
		print("[AdManager] Skipping ad (non-Android).")
		ad_finished.emit()
		return

	# SDK 尚未初始化或廣告還沒載好 → 直接放行不卡住玩家
	if not _is_initialized or _interstitial_ad == null:
		print("[AdManager] No ad ready — skipping.")
		ad_finished.emit()
		# 嘗試重新載入，下次就有了
		if _is_initialized and not _is_ad_loading:
			_load_interstitial()
		return

	# 綁定回呼
	_is_showing_ad = true
	var ad := _interstitial_ad
	_interstitial_ad = null  # 用完即清，防止重複播放

	ad.full_screen_content_callback.on_ad_dismissed_full_screen_content = func() -> void:
		_is_showing_ad = false
		print("[AdManager] Ad dismissed — continuing game.")
		ad_finished.emit()
		# 廣告關閉後立即預載下一支
		_load_interstitial()

	ad.full_screen_content_callback.on_ad_failed_to_show_full_screen_content = func(_error: AdError) -> void:
		_is_showing_ad = false
		print("[AdManager] Ad failed to show — skipping.")
		ad_finished.emit()
		_load_interstitial()

	ad.show()
	print("[AdManager] Showing interstitial ad...")
