# NEXT AI SESSION HANDOFF (進度交接與後續待辦)

Hello 接下來接手的 AI：
請先閱讀本目錄下的 `APP.md` 了解本專案 **Friends & Me (異步社交探索桌遊)** 的核心願景與遊戲狀態機。

## 專案目前進度 (Current Progress)
- **Godot 專案已建立**：位於 `friend&me/` 目錄下 (Godot 4.6)。
- **視窗配置完成**：已設定為直立式手機版解析度 (`1080x1920`)，並支援 `expand` 響應式縮放。
- **基礎狀態機實作完成**：`main.tscn` 中已佈局好 Phase 0 到 Phase 4 的五個 Control 容器，並透過 `main.gd` 實作了切換顯示的基礎邏輯。目前執行能正常顯示全螢幕黑底白字的階段標題。
- **需求更新**：User 剛剛在 `APP.md` 更新了「社交等級層次 (Level 1~5)」的情境化時間線（如：日話家常、下午茶閒聊等），請務必將此概念融入後續的 UI 設計中。

## 接下來未完成的工作事項 (Pending Tasks)

### 1. 實作 Godot UI 介面 (優先事項)
- 根據先前的討論，UI 應採用 **現代感暗黑模式 (Dark Mode)** 搭配 **毛玻璃 (Glassmorphism)** 與霓虹漸變元素。
- **Phase 0 (Waiting for Captain)**：需建立大廳介面，包含「好友清單佔位區塊」以及「等待房主開始」的提示。
- **Phase 1 (Question Selection)**：需實作一個可滾動的卡片列表，列出 Level 1 到 Level 5 的題目標題與情境（請參考 `APP.md` 中新設定的層次），讓隊長可以點擊選擇。
- **Phase 2 (Answering)**：設計中央答題卡與文字輸入框，並且**必須**包含一個獨立且視覺上無壓力的「不回答」按鈕（符合心理安全機制）。
- **Phase 3 & 4 (Guessing & Revelation)**：設計連連看拖曳 (Drag & Drop) 介面與結算畫面。

### 2. 資料結構與連線測試
- 設計 Godot 前端內部暫存的假資料結構 (Mock Data)，以便在未串接後端前，能獨立測試 Phase 1 ~ Phase 4 的完整流程轉換。

---
**接手建議**：請先從 `main.tscn` 的 `Phase0_Lobby` 與 `Phase1_Selection` 開始，加入 Godot 內建的 UI 節點 (如 `VBoxContainer`, `PanelContainer`, `Button` 等) 將畫面刻出來，並與 User 確認視覺效果。
