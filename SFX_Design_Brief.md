# Friends & Me — UI 短音效需求清單 (SFX Design Brief)

> **專案風格定位**：溫暖、親近、稍帶儀式感的社交桌遊。
> 整體音效應偏向「有機溫暖」（木質敲擊、柔和鐘聲、布料摩擦），
> 避免科技感、電子嗶聲或過於遊戲化的音效。

---

## 音效總覽表

| # | 檔名（建議） | 觸發時機 | 建議時長 | 音調 | 情感 |
|---|------------|---------|---------|------|------|
| 1 | `sfx_btn_tap.ogg` | 所有一般按鈕點擊 | 50–80ms | 中音 | 輕快、乾淨 |
| 2 | `sfx_btn_cancel.ogg` | 取消/返回按鈕 | 60–100ms | 低音 | 輕柔退場 |
| 3 | `sfx_room_created.ogg` | 房間建立成功 | 300–500ms | 中高音 | 期待感、開場 |
| 4 | `sfx_player_join.ogg` | 有玩家加入大廳 | 200–350ms | 中音 | 友善、歡迎 |
| 5 | `sfx_copy_id.ogg` | 複製房間碼 | 80–120ms | 高音 | 清脆、即時反饋 |
| 6 | `sfx_game_start.ogg` | 房主按下開始遊戲 | 600–900ms | 上揚曲線 | 儀式感、興奮 |
| 7 | `sfx_level_select.ogg` | Phase 1 選擇難度等級 | 150–250ms | 依等級升高 | 謹慎、選擇感 |
| 8 | `sfx_submit_answer.ogg` | Phase 2 送出答案 | 250–400ms | 中音下沉 | 篤定、落定 |
| 9 | `sfx_no_answer.ogg` | Phase 2 選擇「不回答」 | 150–200ms | 低柔音 | 輕描淡寫、無壓力 |
| 10 | `sfx_pill_select.ogg` | Phase 3 點擊答案 pill（選取） | 60–100ms | 中高音 | 清脆選中感 |
| 11 | `sfx_pill_match.ogg` | Phase 3 配對成功（兩 pill 連線） | 200–350ms | 和弦/泛音 | 滿足、暖心 |
| 12 | `sfx_pill_unmatch.ogg` | Phase 3 解除配對（反悔） | 100–150ms | 下滑音 | 輕微、不懲罰 |
| 13 | `sfx_reveal_card.ogg` | Phase 4 每張結果卡片飛入 | 80–130ms | 輕敲聲 | 懸疑揭曉 |
| 14 | `sfx_result_correct.ogg` | Phase 4 猜對結果出現 | 350–500ms | 大三度上揚 | 喜悅、成就感 |
| 15 | `sfx_result_wrong.ogg` | Phase 4 猜錯結果出現 | 300–400ms | 小二度下滑 | 溫柔失落（不刺耳）|
| 16 | `sfx_next_round.ogg` | 按下「再玩一輪」 | 400–600ms | 循環感旋律 | 活力、期待下一輪 |
| 17 | `sfx_reconnect_ok.ogg` | 斷線後重連成功 | 300–400ms | 輕柔提示音 | 安心、靜默重回 |

---

## 各音效詳細設計說明

## Turn 1

### 🤖 Assistant

這份音效清單整理得非常專業！你把「情感（Emotion）」跟「製作提示（Production Tips）」都明確標示出來，這對於建構遊戲的「聽覺體驗（Audio UX）」非常有幫助，特別是強調「不羞辱玩家」、「無壓力」的心理學設計，完全契合這款 APP 的核心精神。
為了方便你在 Freesound、Envato Elements、Kenney 或其他英文音效庫精準搜尋，我幫你在每個品項下方加上了專屬的 **英文搜尋關鍵字 (Search Keywords)**，這些詞彙是國外音效設計師最常使用的標籤（Tags）：

---

