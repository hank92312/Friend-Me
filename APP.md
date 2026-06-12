# Project Friends & Me - 異步社交探索桌遊 APP

## 1. 核心願景 (Core Vision)
利用「異步遊戲」降低社交壓力，透過「自我揭露」與「社交驗證」促進朋友間的深度連結與自我探索。

## 2. 核心機制與心理學邏輯
- **喬哈里視窗實踐**：透過「猜測他人答案」核對他人眼中的自己與真實自我的落差。
- **心理安全機制**：
    - 「不回答」也是一種有效的答案選項，降低強迫揭露的焦慮，並作為猜測階段的干擾項。
    - 數據隱私：被猜中率與猜中率可自由設定公開或私有。
- **社交等級層次 (話題深度)**：
    - Level 1：閒話家常 (日常習慣)
    - Level 2：下午茶閒聊 (輕鬆話題)
    - Level 3：居酒屋微醺 (感情與生活抱怨)
    - Level 4：深夜真心話 (夜深人靜的秘密)
    - Level 5：靈魂拷問 (挑戰底線的極端情境)

## 3. 遊戲流程狀態機 (Game State Machine)
- **Phase 0: Lobby & Waiting** (等待大廳，房主可輪流派任隊長)
- **Phase 1: Question Selection** (選題階段，隊長選擇 Level 隨機抽題)
- **Phase 2: Answering Stage** (答題階段，玩家輸入答案或選擇「不回答」)
- **Phase 3: Guessing Stage** (配對階段，點擊上方答案 Pill 再點擊下方玩家完成連線配對)
- **Phase 4: Revelation Stage** (結果揭曉，動態展示配對結果，結算單輪與累計數據並準備下一輪)

---

## 4. 技術架構 (Technical Stack)

### A. 前端引擎 (Frontend) - Godot Engine 4.6
- **解析度設定**：設計尺寸 `1080x1920` (直式)，開發預覽 `540x960`，採用 `canvas_items` + `expand` 自適應拉伸。
- **視覺風格**：
  - 深色背景 (`#1F1C1A`)，搭配金橘色 (`#D0813C`) 按鈕，副標與提示採淡黃色 (`#FFF2CC`)。
  - **動態背景**：套用 `GradientTexture2D` 放射漸層（`#161413` 至 `#080707`），提升深邃視覺質感。
  - **按鈕互動**：全域遞迴註冊按鈕懸停（Hover 放大至 `1.04` 倍）與下壓（Press 縮小至 `0.94` 倍）的 Tween 微動畫。
  - **轉場過渡**：切換 Phase 時平行執行舊畫面淡出縮小（0.18s）與新畫面淡入放大（0.22s），帶有 `Cubic` 緩和效果。

### B. 後端 (Backend) - FastAPI (Python)
- **即時通訊**：基於 WebSockets 廣播遊戲狀態、計時與同步事件。
- **資料庫**：SQLite，透過 SQLAlchemy ORM 持久化，並在房間最後一人離開時自動清理資源。
- **部署方式**：透過 Docker 容器部署至 Fly.io (帶有 Persistent Volume)。

### C. 關鍵技術決策與問題解法 (Crucial Solutions)

