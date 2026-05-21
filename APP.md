# Project Friends & Me - 異步社交探索桌遊 APP (中文暫未定)

## 1. 核心願景 (Core Vision)
利用「異步遊戲」降低社交壓力，透過「自我揭露」與「社交驗證」促進朋友間的深度連結與自我探索。

## 2. 核心機制與心理學邏輯
- **喬哈里視窗實踐**：透過「猜測他人答案」核對他人眼中的自己與真實自我的落差。
- **心理安全機制**：
    - 「不回答」也是一種有效的答案選項，降低強迫揭露的焦慮，並作為猜測階段的干擾項。
    - 數據隱私：被猜中率與猜中率可自由設定公開或私有。
- **社交等級層次 (情境化時間線)**：
    - Level 1：日話家常 (觀察得到的表層習慣，如：食衣住行)
    - Level 2：下午茶閒聊 (輕鬆、適合公開討論的話題，帶有一點個人色彩)
    - Level 3：居酒屋微醺 (稍微放鬆戒備，會聊到感情觀或生活抱怨)
    - Level 4：深夜真心話 (只在夜深人靜、面對極少數人時才會吐露的秘密)
    - Level 5：靈魂拷問 (核心自我、挑戰底線的極端情境)

## 3. 遊戲流程狀態機 (Game State Machine)
- **Phase 0: Waiting for Captain** (房主輪流派任隊長)
- **Phase 1: Question Selection** (隊長選擇大標題與對應 Level)
- **Phase 2: Answering Stage** (系統隨機派發子題目給各成員)
    - 使用者可選擇：[輸入答案] 或 [不回答]
    - 所有成員提交後進入下一階段。
- **Phase 3: Guessing Stage (點擊配對模式)**
    - UI 顯示：上方為答案區（橢圓 pill 方塊），下方為參與者區（橢圓 pill 方塊）。
    - 邏輯：點擊上方答案使其高亮，再點擊下方參與者完成配對；配對後雙方變色。全部配對完成後才出現「送出」按鈕。
- **Phase 4: Revelation Stage** (結果揭曉)
    - 系統通知所有人查看答案與配對結果。
    - 累計個人數據：猜中率 (Guess Accuracy)、被猜中率 (Self-Disclosure Recognition)。

## 4. 技術架構 (Technical Stack)

### A. 前端引擎 (Frontend) - [Godot Engine 4.6]
- **選擇原因**：需支援跨平台 (iOS/Android，並保留 PC 版擴展性)，且便於實作 UI 動畫、特效 (VFX) 與音效，強化「桌遊儀式感」。
- **視窗配置**：Viewport 為 `1080x1920` (直式)，開發用視窗覆寫 `540x960`，使用 `canvas_items` stretch mode + `expand` aspect。
- **視覺風格**：
    - 深色穩重背景 (`#1F1C1A`)，按鈕與重要元素採溫暖橘棕色 (`#D0813C`)，hover 為亮橘 (`#E39450`)。
    - 副標題與提示文字使用淡黃色 (`#FFF2CC`)。
    - Phase 3 使用橢圓 pill 形按鈕 (corner_radius=80)，答案區域與參與者區域各以深暖灰圓角面板承載。
    - 「不回答」按鈕為低調外框線風格 (Outline only)，降低心理壓力。
