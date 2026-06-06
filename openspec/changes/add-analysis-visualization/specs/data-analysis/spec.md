## ADDED Requirements

### Requirement: 單價趨勢視覺化

系統 SHALL 輸出實坪制坪價的趨勢折線圖（X 軸＝交易日期、Y 軸＝實坪制坪價），存成 `analysis/` 下的 PNG，並 SHALL 標註新青安專案上路時間（2023-08-01）作為分界線。

#### Scenario: 產生趨勢圖

- **WHEN** 分析計算完成且資料含交易日期與實坪制坪價
- **THEN** 系統輸出趨勢折線圖 PNG 至 `analysis/`
- **AND** 圖上以分界線標出新青安上路時點

### Requirement: 樓層與實坪單價關係視覺化

系統 SHALL 輸出「所在樓層 vs 實坪制坪價」的圖（散布圖或箱型圖），以呈現樓層與單價的關係。

#### Scenario: 產生樓層對單價圖

- **WHEN** 資料含 `所在樓層` 與 `實坪制坪價`
- **THEN** 系統輸出樓層與實坪單價關係圖 PNG 至 `analysis/`

### Requirement: 車位價格分布視覺化

系統 SHALL 輸出 `車位價格(客制)` 的分布圖（直方圖或箱型圖）至 `analysis/`。

#### Scenario: 產生車位價格分布圖

- **WHEN** 資料已算出 `車位價格(客制)`
- **THEN** 系統輸出車位價格分布圖 PNG 至 `analysis/`

### Requirement: 多社區/多縣市比較

系統 SHALL 能依 `來源檔`、`city` 或 `keyword` 分組，於同一張圖比較各組的實坪制坪價，使不同社區或縣市可並列比較。

#### Scenario: 同圖比較多個社區

- **WHEN** 合併後的資料包含多個社區（多個 `來源檔`/`keyword`）
- **THEN** 系統以分組方式於同一張圖繪出各社區的實坪制坪價供比較
