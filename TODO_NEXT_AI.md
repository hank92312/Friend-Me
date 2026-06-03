# NEXT AI SESSION HANDOFF (進度交接與後續待辦)

本專案為 **Friends & Me** (異步社交探索桌遊 APP)。請優先閱讀 [APP.md](file:///c:/FriendAndMe/APP.md) 了解最新的專案架構與重要機制設定。

---

## ✅ 已完成工作 (Completed Tasks)

1. **答題倒數調整至 120 秒**：
   - 伺服器端 ([backend/main.py](file:///c:/FriendAndMe/backend/main.py)) 答題超時設定已調整為 `120` 秒。
   - 伺服器端玩家重連時的時間戳記計算邏輯也修正為以 `120` 秒為基準。
   - 客戶端 ([friendAndme/main.gd](file:///c:/FriendAndMe/friendAndme/main.gd)) 答題倒數的 fallback 預設值與本地顯示時間均已調整為 `120` 秒。
2. **特別感謝協助製作名單**：
   - 於設定選單「個人資料運用說明」下方新增一個不可點擊的灰暗按鈕，以表示不給予點擊。
   - 中英文語系皆已完成翻譯與換行設定：
     - 中文：`特別感謝協助製作:ALICE、Benoit、縩興`
     - 英文：`Special thanks to contributors:\nALICE, Benoit, 縩興`
3. **消除所有 Godot 編輯器警告 (驚嘆號)**：
   - 修正了 `main.gd` 內共計 9 項 GDScript 編輯器警告（包含變數命名混淆、參數遮蔽 Node 信號、未使用的變數與參數），使程式碼清爽無警告。
4. **Google AdSense H5 廣告串接與優化**：
   - **串接修正**：修正了 `build_and_patch.py` 中的載入代碼，在腳本載入前預先初始化全域 `adBreak`/`adConfig`，並在 script 的 `src` 中帶入 `client` 發布商參數以確保 Google SDK 正常載入。
   - **防卡死優化**：在網頁端的 JavaScript 層級加上了 **3 秒鐘安全計時器**，若玩家安裝 AdBlock 阻擋廣告或 Google 廣告無填充，將在 3 秒內自動跳過放行，防止遊戲死鎖。
   - **所有權驗證**：在 Netlify 版的 `index.html` 的 `<head>` 中靜態注入了 Google AdSense 的驗證腳本，現已順利通過 Netlify 網域所有權驗證。
   - **自動生成 `ads.txt`**：打包時會自動在 Netlify 釋出包中生成合法的 `ads.txt` 檔案，宣告授權廣告賣方，防範廣告詐騙。
5. **部署與打包**：
   - 後端服務已成功部署至 Fly.io 並完成健康檢查，新版 120 秒計時器已在線運行。
   - Web 端已重新編譯並產生 cache-busting 與 Google H5 廣告的 Netlify 正式發行版 ([build_web_netlify](file:///c:/FriendAndMe/build_web_netlify)) 與 CrazyGames 版 ([build_web_crazygames](file:///c:/FriendAndMe/build_web_crazygames))。
   - Android 正式版 APK 已避開檔案鎖定，匯出並以發行金鑰完成簽章，檔案位於 [FriendAndMe_Release.apk](file:///c:/FriendAndMe/FriendAndMe_Release.apk)。
6. **Google Play 應用內購買去廣告功能 (IAP / Remove Ads)**：
   - 於 `export_presets.cfg` 正式啟用 `com.android.vending.BILLING` 權限。
   - 於 `translation_data.gd` 新增中英文去廣告狀態之翻譯字典對應。
   - 於 `ad_manager.gd` 完整串接 `GodotGooglePlayBilling` 插件與信號（交易更新、確認交易等），並實作自動確認交易（Acknowledge）機制以防自動退款。
   - 實作本地加密快取機制，將購買結果 AES 加密儲存至 `user://settings_data.dat`，離線或無 Billing 插件平台也能安全攔截並跳過廣告。
   - 於 `main.gd` 的設定（Options）選單中，在 Android 平台與本地 Debug 除錯模式下動態新增「移除廣告」按鈕，並精細安排於 spacer 分割線之前以符合視覺設計；若已購買則按鈕呈現灰暗停用的 `已免除廣告 (感謝支持！)`。
   - 針對未申請 Play 開發者帳號的階段，特別在 `ad_manager.gd` 中加入 Debug 模式模擬購買成功機制，使本地測試 UI 整合邏輯百分之百順暢可行。
7. **Google Play Store 上架準備**：
   - 將 Android 匯出預設格式修改為 **AAB** 格式，設定版本為 `1.0.0` (Code `1`)。
   - 在 `build_and_patch.py` 中實作自動生成極具質感、支援中英雙語切換之 **隱私政策網頁 (`privacy.html`)**，並打包輸出至 Netlify 目錄。
   - 將最新程式碼與配置同步至建置目錄 `C:\FriendAndMe_Build`，並在 headless 模式下執行編譯驗證，確認除了預期的發行金鑰簽章外，無任何語法或檔案缺失錯誤。
   - **Netlify 部署完成**：已將最新的 `build_web_netlify` 目錄（含 `privacy.html`、`ads.txt` 及更新版 HTML 廣告與驗證配置）發佈至 Netlify，目前隱私權政策網址為 `https://friendandme.netlify.app/privacy.html`。
   - 已完成所有變更的本地測試、並提交備份推送至 GitHub。

---

## 📅 下一階段工作規劃 (Next Phase Roadmaps)

- **向 Google Play Console 提交隱私權政策**：
  - 在 Play Console 內的「應用程式內容 (App Content)」->「隱私權政策 (Privacy Policy)」欄位中，填入已部署的隱私權政策連結：`https://friendandme.netlify.app/privacy.html`。
- **在 GUI 中匯出簽名 AAB 檔案**：
  - 開啟 Godot GUI 載入建置目錄 `C:\FriendAndMe_Build` 專案。
  - 點擊「專案」->「匯出」，選擇 Android 預設，點擊「匯出專案」，將輸出檔命名為 `FriendAndMe_Release.aab`（GUI 會使用本地的發行金鑰完成簽署）。
  - 將匯出的 `.aab` 檔案上傳到 Google Play Console 中。
- **追蹤 Google AdSense 審核狀態**：
  - 目前 `friendandme.netlify.app` 已提交「要求複查」，且新版 `ads.txt` 也已部署上線。接下來需要等待 Google 審核完畢（通常需數天到兩週），狀態變為「準備就緒」後網頁端廣告即會開始播放。
- **多端連線與大廳重連壓力測試**：
  - 在正式環境中，利用多台手機（iOS/Android）與不同瀏覽器，進行 4-6 人的實際連線對局測試，以驗證 WebSocket 在多端高延遲下的流暢度與重連秒數同步性。
- **廣告平台正式切換**：
  - 驗證 Netlify 版的 Google AdSense H5 廣告的載入速度，並在 `index.html` 將廣告平台 `AD_PLATFORM` 由測試模式 (MOCK) 切換為正式上線模式。