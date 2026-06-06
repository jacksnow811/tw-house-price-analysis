## MODIFIED Requirements

### Requirement: 抓取明細欄位

系統 SHALL 對每一列觸發明細 API（`GET /SERVICE/QueryPrice/detail/{id}/{token}`），直接解析回傳 JSON 取得 7 個明細欄位：主建物坪數（`buildlist.主建物`）、陽台坪數（`buildlist.陽台`）、**土地移轉面積**、車位類別（`r[].r2`）、車位價格（`r[].r3`）、車位面積（`r[].r4`）、所在樓層（`r[].r6`）；多車位以「；」串接。「土地移轉面積」SHALL 取自 detail API 的 JSON（實作時確認確切路徑）。系統 SHALL NOT 依賴 modal DOM 內容取值。

#### Scenario: 解析明細 JSON

- **WHEN** 系統點擊某列的明細按鈕並收到 detail API 的 JSON 回應
- **THEN** 系統由 JSON 取出 7 個明細欄位（含土地移轉面積）附加到該筆資料

#### Scenario: 缺土地移轉面積時留空

- **WHEN** 某筆 detail JSON 不含土地移轉面積（如純車位交易）
- **THEN** 該筆「土地移轉面積」欄留空，不中斷其餘欄位抓取

#### Scenario: 安全關閉明細 modal

- **WHEN** 明細按鈕同時彈出 `#detailModalCenter` modal
- **THEN** 系統 MUST 先等 modal 開啟動畫完全結束（`show`）再強制關閉
- **AND** 避免在動畫途中關閉被 Bootstrap transition 覆寫而卡住、遮擋下一筆（見 `close_detail_modal()`）

### Requirement: 輸出標準化 CSV

系統 SHALL 將每筆資料輸出為 29 欄＝前置 3 欄（`city`/`district`/`keyword`）＋基本 19 欄＋明細 7 欄，存成 **UTF-8-BOM** 編碼（Excel 可直接開）。檔名 SHALL 由查詢條件自動產生為 `data/{縣市}_{鄉鎮市區}_{社區名稱}_{起始年月}-{結束年月}.csv`。

#### Scenario: 依條件自動命名輸出

- **WHEN** 一次查詢完成共抓得 N 筆
- **THEN** 系統輸出含 29 欄、N 列的 CSV 到 `data/`，檔名反映查詢條件
- **AND** 不將 `data/` 內的 CSV commit 進版控（已列入 `.gitignore`）
