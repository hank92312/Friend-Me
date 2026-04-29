# NEXT AI SESSION HANDOFF (進度交接與後續待辦)

Hello 接下來接手的 AI：
請先閱讀本目錄下的 `APP.md` 了解本專案 **Friends & Me (異步社交探索桌遊)** 的核心願景、遊戲狀態機，以及目前已完成的前端架構。

## 專案目前進度 (Current Progress)
- **Godot 專案已建立**：位於 `friend&me/` 目錄下 (Godot 4.6)。
- **視窗配置完成**：Viewport `1080x1920` (直式)，開發視窗覆寫 `540x960`，stretch mode = `canvas_items`，aspect = `expand`。
- **主視覺風格已建立**：深色穩重背景 + 溫暖橘棕色按鈕，詳見 `APP.md` 第 6~7 節的 StyleBox 資源表。
- **Phase 0~3 UI 與邏輯已完成**：
    - Phase 0 (大廳)：4 個功能按鈕 (創立圈圈/加入圈圈/遊戲說明/選項)。
    - Phase 1 (選題)：6 個 LV 選擇按鈕 (雙行排版：主標題+副標題) + 回首頁按鈕。
    - Phase 2 (答題)：上方大型題目卡 + 下方 LineEdit 輸入框 + 送出按鈕 + 外框風格「不回答」按鈕。
    - Phase 3 (猜測配對)：上下分區 pill 方塊，點擊答案高亮 → 點擊參與者完成配對 → 全部配完才出現送出按鈕。
- **題庫 JSON 已建立**：`friend&me/data/question_bank.json`，5 級共 95 題 (LV1: 25, LV2: 25, LV3~5: 各 15)。
- **題庫載入邏輯已實作**：`main.gd` 在 `_ready()` 時載入 JSON，選完等級後隨機抽題顯示在 Phase 2。

## 接下來未完成的工作事項 (Pending Tasks)

### 1. Phase 4 結算畫面 (Revelation Stage) — 高優先
- 設計結算畫面 UI，顯示配對結果（正確/錯誤）。
- 呈現每位玩家的統計數據（猜中率、被猜中率）。
- 加入「再來一局」或「返回大廳」的按鈕。

### 2. Phase 2 → Phase 3 答案傳遞 — 高優先
- 目前 Phase 3 的答案 pill 方塊還是寫死的佔位文字 ("吃拉麵"、"不回答")。
- 需要把 Phase 2 中玩家輸入的答案（或選擇「不回答」）動態傳遞到 Phase 3 的答案區。
- 搭配 Mock Data (假玩家) 模擬多人場景。

### 3. Mock Data 假資料系統 — 中優先
- 建立一份假的玩家名單 (3~5 人，含名字)。
- 模擬每位玩家的答案（或不回答），使 Phase 3 能有完整的多人配對體驗。
- 建議在 `main.gd` 中用 Dictionary/Array 管理，或獨立為 `mock_data.gd`。

### 4. UI 動效與轉場 — 低優先
- Phase 切換時加入淡入淡出或滑動的 Tween 動畫。
- Phase 3 配對成功時加入小動效 (如放大縮小彈跳)。

### 5. 後端串接準備 — 未來
- 設計 API 介面規格 (REST endpoints)。
- 將目前 Mock Data 邏輯抽象為可替換的資料層，以便未來無縫切換到真實後端。

### 6. 題庫擴充 — 持續
- LV3~5 目前各 15 題，可持續新增。
- 原始設計文件在根目錄 `Friends&Me_Question_Bank.md`，新增後需同步更新 `friend&me/data/question_bank.json`。

---
**接手建議**：建議先實作 Mock Data + 答案傳遞 (Task 2+3)，讓 Phase 2→3→4 的完整流程可以跑通，再處理 Phase 4 結算畫面。
