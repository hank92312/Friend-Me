extends Node

# ── AdManager — 廣告與應用內購買管理單例 ───────────────────────────────────────
# 負責初始化 AdMob SDK、預載入 Interstitial 廣告、控制廣告播放。
# 同時整合 Google Play Billing 實作「移除廣告」應用內購買 (IAP) 功能。
# 非 Android 平台自動跳過廣告，廣告載入失敗時不卡住玩家。

signal ad_finished  # 廣告播放完成（或跳過）後發出
signal purchase_state_changed  # 購買狀態變更時發出（通知 UI 更新）

# ── AdMob ID ─────────────────────────────────────────────────────────────────
# 開發測試時使用 Google 官方測試 ID；正式 ID 由不進版控的 ad_config.gd 注入。
const USE_TEST_ADS := false

# Google 官方測試 Interstitial ID（公開文件 ID，可安全進版控）
const TEST_AD_UNIT_ID := "ca-app-pub-3940256099942544/1033173712"

# 正式廣告 ID 存放於 res://ad_config.gd（見 ad_config.example.gd），該檔不進版控。
# 乾淨 clone（如公開 repo）缺此檔時自動退回測試 ID，避免外流正式 ID。
const _AD_CONFIG_PATH := "res://ad_config.gd"

var _ad_unit_id: String:
	get:
		if USE_TEST_ADS:
			return TEST_AD_UNIT_ID
		if ResourceLoader.exists(_AD_CONFIG_PATH):
			var cfg = load(_AD_CONFIG_PATH)
			if cfg != null:
				return cfg.AD_UNIT_ID
		push_warning("[AdManager] 找不到 ad_config.gd，改用測試廣告 ID。")
		return TEST_AD_UNIT_ID

# ── 狀態 ─────────────────────────────────────────────────────────────────────
var _is_initialized := false
var _interstitial_ad: InterstitialAd = null
var _is_ad_loading := false
var _is_showing_ad := false

# ── 應用內購買 (IAP) ─────────────────────────────────────────────────────────
const CACHE_FILE := "user://settings_data.dat"
const ENCRYPT_PASS := "FriendAndMeSecureIAPKey"

var billing_client: BillingClient = null
var has_removed_ads := false

# ── 防止 GC 回收：將廣告物件與回呼保留為類別變數 ─────────────────────────────
var _current_showing_ad = null               # 正在播放的廣告物件
var _current_full_screen_callback = null      # 正在使用的回呼物件
var _safety_timer: Timer = null               # 安全計時器（防止永遠卡住）
var _web_ad_callback = null                  # Web 平台 JavaScript 回呼物件

func _ready() -> void:
	# 載入本地加密購買快取
	_load_purchase_locally()
	
	# 建立安全計時器（30 秒後如果廣告還沒回應，強制放行）
	_safety_timer = Timer.new()
	_safety_timer.one_shot = true
	_safety_timer.wait_time = 30.0
	_safety_timer.timeout.connect(_on_safety_timeout)
	add_child(_safety_timer)
	
	if OS.get_name() == "Android":
		_initialize_admob()
		_initialize_billing()
	elif OS.has_feature("web"):
		_initialize_web_ads()
	else:
		print("[AdManager] Non-Android/Web platform — AdMob/Web Ads disabled.")

# ── 初始化 Google Play Billing ───────────────────────────────────────────────
func _initialize_billing() -> void:
	if Engine.has_singleton("GodotGooglePlayBilling"):
		print("[AdManager] Google Play Billing singleton found.")
		billing_client = BillingClient.new()
		add_child(billing_client)
		
		# 連接 BillingClient 訊號
		billing_client.connected.connect(_on_billing_connected)
		billing_client.connect_error.connect(_on_billing_connect_error)
		billing_client.on_purchase_updated.connect(_on_billing_purchase_updated)
		billing_client.query_purchases_response.connect(_on_billing_query_purchases_response)
		billing_client.acknowledge_purchase_response.connect(_on_billing_acknowledge_response)
		
		# 開始與 Google Play 商店建立連線
		billing_client.start_connection()
	else:
		print("[AdManager] Google Play Billing singleton NOT found (non-Play Store build or editor).")

func _on_billing_connected() -> void:
	print("[AdManager] Billing connected. Querying purchases...")
	# 查詢使用者已購買的非消耗型/管理型商品
	billing_client.query_purchases(BillingClient.ProductType.INAPP)

func _on_billing_connect_error(response_code: int, debug_message: String) -> void:
	print("[AdManager] Billing connection error: ", response_code, " - ", debug_message)