### 1. `sfx_btn_tap.ogg` — 一般按鈕點擊 21

- **觸發**：所有主要操作按鈕（創立房間、加入房間、確認名字、確認房間碼）
- **建議**：乾燥的木塊敲擊聲或指甲輕彈桌面。不要回音。
- **參數**：A3–C4 音區，快速起音（Attack < 5ms），自然衰減。
- **製作提示**：可用竹製品輕敲，或拇指輕彈嘴唇。
- 🔍 **英文搜尋關鍵字**：`UI click`, `wood tap`, `soft pop`, `dry tap`, `clean click`, `wooden UI`, `snap`

---

### 2. `sfx_btn_cancel.ogg` — 取消/返回 16

- **觸發**：BtnCancelJoin、BtnCancelName、BtnBack
- **建議**：比 btn_tap 略低沉的拍打聲，帶點消音感。
- **製作提示**：手掌輕拍桌面，或將木塊聲 pitch 降低 3–4 個半音。
- 🔍 **英文搜尋關鍵字**：`UI back`, `muted tap`, `soft thud`, `low knock`, `cancel click`, `dull thud`, `UI decline`

---

### 3. `sfx_room_created.ogg` — 房間建立成功 

- **觸發**：`_on_network_room_created()` — HTTP 回傳 room_id 後
- **建議**：溫暖的三音符旋律（如 do-mi-sol），像信件投入信箱的清脆聲後接短旋律。
- **情感**：「我已準備好了！」
- **製作提示**：鋼琴 C-E-G 短奏，或木琴三音符。
- 🔍 **英文搜尋關鍵字**：`success chime`, `positive notification`, `3 note chime`, `achievement ping`, `warm UI success`, `xylophone chord`

---

### 4. `sfx_player_join.ogg` — 玩家加入大廳

- **觸發**：`_on_network_player_list_updated()` — 每當名單更新（有新人進來）
- **建議**：一個輕快的「叮」聲或短促木魚聲，帶小小的上揚感。
- **情感**：朋友走進房間的感覺。
- **製作提示**：三角鐵輕敲一下，或杯緣碰觸聲。
- 🔍 **英文搜尋關鍵字**：`player join`, `glass clink`, `triangle ding`, `bell ding`, `soft chime`, `pop notification`

---

### 5. `sfx_copy_id.ogg` — 複製房間碼

- **觸發**：BtnCopyID 按下（`DisplayServer.clipboard_set()`）
- **建議**：極短的「啪」或「嗒」，像橡皮章蓋下的聲音。
- **製作提示**：指甲彈硬卡片聲，或鍵盤按鍵聲 pitch 調高。
- 🔍 **英文搜尋關鍵字**：`stamp sound`, `card flick`, `mechanical click`, `short snap`, `plastic click`, `typewriter keystroke`

---

### 6. `sfx_game_start.ogg` — 開始遊戲

- **觸發**：`_on_btn_start_game()` — 房主按下開始
- **建議**：帶有儀式感的上揚旋律，2–3 個音符 + 殘響。像桌遊翻開第一張牌的期待感。
- **情感**：「讓我們開始吧！」氣氛要暖，不要像電玩開場那樣強烈。
- **製作提示**：豎琴或鋼琴 C-G-C 八度，帶輕微殘響。
- 🔍 **英文搜尋關鍵字**：`game start`, `warm intro`, `harp glissando short`, `positive transition`, `level begin chime`, `magic glimmer`

---

### 7. `sfx_level_select.ogg` — 選擇難度等級

- **觸發**：Phase 1 的 BtnLevel1~5、BtnRandom 按下
- **建議**：類似翻牌的柔和聲，不同等級可加一點 pitch 差異（LV1 低、LV5 高）。
- **製作提示**：紙牌翻轉聲，或木琴單音（按等級調整音高）。
- **實作備註**：可以是同一音效 + GDScript 動態調整 `pitch_scale`（LV1=0.85, LV5=1.15）
- 🔍 **英文搜尋關鍵字**：`card flip`, `paper slide`, `soft marimba`, `wood block single`, `percussion UI`, `gentle click`

