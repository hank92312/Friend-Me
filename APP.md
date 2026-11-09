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

### B. 後端 (Backend) - Cloudflare Workers + Durable Objects (生產環境) & FastAPI (參考實作)
- **生產環境（Cloudflare Workers + Durable Objects）**：
  - **邊緣無狀態架構**：以 TypeScript 撰寫，部署於 Cloudflare 全球 Edge 節點，真正零維護成本（$0/月，無需綁定信用卡）。
  - **即時通訊**：原生支援 WebSockets，每個遊戲房間為獨立的 Durable Object 實例（`GameRoom`），天然隔離房間狀態。
  - **狀態守衛與自動回收**：內建五階段狀態機與逾時推進，房間最後一位玩家離開時自動銷毀實例，無需依賴傳統關聯式資料庫。
- **參考實作（FastAPI / Python，位於 `backend/`）**：
  - 適用本地端開發除錯，基於 FastAPI + WebSocket + SQLite (SQLAlchemy async)。原部署於 Fly.io，因計費考量已全數遷移至 Cloudflare。

### C. 關鍵技術決策與問題解法 (Crucial Solutions)

#### 1. 中英文多語系動態折行與自適應 (Multi-Language Wrap)
- **問題**：Godot Web/APK 無完整中文字庫折行資料庫，中文使用 `WORD_SMART` 會因無空格而被判定為超長單字，導致 UI 爆版。
- **解法**：在 [translation_data.gd](file:///C:/Friend&Me/friendAndme/translation_data.gd) 中動態切換：**中文語系** 強制使用 `TextServer.AUTOWRAP_ARBITRARY`；**英文語系** 使用 `TextServer.AUTOWRAP_WORD_SMART` 防止單字遭腰斬。

#### 2. Unix 時間戳記防凍結倒數同步 (Timing Sync)
- **問題**：手機 App 進入背景或掛起時，Godot 的 `_process` 會凍結，導致切回時本地倒數計時與伺服器不同步。
- **解法**：本地改為記錄「截止的 Unix 時間戳記」（`Time.get_unix_time_from_system()`），切回前台時透過差值計算剩餘時間；並在 `reconnect_status` 重連事件中接收伺服器提供的精確秒數重新校準。

#### 3. Web 端 Wasm / PCK 快取防舊版殘留 (Cache-Busting)
- **問題**：瀏覽器會強力快取重達 37MB 的 `index.wasm` 檔案，導致後端代碼更新後，網頁端依然執行舊版而產生協議不一致或排版錯誤。
- **解法**：透過 [build_and_patch.py](file:///C:/Friend&Me/build_and_patch.py) 自動在 HTML 中注入攔截器，強制在 `.wasm` 與 `.pck` 請求後方補上時間戳記 `?v=timestamp`，強制載入最新代碼。

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
- **解法**：將題庫複製到 [backend/data/](file:///C:/Friend&Me/backend/data/) 並打包進 Docker。超時後後端加載本地 JSON 檔隨機抽取題目並廣播 question 文字給客戶端，客戶端再依據 question 文字於本地對照表進行多語系翻譯。

#### 14. 題庫擴充與多語系同步部署 (Question Bank Expansion)
- **問題**：初始題庫每等級 15–25 題，重複率高，長時間遊玩容易遇到重複題目，降低遊戲新鮮感。
- **解法**：每等級新增 10 題，總題數 105 → 155 題（Level 1–3 各 35 題，Level 4–5 各 25 題）。新增題目以台灣文化為主（夜市、手搖飲、颱風假、KTV、圍爐、親戚聚會等），全為開放式且單一答案。同步更新：中英文 MD 種子文件、`backend/data/` 後端 JSON（超時自動選題用）、`friendAndme/data/` 前端 JSON（打包進 PCK）；ID 格式接續舊編號（L1Q26–35 等），`_get_localized_question()` 有 fallback 不會崩潰。

#### 15. Android 簽章 Keystore 密碼安全管理 (Keystore Password Security)
- **問題**：Keystore 密碼曾被存入 `export_presets.cfg` 並遺留在 git 歷史中，有洩漏風險；且每次發布容易忘記密碼。
- **解法**：`export_presets.cfg` 的簽章欄位保持空白，改用 Godot 支援的環境變數 `GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD` 在匯出時傳入，不寫入任何檔案。密碼更換透過 `keytool -storepasswd` 執行（PKCS12 格式 store 密碼即 key 密碼，`-keypasswd` 不適用）。密碼存放於 Google 雲端硬碟私人文件，而非 repo 內。

#### 16. 多人 desync 階段守衛防階段倒退與重複計分 (Server-Side Phase Guard)
- **問題**：手機端瀏覽器切至背景約 1 分鐘後返回，因進入 GUESSING/REVELATION 時前端答題倒數 `answering_timer_active` 未被關閉，殘留的 120 秒計時器在「結果揭曉」階段歸零，觸發 `_on_btn_no_answer()` 送出過期的 `answer_submitted`。伺服器處理事件時完全未驗證當前階段，照單全收後 `all_done` 成立並**強制將所有人退回 GUESSING**；重新配對後 `guesses_submitted` 再次被接受，使 `_persist_round_results` 二次寫入資料庫，導致猜對猜錯次數超過實際輪數。
- **解法（雙層）**：
  - **後端（權威修補）**：在 [main.py](file:///C:/Friend&Me/backend/main.py) 的 `topic_selected`/`answer_submitted`/`guesses_submitted` 三個 WebSocket 事件各加一道階段守衛——若 `room_states[room_id]["phase"]` 與該事件對應階段不符，一律 `continue` 忽略。單一防線擋掉所有平台、所有原因的過期/重複事件。
  - **前端（輔助）**：在 `_on_network_phase_sync()` 開頭，收到任何非 ANSWERING 階段廣播時強制 `answering_timer_active = false`，從源頭避免殘留計時器送出過期事件。

#### 13. 單人遊玩結果揭曉防空包機制 (Single-Player Results Resolution)
- **問題**：當房間內只有單一玩家遊玩時，由於 Phase 3 (配對階段) 不需要配對，進入 Phase 4 (結果揭曉) 後，原有的統計與配對結果邏輯會跳過本機玩家 (`mock_self_name`)，導致 `last_round_results_data` 陣列為空，造成結果揭曉頁面空白。
- **解法**：在 `_generate_phase4_ui()` 產生結果 UI 時，優先檢查 `round_answers.size() <= 1`。若是單人遊玩，則自動建立一筆包含玩家自身回答（`mock_self_name`）且配對正確（`is_correct = true`）的結果資料，確保在單人遊玩情境下能正常渲染自己的答案，而不會出現空白畫面。

#### 17. Fly.io 退役與 Cloudflare Workers + Durable Objects 邊緣遷移 (Zero-Cost Migration)
- **問題**：Fly.io 每月產生主機與持久磁碟帳單；若採用傳統免費雲端（如 Hugging Face / Render），又有冷啟動休眠與 48 小時無人連線睡眠導致首位玩家等候過久的 UX 痛點。
- **解法**：全面遷移至 **Cloudflare Workers + Durable Objects**：
  - 每個房間以 6 碼大寫代碼對應獨立的 `GameRoom` Durable Object 實例，毫秒級喚醒，全球邊緣就近連線。
  - 將房間狀態、倒數計時器、題庫抽取與斷線寬限期整合於 TypeScript 狀態機中，零伺服器主機成本（$0/月），免綁信用卡。
  - Durable Objects 免費方案配置 `new_sqlite_classes: ["GameRoom"]`，避免 Code 10097。

#### 18. Windows 特殊路徑字元 `&` 破壞 Android Gradle 匯出 (Windows Ampersand Isolation)
- **問題**：本專案工作目錄路徑為 `C:\Friend&Me`，其中包含 `&`。當 Godot 呼叫 Gradle 打包 AAB 時，Windows `cmd.exe` 會將 `&` 視為命令串接分隔符號，造成命令被截斷並引發 Gradle 執行崩潰。
- **解法**：在打包腳本 `build_android.ps1` 中建立路徑隔離機制：先使用 `robocopy` 將專案鏡像同步至乾淨路徑 `C:\GodotBuild\friendAndme`（排除 build 暫存與套件），於乾淨路徑呼叫 Godot CLI 匯出 AAB，完成後再將產物簽章複製回 `C:\Friend&Me\FriendAndMe_Release.aab`。

#### 19. Google AdMob 正式廣告單元注入與 app-ads.txt 驗證 (AdMob & app-ads.txt)
- **問題**：正式 AdMob 廣告單元 ID 與 App ID 若直接硬編碼並推上公開 Git repository，會有被惡意濫用風險；同時 Google AdMob 需透過開發人員網站的 `app-ads.txt` 驗證發布商資格。
- **解法**：
  - **app-ads.txt 邊緣託管**：於 Cloudflare Worker 進入點新增 `/app-ads.txt` 與 `/ads.txt` 路由，回傳 `google.com, pub-2975760496012521, DIRECT, f08c47fec0942fa0`，讓 AdMob 爬蟲直接在全球 CDN 秒級抓取驗證通過。
  - **動態注入機制**：AdMob Application ID 設定於 `friendAndme/addons/admob/android/config.gd`（注入 AndroidManifest）；Ad Unit ID 則透過 [ad_manager.gd](file:///C:/Friend&Me/friendAndme/ad_manager.gd) 動態載入 `res://ad_config.gd`，並將 `ad_config.gd` 加入 `.gitignore` 隔離保護，若本機未建立則自動退回 Google 官方測試 ID。
  - **發布版本**：Android 版本升級至 `1.4.1` (Version Code `9`)。

---

## 5. 檔案與場景結構 (Project Directory & Nodes)

### A. 前端檔案 (`friendAndme/`)
- [main.tscn](file:///C:/Friend&Me/friendAndme/main.tscn)：包含 Phase 0 到 Phase 4 的 UI 節點佈局。
- [main.gd](file:///C:/Friend&Me/friendAndme/main.gd)：包含主遊戲循環、時間倒數、API 請求與動畫。
- [translation_data.gd](file:///C:/Friend&Me/friendAndme/translation_data.gd)：中英文翻譯字典檔。
- [network_manager.gd](file:///C:/Friend&Me/friendAndme/network_manager.gd)：封裝 WebSockets 及 HTTP 通訊單例（已指向 Cloudflare Workers）。
- [audio_manager.gd](file:///C:/Friend&Me/friendAndme/audio_manager.gd)：封裝全域音效播放與音效淡入淡出、動態音高控制。

### B. 後端檔案

#### 1. 正式生產環境 (`cloudflare-backend/`)
- [index.ts](file:///C:/Friend&Me/cloudflare-backend/src/index.ts)：Cloudflare Worker 進入點與 `GameRoom` Durable Object 狀態機核心。
- [question_bank.json](file:///C:/Friend&Me/cloudflare-backend/src/question_bank.json)：後端內嵌完整 155 題題庫。
- [wrangler.jsonc](file:///C:/Friend&Me/cloudflare-backend/wrangler.jsonc)：Cloudflare 部署與 Durable Objects 遷移設定。
- [deploy.bat](file:///C:/Friend&Me/cloudflare-backend/deploy.bat)：一鍵發布腳本。

#### 2. 本地除錯與參考實作 (`backend/`)
- [main.py](file:///C:/Friend&Me/backend/main.py)：FastAPI 核心連線邏輯與超時自動推進任務管理。
- [room_manager.py](file:///C:/Friend&Me/backend/room_manager.py)：管理房間狀態、輪替隊長、同步玩家與斷線快取。