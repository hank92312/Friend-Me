# Friends & Me — 專案現況分析與後續開發計畫

## 專案現況總結

### ✅ 已完成的功能

| 層面 | 功能 | 狀態 |
|------|------|------|
| **後端** | FastAPI + WebSocket 即時通訊架構 | ✅ 完成 |
| **後端** | 房間系統（創建/加入/6位數房間碼） | ✅ 完成 |
| **後端** | 隊長輪替邏輯 | ✅ 完成 |
| **後端** | 答案提交 & 猜測提交 同步 | ✅ 完成 |
| **後端** | 靜默斷線重連（標記保留 + 等待下一輪） | ✅ 完成 |
| **後端** | SQLite 數據持久化（User/Room/Round/Answer/Guess） | ✅ 完成 |
| **後端** | 結算後自動累計個人統計到 DB | ✅ 完成 |
| **前端** | Phase 0~5 完整 UI 佈局（Godot 4.6） | ✅ 完成 |
| **前端** | 暱稱輸入系統 | ✅ 完成 |
| **前端** | 題庫載入（5級 95 題 JSON） | ✅ 完成 |
| **前端** | Phase 3 配對 UI（pill 按鈕 + 動態配色） | ✅ 完成 |
| **前端** | Phase 4 結算揭曉（stagger 動畫 + 計分） | ✅ 完成 |
| **前端** | Phase 5 個人結算歷史 | ✅ 完成 |
| **前端** | 淡入淡出轉場動畫 | ✅ 完成 |
| **前端** | NetworkManager Autoload（HTTP + WebSocket） | ✅ 完成 |
| **前端** | AudioManager Autoload（14 音效 + 動態音高） | ✅ 完成 |
| **前端** | Tutorial 分頁教學覆蓋層 | ✅ 完成 |
| **前端** | Options 設定（靜音 + 製作人聯絡） | ✅ 完成 |

### ⚠️ 已建立但尚未啟用的項目

| 項目 | 說明 |
|------|------|
| `sfx_pill_select` | 音效存在但 AudioManager 中已註解，未綁定 |
| `sfx_reveal_card` | 音效不存在，AudioManager 已註解 |
| `sfx_reconnect_ok` | 音效不存在，AudioManager 已註解 |
| `database.py` + `models.py` | ✅ 已完整建立，但 `requirements.txt` 缺少 `sqlalchemy` 和 `aiosqlite` |

### 🔴 待完成的核心功能

根據 `APP.md` 與 `TODO_NEXT_AI.md` 的規劃，以及實際程式碼分析：

1. **Phase 4 計數動畫** — 猜中率百分比數字從 0% 跳到實際數值的 tween 動畫
2. **部署上線** — 目前後端僅本地運行，需部署到雲端才能手機端連線
3. **推播通知** — FCM/APNs 串接（APP.md 規劃，待實作）
4. **手機端匯出** — Godot 匯出 APK/IPA
5. **音效缺失** — 3 個音效佔位但未啟用

---

## 可行性評估

> [!IMPORTANT]
> **核心遊戲邏輯已 100% 完成**，目前的版本在本地雙開 Godot 測試下已經可以完整體驗全流程。
> 最大的瓶頸不在於功能開發，而在於「部署」（讓手機端能連到伺服器）。

### 技術風險分析

| 風險 | 評估 | 說明 |
|------|------|------|
| 後端部署 | 🟡 中等 | 需要雲端主機 + HTTPS + WSS，成本與配置需考量 |
| Godot APK 匯出 | 🟢 低 | Godot 原生支援，但需要 Android SDK |
| iOS 匯出 | 🔴 較高 | 需要 macOS + Xcode + Apple Developer 帳號 |
| 推播通知 | 🟡 中等 | FCM 較容易，APNs 需 Apple 設定 |
| SQLite 擴展性 | 🟡 中等 | 目前夠用，若多人同時使用需遷移 PostgreSQL |
| WebSocket 並發 | 🟢 低 | 小型社交遊戲，FastAPI 足以應付 |

---

## 後續開發計畫（建議優先順序）

### 🔴 Phase A：修復與打磨（最優先 — 確保 MVP 品質）

> [!NOTE]
> 這些是讓現有功能更完善、更穩定的小修改，不涉及新架構。

#### A1. 修復 `requirements.txt` 缺漏
- 新增 `sqlalchemy[asyncio]` 和 `aiosqlite` 到 `requirements.txt`
- 確保新環境可直接 `pip install -r requirements.txt` 完成安裝

