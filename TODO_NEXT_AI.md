# NEXT AI SESSION HANDOFF (進度交接與後續待辦)

Hello 接下來接手的 AI：
本專案為 **Friends & Me** (異步社交探索桌遊 APP)。請優先閱讀 [APP.md](file:///c:/FriendAndMe/APP.md) 了解最新的專案架構與重要機制設定。

---

## 📅 下一階段工作規劃 (Next Phase Roadmaps)

- **多端連線與大廳重連壓力測試**：
  - 在正式環境中，利用多台手機（iOS/Android）與不同瀏覽器，進行 4-6 人的實際連線對局測試，以驗證 WebSocket 在多端高延遲下的流暢度與重連秒數同步性。
- **正式版網頁端 (Production Web Client) 部署上傳**：
  - 將本地經 `build_and_patch.py` 處理完畢的 `build_web` 靜態網頁資源，發布部署至 Netlify 正式環境。
- **廣告平台正式切換**：
  - 驗證 CrazyGames SDK 或 Google AdSense H5 廣告的載入速度，並在 `index.html` 將廣告平台 `AD_PLATFORM` 由測試模式 (MOCK) 切換為正式上線模式。
- **Android APK 簽章與 Google Play 準備**：
  - 配置正式的 Release keystore 簽章金鑰，更新 `export_presets.cfg`，準備進行上架 Google Play 的 Release AAB/APK 打包。

---

## ⚠️ 待測試的優先驗證事項 (Priority Untested Items)
- **結果揭曉畫面 (Phase 4) 房號顯示與複製按鈕實機測試**：
  - 驗證結果揭曉（Phase 4）畫面左上角是否正確顯示房號（如 `房間碼: ABC123`），且按鈕與右側「離開圈圈」在直式螢幕上完美對稱。
  - 切換為 English 語言，確認該區域是否能自動對齊顯示為 `Room Code: ABC123` 與 `Copy`。
- **手機端縮小至背景與斷線重連後時間同步實機測試**：
  - 手機 App 暫時縮小到背景，過 10~15 秒再切回來，確認倒數計時是否有扣除該時間並與全房同步。
  - 測試在斷網 10 秒後重連，確認時間是否自動與伺服器對齊。