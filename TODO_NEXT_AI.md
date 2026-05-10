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
- **靜默斷線重連 (新完成)**：
    - `network_manager.gd`：WebSocket 斷線後每 3 秒自動嘗試重連，最多 8 次。
    - `backend/room_manager.py`：斷線玩家「標記保留」而非刪除，重連後可識別身份。
    - `backend/main.py`：重連玩家加入「等待下一輪」名單，遊戲繼續，不卡其他玩家。
    - 斷線後若其他玩家全數提交，伺服器自動推進階段（不因斷線者卡住）。
- **UI 轉場動畫與介面 (新完成)**：
    - 所有 Phase 切換採用 0.18s 淡出 + 0.22s 淡入的 Sine 緩動。
    - Phase 3 pill 選取：Back 彈跳 scale-up；配對成功：Elastic bounce。
    - Phase 4 揭幕：標題淡入 + 結果卡片 stagger（每張間隔 0.18s）從右滑入。
    - Phase 4 結算：字體放大優化，猜中率與被猜中率加入 0.0% 到實際值的平滑計數動畫 (Tween)。
    - **動態遊戲說明 (Tutorial)**：點擊後彈出深色覆蓋層，支援分頁觀看房間創建與遊戲流程。
    - **設定選項 (Options)**：支援全域音效開關，並具備「點擊複製製作人信箱」功能。
- **音效系統 (新完成)**：
    - 建立 `audio_manager.gd` Autoload 單例。
    - 導入 14 個 `.ogg` 音效並全部利用 `ffmpeg` 進行 loudness 正規化至 -12 LUFS。
    - 實作 **動態音高與殘響**，同一選題音效在 LV1 (明亮) 到 LV5 (沉重且有兩次回音) 會呈現不同的社交情境氛圍。
    - 成功綁定 UI 點擊、房間建立、難度選擇、成功配對、結果揭曉等觸發點。

- **後端雲端部署 (新完成)**：
    - 成功封裝 FastAPI 後端成 Docker 容器。
    - 成功部署至 Fly.io (`friends-and-me.fly.dev`)，支援 24 小時 WebSockets 即時連線。
    - 使用 Fly.io Volume 掛載硬碟 (`/data`) 存放 SQLite 資料庫，確保重啟不遺失資料。
    - `room_manager.py` 實作自動清空機制：最後一人離開房間時，自動清除資料庫中的該房所有問答紀錄。
    - `network_manager.gd` 加入 `USE_LOCAL` 開關，方便一鍵切換本地測試或雲端連線。

## godot_ai 插件說明 (新增)
- **位置**：`friend&me/addons/godot_ai/`
- **用途**：MCP (Model Context Protocol) 橋接插件，讓 Antigravity 等 AI 助手可直接控制 Godot 編輯器。
- **啟用方式**：Project > Project Settings > Plugins > Godot AI > 啟用
- **依賴**：需要安裝 `uv`（Python 套件管理工具）
- **整合建議**：在 Godot 啟用插件後，Antigravity 即可直接操作場景樹、修改節點屬性、執行測試，無需手動切換。

## 接下來未完成的工作事項 (Pending Tasks)

### 1. Phase C：體驗優化與擴充 (下一步規劃)
- **推播通知 (Push Notifications)**：實作 FCM 或 APNs 確保玩家在縮小 App 時能收到輪到他的通知。
- **資料庫轉移 (選作)**：若未來玩家數量大增且需要多節點擴充，可將 SQLite 轉移至 PostgreSQL。
- **題庫動態導入**：實作 CSV 或從雲端抓取新題庫的功能。

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

**接手建議**：先進行雙開連線測試確認動畫效果，再實作音效系統。