#### A2. 補齊缺失音效
- **已決定**：`sfx_pill_select`、`sfx_reveal_card`、`sfx_reconnect_ok` 經測試會打亂遊玩節奏，**暫時停用**。
- 其餘音效確保正確觸發。

#### A3. Phase 4 計數動畫
- 實作猜中率百分比數字 tween（從 0% 跳到實際值），增加揭曉戲劇感
- 參考 `TODO_NEXT_AI.md` 中的規劃

#### A4. 後端啟動時自動建表
- 目前需手動執行 `init_db.py`，應在 FastAPI `startup` 事件中自動執行 `create_all`

---

### 🟡 Phase B：部署與連線（讓真正的手機能玩）

> [!IMPORTANT]
> 這是 MVP 從「開發測試」到「可以讓朋友們玩」的關鍵步驟。

#### B1. 後端部署到雲端
- **建議方案**：使用 [Railway](https://railway.app/) 或 [Render](https://render.com/) 或 [Fly.io](https://fly.io/)
  - 支援 FastAPI + WebSocket
  - 免費方案足夠初期使用
  - 自動 HTTPS/WSS
- **需修改**：
  - `network_manager.gd` 中的 `BASE_URL` 和 `WS_URL` 改為雲端地址
  - 考慮環境變數管理（dev vs prod URL）
  - 資料庫從 SQLite 遷移到 PostgreSQL（雲端長期穩定性）

#### B2. Godot 前端網路地址可配置化
- 將 `BASE_URL` / `WS_URL` 從寫死改為從設定檔讀取或提供切換機制
- 方便開發時使用 localhost、上線時切換到雲端

#### B3. Android APK 匯出測試
- 配置 Godot Export Template for Android
- 設定 Android SDK path
- 首次匯出 debug APK 在手機上測試

---

### 🟢 Phase C：功能增強（提升體驗）

> [!NOTE]
> 基礎 MVP 穩定後，可逐步加入這些提升用戶體驗的功能。

#### C1. 推播通知系統
- 串接 Firebase Cloud Messaging (FCM) for Android
- 當輪到你當隊長、遊戲開始時推送通知
- Godot 插件：使用現有的 FCM GDExtension

#### C2. 題庫擴充機制
- 支援使用者自定義題庫（JSON 導入）
- 考慮 AI 動態生成題目的接口

#### C3. 玩家帳號系統
- 目前玩家身份靠「暱稱」區分，無持久化身份
- 可考慮簡單的帳號機制（Guest ID 或 Google/Apple 登入）

#### C4. 響應式 UI 優化
- 適配不同手機螢幕尺寸（特別是 iPhone 瀏海 / Android 折疊機）
- 橫式佈局預留（PC 版擴展）

#### C5. 隱私設定
- 實作 APP.md 中提到的「被猜中率與猜中率可自由設定公開或私有」
- 加入 User 的 PrivacySettings 功能

---

## Open Questions

> [!IMPORTANT]
> **部署平台選擇**：你偏好哪個雲端平台？Railway / Render / Fly.io / 自架 VPS？
> 這會影響 Phase B 的具體實作方式。

> [!IMPORTANT]
> **資料庫遷移時機**：是否在 Phase B 就從 SQLite 遷移到 PostgreSQL？
> 還是先用 SQLite 部署，等用戶數增長再遷移？

> [!IMPORTANT]
> **優先目標確認**：你目前最想達成的里程碑是什麼？
> - (a) 先讓手機上可以玩（Phase B 優先）
> - (b) 先把現有功能打磨到最好（Phase A 優先）
> - (c) 其他你想先做的功能？

> [!WARNING]
> **iOS 匯出**需要 macOS + Apple Developer 帳號（年費 $99 USD），
> 如果你沒有這些資源，建議先專注 Android APK。

---

## Verification Plan

### Phase A 驗證
- 在新虛擬環境中執行 `pip install -r requirements.txt`，確認所有套件安裝成功
- 啟動後端伺服器 → 雙開 Godot 測試 → 完整走過一輪遊戲流程
- 驗證 Phase 4 計數動畫視覺效果
- 驗證所有音效是否正確觸發

### Phase B 驗證
- 部署到雲端後，用手機瀏覽器/APK 連線測試
- 測試斷線重連在 4G/WiFi 切換情境下的穩定性
- 測試多人同時連線（3-5 人）的延遲表現