---

### 8. `sfx_submit_answer.ogg` — 送出答案

- **觸發**：`_on_btn_submit_answer()`
- **建議**：帶「確定落地」感的聲音，像信封封口或書本闔上。略帶殘響。
- **情感**：篤定感，代表「我說完了」。
- **製作提示**：書本關閉聲，或低沉的木塊「咚」。
- 🔍 **英文搜尋關鍵字**：`book close`, `solid drop`, `confirm stamp`, `wood thud`, `UI confirm`, `heavy snap`, `envelope seal`

---

### 9. `sfx_no_answer.ogg` — 選擇「不回答」

- **觸發**：BtnNoAnswer 按下
- **建議**：比 submit_answer 更輕柔、幾乎無聲的吐氣感。不應有明顯音符。
- **情感**：「我保留這個」，低調、無壓力。
- **製作提示**：極輕的布料摩擦聲，或氣音（口吹麥克風）。
- 🔍 **英文搜尋關鍵字**：`soft whoosh`, `gentle breath`, `fabric rustle`, `cloth swipe`, `subtle swoosh`, `airy UI`, `wind sweep`

---

### 10. `sfx_pill_select.ogg` — 選取答案 Pill

- **觸發**：Phase 3 點擊答案 pill（`_on_answer_btn_pressed`）
- **建議**：清脆的「叮」或玻璃珠碰撞聲，短促有活力。
- **製作提示**：玻璃杯輕碰，或鐘琴高音 A4–B4。
- 🔍 **英文搜尋關鍵字**：`crystal clink`, `glass ding`, `bright pop`, `glockenspiel note`, `light ping`, `bubble pop`

---

### 11. `sfx_pill_match.ogg` — 配對成功

- **觸發**：`_on_participant_btn_pressed` — 兩 pill 成功連線時
- **建議**：**最重要的音效之一**。溫暖的和弦音（大三度），像拼圖卡上的聲音。帶些微殘響。
- **情感**：「對！就是這個！」滿足感 + 暖意。
- **製作提示**：鋼琴/木琴 C+E 同時敲，或碰鈴（ting-sha）一聲。
- 🔍 **英文搜尋關鍵字**：`puzzle match`, `correct fit`, `snap together`, `warm chord`, `positive ping`, `magic chime short`, `puzzle lock`

---

### 12. `sfx_pill_unmatch.ogg` — 解除配對

- **觸發**：點擊已配對的 pill（`_unmatch_pair`）
- **建議**：輕柔的下滑音，不能讓人有「做錯了」的羞愧感。
- **製作提示**：降半音的輕彈聲，或 pitch 下滑的拔弦聲。
- 🔍 **英文搜尋關鍵字**：`detach`, `pop out`, `slide out`, `gentle cancel`, `soft disconnect`, `descending pluck`, `unclip`

---

### 13. `sfx_reveal_card.ogg` — 結果卡片飛入

- **觸發**：Phase 4 每張結果卡片的 stagger 動畫（每 0.18s 一次）
- **建議**：輕輕的翻頁聲或牌卡滑過桌面聲。非常短，因為會連續觸發。
- **製作提示**：指腹划過書頁聲，或紙牌彈出聲。播放時建議 `pitch_scale` 每張稍微隨機 ±0.05。
- 🔍 **英文搜尋關鍵字**：`card deal`, `paper flutter`, `card slide`, `quick swipe`, `whoosh short`, `card distribute`

---

### 14. `sfx_result_correct.ogg` — 猜對

- **觸發**：Phase 4 `_create_result_row` 中 `is_correct == true`
- **建議**：上揚的大三度旋律，溫暖歡快。像「答對了！」的鈴聲。
- **製作提示**：鋼琴 C-E 兩音，或木琴 do-mi 上行。
- 🔍 **英文搜尋關鍵字**：`correct answer`, `success chime`, `win short`, `warm piano ascend`, `positive feedback`, `right answer ding`