- **視覺與動效重點**：
    - **動態放射漸層背景 (Radial Gradient BG)**：於 `_ready()` 中動態套用 `GradientTexture2D` (中心 `#161413` 至邊緣 `#080707` 漸層)，取代原本單色背景，提升深邃視覺質感。
    - **全域按鈕懸停與下壓微互動 (Hover & Press Tweens)**：實作全域遞迴註冊，滑鼠懸停 (Hover) 放大至 `1.04` 倍，按鍵下壓 (Press) 縮小至 `0.94` 倍，利用 `Tween` 進行平滑過渡（自動排除 Phase 3 流式佈局中具備特定配對動畫的 Pill 按鈕）。
    - **客製化 LineEdit 輸入框**：美化所有輸入欄位（房號、暱稱、答案），套用圓角黑底外框、金黃色 Focus 外框發光與 shadow 效果。
    - **優雅 Cubic 轉場動畫 (Transitions)**：階段切換時，舊畫面的淡出與縮小 (0.18s)、新畫面的淡入與放大 (0.22s) 平行進行，利用 `TRANS_CUBIC` 增添介面操作的流暢與靈動感。
    - **浮動模態視窗與彈跳動畫 (Pop Card Modals)**：遊戲說明、設定選項、廣告警語等全數改為半透明暗底覆蓋層 (`#0D0A0A` 82% 透明) + 居中懸浮圓角卡片，並搭配 Entry (scale 0.9->1.0, `TRANS_BACK`) 與 Exit (縮小淡出) 的彈跳特效。
    - Phase 3 配對的顏色變化回饋：金黃色高亮 → 溫暖綠色已配對。
    - 異步狀態同步：需能處理離線與重新登入後的畫面恢復。
- **平台感知 Emoji 輔助**：為解決 Android 系統字型不支援部分 Emoji 導致顯示亂碼豆腐塊的問題，實作全域 `_emoji(emoji_text, fallback)` 輔助函數，在 Web/PC 顯示 Emoji，而在 Android 上顯示純文字替代方案。
- **推播系統**：採用 Android 本地通知插件 (`NotificationScheduler`)，註冊為 `NotifManager` 單例。已實作 App 前背景狀態感知邏輯：
    - 僅在 App 進入背景或暫停時（`NOTIFICATION_APPLICATION_FOCUS_OUT`/`PAUSED`）才允許發送通知，避免浮島視窗干擾遊玩。
    - 當 App 回到前景時（`NOTIFICATION_APPLICATION_FOCUS_IN`/`RESUMED`），自動呼叫 `cancel_all()` 清除所有發出的通知，並靜音後續通知。

### B. 後端 (Backend) — [已部署至 Fly.io]
- **語言/框架**：FastAPI (Python)。
- **即時通訊**：WebSockets (用於全體同步遊戲狀態)。
- **部署平台**：Fly.io (利用 Docker 容器與 Volume 持久化 SQLite 資料庫)。
- **自動清理**：當房間最後一人離開時，資料庫會自動清除該房間的所有對話紀錄，節省空間。
- **虛擬環境**：使用 `venv` 管理套件 (`backend/venv`)。
**虛擬環境指令**
cd backend
.\venv\Scripts\Activate

- **核心組件**：
    - `main.py`：API 進入點與 WebSocket 路由，加入 `lifespan` 自動建表邏輯。
    - `room_manager.py`：處理房間連線管理、玩家名單同步、狀態廣播與資料庫清理。
- **API 邏輯**：
    - `POST /create_room`：建立房間並生成 6 位數房間碼。
    - `POST /join_room`：加入指定房間。
    - `WS /ws/{room_id}/{player_name}`：即時同步玩家進入大廳、選題與換關。

### C. 數據模型 (Data Model)
- **Users**: ID, Name, PrivacySettings.
- **Rooms**: RoomID, Members[], CurrentPhase, CurrentCaptain.
- **QuestionBank**: LevelID, Topic, SubQuestions[] — 已建立 JSON 題庫。
- **RoundRecords**: (未來實作) 儲存配對正確率與歷史紀錄。

### D. 音效與 UI 系統 (Audio & UI Enhancements)
- **音效系統 (Audio System)**：
    - 使用 `audio_manager.gd` (Autoload) 統一管理。
    - 所有 `.ogg` 音效檔已透過 `ffmpeg loudnorm` 正規化至標準音量 (-12 LUFS)。
    - **動態音高 (Dynamic Pitching)**：難度選擇 (LV1~LV5) 共用同一音效，但透過調整 `pitch_scale` 與延遲回音 (Echo) 來營造不同深度的社交氛圍（LV1 輕快明亮 → LV5 低沉且帶有雙層殘響）。
    - 支援全域靜音控制 (`is_muted`)。
