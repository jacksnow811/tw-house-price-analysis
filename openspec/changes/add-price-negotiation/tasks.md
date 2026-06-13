## 1. Skill 骨架

- [x] 1.1 建立 `.claude/skills/price-negotiation/` 目錄與 `SKILL.md`（frontmatter：`name`、主動觸發的 `description`、`allowed-tools: Read, Glob, Bash, WebSearch, WebFetch`、`metadata`）
- [x] 1.2 撰寫「何時使用」「僅限大樓範圍／非大樓如何處理」「輸入（目標物件資訊＋指定社區）」三節

## 2. 定價方法論（參考檔）

- [x] 2.1 新增參考檔，寫實坪制坪價公式（沿用 `analysis.py`）與「單一社區自算每車均價」的拆車位作法
- [x] 2.2 寫 comps 篩選規則：剔除特殊交易／離群值、近期優先、與目標物件條件相稱的配對
- [x] 2.3 寫價格因子調整對照（樓層、景觀／棟距、車位類別、主建物坪數、總坪數／公設比、屋齡、格局、地段）與「起點參考區間（須以即時查詢與 comps 校準）」
- [x] 2.4 寫即時查詢 playbook：要查的字串、可靠來源、如何用即時行情校準 comps
- [x] 2.5 寫三段式報價推導（起始出價／目標成交價／心理天花板）與買方市場議價空間的套用方式

## 3. Skill 流程與輸出

- [x] 3.1 SKILL.md 寫流程：辨識標的（僅大樓）→ 讀社區 CSV 算實坪制坪價行情 → 目標物件定位 → 即時查行情 → 三段式報價
- [x] 3.2 定義固定輸出模板（完整報告 7 區塊：comps 摘要／物件定位／三段式報價／談判話術／風險提醒／行情比較表／資料來源）
- [x] 3.3 寫誠實性規則、免責聲明、非大樓標的處理

## 4. 驗證

- [x] 4.1 用 `data/` 現有社區（東都綠學）模擬目標物件跑 `comps_stats.py`，確認能算出實坪制坪價行情（中位數/各樓層帶/車位均價/剔除特殊交易）
- [x] 4.2 測非大樓輸入（SKILL.md 明定拒答＋eval #3）；測 `data/` 無資料社區 → `comps_stats.py` 正確回友善訊息並 exit 2
- [x] 4.3 `openspec validate add-price-negotiation --strict` 通過（封存 `openspec archive` 留待使用者驗收後再執行）
