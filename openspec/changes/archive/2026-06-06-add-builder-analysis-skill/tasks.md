## 1. 釐清需求（capture intent / interview）

- [x] 1.1 確認觸發情境、輸入（社區/建案名）、輸出模板（建商簡介/優點/缺點/總評/歷史案例）
- [x] 1.2 確認建商識別策略（哪些來源優先）與「無法確定時請使用者澄清」的行為
- [x] 1.3 確認輸出語言（繁體中文）與來源標註、誠實性規則
- [x] 1.4 挑選真實台灣建案作為評測案例（東都綠學、遠雄、同名歧義、查無）

## 2. 建立 skill 骨架（官方 Agent Skills 標準）

- [x] 2.1 建立目錄 `.claude/skills/builder-analysis/`
- [x] 2.2 建立 `SKILL.md`，含 YAML frontmatter：`name`、主動觸發的 `description`、`allowed-tools`（WebSearch、WebFetch）

## 3. 撰寫 SKILL.md 內容

- [x] 3.1 建商識別流程（先查建商；多候選/查無 → 請使用者澄清，不臆測）
- [x] 3.2 搜尋策略（多關鍵字、主動涵蓋負面資訊：漏水/糾紛/延遲/客訴/財務新聞）
- [x] 3.3 固定輸出模板（建商簡介、優點、缺點、優劣總評、參考歷史建案案例含案名與事件）
- [x] 3.4 來源標註與誠實性規則（每主張附連結、區分事實/推論、資料不足明說、禁止捏造）

## 4. 測試與評估（test / eval）

- [x] 4.1 建立 `evals/evals.json`，放入步驟 1.4 的真實建案案例
- [x] 4.2 煙霧測試：以「東都綠學」驗證步驟 1 可正確查得建商（昌益建設、理銘開發）且有可分析素材
- [ ] 4.3 完整多案實跑 + 邊界測試（查無建商、同名建案、資訊極少的小建商）— 後續 polish

## 5. 迭代與收尾

- [ ] 5.1 依測試結果調整 description（觸發率）與指令內容 — 後續 polish
- [x] 5.2 更新 `CLAUDE.md` / `openspec/config.yaml` 提及此 skill
- [x] 5.3 封存本變更（`openspec archive add-builder-analysis-skill`），建立 `builder-analysis` 正式 spec
