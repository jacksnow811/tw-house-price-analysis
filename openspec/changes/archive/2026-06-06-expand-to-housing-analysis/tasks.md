## 1. 重新命名與骨架

- [x] 1.1 將 skill 目錄 `.claude/skills/builder-analysis/` 改名為 `.claude/skills/housing-analysis/`
- [x] 1.2 更新 `SKILL.md` frontmatter：`name: housing-analysis`、改寫 `description` 為「建案分析」且主動觸發（涵蓋建案/建商評價、買房評估等詞）

## 2. SKILL.md 內容（建案分析）

- [x] 2.1 建案識別與基本資料流程（縣市/區域、建商、規模、屋齡/型態；歧義或查無 → 請使用者澄清，不臆測）
- [x] 2.2 建案層級分析（地段/生活機能、格局/公設、價格行情、社區管理、已知問題：漏水/施工/糾紛/交屋）
- [x] 2.3 將原建商分析改寫為「建商分析」子區塊（保留：找建商→評價/新聞→簡介/優缺點）
- [x] 2.4 新增社群來源策略：搜尋嘗試涵蓋 PTT、Dcard、Threads、Facebook（建案與建商皆適用），附來源、標註匿名可信度
- [x] 2.5 更新固定輸出模板（建案總覽 → 建商分析 → 建案優點 → 建案缺點 → 優劣總評 → 參考案例 → 資料來源）

## 3. 評測

- [x] 3.1 更新 `evals/evals.json`：`skill_name` 改為 housing-analysis，加入建案層級與社群來源的期望輸出
- [x] 3.2 煙霧測試：確認建案識別、社群來源可行（PTT home-sale 有昌益建設真實討論；東都綠學個案社群討論有限 → 走「明說查無」路徑）

## 4. 收尾

- [x] 4.1 更新 `CLAUDE.md`、`openspec/config.yaml`：`builder-analysis` → `housing-analysis`
- [x] 4.2 封存本變更（`openspec archive expand-to-housing-analysis`），建立 `housing-analysis` 正式 spec
- [x] 4.3 移除已被取代的 `openspec/specs/builder-analysis/`（封存不會自動刪除，需手動清掉）
