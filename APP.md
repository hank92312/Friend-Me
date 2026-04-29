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
- **Phase 3: Guessing Stage (連連看模式)**
    - UI 顯示：[題目列表]、[答案列表(含"不回答")]、[成員名單]
    - 邏輯：成員需將答案與名單進行 1-to-1 拖曳配對。
- **Phase 4: Revelation Stage** (結果揭曉)
    - 系統通知所有人查看答案與配對結果。
    - 累計個人數據：猜中率 (Guess Accuracy)、被猜中率 (Self-Disclosure Recognition)。

## 4. 技術架構 (Technical Stack)

### A. 前端引擎 (Frontend) - [Godot Engine]
- **選擇原因**：需支援跨平台 (iOS/Android，並保留 PC 版擴展性)，且便於實作 UI 動畫、特效 (VFX) 與音效，強化「桌遊儀式感」。
- **視覺與動效重點**：
    - 狀態切換時的平滑轉場 (Transitions)。
    - 連連看配對時的拖拉回饋 (Drag & Drop UI) 與正確/錯誤特效。
    - 異步狀態同步：需能處理離線與重新登入後的畫面恢復。
- **推播系統**：透過 Godot 插件串接 Firebase Cloud Messaging (FCM) & APNs。

### B. 後端 (Backend)
- **語言/框架**：FastAPI (Python) 或 Node.js。
- **資料庫**：PostgreSQL (主要存儲)、Redis (暫存遊戲狀態與加速查詢)。
- **API 邏輯**：
    - `POST /submit_answer`：隱藏真實答案直到 Guessing Stage 結束，防止前端抓包。
    - `GET /get_guessing_payload`：隨機打亂答案順序提供前端連連看。

### C. 數據模型 (Data Model)
- **Users**: ID, Name, PrivacySettings, GlobalStats(GuessRate, GuessedRate).
- **Rooms**: RoomID, Members[], CurrentRoundID, CurrentCaptainID.
- **QuestionBank**: LevelID, Topic, SubQuestions[].
- **RoundRecords**: RoundID, UserID, SubQuestionID, Answer, IsPassed(Bool), Guesses(JSON), Timestamp.

## 5. 擴展設計 (Scalability)
- **題庫擴充接口**：預留 CSV/JSON 導入機制，支援未來「使用者自定義題庫」與「AI 動態題庫」。
- **跨平台佈局**：Godot UI 節點需設定 Anchors 與 Margins，確保手機直式與未來 PC 橫式佈局的響應式適應 (Responsive Design)。

---