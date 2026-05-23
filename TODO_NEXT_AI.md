# NEXT AI SESSION HANDOFF (進度交接與後續待辦)

Hello 接下來接手的 AI：
本專案為 **Friends & Me** (異步社交探索桌遊 APP)。請優先閱讀 [APP.md](file:///c:/FriendAndMe/APP.md) 了解完整的專案架構、機制、UI 設計與最近重要更新。

---

## 🟢 最新實測已驗證 (Recent Verifications)
在 2026-05-21/22 的測試中，使用者已在 **Web 瀏覽器端** 實測驗證以下功能正常：
- **字體變大變粗**：NotoSansTC-Bold 成功透過 Wasm/PCK Cache-Busting 載入，解決字型大小/粗細問題。
- **退回首頁正常**：廣告警語面板順利在退出房間時關閉並銷毀，不會卡死在大廳畫面上。
- **雲端連線正常**：網頁端可順利與 Fly.io 雲端伺服器 (`friends-and-me.fly.dev`) 連接，無 CORS 阻擋。
- **亂碼豆腐塊修復**：Emoji 已成功降級為純文字，Android 直角引號已自動轉為標準雙引號。
- **中英文雙語支援 (Bilingual Localization)**：
  - 於主畫面左下角加入 Language 切換按鈕與滑出式選單，支援「中文/English」即時切換與保存。
  - 解決了英文排版換行與按鈕高度自適應問題（關卡選擇按鈕動態高度計算）。
  - 將 11 處硬編碼中文改為 `tr()` 包裹，補齊 `translation_data.gd` 中的 `提交配對` 與 `送出配對結果` 翻譯對照表。
  - 完成導入英文題庫共 105 題（Level 1-5），ID 與中文題庫完美對齊。
  - 修復了 Godot 中變數 `notification` 遮蔽 (shadowing) 基類 Object 方法的警告，以及 `EN_MAP` 字典鍵值重複導致的解析器錯誤。

---

## 🔴 接下來待辦事項 (Pending Tasks)

### 1. 最優先：AdMob 正式發布準備與 Android APK 最終測試
- [x] **關閉測試廣告**：將 `ad_manager.gd` 的 `USE_TEST_ADS` 改為 `false`。
- [x] **替換正式廣告 ID**：已設定並啟用正式的 Interstitial Ad Unit ID：`ca-app-pub-XXXXXXXXXXXXXXXX/XXXXXXXXXX`。
- [ ] **Android 匯出路徑與建置**：
  - 開發目錄為 `C:\FriendAndMe\friendAndme\`。
  - 由於已統一將包含 `&` 的專案資料夾名稱修改為 `friendAndme`（已無特殊符號），現在可以直接在該目錄下進行 Android APK 匯出，或依然使用一鍵同步腳本 `C:\FriendAndMe\sync_to_build.bat` 同步至 `C:\FriendAndMe_Build` 再行匯出。

### 2. 次優先：音效缺漏補充 (已完成 ✅)
- [x] **音效缺漏補充**：無須引入新音效，直接套用現有 `sfx_btn_cancel` 並於 `audio_manager.gd` 降低音調。

### 3. Web 端廣告整合 (Phase D - 已完成 ✅)
- [x] **Web 廣告整合**：已在 `build_and_patch.py` 中實作多功能 JS 廣告控制器，並注入 `index.html`，完美支援：
  - `MOCK`：自製精美磨砂玻璃倒數廣告。
  - `CRAZYGAMES`：CrazyGames SDK 廣告 API。
  - `GOOGLE_H5`：Google AdSense H5 遊戲廣告 API（含測試廣告引導）。
  - 可以透過 `index.html` 中的 `AD_PLATFORM` 變數一鍵切換。
- [ ] **AdBlock 偵測**：未來可選實作。

---

## 🚀 快速啟動與開發測試指南

### 1. 本地啟動後端伺服器 (FastAPI)
在 Godot 雙開測試前，必須先讓後端運行：
```powershell
cd backend
.\venv\Scripts\Activate
uvicorn main:app --reload
```
*伺服器啟動成功後，預設運行於 `http://127.0.0.1:8000`*

### 2. 雙開測試 (Godot PC 端)
1. 開啟兩個 Godot 視窗 (F5) 進行同步測試。
2. 視窗 A：創立房間 -> 輸入名字 -> 獲得 6 位數房間碼。
3. 視窗 B：輸入房間碼 -> 輸入名字 -> 加入房間 -> 開始同步遊玩。

### 3. 本地網頁端測試
1. 本地 Python HTTP 伺服器已在背景運行於 Port 8080 (指向 `C:\FriendAndMe\build_web`)。
2. 瀏覽器開啟 `http://127.0.0.1:8080` 即可測試 Web 版。
3. 若修改程式，可執行專案根目錄的 `build_and_patch.py` 腳本，一鍵重新編譯 Web 版並自動回寫 Wasm/PCK Cache-Busting 邏輯。

---

## 💡 專案小工具與輔助插件
- **godot_ai 插件** (`friendAndme/addons/godot_ai/`)：MCP (Model Context Protocol) 橋接插件，啟用後可讓 AI 助理直接控制 Godot 編輯器，執行場景編輯與測試。