---

### 15. `sfx_result_wrong.ogg` — 猜錯

- **觸發**：Phase 4 `is_correct == false`
- **建議**：**重要**：不能讓人感到羞辱。選擇「溫柔的小三度下滑」，絕對不要用刺耳的蜂鳴。
- **製作提示**：小提琴輕拉下行二度，或鋼琴 E-D 輕柔下行。
- 🔍 **英文搜尋關鍵字**：`soft deny`, `gentle error`, `wrong guess soft`, `descending piano`, `fail short`, `UI error gentle`

---

### 16. `sfx_next_round.ogg` — 再玩一輪

- **觸發**：BtnNextRound 按下（`_on_btn_next_round`）
- **建議**：輕快的循環感旋律，像洗牌的聲音後接一個上揚音。
- **製作提示**：洗牌聲 + 鋼琴 C-E-G-C 四音上行。
- 🔍 **英文搜尋關鍵字**：`card shuffle`, `level up short`, `restart chime`, `phase transition`, `sweep up`, `refresh chime`

---

### 17. `sfx_reconnect_ok.ogg` — 重連成功

- **觸發**：`_on_reconnect_status()` — WebSocket 斷線後重連成功
- **建議**：非常輕柔的提示音，不打擾遊戲進行中的其他玩家。
- **製作提示**：極輕的碰鈴半聲（cut off early），或輕柔的 sine 波短音。
- 🔍 **英文搜尋關鍵字**：`subtle ping`, `connection restore`, `soft notification`, `gentle chime`, `sine wave beep`, `low alert`

---
**💡 搜尋小技巧：**
在 Freesound.org 搜尋時，除了輸入這些關鍵字，建議在左側濾波器（Filters）勾選 **"Creative Commons 0" (CC0)** 授權，這樣你下載的音效就可以無條件、不需標註來源地用在你的專案中，未來上架雙平台完全沒有版權疑慮！

---

## 建議放置路徑

```
friend&me/
└── audio/
    └── sfx/
        ├── sfx_btn_tap.ogg
        ├── sfx_btn_cancel.ogg
        ├── sfx_room_created.ogg
        ├── sfx_player_join.ogg
        ├── sfx_copy_id.ogg
        ├── sfx_game_start.ogg
        ├── sfx_level_select.ogg
        ├── sfx_submit_answer.ogg
        ├── sfx_no_answer.ogg
        ├── sfx_pill_select.ogg
        ├── sfx_pill_match.ogg
        ├── sfx_pill_unmatch.ogg
        ├── sfx_reveal_card.ogg
        ├── sfx_result_correct.ogg
        ├── sfx_result_wrong.ogg
        ├── sfx_next_round.ogg
        └── sfx_reconnect_ok.ogg
```

---

## 製作優先順序建議

1. 🔴 **最先做（核心互動）**：`sfx_btn_tap` / `sfx_pill_match` / `sfx_result_correct` / `sfx_result_wrong`
2. 🟡 **次優先（流程關鍵）**：`sfx_game_start` / `sfx_submit_answer` / `sfx_pill_select` / `sfx_reveal_card`
3. 🟢 **最後補齊（輔助音效）**：其餘 9 個

---

## Godot 整合備註

- 全部使用 `.ogg` 格式（Godot 最佳化格式，檔案小）
- 建議音量正規化至 **-12 dBFS**（預留後期混音空間）
- `sfx_reveal_card`：播放時用 `pitch_scale = randf_range(0.95, 1.05)` 增加自然感
- `sfx_level_select`：用 `pitch_scale` 對應等級（LV1=0.85、LV3=1.0、LV5=1.15）
- 下一步：建立 `audio_manager.gd` Autoload 統一管理所有音效播放