- **動態介面 (Dynamic UI)**：
    - **遊戲說明 (Tutorial)**：在首頁點擊，透過程式動態生成滿版覆蓋層，提供分頁式的遊戲操作與流程教學。
    - **設定選項 (Options)**：包含音效開關，以及「問題回饋」按鈕（點擊後自動複製開發者信箱並播放專屬音效）。

## 5. 擴展設計 (Scalability)
- **題庫策略：本地打包 (Local Bundle)**：
    - **當前決策**：題庫以 `question_bank.json` 打包在 Godot 專案內（`res://data/`），隨 App 安裝檔一同發行。
    - **採用原因（輕量化 & 低伺服器負擔）**：
        1. **零伺服器頻寬消耗**：客戶端直接從本地記憶體讀取題目，FastAPI 伺服器僅需傳遞輕量的控制指令（如題目 ID 或等級代碼），完全不需要透過網路傳輸題目文字內容，大幅降低流量費用與後端壓力。
        2. **即時載入，無網路延遲**：題目讀取為本地操作，無 API 延遲，UI 切換更順暢。
        3. **架構精簡**：後端無需建立題庫的 CRUD API，降低系統複雜度與潛在故障點。
    - **更新方式**：修改題庫後重新打包 App 上傳至各平台商店（手機端），或重新部署網頁（Web 端）。
    - **未來選項（備用）**：若日後需高頻更新題庫而不願重新上架，可引入「輕量 CDN 版本檢查」機制——App 啟動時僅向靜態空間比對一個 `version.txt`，確認有新版本後才下載更新，既不佔用 FastAPI 伺服器，也能讓玩家免去商店更新。
- **跨平台佈局**：Godot UI 節點需設定 Anchors 與 Margins，確保手機直式與未來 PC 橫式佈局的響應式適應 (Responsive Design)。

## 6. 主視覺
- 主題深色系 (`#1F1C1A`)，整體氛圍以溫暖為主軸
- 按鈕：實心橘棕色圓角，hover 時亮橘色
- 特殊按鈕（如「不回答」）：透明背景 + 橘色外框線
- Phase 3 pill 方塊：答案為橘色 pill / 參與者為中棕色 pill，圓角 80px (接近橢圓)
- 狀態顏色語言：金黃色=選取中 / 溫暖綠=已配對

---

## 8. 商業模式 (Monetization)

### 發行平台與廣告策略
| 平台 | 廣告方案 | 狀態 |
|------|---------|------|
| **Android (Google Play)** | Google AdMob SDK — 插頁廣告 (Interstitial) / 獎勵影片 (Rewarded Video) | ✅ 已完成 (AdManager 單例整合) |
| **Web (HTML5)** | Google AdSense for Games / H5 遊戲廣告聯播網 (CrazyGames, Poki 等)，透過 `JavaScriptBridge` 與 Godot 互動 | 🔲 待實作 |
| **iOS (Apple App Store)** | 暫緩 — 目前尚無 Apple 開發者帳號，待未來取得後再規劃 | ⏸️ 暫緩 |

### 廣告觸發時機設計
- **最佳觸發點**：在「建立房間」或「加入房間」**之前**安插一個可跳過的短影片廣告 (Skippable Interstitial)，此時玩家處於等待狀態，不會感到遊戲被打斷。
- **備選觸發點**：每局結束 (Phase 4 結算) 到下一局開始之間的過渡畫面。
- **體驗原則**：遊戲進行中 (Phase 1~4) **絕不插入廣告**，保護核心社交體驗的沉浸感。

