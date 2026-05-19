# NEXT AI SESSION HANDOFF (進度交接與後續待辦)

Hello 接下來接手的 AI：
請先閱讀本目錄下的 `APP.md` 了解本專案 **Friends & Me** 的聯網 MVP 現況。

## 專案目前進度 (Current Progress)
- **聯網架構已確立**：採用 **FastAPI (Python) + WebSockets** 實現即時同步。
- **房間系統完成**：實作了「創立房間碼 (6位數)」、「加入房間」、「複製代碼」以及「待機大廳」功能。
- **暱稱輸入系統**：實作了彈出式視窗讓玩家輸入朋友認得的名字，取代了隨機名稱。
- **真實數據同步 (核心完成)**：
    - **答案同步**：實作了 `answer_submitted` 機制，伺服器會收集所有真實玩家的答案並在全員完成後進行廣播。
    - **猜測同步**：實作了 `guesses_submitted` 機制，伺服器會收集所有玩家的配對結果，並根據真實數據計算「被猜中率」。
- **隊長輪替邏輯 (聯網版)**：伺服器統一管理隊長輪替，支援無限輪次的換隊長遊玩。
- **Phase 3/4 聯網優化**：結算畫面不再使用 Mock 隨機機率，改用伺服器傳回的真實猜測數據進行統計。
- **靜默斷線重連**：
    - `network_manager.gd`：WebSocket 斷線後每 3 秒自動嘗試重連，最多 8 次。
    - `backend/room_manager.py`：斷線玩家「標記保留」而非刪除，重連後可識別身份。
    - `backend/main.py`：重連玩家加入「等待下一輪」名單，遊戲繼續，不卡其他玩家。
    - 斷線後若其他玩家全數提交，伺服器自動推進階段（不因斷線者卡住）。
- **UI 轉場動畫與介面**：
    - 所有 Phase 切換採用 0.18s 淡出 + 0.22s 淡入的 Sine 緩動。
    - Phase 3 pill 選取：Back 彈跳 scale-up；配對成功：Elastic bounce。
    - Phase 4 揭幕：標題淡入 + 結果卡片 stagger（每張間隔 0.18s）從右滑入。
    - Phase 4 結算：字體放大優化，猜中率與被猜中率加入 0.0% 到實際值的平滑計數動畫 (Tween)。
    - **動態遊戲說明 (Tutorial)**：點擊後彈出深色覆蓋層，支援分頁觀看房間創建與遊戲流程。
    - **設定選項 (Options)**：支援全域音效開關，並具備「點擊複製製作人信箱」功能。
- **音效系統**：
    - 建立 `audio_manager.gd` Autoload 單例。
    - 導入 14 個 `.ogg` 音效並全部利用 `ffmpeg` 進行 loudness 正規化至 -12 LUFS。
    - 實作 **動態音高與殘響**，同一選題音效在 LV1 (明亮) 到 LV5 (沉重且有兩次回音) 會呈現不同的社交情境氛圍。
    - 成功綁定 UI 點擊、房間建立、難度選擇、成功配對、結果揭曉等觸發點。
- **後端雲端部署**：
    - 成功封裝 FastAPI 後端成 Docker 容器。
    - 成功部署至 Fly.io (`friends-and-me.fly.dev`)，支援 24 小時 WebSockets 即時連線。
    - 使用 Fly.io Volume 掛載硬碟 (`/data`) 存放 SQLite 資料庫，確保重啟不遺失資料。
    - `room_manager.py` 實作自動清空機制：最後一人離開房間時，自動清除資料庫中的該房所有問答紀錄。
    - `network_manager.gd` 加入 `USE_LOCAL` 開關，方便一鍵切換本地測試或雲端連線。
- **Android 廣告 + 本地通知整合 (本次 Session 完成) ✅**：
    - 建立 `ad_manager.gd` Autoload — AdMob Interstitial 初始化、預載入、播放、失敗容錯。
    - 建立 `notification_manager.gd` Autoload — 通知頻道建立、權限請求、各階段通知排程。
    - 修改 `main.gd`：進入房間前插入友善廣告警語面板 → 播放廣告 → 完成後進房間。
    - 斷線重連玩家自動豁免廣告流程。
    - 各遊戲階段切換時觸發本地推播通知（ANSWERING/GUESSING/REVELATION/SELECTION）。
    - App 回到前景時自動取消所有通知。
    - 註冊 `AdManager` 和 `NotifManager` 為 Autoload。