#### 1. 中英文多語系動態折行與自適應 (Multi-Language Wrap)
- **問題**：Godot Web/APK 無完整中文字庫折行資料庫，中文使用 `WORD_SMART` 會因無空格而被判定為超長單字，導致 UI 爆版。
- **解法**：在 [translation_data.gd](file:///C:/FriendAndMe/FriendAndMe/translation_data.gd) 中動態切換：**中文語系** 強制使用 `TextServer.AUTOWRAP_ARBITRARY`；**英文語系** 使用 `TextServer.AUTOWRAP_WORD_SMART` 防止單字遭腰斬。

#### 2. Unix 時間戳記防凍結倒數同步 (Timing Sync)
- **問題**：手機 App 進入背景或掛起時，Godot 的 `_process` 會凍結，導致切回時本地倒數計時與伺服器不同步。
- **解法**：本地改為記錄「截止的 Unix 時間戳記」（`Time.get_unix_time_from_system()`），切回前台時透過差值計算剩餘時間；並在 `reconnect_status` 重連事件中接收伺服器提供的精確秒數重新校準。

#### 3. Web 端 Wasm / PCK 快取防舊版殘留 (Cache-Busting)
- **問題**：瀏覽器會強力快取重達 37MB 的 `index.wasm` 檔案，導致後端代碼更新後，網頁端依然執行舊版而產生協議不一致或排版錯誤。
- **解法**：透過 [build_and_patch.py](file:///C:/FriendAndMe/build_and_patch.py) 自動在 HTML 中注入攔截器，強制在 `.wasm` 與 `.pck` 請求後方補上時間戳記 `?v=timestamp`，強制載入最新代碼。

#### 4. 浮動模態彈窗自適應防塌陷 (Dynamic Modal Layout)
- **問題**：`ScrollContainer` 在 `CenterContainer` 底下預設高度會縮為 0，導致說明與設定等卡片塌陷。
- **解法**：視窗縮放或內容更新時，動態計算內容高度 `vbox.get_combined_minimum_size().y` 與最大高度限制，動態給予 `custom_minimum_size.y`。

#### 5. 手機瀏覽器虛擬鍵盤 UX 全面修正 (Mobile Web Virtual Keyboard)
- **問題**：Web 端手機瀏覽器鍵盤遮擋輸入框、看不到自己打的字、游標超出 6 碼房號仍繼續跑、收起鍵盤後按鈕點不到。
- **解法（分三層）**：
  - **Godot 層**：在 `export_presets.cfg` 啟用 `html/experimental_virtual_keyboard=true`，讓 Godot 在呼叫鍵盤時建立 HTML `<input>` 元素。焦點進入時只隱藏「不回答」按鈕（不隱藏題目卡）。
  - **JS 補丁層**（`build_and_patch.py`）：攔截 Godot 建立的 `<input>`，在 `focus` 時將其改為固定置頂可見輸入列（深色背景 + 金橘色底線，高 58px，font-size 22px），並設 `pointer-events: auto` 讓手指可點擊文字中移動游標；在 `blur` 時將輸入框移至螢幕外避免殘留觸控攔截。
  - **visualViewport 狀態機**：以 `fmKbWasOpen` flag 配合 150px 下降閾值偵測鍵盤真正收起（避免鍵盤開啟動畫中途誤觸），收起後主動呼叫 `blur()` 釋放焦點，確保按鈕可被點擊。

#### 6. Web 端 HTTP 回應標頭修正與快取策略 (HTTP Headers & Cache Policy)
- **問題一**：`Cross-Origin-Embedder-Policy: require-corp` 標頭在單執行緒 Wasm 建構下不需要，卻會阻擋 iOS Safari 跨來源資源（廣告、字型 CDN），造成 iOS 卡在載入畫面。
- **問題二**：`index.html` 與 `index.js` 在 Netlify CDN 被強快取，更新部署後玩家仍讀到舊版，導致 PCK 大小宣告與實際不符而載入失敗。
- **解法**：在 `build_and_patch.py` 的 Netlify `_headers` 中移除 `COEP` 標頭；對 `/index.html` 與 `/index.js` 加上 `Cache-Control: no-cache, no-store, must-revalidate`，`.wasm`/`.pck` 已有時間戳記 Query String 故無需特別設定。

#### 7. iOS Safari 背景後頁面重置自動恢復 (iOS Auto-Restart)
- **問題**：iOS Safari 在系統記憶體不足時會直接回收 WebGL Tab，切回 App 後網頁從頭 reload，玩家從遊戲畫面被踢回入口登陸頁。
- **解法**：在 `launchEngine()` 執行時寫入 `sessionStorage.setItem('fm_launched', '1')`；`DOMContentLoaded` 時若偵測到此旗標，自動跳過登陸頁直接呼叫 `launchEngine(true)` 恢復遊戲。`sessionStorage` 在 tab 仍存在時不受 reload 影響，但關閉 tab 後自動清除，不影響新訪客。

#### 8. Android 切換 App 後 WebSocket 假死重連 (Android WS Zombie State)
- **問題**：Android Chrome 在 App 切至背景後，WebSocket 狀態 API 依然回報 `STATE_OPEN`，但連線實際已斷；`_process` 無法偵測到 `STATE_CLOSED`，玩家回到前台後遊戲卡在「等待」畫面。
- **解法**：在 `main.gd` 的 `_notification()` 中監聽 `NOTIFICATION_APPLICATION_FOCUS_OUT` 記錄背景時間；偵測到 `NOTIFICATION_APPLICATION_FOCUS_IN` 且背景時間 ≥ 2 秒時，呼叫 `NetworkManager.resync_on_foreground()`，主動丟棄舊 socket 並立即重建連線，伺服器回傳 `reconnect_status` 重新同步階段狀態。

#### 9. iPad WebGL Context Lost 自動恢復 (WebGL Context Lost Recovery)
- **問題**：低 RAM 設備（如 iPad 9 代，3GB RAM）在瀏覽器分頁切換後，作業系統會強制回收 WebGL 繪圖上下文，畫面黑屏並顯示錯誤。
- **解法**：在 `build_and_patch.py` 監聽 canvas 的 `webglcontextlost` 事件，以 `sessionStorage` 計數最多自動 reload 2 次；15 秒穩定後清除計數，防止無限重載。純硬體限制情境下無法完全避免，但大多數情況下可透明自動恢復。

#### 10. PCK 體積優化 — 移除未使用字型 (PCK Size Optimization)
- **問題**：專案資料夾內有 `NotoSansTC-VF.ttf`（11.4 MB）但從未被任何場景或腳本參照，卻在每次 Godot 匯出時被打包進 `.pck`，造成 PCK 從 11.21 MB 膨脹至 19.69 MB，行動端初次載入緩慢。
- **解法**：將字型檔移至 `_unused_assets_backup/fonts/` 目錄（不刪除，保留備份），重新匯出後 PCK 恢復至 11.21 MB，總下載量從 ~56 MB 降至 ~47 MB。

#### 11. 跨平台特殊字元豆腐塊防範 (Tofu Character Fallbacks)
- **問題**：Android 預設字型缺少中直角引號（`「」`）以及全平台 Emoji 字元，會渲染成豆腐塊。
- **解法**：實作 `_quote` 與 `_emoji` 函數，在 Android 平台自動將引號轉為標準雙引號 `"`，且全平台一律將 Emoji 降級回傳純文字替代方案。

#### 12. 題庫本地打包與超時自動選題機制 (Question Bank Local Bundle)
- **問題**：為降低後端 API 頻寬壓力，題庫採本地打包。當選題階段逾時，後端需要能自動選題並廣播。
- **解法**：將題庫複製到 [backend/data/](file:///C:/FriendAndMe/backend/data/) 並打包進 Docker。超時後後端加載本地 JSON 檔隨機抽取題目並廣播 question 文字給客戶端，客戶端再依據 question 文字於本地對照表進行多語系翻譯。

#### 14. 題庫擴充與多語系同步部署 (Question Bank Expansion)
- **問題**：初始題庫每等級 15–25 題，重複率高，長時間遊玩容易遇到重複題目，降低遊戲新鮮感。
- **解法**：每等級新增 10 題，總題數 105 → 155 題（Level 1–3 各 35 題，Level 4–5 各 25 題）。新增題目以台灣文化為主（夜市、手搖飲、颱風假、KTV、圍爐、親戚聚會等），全為開放式且單一答案。同步更新：中英文 MD 種子文件、`backend/data/` 後端 JSON（超時自動選題用）、`friendAndme/data/` 前端 JSON（打包進 PCK）；ID 格式接續舊編號（L1Q26–35 等），`_get_localized_question()` 有 fallback 不會崩潰。

#### 15. Android 簽章 Keystore 密碼安全管理 (Keystore Password Security)
- **問題**：Keystore 密碼曾被存入 `export_presets.cfg` 並遺留在 git 歷史中，有洩漏風險；且每次發布容易忘記密碼。
- **解法**：`export_presets.cfg` 的簽章欄位保持空白，改用 Godot 支援的環境變數 `GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD` 在匯出時傳入，不寫入任何檔案。密碼更換透過 `keytool -storepasswd` 執行（PKCS12 格式 store 密碼即 key 密碼，`-keypasswd` 不適用）。密碼存放於 Google 雲端硬碟私人文件，而非 repo 內。

#### 13. 單人遊玩結果揭曉防空包機制 (Single-Player Results Resolution)
- **問題**：當房間內只有單一玩家遊玩時，由於 Phase 3 (配對階段) 不需要配對，進入 Phase 4 (結果揭曉) 後，原有的統計與配對結果邏輯會跳過本機玩家 (`mock_self_name`)，導致 `last_round_results_data` 陣列為空，造成結果揭曉頁面空白。
- **解法**：在 `_generate_phase4_ui()` 產生結果 UI 時，優先檢查 `round_answers.size() <= 1`。若是單人遊玩，則自動建立一筆包含玩家自身回答（`mock_self_name`）且配對正確（`is_correct = true`）的結果資料，確保在單人遊玩情境下能正常渲染自己的答案，而不會出現空白畫面。

---

## 5. 檔案與場景結構 (Project Directory & Nodes)

### A. 前端檔案
- [main.tscn](file:///C:/FriendAndMe/FriendAndMe/main.tscn)：包含 Phase 0 到 Phase 4 的 UI 節點佈局。
- [main.gd](file:///C:/FriendAndMe/FriendAndMe/main.gd)：包含主遊戲循環、時間倒數、API 請求與動畫。
- [translation_data.gd](file:///C:/FriendAndMe/FriendAndMe/translation_data.gd)：中英文翻譯字典檔。
- [network_manager.gd](file:///C:/FriendAndMe/FriendAndMe/network_manager.gd)：封裝 WebSockets 及 HTTP 通訊單例。
- [audio_manager.gd](file:///C:/FriendAndMe/FriendAndMe/audio_manager.gd)：封裝全域音效播放與音效淡入淡出、動態音高控制。

### B. 後端檔案
- [main.py](file:///C:/FriendAndMe/backend/main.py)：FastAPI 核心連線邏輯與超時自動推進任務管理。
- [room_manager.py](file:///C:/FriendAndMe/backend/room_manager.py)：管理房間狀態、輪替隊長、同步玩家與斷線快取。