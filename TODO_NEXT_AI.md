# NEXT AI SESSION HANDOFF (進度交接與後續待辦)

Hello 接下來接手的 AI：
本專案為 **Friends & Me** (異步社交探索桌遊 APP)。請優先閱讀 [APP.md](file:///c:/FriendAndMe/APP.md) 了解最新的專案架構與重要機制設定。

---

## 📅 下一階段工作規劃 (Next Phase Roadmaps)

- **多端連線與大廳重連壓力測試**：
  - 在正式環境中，利用多台手機（iOS/Android）與不同瀏覽器，進行 4-6 人的實際連線對局測試，以驗證 WebSocket 在多端高延遲下的流暢度與重連秒數同步性。
- **正式版網頁端 (Production Web Client) 部署上傳**：
  - 將本地經 `build_and_patch.py` 處理完畢的 `build_web_netlify` 靜態網頁資源，發布部署至 Netlify 正式環境；並將 `build_web_crazygames` 資料夾壓縮後上架至 CrazyGames 平台。
- **廣告平台正式切換**：
  - 驗證 CrazyGames SDK 或 Google AdSense H5 廣告的載入速度，並在 `index.html` 將廣告平台 `AD_PLATFORM` 由測試模式 (MOCK) 切換為正式上線模式。
- **Android APK 簽章與 Google Play 準備**：
  - **F1.0 階段 APK 打包方案決策**：在匯出正式 Release APK 時需要配置安全性簽章金鑰（否則會回報找不到發行 keystore 的錯誤），目前有以下兩個方案待下階段評估執行：
    * **方案 A（測試首選，直接匯出）**：使用 `--export-debug` 匯出。此方案直接使用 Godot 內建之 debug 金鑰進行自動簽署，產出的 APK 在遊戲功能、邏輯與效能上與正式版 100% 相同，可直接安裝至實機上進行完整測試，最適合目前的測試與體驗期。
    * **方案 B（發布首選，配置正式金鑰）**：在本地使用 `keytool` 生成正式的 `release.keystore` 密鑰檔案，配置於 `export_presets.cfg` 的 keystore 屬性中，並執行 `--export-release`。此方案產出的 APK/AAB 專供上架 Google Play 商店使用，金鑰一旦產生需妥善保存（遺失將無法更新商店上的 App）。