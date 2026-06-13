## ADDED Requirements

### Requirement: Skill 觸發與大樓範圍限定

Skill SHALL 在使用者想知道某物件「該出多少／怎麼議價／開價合不合理／幫我談價」時被觸發，其 `description` SHALL 寫成主動觸發（pushy）。Skill SHALL 僅處理**電梯大樓／住宅大樓**；當標的為透天、土地、店面、套房、廠辦等非大樓時，Skill SHALL 明確說明不在範圍、SHALL NOT 逕自給出價建議。

#### Scenario: 詢問出價即觸發

- **WHEN** 使用者提供一個大樓物件並問「該出多少／這價格合理嗎／幫我議價」
- **THEN** skill 啟動談價流程（辨識標的 → 讀社區 comps → 物件定位 → 即時查行情 → 三段式報價）

#### Scenario: 非大樓標的不給價

- **WHEN** 標的為透天、土地、店面、套房或廠辦
- **THEN** skill 說明本 skill 僅適用大樓、不提供該標的的出價建議，並建議改用適當方法

### Requirement: 以社區實價登錄 comps 為定價基準

Skill SHALL 從 `data/` 找出使用者指定社區的實價登錄 CSV，計算該社區的**實坪制坪價**（＝（總價 − 車位價格）÷ 主建物坪數，公式以 `analysis.py` 為準），且每車均價 SHALL 以**該社區內**車位獨立販售的 comps 自行計算，不跨社區平均。Skill SHALL 剔除與市價差距過大的特殊交易與離群值，並以近期成交為主（量少時得拉長期間）。當 `data/` 無對應社區資料時，Skill SHALL 請使用者先抓取或改指定檔案，SHALL NOT 臆測行情。

#### Scenario: 算出社區實坪制坪價行情

- **WHEN** `data/` 內存在指定社區的 CSV 且有有效的總價、車位、主建物坪數
- **THEN** skill 算出該社區實坪制坪價的中位數與分位區間，作為定價錨點，並說明剔除了哪些特殊交易

#### Scenario: 查無社區資料

- **WHEN** `data/` 找不到指定社區的 CSV
- **THEN** skill 告知無資料、請使用者先用 scraper 抓取或指定正確檔案，不自行假設行情

### Requirement: 目標物件相對 comps 的因子調整

Skill SHALL 依目標物件的樓層、景觀／棟距、車位類別、主建物坪數、總坪數（公設比）、屋齡、格局與地段，相對 comps 做加減價調整，每項調整 SHALL 附理由（comps 對照或即時行情）。

#### Scenario: 依物件條件量化調整

- **WHEN** 目標物件在樓層、景觀、車位類別或公設比上與 comps 中位數條件不同
- **THEN** skill 對各因子做加減價調整並逐項說明依據

### Requirement: 即時行情查詢與佐證

Skill SHALL 於每次執行時用 WebSearch／WebFetch 查當下區域行情與各價格因子的加減價幅度，作為 comps 之外的佐證與校準；引用 SHALL 附來源、SHALL 區分「查到的事實」與「推論」、SHALL NOT 捏造。當查無可靠行情時，Skill SHALL 明說資料有限並以 comps 為主。

#### Scenario: 即時補當地行情

- **WHEN** 進入報價前
- **THEN** skill 即時查詢區域行情與因子幅度，於報告附來源並用以校準 comps

#### Scenario: 行情查無

- **WHEN** 即時查詢查無可靠的當地行情
- **THEN** skill 明確標示「行情資料有限」，改以社區 comps 為主要依據

### Requirement: 買方最有利的三段式報價

Skill SHALL 產出三段式報價：**起始出價**（積極壓低但可用 comps 或物件缺點佐證）、**目標成交價**（買方理想落點）、**心理天花板**（可走人價，不超過相稱 comps 合理上緣）。三個價位 SHALL 以「實坪制坪價 × 目標主建物坪數 ＋ 車位合理價」回推總價並說明推導，且 SHALL 反映當下買方市場的議價空間。

#### Scenario: 產出三個價位與推導

- **WHEN** 已取得 comps 行情、物件定位與即時行情
- **THEN** skill 給出起始／目標／天花板三個總價與單價，並逐一說明如何由 comps 與議價空間導出

#### Scenario: 開價偏貴時明確指出

- **WHEN** 目標物件開價高於相稱 comps 的合理區間
- **THEN** skill 明確標示偏貴幅度，並據此給出壓價空間與話術

### Requirement: 完整報告輸出模板

Skill SHALL 以固定的完整報告模板（繁體中文）輸出，至少含：comps 行情摘要、目標物件定位、三段式報價、壓價談判話術、物件風險提醒、區域行情比較表、資料來源。無資料的區塊 SHALL 保留並註明「資訊有限」。

#### Scenario: 依模板輸出

- **WHEN** 談價分析完成
- **THEN** skill 依固定模板輸出各區塊；缺資料的區塊保留並標明資訊有限

### Requirement: 誠實性與免責

Skill SHALL 區分事實與推論、為重要主張附來源、說明估價的信心高低與不確定處，並 SHALL NOT 捏造成交、行情或評價。報告結尾 SHALL 提醒此為公開資訊彙整、非投資或法律建議，請使用者自行查證、現場看屋、詳閱合約。

#### Scenario: 標示信心與不確定

- **WHEN** comps 過少或行情矛盾
- **THEN** skill 明說信心下降與不確定處，不寫成定論

#### Scenario: 結尾免責

- **WHEN** 輸出報告
- **THEN** 報告結尾附免責提醒（非投資／法律建議、請自行查證與現場勘查）
