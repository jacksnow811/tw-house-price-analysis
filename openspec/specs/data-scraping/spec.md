# 資料抓取 Specification

## Purpose

用 Python + Playwright 從內政部實價登錄網（https://lvr.land.moi.gov.tw/）依指定條件查詢不動產成交資料，將每筆結果整理成標準化的 29 欄並輸出 CSV 到 `data/`，作為 `data-analysis` 能力的輸入。本能力對應 `scraper.py`。

## Requirements

### Requirement: 查詢條件設定

系統 SHALL 透過 `scraper.py` 最上方的 `CONFIG` dict 接受查詢條件：縣市、鄉鎮市區、門牌/社區名稱、訂約起訖年月，其中年月皆以**民國年**表示。系統 SHALL 另提供 `headless` 與 `slow_mo` 兩個除錯用參數。

#### Scenario: 指定單一社區與年月區間

- **WHEN** 使用者在 `CONFIG` 設定 縣市=台南市、鄉鎮市區=仁德區、社區名稱=東都綠學、起始=民國114年5月、結束=民國115年5月
- **THEN** 系統據此查詢該社區於該區間的成交資料
- **AND** 縣市以代碼帶入（台南市=`D`），鄉鎮市區以 label 選取（AJAX 動態載入）

#### Scenario: 開啟除錯模式

- **WHEN** 使用者設定 `headless=False` 且調大 `slow_mo`（如 300）
- **THEN** 系統開啟瀏覽器視窗並放慢每個操作，便於觀察抓取過程

### Requirement: 繞過自動化瀏覽器偵測

網站搜尋按鈕並非送 AJAX，而是一段 JS handler；其第一行偵測 `navigator.webdriver`，若為 true 即直接 return 不搜尋。系統 SHALL 在 context 注入 init script（`STEALTH_JS`）將 `navigator.webdriver` 偽裝為 `undefined`，否則查詢完全不會執行。

#### Scenario: 注入偽裝腳本後搜尋生效

- **WHEN** 系統於頁面載入前注入 `Object.defineProperty(navigator,'webdriver',{get:()=>undefined})`
- **THEN** 搜尋 handler 不再於第一行 return，得以往下執行驗證與導向

### Requirement: 觸發查詢

系統 SHALL 勾選所有「交易標的」核取方塊（`input[name='ptype']`，為必填欄位），並以原生 JS `button[go_type="list"].click()` 觸發 handler，MUST NOT 使用座標點擊。handler 會把表單值寫入 `localStorage["form-data"]` 並導向 `list.jsp` 呈現結果。

#### Scenario: 必填交易標的已勾選並送出

- **WHEN** 系統勾選房地/土地/建物/車位全部 `ptype` 後呼叫 `button[go_type="list"].click()`
- **THEN** handler 通過必填驗證，將條件存入 localStorage 並導向 `list.jsp`
- **AND** 結果出現在 list.jsp frame 的 `#price_table`

### Requirement: 抓取基本結果欄位

系統 SHALL 自 list.jsp 的 `#price_table` 抓取每筆成交的基本 19 欄（地段位置或門牌、社區簡稱、總價、交易日期、單價、總面積、主建物佔比、型態、屋齡、樓別/樓高、主要用途、交易標的、建物格局、車位總價、管理組織、電梯、交易/歷次轉移、備註等）。

#### Scenario: 解析結果表格

- **WHEN** `#price_table` 已載入結果列
- **THEN** 系統逐列（`tbody tr`）解析欄位並對應到 thead 欄名

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

### Requirement: 結果筆數驗證（已知限制）

目前系統僅抓取 `#price_table` 在 DOM 內的列，**尚未驗證 DataTable 分頁**；小社區（如東都綠學 15 筆）單頁顯示完整、已確認，但上百筆社區可能分頁而只抓到第一頁。查大量資料前，使用者 SHALL 比對網站回報的「共 N 筆」與實際抓到筆數，以確認是否需補上換頁處理。

#### Scenario: 大量資料前比對筆數

- **WHEN** 查詢結果可能超過單頁顯示量
- **THEN** 使用者比對「共 N 筆」與輸出 CSV 列數
- **AND** 若不一致則代表分頁未被完整抓取，需加入換頁/載入全部的處理

