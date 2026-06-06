## Why

目前的 `builder-analysis` skill 只分析「建商好不好」。但使用者真正在意的是「**這個建案值不值得買**」——建商只是其中一個（很重要的）面向，還要看建案本身的地段、生活機能、格局/公設、價格行情、管理、以及該案已知問題（漏水、施工、糾紛、交屋延遲）。因此把 skill 從「建商分析」升級為「**建案分析**」，建商分析降為其中一個必備環節。同時，台灣民眾的真實評價多半在 PTT、Dcard、Threads、Facebook（社團/粉專），分析時應主動參考這些社群。

## What Changes

- **重新命名能力與 skill**：`builder-analysis` → `housing-analysis`（指令 `/housing-analysis`）。舊的 `builder-analysis` 能力與 skill 由本變更取代。
- **擴大範圍為建案分析**：以一個建案/社區名稱為輸入，分析建案本身（地段、機能、格局、公設、價格行情、管理、已知問題），比照原建商分析的模式產出優點、缺點、總評與參考案例。
- **建商分析變成子環節**：保留原本完整的建商分析（找建商→蒐集評價/新聞→簡介/優缺點），作為建案分析輸出中的一個必備區塊。
- **社群來源（建案與建商皆適用）**：蒐集資料時必須嘗試參考台灣常用社群 **PTT、Dcard、Threads、Facebook**，並標註來源、注意單一匿名貼文的可信度。
- 沿用 Anthropic 官方 Agent Skills 標準與 skill-creator 流程；更新 `evals/`。

## Capabilities

### New Capabilities

- `housing-analysis`: 由單一建案/社區名稱出發，分析該建案的優劣（含建商分析子環節），主動參考台灣社群評價與新聞，產出結構化分析與參考案例。

## Impact

- 取代能力 `builder-analysis`：本變更封存後，需移除 `openspec/specs/builder-analysis/`（已被 `housing-analysis` 取代）。
- 檔案：skill 目錄 `.claude/skills/builder-analysis/` → `.claude/skills/housing-analysis/`（含 `SKILL.md`、`evals/evals.json`）。
- 文件：`CLAUDE.md`、`openspec/config.yaml` 內的 `builder-analysis` 名稱需更新為 `housing-analysis`。
- 工具：skill 仍使用 `WebSearch`、`WebFetch`。

## Non-goals

- 不做投資/法律建議；僅彙整公開資訊供參考。
- 不在此變更串接本專案 `data/` 成交資料（未來可另開變更整合實價登錄行情）。
- 不保證社群一定有該建案的討論；查無時誠實說明。
