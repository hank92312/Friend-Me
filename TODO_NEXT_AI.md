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
8. **Google AdSense 審核「沒有發布商內容」修正**：
   - **問題分析**：因 Godot 網頁版為 Canvas 渲染，頁面無爬蟲可讀之 HTML 文字，導致 AdSense 判定為「沒有發布商內容」而退件。
   - **技術方案**：於 `build_and_patch.py` 實作 **SEO 質感登陸頁面自動注入**。在 Netlify 的 `index.html` 注入擁有與遊戲一致之深色玻璃擬態說明的登陸首頁，提供遊戲介紹、喬哈里視窗理念、心理安全機制、Level 1-5 話題分級、核心步驟與 FAQ。
   - **體驗優化**：包裝 Godot 的 `engine.startGame` 到 `window.launchGame` 函數中，使用者點擊首頁「開始遊戲」時始下載 37MB Wasm 資源，避免強制消耗行動端流量並解決爬蟲無內容判定。
   - 已完成本地編譯與變更，並提交備份推送至 GitHub。
9. **Google Play Console 開發者帳號註冊與 AAB 上架**：
   - 已成功建立開發者帳號、解決了上傳時 AAB 的「所有上傳套件都必須經過簽署」與「金鑰指紋不符」問題（透過在本機 `.godot/export_credentials.cfg` 中配置發行金鑰與密碼，並匯出已導出的 `upload_certificate.pem` 向 Google 申請重設上傳金鑰並獲得批准）。
   - 已成功將簽章完成的 AAB 檔案上傳至封閉測試（Closed Testing）軌道，並順利通過 Google 審核，目前測試通道已發布上線。
   - 在商店資訊中成功配置了自訂生成的隱私權政策連結 `https://friendandme.netlify.app/privacy.html`，且完成「應用程式存取權」、「廣告 ID 聲明（廣告與行銷理由）」等政策表單。
10. **單人遊玩「結果揭曉」防空包修復**：
    - 修復了單人遊玩時 Phase 4 結果頁面為空白的 Bug，在 [friendAndme/main.gd](file:///c:/FriendAndMe/friendAndme/main.gd) 中新增單人遊玩（`round_answers.size() <= 1`）的 Fallback 邏輯，能自動在結果頁面中顯示玩家自己的答案。
    - 已完成本地編譯同步並重新產生已包含此 Bug 修復之正式簽章 AAB 套件。

---

## 📅 下一階段工作規劃 (Next Phase Roadmaps)

- **招募 20 位閉門測試 (Closed Testing) 人員**：
  - 目前封閉測試已審核通過。需複製「測試人員」分頁底下的**「加入測試專屬網址」**發送給 20 名測試人員。
  - 確保這 20 位測試人員下載並在手機中**連續保留 App 至少 14 天**，以解除 Google Play 個人帳號發布正式版的限制。
  - 可前往左側選單的 **「資訊主頁」** 查看 20 人/14 天倒數計時器的具體進度。
- **追蹤 Google AdSense 審核狀態**：
  - 目前已提交「要求複查」，新版 SEO 質感登陸網頁與 `ads.txt` 已部署上線，等待 Google 審核完畢後（約數天至兩週）即可將網頁端廣告平台由測試模式 (MOCK) 切換為正式上線模式。
- **多端連線與大廳重連壓力測試**：
  - 在正式環境中，利用多台手機（iOS/Android）與不同瀏覽器，進行 4-6 人的實際連線對局測試，以驗證 WebSocket 在多端高延遲下的流暢度與重連秒數同步性。
- **廣告平台正式切換**：
  - 驗證 Netlify 版的 Google AdSense H5 廣告的載入速度，並在 `index.html` 將廣告平台 `AD_PLATFORM` 由測試模式 (MOCK) 切換為正式上線模式。