### 技術實作概念
- **Android**：透過 Godot 的 Android Plugin 機制整合 AdMob SDK，在 GDScript 中呼叫 Java 端的廣告顯示函式。
- **Web**：Godot 匯出 HTML5 後，在外層 HTML 頁面中引入廣告 SDK 的 JavaScript。遊戲內透過 `JavaScriptBridge.eval("showVideoAd()")` 觸發廣告播放，廣告結束後由 JS 回呼 Godot 函式 `ad_finished()` 繼續遊戲流程。
- **AdBlock 防護 (Web)**：偵測廣告是否被阻擋，若被擋則直接放行遊玩或彈出友善提示。

## 7. 已完成的前端架構 (Current Frontend Implementation)

### 檔案結構
```
friend&me/
├── project.godot          # 專案配置 (1080x1920, 開發視窗 540x960)
├── main.tscn              # 主場景 (Phase 0~4 UI 佈局)
├── main.gd                # 主腳本 (狀態機 + 題庫載入 + 配對邏輯)
└── data/
    └── question_bank.json # 結構化題庫 (5 級，共 105 題)
```

### 場景節點架構 (main.tscn)
```
Main (Control)
├── Background (Panel) — 深色全螢幕背景
└── Phases (Control) — 透過 visible 控制顯示哪個 Phase
    ├── Phase0_Lobby — 4 個按鈕 (創立圈圈/加入圈圈/遊戲說明/選項)
    ├── Phase1_Selection — 6 個 LV 選擇按鈕 + 回首頁按鈕
    ├── Phase2_Answering — 題目卡 + 輸入框 + 送出按鈕 + 不回答按鈕
    ├── Phase3_Guessing — 上下分區 (答案 pill + 參與者 pill) + 完成配對按鈕
    └── Phase4_Revelation — 佔位文字 (待實作)
```

### 腳本邏輯 (main.gd)
- **GamePhase 枚舉**：WAITING → WAIT_LOBBY → SELECTION → ANSWERING → GUESSING → REVELATION → SELECTION_WAITING
- **NetworkManager (Autoload)**：全域單例，封裝 HTTP 與 WebSocket 通訊。
- **名字輸入系統**：實作了彈出式視窗讓玩家輸入自訂暱稱，並同步至伺服器。
- **大廳同步**：創立/加入房間後進入 `Phase0_WaitLobby`，透過伺服器推播 `player_list_updated` 同步名單。
- **動態教學與選項 UI**：不依賴 tscn 節點，由腳本動態生成覆蓋層，避免破壞場景結構。
- **Phase 3 聯網同步**：
    - **真實答案**：不再使用 Mock 資料，答案按鈕完全來自房間內真實玩家的提交內容。
    - **真實參與者**：名單同步顯示房間內真實玩家的名字。
- **Phase 4 聯網結算**：
    - **真實統計**：根據伺服器彙整的所有玩家猜測數據，計算真實的「被隊友猜中率」。
    - **動態結果飛入**：結合音效（猜對/猜錯）與 `tween` 動畫，實現結果卡片錯開飛入的揭曉感。
    - **循環遊玩**：支援由伺服器驅動的隊長輪替，可連續進行多輪遊戲。

### 結算與統計 (Phase 4)
- **單輪正確率**：顯示「你猜對幾個隊友」。
- **累計統計**：跨輪次紀錄「你的答案被隊友猜中率」與「你猜中隊友答案率」。
- **自適應 UI**：結算清單具備卷軸與字體自動縮放功能，因應人數多寡自動調整。

### 題庫 (question_bank.json)
- **格式**：`levels.{1~5}.questions[]`，每題有 `id`、`tag`、`text`
- **數量**：LV1: 25題 / LV2: 25題 / LV3: 25題 / LV4: 15題 / LV5: 15題，共 105 題
- **原始設計文件**：`Friends&Me_Question_Bank.md` (根目錄)

