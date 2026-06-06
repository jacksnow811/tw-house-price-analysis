## Why

買房最關鍵的風險之一是「建商品質」，但相關資訊（住戶評價、施工糾紛、交屋延遲、漏水客訴、財務新聞）散落在 PTT、Mobile01、新聞、論壇等各處，使用者很難自己彙整。本專案已能抓取與分析單一社區的成交價，但缺少「這個建商到底好不好」的判斷。我們想做一個 Claude Code skill：使用者只給一個社區/建案名稱，skill 自動找出背後建商、上網蒐集評價與新聞，產出結構化的優劣分析。

## What Changes

- 新增一個 Claude Code skill `builder-analysis`，依 **Anthropic 官方 Agent Skills 標準**建立於 `.claude/skills/builder-analysis/SKILL.md`。
- 輸入：單一社區/建案名稱。流程：
  1. **先上網查出該建案的建商**（無法唯一確定時請使用者澄清，不臆測）。
  2. 用 WebSearch / WebFetch 蒐集該建商歷年建案的住戶評價與新聞（含負面資訊）。
  3. 整理優劣並輸出固定模板：**建商簡介、優點、缺點、優劣總評、參考的歷史建案案例**。
- 每個重要主張附上**來源連結**，區分事實與推論，資料不足時明說，不得捏造。
- 以官方 **skill-creator** 流程製作（capture intent → interview → write SKILL.md → test/eval → iterate），並建立 `evals/` 評測集。

## Capabilities

### New Capabilities

- `builder-analysis`: 由單一社區/建案名稱出發，識別建商、上網蒐集評價與新聞，產出建商優劣的結構化分析（含參考的歷史建案）。

## Impact

- 新增檔案：`.claude/skills/builder-analysis/SKILL.md`（必要）、`.claude/skills/builder-analysis/evals/evals.json`（評測，選用 references/ 等）。
- 工具：skill 需使用 `WebSearch`、`WebFetch`。
- 與現有 `data-scraping` / `data-analysis` 能力獨立，不影響爬蟲與坪價分析。

## Non-goals

- 不做投資建議或法律意見；僅彙整公開資訊供參考。
- 不保證能識別所有建案的建商（資訊不足時誠實說明並請使用者補充）。
- 不在此變更中串接本專案的 `data/` 成交資料（未來可另開變更整合）。
