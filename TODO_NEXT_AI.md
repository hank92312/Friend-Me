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