### StyleBox 資源 (Sub Resources in main.tscn)
| ID | 用途 | 顏色 |
|----|------|------|
| StyleBoxFlat_bg | 全螢幕背景 | `#1F1C1A` |
| StyleBoxFlat_btn_normal | 按鈕預設 | 橘棕 `#D0813C` |
| StyleBoxFlat_btn_hover | 按鈕 hover/pressed | 亮橘 `#E39450` |
| StyleBoxFlat_btn_outline | 「不回答」按鈕 | 透明底 + 橘色邊框 |
| StyleBoxFlat_card | 題目卡面板 | 深灰 `#2E2924` |
| StyleBoxFlat_pill | 答案 pill (Phase 3) | 橘棕，圓角 80 |
| StyleBoxFlat_pill_hover | 答案 pill hover | 金黃 |
| StyleBoxFlat_pill_participant | 參與者 pill | 中棕 `#6B4D2E`，圓角 80 |
| StyleBoxFlat_section_panel | Phase 3 上下背景框 | 深暖灰，圓角 32 |

---

## 9. 最近重要更新紀錄 (Recent Updates - 2026-05-21)

### 1. UI 懸浮面板置中自適應優化
- 針對 `TutorialPanel` (遊戲說明)、`OptionsPanel` (設定選項)、`AdDisclaimerPanel` (廣告提示) 等動態生成卡片，在半透明覆蓋層下引入 `CenterContainer` 節點包裹 `DialogCard`。
- 修改所有相關 `get_node()` 內部路徑至 `CenterContainer/DialogCard/...`，確保在各種寬高比解析度下（包括 PC 端寬螢幕與手機端窄螢幕）卡片皆能保持置中，防偏置跑版。

### 2. 連連看題目換行與手機自適應
- Phase 3 配對階段頂部的題目 Label 屬性調整：
  - `size_flags_horizontal` 設為 `Control.SIZE_EXPAND_FILL`。
  - `autowrap_mode` 設為 `TextServer.AUTOWRAP_WORD_SMART`，以便能流暢折行中文與英文混排。
  - 字體大小調大至 `42`，徹底解決原本字體過小、超出螢幕的問題。

### 3. Android 系統引號 tofu 豆腐塊亂碼修正
- 利用平台感知輔助函數 `_quote(text: String) -> String`，檢測如果當前平台為 `Android`，則自動將 `「` 與 `」` 引號更換為標準雙引號 `"`。
- 將 Phase 3/4 的題目與 Phase 4 結果卡片的引號拼接皆替換為 `_quote()`，解決 Android 預設中文字型缺少直角引號造成的豆腐塊亂碼。

### 4. 網頁端 Web 匯出與本地測試伺服器建立
- 在 `export_presets.cfg` 中追加 `Web` (HTML5) 導出預設。
- **解決 Web 端中文顯示亂碼問題**：引入微軟系統內建思源黑體繁體中文變量字型 `NotoSansTC-VF.ttf` 至專案資源目錄 `assets/fonts/` 中，並於 `project.godot` 配置全域 `gui/theme/custom_font`。此舉使得 HTML5 Web 端在瀏覽器中能夠無縫載入中文，徹底解決了標題與遊戲中文字元顯示為亂碼豆腐塊的問題。
- 使用 Godot Console 執行檔 `--headless` 成功導出 Web 專案檔案至 `C:\FriendAndMe\build_web`。
- 啟動本地 Python HTTP 伺服器 (Port 8080)，支援電腦端、手機端、網頁端三端同步聯合連線測試。

### 5. 全域專案圖示替換 (Project Icon Replacement)
- 將專案根目錄下新作好的 `icon-new.png` 複製至專案資源目錄為 `icon_new.png`。
- 修改 `project.godot` 配置全域 `config/icon="res://icon_new.png"`，確保遊戲主圖示已替換。
- 修改 `export_presets.cfg` 設定 Android 端的各尺寸啟動圖示、自適應圖示 (Launcher Icons) 及 Web 端的 PWA 圖示路徑全數指向新圖示 `res://icon_new.png`，完成全平台圖示的一致性更替。
- 重新執行 Web 平台釋出匯出，產出包含新圖示與修復後字型的最新靜態資源包。