func _on_billing_purchase_updated(response: Dictionary) -> void:
	print("[AdManager] on_purchase_updated: ", response)
	var response_code = response.get("response_code", -1)
	if response_code == 0: # BillingResponseCode.OK
		var purchases = response.get("purchases", [])
		_process_purchases(purchases)
	elif response_code == 7: # ITEM_ALREADY_OWNED
		print("[AdManager] Purchase updated: Item already owned.")
		has_removed_ads = true
		_save_purchase_locally()
		purchase_state_changed.emit()
	else:
		print("[AdManager] Purchase failed or cancelled. Response code: ", response_code)

func _on_billing_query_purchases_response(response: Dictionary) -> void:
	print("[AdManager] query_purchases_response: ", response)
	var response_code = response.get("response_code", -1)
	if response_code == 0: # OK
		var purchases = response.get("purchases", [])
		_process_purchases(purchases)
	else:
		print("[AdManager] query_purchases failed with response_code: ", response_code)

func _on_billing_acknowledge_response(response: Dictionary) -> void:
	print("[AdManager] acknowledge_purchase_response: ", response)
	var response_code = response.get("response_code", -1)
	if response_code == 0:
		print("[AdManager] Purchase acknowledged successfully!")
	else:
		print("[AdManager] Acknowledge failed with response_code: ", response_code)

func _process_purchases(purchases: Array) -> void:
	var owned_remove_ads = false
	for purchase in purchases:
		# 檢查商品 ID 是否為 "remove_ads" 且狀態為已購買 (PURCHASED = 1)
		var products = purchase.get("products", [])
		var purchase_state = purchase.get("purchase_state", -1)
		
		# 相容舊版 API 欄位 (如 product_id 或 sku)
		if products.is_empty() and purchase.has("product_id"):
			products = [purchase["product_id"]]
		elif products.is_empty() and purchase.has("sku"):
			products = [purchase["sku"]]
			
		if "remove_ads" in products:
			if purchase_state == 1: # PURCHASED
				owned_remove_ads = true
				var is_acknowledged = purchase.get("is_acknowledged", true)
				# 如果尚未確認購買，必須在 3 天內確認，否則 Google 會自動退款
				if not is_acknowledged:
					var token = purchase.get("purchase_token", "")
					if token != "":
						print("[AdManager] Acknowledging purchase of remove_ads...")
						billing_client.acknowledge_purchase(token)
	
	if owned_remove_ads != has_removed_ads:
		has_removed_ads = owned_remove_ads
		_save_purchase_locally()
		purchase_state_changed.emit()

# ── 發起購買 ──
func purchase_remove_ads() -> void:
	if has_removed_ads:
		print("[AdManager] Ads already removed.")
		return
		
	if billing_client == null or not billing_client.is_ready():
		# 開發者帳號尚未申請、未連線或不支援 Billing (例如本地測試或非 Play 商店環境)
		print("[AdManager] Billing client is not ready.")
		if OS.is_debug_build():
			# 除錯模式下直接放行模擬購買，便於測試 UI/選項選單轉變
			print("[AdManager] Debug build detected. Simulating successful purchase of remove_ads...")
			has_removed_ads = true
			_save_purchase_locally()
			purchase_state_changed.emit()
		else:
			OS.alert("無法連接至 Google Play 商店，請確認您已登入 Google 帳號並連接網路後再試一次。", "連線失敗")
		return
		
	print("[AdManager] Launching purchase flow for: remove_ads")
	var result = billing_client.purchase("remove_ads")
	if result.get("status", -1) != 0:
		print("[AdManager] Failed to launch purchase flow, result: ", result)

# ── 本地加密快取 ──
func _save_purchase_locally() -> void:
	var file = FileAccess.open_encrypted_with_pass(CACHE_FILE, FileAccess.WRITE, ENCRYPT_PASS)
	if file:
		var data = {
			"has_removed_ads": has_removed_ads
		}
		file.store_var(data)
		file.close()
		print("[AdManager] Purchase state saved locally: ", has_removed_ads)
	else:
		print("[AdManager] Failed to save purchase state locally.")

func _load_purchase_locally() -> void:
	if not FileAccess.file_exists(CACHE_FILE):
		return
	var file = FileAccess.open_encrypted_with_pass(CACHE_FILE, FileAccess.READ, ENCRYPT_PASS)
	if file:
		var data = file.get_var()
		if data is Dictionary and data.has("has_removed_ads"):
			has_removed_ads = data["has_removed_ads"]
			print("[AdManager] Purchase state loaded from local cache: ", has_removed_ads)
		file.close()
	else:
		print("[AdManager] Failed to load purchase state from local cache.")

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
	# 如果已購買移除廣告，直接跳過並放行
	if has_removed_ads:
		print("[AdManager] Ads permanently disabled by IAP. Skipping ad.")
		ad_finished.emit.call_deferred()
		return

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
