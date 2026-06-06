## ADDED Requirements

### Requirement: Skill 輸入與觸發

Skill SHALL 以單一輸入運作——一個社區或建案名稱——即可啟動完整分析，使用者無需提供建商名稱。Skill 的 `description` SHALL 寫成主動觸發（pushy），使其在使用者提到「評估／查某建商或建案好不好、住戶評價、建商風評、買房想了解建商」等情境時即被觸發。

#### Scenario: 只給建案名稱即啟動

- **WHEN** 使用者輸入一個社區/建案名稱（例如「東都綠學」）
- **THEN** skill 啟動「先找建商 → 再蒐集分析」的完整流程，不要求使用者額外提供建商

#### Scenario: 提及建商評價時自動觸發

- **WHEN** 使用者詢問「○○建案的建商好不好 / 風評如何」
- **THEN** skill 被觸發並進入分析流程

### Requirement: 建商識別優先

Skill SHALL 在分析前先上網查出該社區/建案對應的**建商（起造人/品牌）**。當無法唯一確定建商時，skill SHALL 列出候選並請使用者澄清，SHALL NOT 在不確定時臆測或編造建商。

#### Scenario: 成功識別建商

- **WHEN** 該建案的建商可由公開資料明確查得
- **THEN** skill 標明建商名稱與其判定依據（來源），再進入資料蒐集

#### Scenario: 無法唯一確定建商

- **WHEN** 查到多個可能建商，或查無對應
- **THEN** skill 列出候選（或說明查無）並請使用者澄清，不逕自假設

### Requirement: 網路資料蒐集

Skill SHALL 使用 `WebSearch` 與 `WebFetch` 蒐集該建商歷年建案的住戶評價與新聞，且 SHALL 主動涵蓋負面資訊（漏水、施工品質、交屋延遲、糾紛/客訴、財務或法律新聞），避免只取正面。

#### Scenario: 蒐集評價與新聞

- **WHEN** 建商已識別
- **THEN** skill 以多組關鍵字搜尋住戶評價與新聞，並抓取代表性來源內容供分析

### Requirement: 結構化分析輸出

Skill SHALL 以固定模板輸出分析，至少包含下列區塊：**建商簡介**、**優點**、**缺點**、**優劣總評**、**參考的歷史建案案例**。其中「參考的歷史建案案例」SHALL 列出具體案名，並說明該案發生過什麼事、如何支撐本次判斷。

#### Scenario: 輸出包含所有區塊

- **WHEN** 資料蒐集完成
- **THEN** skill 依固定模板輸出建商簡介、優點、缺點、優劣總評與參考歷史建案案例（含案名與事件）

### Requirement: 來源標註與誠實性

Skill SHALL 為每個重要主張附上來源連結，並清楚區分「查到的事實」與「推論」；當資料不足或互相矛盾時 SHALL 明說，SHALL NOT 捏造評價、新聞或建案案例。

#### Scenario: 附來源並標註不確定

- **WHEN** 某主張來自特定來源
- **THEN** 該主張旁標註可點擊來源連結
- **AND** 資料不足之處明確標示為「資訊有限/未證實」而非編造

### Requirement: 依官方 Agent Skills 標準建立

Skill SHALL 依 Anthropic 官方 Agent Skills 開放標準建立於 `.claude/skills/builder-analysis/SKILL.md`，含 `name` 與 `description` 的 YAML frontmatter、markdown 指令本體，並 SHALL 透過官方 **skill-creator** 流程（capture intent → interview → 撰寫 SKILL.md → test/eval → iterate）製作；SHALL 在 frontmatter 宣告所需工具（至少 `WebSearch`、`WebFetch`），並 SHALL 附評測集 `evals/evals.json` 以真實建案驗證觸發與輸出。

#### Scenario: SKILL.md 結構符合標準

- **WHEN** skill 建立完成
- **THEN** `.claude/skills/builder-analysis/SKILL.md` 具備合法 YAML frontmatter（name、description、所需工具）與指令本體
- **AND** 可由 `/builder-analysis` 直接呼叫，或在相關情境被自動觸發

#### Scenario: 具備評測集

- **WHEN** skill 隨附 `evals/evals.json`
- **THEN** 內含數個真實建案的測試案例（prompt 與期望輸出描述），可用於驗證與描述最佳化
