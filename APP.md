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

#### 5. 手機虛擬鍵盤遮擋與焦點釋放 (Focus & Auto-Dismiss)
- **問題**：手機網頁端或 APK 彈出虛擬鍵盤時，會遮擋位於螢幕下方的答題輸入框。
- **解法**：監聽 `LineEdit` 獲得焦點時暫時隱藏題目卡與不回答按鈕以空出空間；並在觸控輸入框外部時主動呼叫 `release_focus()` 以收起鍵盤。

#### 6. 跨平台特殊字元豆腐塊防範 (Tofu Character Fallbacks)
- **問題**：Android 預設字型缺少中直角引號（`「」`）以及全平台 Emoji 字元，會渲染成豆腐塊。
- **解法**：實作 `_quote` 與 `_emoji` 函數，在 Android 平台自動將引號轉為標準雙引號 `"`，且全平台一律將 Emoji 降級回傳純文字替代方案。

#### 7. 題庫本地打包與超時自動選題機制 (Question Bank Local Bundle)
- **問題**：為降低後端 API 頻寬壓力，題庫採本地打包。當選題階段逾時，後端需要能自動選題並廣播。
- **解法**：將題庫複製到 [backend/data/](file:///C:/FriendAndMe/backend/data/) 並打包進 Docker。超時後後端加載本地 JSON 檔隨機抽取題目並廣播 question 文字給客戶端，客戶端再依據 question 文字於本地對照表進行多語系翻譯。

#### 8. 單人遊玩結果揭曉防空包機制 (Single-Player Results Resolution)
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