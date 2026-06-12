# NEXT AI SESSION HANDOFF (進度交接與後續待辦)

本專案為 **Friends & Me** (異步社交探索桌遊 APP)。請優先閱讀 [APP.md](file:///c:/FriendAndMe/APP.md) 了解最新的專案架構與重要機制設定。

---

## ✅ 本次 Session 完成項目 (題庫擴充 + Android v1.1.0 — 2026-06-12)

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

9. **題庫擴充至 155 題（每等級 +10 題）**
   - 新題全為開放式、單一答案、台灣文化導向（夜市、手搖、颱風假、KTV、圍爐、親戚聚會等）
   - 同步更新：中英文 MD 種子文件 + 前後端 JSON 共 6 個檔案
   - 重新匯出 Web 版（build ver 1781232924）並部署至 Netlify
   - 後端重新部署至 Fly.io

10. **Android AAB v1.1.0 (code 3) 匯出與上傳**
    - `export_presets.cfg` 版本號升級：`1.0.1` / code 2 → `1.1.0` / code 3
    - 使用環境變數 `GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD` 傳入密碼（不寫入任何檔案）
    - AAB 已匯出（41.4 MB），已上傳 Google Play 封閉測試軌道
    - 兩則 Play Console 警告（ProGuard mapping、native debug symbols）均為非關鍵警告，可忽略

11. **Keystore 密碼安全性修正**
    - 舊密碼曾洩漏在 git 歷史中（repo 為私有，keystore 本體從未被 commit，風險低）
    - 執行 `keytool -storepasswd` 更換密碼（PKCS12 格式，`-keypasswd` 不適用）
    - 新密碼存放於 Google 雲端硬碟私人文件

12. **多人 desync 階段倒退與重複計分 bug 修正**
    - 根因：後端 WebSocket 事件未驗證階段，背景分頁殘留計時器送出的過期事件被接受 → 階段退回 GUESSING + `_persist_round_results` 二次寫入
    - 後端（權威）：`topic_selected`/`answer_submitted`/`guesses_submitted` 各加階段守衛，非對應階段一律忽略（`main.py`）
    - 前端（輔助）：非 ANSWERING 廣播時強制關閉 `answering_timer_active`（`main.gd` `_on_network_phase_sync`）
    - 已部署 Fly.io（後端）+ Netlify（前端 build 1781245889）
    - ⚠️ 注意：此修正僅防止「未來」再發生，已污染的舊測試統計需另外清理（測試帳號可直接砍掉重來）

---

## 📋 已知狀態 / 環境備忘

| 項目 | 狀態 |
|---|---|
| Netlify 方案 | 已升級 Pro（2025-06 前），新版已部署 |
| Fly.io 後端 | 正常運行 (`friends-and-me.fly.dev`) |
| Google Play 封閉測試 | 已通過審核，進行中（需 20 人 × 14 天） |
| Google AdSense | 已提交複查（等待審核，約數天至兩週） |
| Android AAB 正式版 | v1.1.0 (Code 3)，已簽章，位於 `FriendAndMe_Release.aab` |
| Web build | `C:\FriendAndMe\build_web_netlify` (最新，build ver 1781232924) |
| 題庫 | 155 題（L1–3 各 35 題，L4–5 各 25 題），中英文同步 |

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

- **（擱置）手機瀏覽器返回後倒數計時器不同步（純顯示問題）**
  - 現象：手機瀏覽器縮小約 1 分鐘後返回，倒數仍從 120 秒開始，未與其他玩家同步。
  - 根因：`resync_on_foreground()` 靠 `NOTIFICATION_APPLICATION_FOCUS_IN` 觸發，此通知在 Android 原生 App 可靠，但手機瀏覽器縮小/切走時 Godot Web 不一定收到，導致重新同步未被觸發。
  - **已無功能性危害**：伺服器階段守衛（APP.md #16）+ 前端非答題階段關閉計時器，已確保錯誤計時器不會造成階段倒退或重複計分；階段一推進即自動修正，剩餘僅為返回後幾十秒的顯示誤差。
  - 正解：在 `build_and_patch.py` 加 `visibilitychange` 監聽器，分頁重新可見時透過 JavaScriptBridge 呼叫 `resync_on_foreground()`。需手機實測驗證。
  - **決議：先擱置，封測若出現類似問題導致 bug 再一併修復。**
