# NEXT AI SESSION HANDOFF (進度交接與後續待辦)

Hello 接下來接手的 AI：
本專案為 **Friends & Me** (異步社交探索桌遊 APP)。請優先閱讀 [APP.md](file:///c:/FriendAndMe/APP.md) 了解完整的專案架構、機制、UI 設計與最近重要更新。

> [!IMPORTANT]
> **🚨 核心開發守則：每次輸出網頁與 APK 前的排版檢查規範**
> 
> 為避免每次修改後輸出又產生排版跑版而反覆編譯打包，**任何 AI 助理在修改 UI/語系/文字並重新執行 `build_and_patch.py` 或匯出 APK 之前，必須先完成以下檢查項目**：
> 
> 1. **中文語系折行模式限制 (必須為 AUTOWRAP_ARBITRARY)**：
>    * Godot Wasm 網頁導出及 Android APK 預設不包含完整的 ICU 折行資料庫。
>    * 在**中文語系**下，如果使用 `AUTOWRAP_WORD_SMART` 或 `AUTOWRAP_WORD`，引擎會將無空格的整句中文判定為一個「超長單字」而拒絕換行，進而向橫向拉伸，撐爆彈出卡片（Dialog Card）與滾動區域，導致 UI 排版完全崩潰。
>    * 因此，在中文語系下，所有支援折行的 Label **必須動態切換為 `TextServer.AUTOWRAP_ARBITRARY`**。
> 2. **英文語系折行模式限制 (必須為 AUTOWRAP_WORD_SMART)**：
>    * 在**英文語系**下，若使用 `AUTOWRAP_ARBITRARY` 會使英文單字在任意字元截斷（如 `notifications` 被劈開成兩行）。
>    * Therefore，英文語系下必須使用 `TextServer.AUTOWRAP_WORD_SMART` 以確保單字完整折行。
> 3. **動態更新驗證**：
>    * 修改 UI 後，確認已在對應的初始化/語言變更處（如 `_update_localized_ui`）執行 `_update_all_autowrap_modes_recursively(self)` 或透過 `_get_local_autowrap_mode()` 動態給予 `autowrap_mode`。
> 4. **前置測試流程**：
>    * 執行打包前，務必先在 Godot 編輯器內執行（F5）或在本機網頁端（`http://localhost:8080`）切換 **「中文」** 與 **「English」**，點開 **「遊戲說明」**、**「選項」** 與 **「廣告提示」** 等視窗，實測確認：
>      * 文字折行是否正確？
>      * 卡片寬度是否正常（無橫向異常拉伸爆版）？
>      * 翻頁後的高度自適應是否貼合？
>    * **確認排版完全正確無誤後，方可執行網頁編譯與 APK 打包！**

---

## ⚠️ 待測試的優先驗證事項 (Priority Untested Items)
- **手機端縮小至背景與斷線重連後時間同步實機測試 (2026-05-26 待玩家實測驗證)**：
  - **待實測細節**：
    1. 手機 App 暫時縮小到背景，過 10~15 秒再切回來，確認倒數計時是否有扣除該時間並與全房同步。
    2. 確認若在背景時倒數歸零，切回 App 時是否能正確自動推進至下個畫面。
    3. 測試在斷網 10 秒後重連，確認時間是否自動與伺服器對齊。

---

## 📅 下一階段工作規劃 (Next Phase Roadmaps)
- **後端 Fly.io 雲端伺服器部署**：
  - 將本機最新修正的 `backend/main.py`（加入 started_at 與重連時間精確同步邏輯）部署至 Fly.io 雲端伺服器 (`friends-and-me.fly.dev`)。
- **正式版網頁端 (Production Web Client) 部署上傳**：
  - 將本地經 `build_and_patch.py` 處理完畢的 `build_web` 靜態網頁資源，發布部署至 Netlify 正式環境。
- **多端連線與大廳重連壓力測試**：
  - 在正式環境中，利用多台手機（iOS/Android）與不同瀏覽器，進行 4-6 人的實際連線對局測試，以驗證 WebSocket 在多端高延遲下的流暢度與重連秒數同步性。
- **廣告平台正式切換**：
  - 驗證 CrazyGames SDK 或 Google AdSense H5 廣告的載入速度，並在 `index.html` 將廣告平台 `AD_PLATFORM` 由測試模式 (MOCK) 切換為正式上線模式。
- **Android APK 簽章與 Google Play 準備**：
  - 配置正式的 Release keystore 簽章金鑰，更新 `export_presets.cfg`，準備進行上架 Google Play 的 Release AAB/APK 打包。

---

## 🟢 最新實測已驗證 (Recent Verifications)
- **手機端 App 縮小至背景再切回之倒數不同步修復 (2026-05-26 已完成修復，待玩家實測驗證)**：
  - **問題原因**：因 Godot 引擎在 App 進入背景時會被系統掛起暫停 `_process`，導致本地計時被「凍結」，切回時便與伺服器脫節。且 WebSocket 重連成功時未同步更新遊戲內的倒數計時。
  - **修復內容**：
    1. **Unix 截止時間戳記比對**：全面改用 `Time.get_unix_time_from_system()` 來設定目標截止時間戳記，在 `_process` 內透過當下系統時間與目標截止時間差值計算剩餘秒數，保證 App 縮小切回後時間自動扣除並正確同步。
    2. **重連自動同步**：在 `_on_reconnect_status` 重連事件中接收伺服器回傳的 `remaining_seconds` 並重新校正本地截止時間，確保斷線重連後的計時器 100% 精準。
    3. **遊戲說明修改**：將說明第一頁的第二點由「輸入一個朋友認得的暱稱」修改為更明確的「輸入你的名字(暱稱)」（中英文已同步）。
- **倒數計時強制切換與 1、2 分鐘倒數強制前進功能 (2026-05-26 玩家實測已驗證完成)**：
  - **修復內容**：在 `SELECTION`、`GUESSING` 及 `REVELATION` 階段在本地倒數歸零時主動執行強制預設操作（隊長隨機選題、強制送出已配對答案、宣告下一輪準備完畢），且結果揭曉階段為 120 秒；配合後端 fly.io 記錄 `started_at` 與重連精確扣除已耗時間，多端測試運作正常。
- **彈出視窗 (Dialog Cards) 佈局塌陷與首頁卡死修復 (2026-05-26 玩家實測已驗證完成)**：
  - **修復內容**：在 [main.gd](file:///C:/FriendAndMe/FriendAndMe/main.gd) 中，藉由 `_on_dialog_viewport_resized` 內的 `_adjust_single_dialog_card()` 機制，動態計算內容高度 `vbox.get_combined_minimum_size().y` 與最大容許高度 `viewport_height - 200` 取較小者設給 `ScrollContainer` 的 `custom_minimum_size.y`，解決了遊戲說明、設定選項、廣告聲明卡片塌陷成一條窄線的問題。
- **英文版折行單字截斷與遊戲說明自適應/排版跑掉修復 (2026-05-26 玩家實測已驗證完成)**：
  - **修復內容**：實作中英文雙語折行模式動態切換（中文為 `AUTOWRAP_ARBITRARY`，英文為 `AUTOWRAP_WORD_SMART`），並在切換語系及翻頁時重新觸發 `_adjust_single_dialog_card()` 調整高度，徹底解決首次打開高度拉長及折行單字在英文字元截斷的排版問題。
- **貼上功能與字體大小優化驗證完成 (2026-05-25)**：
  - 實作了 JavaScriptBridge 搭配原生 `prompt()` 彈窗做為 iOS Safari 等安全性沙盒下的 Clipboard 備用貼上方案，完成 100% 行動端貼上暱稱與房號支援。
  - 修正了回答超時空提交防卡死，移除了亂碼碼錶 Emoji，並實作遞迴字體縮放（網頁端增加 12、手機端增加 10 單位），使全域字體明顯變大。

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

### 3. 本地網頁端測試與開發流程 (電腦與手機同 Wi-Fi 區域網路測試)
為了避免頻繁部署至 Netlify 浪費部署時間與 Netlify 頻寬用量，您可以在本地進行多端測試，完整測試流程如下：

1. **啟動後端伺服器** (Port 8000)：
   確保已啟動 FastAPI 服務（參考上述步驟 1）。
2. **啟動專屬網頁伺服器** (Port 8080)：
   在專案根目錄執行以下命令：
   ```powershell
   python serve.py
   ```
   > [!IMPORTANT]
   > **為什麼使用 `serve.py`？**  
   > Godot 4 的 Web (WebGL/Wasm) 導出大量使用 `SharedArrayBuffer`，現代瀏覽器安全策略規定，伺服器必須返回 `Cross-Origin-Opener-Policy: same-origin` 與 `Cross-Origin-Embedder-Policy: require-corp` 標頭才能正常執行。  
   > 傳統的 `python -m http.server` 沒有這些標頭，會導致網頁開啟時出現空白或 SharedArrayBuffer 未定義的錯誤。因此**請務必使用 `python serve.py`。**
3. **電腦端本機網頁測試**：
   - 在您的電腦瀏覽器打開網址：`http://localhost:8080` 即可立即遊玩測試。
   - **多端模擬技巧**：您可以開啟多個瀏覽器分頁，或搭配「無痕視窗 (Incognito Window)」，即可在同一台電腦上同時模擬多個不同的玩家加入同一個房間進行連線測試。
4. **手機端實機區域網路測試 (不需部署)**：
   - 確保您的手機與電腦連接在 **同一個 Wi-Fi 區域網路** 下。
   - 在電腦端打開 Windows 終端機 (CMD) 輸入 `ipconfig`，尋找您電腦的區域網路 IP（通常是 IPv4 地址，例如 `192.168.1.100` 或 `192.168.50.X`）。
   - 在手機的 Safari 或 Chrome 瀏覽器網址列輸入 `http://[您的電腦IP]:8080`（例如 `http://192.168.1.100:8080`），手機就能無縫載入電腦本地的遊戲網頁進行測試。
5. **程式碼修改與更新（一鍵重譯與熱重載）**：
   - 當您在 Godot 中修改了程式碼，**不需**打包 APK 或重新部署。
   - 僅需在專案根目錄執行：
     ```powershell
     python build_and_patch.py
     ```
   - 這會自動觸發 Godot 重新編譯 Web 版本，並套用本地快取與輸入框修正補丁。
   - 編譯完成後，直接**重新整理**（F5 / Ctrl+F5）您的瀏覽器網頁分頁，即可立即看到修改後的效果，極大節省打包與部署時間。

### 4. Android APK 本地直接建置打包指南 (新 ✅)
- **一鍵打包 Android APK 命令**（在 Windows PowerShell 中執行）：
  ```powershell
  & "C:\Users\hank9\Downloads\Godot_v4.6.2-stable_win64.exe\Godot_v4.6.2-stable_win64_console.exe" --path "C:\FriendAndMe\FriendAndMe" --export-debug "Friend&Me" "C:\FriendAndMe\FriendAndMe.apk"
  ```
  > [!TIP]
  > **為什麼使用 `--export-debug`？**  
  > 導出 Android release 版本需要配置正式發布密鑰 keystore。本地及測試安裝使用 `--export-debug` 可以直接利用 Godot 預設的 debug keystore 完成簽章，避免建置失敗。

---

## 💡 專案小工具與輔助插件
- **godot_ai 插件** (`friendAndme/addons/godot_ai/`)：MCP (Model Context Protocol) 橋接插件，啟用後可讓 AI 助理直接控制 Godot 編輯器，執行場景編輯與測試。