- **Android 建置環境設定 (本次 Session 完成) ✅**：
    - 安裝 **JDK 17** (Microsoft OpenJDK 17.0.19)。
    - 安裝 **Android SDK** (platform-tools + build-tools;35.0.0 + platforms;android-35)。
    - 在 Godot Editor Settings 中設定 Java SDK Path 和 Android SDK Path。
    - 啟用 ETC2/ASTC 紋理壓縮。
    - 首次嘗試匯出 APK：Gradle 建置成功，僅因輸出路徑權限問題（C:\ 根目錄）未完成最終輸出。

## godot_ai 插件說明
- **位置**：`friend&me/addons/godot_ai/`
- **用途**：MCP (Model Context Protocol) 橋接插件，讓 Antigravity 等 AI 助手可直接控制 Godot 編輯器。
- **啟用方式**：Project > Project Settings > Plugins > Godot AI > 啟用
- **依賴**：需要安裝 `uv`（Python 套件管理工具）
- **整合建議**：在 Godot 啟用插件後，Antigravity 即可直接操作場景樹、修改節點屬性、執行測試，無需手動切換。

## 接下來未完成的工作事項 (Pending Tasks)

### 🔴 最優先：Android APK 實機測試 + 上架準備

> ⚠️ **路徑注意事項**：
> - 開發目錄：`C:\FriendAndMe\friend&me\`
> - 因為 Windows 命令列會將 `&` 解讀為指令分隔符，**匯出 Android APK 時必須使用不含 `&` 的路徑**。
> - 建議方案：將專案複製到 `C:\FriendAndMe_Build\` 匯出，或直接將外層資料夾改名為 `FriendAndMe`。
> - 已建立一鍵同步腳本：`C:\FriendAndMe\sync_to_build.bat`

#### Step A：匯出 APK 並進行實機測試（下次 Session 立即執行）
- [x] 從 Godot 匯出 APK（**不要**存到 C:\ 根目錄，改存桌面或專案資料夾內）
- [x] 安裝到 Android 手機，驗證以下功能：
  - [x] 廣告警語面板正常顯示
  - [x] AdMob 測試廣告正常播放（使用 Google 測試 ID）
  - [x] 廣告播放後能正常建立/加入房間
  - [x] 各階段通知正常推送 (ANSWERING/GUESSING/REVELATION/SELECTION)
  - [x] App 回到前景時通知自動取消
  - [x] WebSocket 連線正常（連到 `friends-and-me.fly.dev`）
  - [x] 多人遊戲完整流程跑通

#### Step B：Android 匯出設定微調
- [x] 確認權限設定：`INTERNET`、`ACCESS_NETWORK_STATE`、`POST_NOTIFICATIONS`
- [x] 確認 AdMob 與 Notification 插件已在 Export 中勾選

#### Step C：AdMob 後台建議設定
- [ ] **關閉「High-engagement ads」** → 廣告最快 5 秒即可跳過
- [ ] **禁用「Non-skippable video ads」** → 杜絕 30 秒不可跳過廣告
- [ ] 設定 **Frequency Capping**（每人每小時最多 N 次廣告）

#### Step D：正式發布前
- [ ] `ad_manager.gd` 第 12 行：將 `USE_TEST_ADS` 改為 `false`
- [ ] 替換為正式 Ad Unit ID：`ca-app-pub-XXXXXXXXXXXXXXXX/XXXXXXXXXX`

> ⚠️ **AdMob 帳號資訊：**
> - **AdMob App ID**：`ca-app-pub-XXXXXXXXXXXXXXXX~7080207414`
> - **Interstitial Ad Unit ID**：`ca-app-pub-XXXXXXXXXXXXXXXX/XXXXXXXXXX`
> - *(開發測試時請使用 Google 官方測試 ID，正式發布前再替換為上方 ID)*

---

### 2. Phase C：體驗優化與擴充
- **推播通知 (Push Notifications)**：✅ 已完成（採本地通知方案）。
- **資料庫轉移 (選作)**：若未來玩家數量大增且需要多節點擴充，可將 SQLite 轉移至 PostgreSQL。
- ~~**題庫動態導入**~~：已完成 — 採「本地打包」策略 (V3 擴充版，共 105 題)，因應輕量化與低伺服器負擔需求。詳見 `APP.md` 第 5 章。
- **音效缺漏 (🔍 尋找適合音效中)**：
  - [ ] 「離開圈圈」按鈕 (`BtnLeaveCircle`) — 需要一個柔和的離開/退出音效
  - [ ] 「確定離開」按鈕 (`BtnFinalLeave`) — 需要一個確認離開的音效（比上面稍微強調一點）

### Android 實機測試發現的 Bug（已修正 ✅）
- [x] **廣告警語面板 Emoji 亂碼**：📢 和 ❤️ 在 Android 上無法正常顯示 → 已替換為純中文字串
- [x] **題目超出螢幕不換行**：Phase 2 題目 Label 在手機上超過一行時不會自動折行 → 已改用 `TextServer.AUTOWRAP_WORD_SMART`
- [x] **難度選擇全形冒號亂碼**：`LV 1：` 全形冒號在部分 Android 裝置顯示為豆腐方塊 → 已修正為半形 `LV 1: `
- [x] **結算畫面長題目與結果折行**：結算畫面題目與對比結果在字數過多時未自動折行 → 已將自動換行模式改為 `TextServer.AUTOWRAP_WORD_SMART` 並補上擴充填充
- [x] **相同答案配對覆寫邏輯**：多位玩家選「不回答」時，配對結果字典被覆寫導致錯誤 → 已重構為 `{"玩家": "答案"}` 結構

### 3. Phase D：商業化 — Web 端廣告 (待實作，優先級低於 Android)
- **Web 廣告整合**：在 HTML5 匯出的外層頁面引入 H5 遊戲廣告 SDK (Google AdSense for Games 或 CrazyGames/Poki 等聯播網)，透過 `JavaScriptBridge` 讓 Godot 與 JS 廣告程式碼互動。
- **AdBlock 偵測 (Web)**：實作友善提示或直接放行機制。
- **iOS 廣告 (暫緩)**：待取得 Apple 開發者帳號後再規劃。

---
## 🚀 啟動後端伺服器 (測試前必做)

在 Godot 雙開測試之前，**必須先讓後端 FastAPI 伺服器運行**。

### Windows PowerShell 啟動步驟

```powershell
# 步驟 1：進入後端資料夾
cd backend

