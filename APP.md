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
    - 狀態切換時的平滑轉場 (Transitions) — 待實作。
    - Phase 3 配對的顏色變化回饋：金黃色高亮 → 溫暖綠色已配對。
    - 異步狀態同步：需能處理離線與重新登入後的畫面恢復。
- **推播系統**：透過 Godot 插件串接 Firebase Cloud Messaging (FCM) & APNs — 待實作。

### B. 後端 (Backend) — [已實作基礎架構]
- **語言/框架**：FastAPI (Python)。
- **即時通訊**：WebSockets (用於全體同步遊戲狀態)。
- **虛擬環境**：使用 `venv` 管理套件 (`backend/venv`)。
- **核心組件**：
    - `main.py`：API 進入點與 WebSocket 路由。
    - `room_manager.py`：處理房間連線管理、玩家名單同步與狀態廣播。
- **API 邏輯**：
    - `POST /create_room`：建立房間並生成 6 位數房間碼。
    - `POST /join_room`：加入指定房間。
    - `WS /ws/{room_id}/{player_name}`：即時同步玩家進入大廳、選題與換關。

### C. 數據模型 (Data Model)
- **Users**: ID, Name, PrivacySettings.
- **Rooms**: RoomID, Members[], CurrentPhase, CurrentCaptain.
- **QuestionBank**: LevelID, Topic, SubQuestions[] — 已建立 JSON 題庫。
- **RoundRecords**: (未來實作) 儲存配對正確率與歷史紀錄。

## 5. 擴展設計 (Scalability)
- **題庫擴充接口**：預留 CSV/JSON 導入機制，支援未來「使用者自定義題庫」與「AI 動態題庫」。
- **跨平台佈局**：Godot UI 節點需設定 Anchors 與 Margins，確保手機直式與未來 PC 橫式佈局的響應式適應 (Responsive Design)。

## 6. 主視覺
- 主題深色系 (`#1F1C1A`)，整體氛圍以溫暖為主軸
- 按鈕：實心橘棕色圓角，hover 時亮橘色
- 特殊按鈕（如「不回答」）：透明背景 + 橘色外框線
- Phase 3 pill 方塊：答案為橘色 pill / 參與者為中棕色 pill，圓角 80px (接近橢圓)
- 狀態顏色語言：金黃色=選取中 / 溫暖綠=已配對

---

## 7. 已完成的前端架構 (Current Frontend Implementation)

### 檔案結構
```
friend&me/
├── project.godot          # 專案配置 (1080x1920, 開發視窗 540x960)
├── main.tscn              # 主場景 (Phase 0~4 UI 佈局)
├── main.gd                # 主腳本 (狀態機 + 題庫載入 + 配對邏輯)
└── data/
    └── question_bank.json # 結構化題庫 (5 級，共 95 題)
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
- **Phase 3 聯網同步**：
    - **真實答案**：不再使用 Mock 資料，答案按鈕完全來自房間內真實玩家的提交內容。
    - **真實參與者**：名單同步顯示房間內真實玩家的名字。
- **Phase 4 聯網結算**：
    - **真實統計**：根據伺服器彙整的所有玩家猜測數據，計算真實的「被隊友猜中率」。
    - **循環遊玩**：支援由伺服器驅動的隊長輪替，可連續進行多輪遊戲。

### 結算與統計 (Phase 4)
- **單輪正確率**：顯示「你猜對幾個隊友」。
- **累計統計**：跨輪次紀錄「你的答案被隊友猜中率」與「你猜中隊友答案率」。
- **自適應 UI**：結算清單具備卷軸與字體自動縮放功能，因應人數多寡自動調整。

### 題庫 (question_bank.json)
- **格式**：`levels.{1~5}.questions[]`，每題有 `id`、`tag`、`text`
- **數量**：LV1: 25題 / LV2: 25題 / LV3: 15題 / LV4: 15題 / LV5: 15題，共 95 題
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