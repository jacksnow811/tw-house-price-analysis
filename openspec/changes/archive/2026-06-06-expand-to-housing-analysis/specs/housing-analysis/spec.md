## ADDED Requirements

### Requirement: Skill 輸入與觸發

Skill SHALL 以單一輸入運作——一個建案/社區名稱——即可啟動完整的**建案分析**，使用者無需提供建商。Skill 的 `description` SHALL 寫成主動觸發（pushy），在使用者提到「某建案/社區好不好、值不值得買、住戶評價、建商風評、施工品質、漏水/糾紛/交屋」等情境時即被觸發。

#### Scenario: 只給建案名稱即啟動建案分析

- **WHEN** 使用者輸入一個建案/社區名稱（例如「東都綠學」）
- **THEN** skill 啟動建案分析流程（建案識別 → 建商分析子環節 → 建案層級分析 → 輸出）

#### Scenario: 詢問建案好壞時自動觸發

- **WHEN** 使用者問「○○建案值不值得買 / 風評如何」
- **THEN** skill 被觸發並進入建案分析

### Requirement: 建案識別與基本資料

Skill SHALL 先上網確認該建案並蒐集基本資料（縣市/區域、所屬建商、規模/棟戶數、屋齡或預售/新成屋、型態）。當建案無法唯一確定（同名、多個案）或查無時，skill SHALL 列出候選或請使用者補充縣市/區域，SHALL NOT 臆測。

#### Scenario: 成功確認建案

- **WHEN** 建案可由公開資料明確查得
- **THEN** skill 標明建案基本資料與來源，再進入後續分析

#### Scenario: 建案歧義或查無

- **WHEN** 查到多個同名建案或查無對應
- **THEN** skill 列出候選或請使用者補充地區，不逕自假設

### Requirement: 建商分析子環節

Skill SHALL 將建商分析作為建案分析的**必備子環節**：找出該建案的建商、蒐集其歷年建案的住戶評價與新聞（含負面），產出建商簡介、優點、缺點。建商無法唯一確定時 SHALL 請使用者澄清，不臆測。

#### Scenario: 輸出建商分析區塊

- **WHEN** 建案的建商已識別
- **THEN** skill 在輸出中提供「建商分析」區塊（簡介/優點/缺點），並附來源

### Requirement: 建案層級分析

Skill SHALL 比照建商分析的模式，分析**建案本身**的優劣，涵蓋（依可得資料）：地段與生活機能、格局與公設比、價格/行情、社區管理、以及該案已知問題（漏水、施工品質、糾紛、交屋延遲等）。輸出 SHALL 包含建案層級的優點與缺點。

#### Scenario: 產出建案優缺點

- **WHEN** 建案資料蒐集完成
- **THEN** skill 整理出建案本身的優點與缺點（每點附佐證與來源）

### Requirement: 參考台灣社群來源

蒐集建案與建商資料時，skill SHALL 嘗試參考台灣民眾常用社群——**PTT、Dcard、Threads、Facebook（社團/粉專）**——作為評價來源，並以站內/站外搜尋方式涵蓋之。skill SHALL 標註社群來源連結，並對單一匿名貼文的可信度保持審慎（多來源互相印證才視為較可靠）。

#### Scenario: 涵蓋社群評價

- **WHEN** skill 蒐集建案或建商評價
- **THEN** 搜尋 SHALL 嘗試涵蓋 PTT、Dcard、Threads、Facebook 等社群
- **AND** 引用社群內容時附來源連結並標註其為網路討論（可信度需審慎）

#### Scenario: 社群查無討論

- **WHEN** 上述社群查無該建案/建商的明顯討論
- **THEN** skill 明說社群討論有限，不捏造評價

### Requirement: 結構化分析輸出

Skill SHALL 以固定模板輸出，至少包含：**建案總覽**（基本資料）、**建商分析**（子環節）、**建案優點**、**建案缺點**、**優劣總評**、**參考的歷史/類似建案案例**、**資料來源**。無資料的區塊也要保留並註明「資訊有限」。

#### Scenario: 輸出包含所有區塊

- **WHEN** 分析完成
- **THEN** skill 依固定模板輸出上述所有區塊，缺資料處明確標示

### Requirement: 來源標註與誠實性

Skill SHALL 為每個重要主張附上來源連結，區分「查到的事實」與「推論」；資料不足或矛盾時 SHALL 明說，SHALL NOT 捏造評價、新聞或建案案例。SHALL 區分「建案個案問題」與「建商整體表現」，並標註舊資訊的日期與是否已改善。

#### Scenario: 附來源並標註不確定

- **WHEN** 某主張來自特定來源
- **THEN** 該主張旁標註可點擊來源連結
- **AND** 資料不足之處標示為「資訊有限/未證實」而非編造

### Requirement: 依官方 Agent Skills 標準建立

Skill SHALL 依 Anthropic 官方 Agent Skills 標準建立於 `.claude/skills/housing-analysis/SKILL.md`，含 `name`、主動觸發的 `description`、所需工具（至少 `WebSearch`、`WebFetch`）的 YAML frontmatter 與指令本體，並 SHALL 透過官方 skill-creator 流程製作、附評測集 `evals/evals.json`（含建案層級的期望輸出）。

#### Scenario: SKILL.md 結構符合標準

- **WHEN** skill 建立完成
- **THEN** `.claude/skills/housing-analysis/SKILL.md` 具備合法 YAML frontmatter 與指令本體
- **AND** 可由 `/housing-analysis` 直接呼叫，或在相關情境被自動觸發
