## Why

目前爬蟲從每筆「明細」抓取 6 個欄位（主建物/陽台坪數、車位類別/價格/面積、所在樓層），但明細頁面還有「土地移轉面積」這個欄位尚未抓取。土地移轉面積對後續分析（如土地持分、地坪換算）有用，應一併抓回。

## What Changes

- 在明細解析（`enrich_with_details`）新增抓取「土地移轉面積」欄位，使明細欄位由 6 欄增為 7 欄。
- 每筆輸出欄數由 28 欄增為 29 欄（前置 3 欄＋基本 19 欄＋明細 7 欄）。
- 「土地移轉面積」由 detail API 的 JSON 取得（實作時確認確切路徑，預期在 `buildlist` 或回應頂層）。

## Capabilities

### Modified Capabilities

- `data-scraping`: 明細欄位新增「土地移轉面積」，並更新標準化 CSV 的欄位數與組成。

## Impact

- 程式：`scraper.py`（`DETAIL_FIELDS` 與 `enrich_with_details` 的 `detail` dict）。
- 輸出：`data/*.csv` 每筆由 28 欄變 29 欄；既有舊 CSV 不含此欄（向下相容由分析端處理）。
- 規格：封存本變更時，`data-scraping` spec 的明細欄位（6→7）與輸出欄數（28→29）會一併更新。
