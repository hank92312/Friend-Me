# NEXT AI SESSION HANDOFF (進度交接與後續待辦)

本專案為 **Friends & Me** (異步社交探索桌遊 APP)。請優先閱讀 [APP.md](file:///c:/FriendAndMe/APP.md) 了解最新的專案架構與重要機制設定。

---

## ✅ 本次 Session 完成項目 (Web 端手機 Bug 修正 — 2025-06)

1. **iOS Safari 無法輸入文字**
   - `export_presets.cfg` 啟用 `html/experimental_virtual_keyboard=true`

2. **鍵盤擋住輸入 / 游標跑掉 / 收鍵盤後按鈕點不到**
   - `build_and_patch.py` 補丁：Godot HTML `<input>` 改為固定置頂可見輸入列（金橘色主題，58px）
   - `pointer-events: auto` 允許游標移動；`blur` 後移至螢幕外防殘留攔截
   - visualViewport 狀態機（`fmKbWasOpen` + 150px 下降閾值 + 60px 恢復閾值）確保收鍵盤後可靠觸發 blur

3. **iOS Safari 切回 App 跳回登陸頁**
   - `sessionStorage fm_launched` 旗標：`DOMContentLoaded` 偵測後自動繞過登陸頁重啟引擎

4. **Android Chrome 切換 App 後卡在「等待」**
   - `main.gd _notification()` 監聽 `FOCUS_OUT/IN`，背景 ≥ 2 秒後呼叫 `NetworkManager.resync_on_foreground()`
   - `resync_on_foreground()` 主動丟棄假死 socket 並重建連線

5. **iPad 9 WebGL Context Lost 黑屏**
   - canvas `webglcontextlost` 監聽器 + `sessionStorage fm_gl_reloads` 計數（上限 2 次）自動 reload

6. **手機初次載入過慢 (pck 膨脹)**
   - 移除未被參照的 `NotoSansTC-VF.ttf`（11.4 MB），PCK 19.69 MB → 11.21 MB，總下載 ~56 MB → ~47 MB
   - 字型備份至 `C:\FriendAndMe\_unused_assets_backup\fonts\`

7. **更新後手機跑到舊版 (快取問題)**
   - `_headers` 加上 `Cache-Control: no-cache` for `/index.html` 和 `/index.js`
   - 同時移除不必要的 `Cross-Origin-Embedder-Policy: require-corp`（會阻擋 iOS 跨來源資源）

8. **輸入答案時無法看到題目**
   - `_on_answer_focus_entered()` 改為只隱藏 BtnNoAnswer，不隱藏 QuestionCard
   - 使用者收起鍵盤或按手機返回鍵即可回到題目頁（確認可接受，無需特別實作題目鏡射）

---

## 📋 已知狀態 / 環境備忘

| 項目 | 狀態 |
|---|---|
| Netlify 方案 | 已升級 Pro（2025-06 前），新版已部署 |
| Fly.io 後端 | 正常運行 (`friends-and-me.fly.dev`) |
| Google Play 封閉測試 | 已通過審核，進行中（需 20 人 × 14 天） |
| Google AdSense | 已提交複查（等待審核，約數天至兩週） |
| Android AAB 正式版 | v1.0.1 (Code 2)，已簽章，位於 `FriendAndMe_Release.aab` |
| Web build | `C:\FriendAndMe\build_web_netlify` (最新) |

---

## 📅 下一階段工作規劃 (Next Phase Roadmap)

- **招募 20 位閉門測試人員（Google Play）**
  - 封閉測試已通過審核。複製「測試人員」分頁底下的**「加入測試專屬網址」**發送給 20 位測試者。
  - 確保 20 位測試者在手機中**連續保留 App 至少 14 天**，以解除個人帳號發布正式版的限制。
  - 可於左側選單「資訊主頁」查看 20 人/14 天計時進度。

- **追蹤 Google AdSense 審核狀態**
  - 已提交複查，SEO 登陸頁 + `ads.txt` 已上線。審核通過後將 `AD_PLATFORM` 由 MOCK 切換為正式模式。

- **多端連線壓力測試**
  - 使用多台 iOS/Android 手機及不同瀏覽器進行 4–6 人真實對局，驗證 WebSocket 重連與倒數同步。

- **廣告正式切換**
  - AdSense 審核通過後，`build_and_patch.py` 中將 `AD_PLATFORM` 切換為正式模式並重新部署。

- **（選擇性）Android Chrome 打字時 Canvas 上推黑屏**
  - 打字當下 Godot canvas 被 Android 系統上推以空出鍵盤空間，畫面全黑但輸入列仍可見。
  - 目前使用者接受（收鍵盤即恢復），如未來需改善可研究 `viewport-fit=cover` + JS 鎖定 viewport 高度方案。
