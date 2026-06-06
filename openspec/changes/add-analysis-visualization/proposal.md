## Why

`data-analysis` 能力已實作「實坪制坪價」計算，但視覺化與跨社區比較尚未動工。目前分析只輸出 CSV 與基本統計，使用者難以一眼看出價格趨勢、樓層與單價的關係、車位價格分布，也無法在同一張圖比較不同社區/縣市。本變更補上這些分析產出。

## What Changes

- 新增**單價趨勢圖**：以交易日期為 X 軸、實坪制坪價為 Y 軸，輸出趨勢折線圖（沿用既有的新青安分界線標註）。
- 新增**樓層 vs 實坪單價**圖：呈現樓層與實坪單價的關係（散布/箱型）。
- 新增**車位價格分布**圖：呈現車位價格(客制)的分布。
- 新增**多社區 / 多縣市比較**：以 `來源檔` / `city` / `keyword` 分組，於同一圖比較實坪制坪價。
- 圖檔輸出至 `analysis/`，沿用 matplotlib（Agg backend）與既有中文字型設定。

## Capabilities

### Modified Capabilities

- `data-analysis`: 在既有實坪制坪價計算之上，新增視覺化與分組比較等分析產出需求。

## Impact

- 程式：`analysis.py`（新增繪圖函式與分組比較邏輯）。
- 依賴：matplotlib（已在 `pyproject.toml`）。
- 輸出：`analysis/` 下新增多個 `.png`（已在 `.gitignore`，不進版控）。