# 步驟 2：啟動虛擬環境 (venv)
.\venv\Scripts\Activate

# 步驟 3：啟動 FastAPI 伺服器（熱重載模式）
uvicorn main:app --reload
```

> ⚠️ 若 PowerShell 顯示「無法執行指令碼」錯誤，請先執行：
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### 伺服器啟動成功的標誌
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```
看到這行就代表後端就緒，可以開啟 Godot 測試。

### 關閉伺服器
在 PowerShell 視窗按 `Ctrl + C` 即可停止。

---
## 測試指南 (How to Test)
1. **啟動後端**：依照上方「啟動後端伺服器」步驟操作。
2. **啟動 Godot**：同時開啟兩個 Godot 視窗 (F5) 進行「雙開測試」。
3. **驗證流程**：
   - 視窗 A：創立房間 -> 輸入名字 -> 獲得房間碼。
   - 視窗 B：輸入房間碼 -> 輸入名字 -> 加入房間。
   - 視窗 A：點擊「開始遊戲」 -> 兩邊同步進入選題。
   - **重點測試(新)**：視窗 B 強制關閉 -> 視窗 A 繼續遊戲 -> 視窗 B 重開後自動重連 -> 加入下一輪。
4. **Android 實機測試 (新)**：
   - 匯出 APK 到手機 -> 建立/加入房間 -> 測試廣告流程 -> 測試通知推送。

**接手建議**：下次 Session 請**立即執行 APK 實機測試**，確認廣告與通知功能正常後，即可進入上架流程。
