# CLAUDE.md

本檔提供給 Claude Code 在此專案工作時的指引。

## 專案概述

台灣不動產實價登錄的**抓取 + 分析**工具，分兩部分：

1. **資料抓取（已完成 ✅）**：用 Playwright 爬 [內政部實價登錄網](https://lvr.land.moi.gov.tw/)，依查詢條件抓取成交資料，存成 CSV 到 `data/`。詳見 `01_資料抓取.md`。
2. **資料分析（尚未開始 🚧）**：針對 `data/` 內的 CSV 做整理與分析（單價趨勢、樓層 vs 單價、車位分布等）。規劃見 `02_資料分析.md`。

語言以**繁體中文**為主（程式碼註解、文件、輸出訊息皆中文）。

## 開發環境

用 [uv](https://docs.astral.sh/uv/) 管理。Python >= 3.9，主要依賴 Playwright。

```bash
# 安裝依賴
uv sync
# 首次需安裝 Playwright 瀏覽器
uv run playwright install chromium
# 執行爬蟲
uv run scraper.py
```

## 修改查詢條件

改 `scraper.py` 最上方的 `CONFIG` dict（縣市、鄉鎮市區、社區名稱、訂約年月皆民國年）。
`headless=False` + 調大 `slow_mo` 可開視窗觀察抓取過程（除錯用）。

輸出檔名自動由條件產生：`data/{縣市}_{鄉鎮市區}_{社區名稱}_{起始年月}-{結束年月}.csv`（UTF-8-BOM，Excel 可直接開）。

## 爬蟲關鍵原理（改 scraper.py 前必讀）

此網站的搜尋按鈕**不是送 AJAX**，而是一段 JS handler：

1. 偵測 `navigator.webdriver`，若為自動化瀏覽器**直接 return**（不搜尋）→ 必須用 init script 把它偽裝成 `undefined`（`STEALTH_JS`）。
2. 驗證必填欄位，其中「交易標的」(`input[name='ptype']`) **至少要勾一個** → 程式全部勾選。
3. 把表單值寫入 `localStorage["form-data"]`，再 `location.href = "list.jsp"`，由 list.jsp 讀取後呈現結果。

因此送出查詢要用 JS `button[go_type="list"].click()` 觸發 handler，**勿用座標點擊**。結果出現在 list.jsp frame 的 `#price_table`。

**明細 modal**：每列「明細」按鈕觸發 `/QueryPrice/detail/` AJAX（回 JSON，直接解析、不依賴 modal 內容），並彈出 `#detailModalCenter`。**關 modal 前要先等動畫完全結束再強制關閉**，否則 Bootstrap transition 會覆寫關閉動作、modal 卡住擋下一筆。見 `close_detail_modal()`。

## 輸出資料格式

每筆 **28 欄** = 前置 3 欄（`city`/`district`/`keyword`，查詢條件）+ 基本 19 欄（來自 `#price_table`）+ 明細 6 欄（主建物坪數、陽台坪數、車位類別/價格/面積、所在樓層，來自 detail API）。

## 已知限制

- **分頁未驗證（重要）**：目前一次抓 `#price_table` DOM 內的列。小社區（如東都綠學 15 筆）單頁顯示完整、已確認；但**上百筆的社區 DataTable 可能分頁、只抓到第一頁**——尚未測過。查大量資料前先比對網站「共 N 筆」與實際筆數，必要時加換頁處理。
- 速度：每筆都打一次明細 API，N 筆約需 N×1~2 秒。

## 檔案結構

| 檔案 | 說明 |
|------|------|
| `scraper.py` | 主爬蟲（已完成可用） |
| `01_資料抓取.md` | 第一部分文件（爬蟲，含完整頁面欄位 id / 縣市代碼 / 原理） |
| `02_資料分析.md` | 第二部分文件（分析，待規劃） |
| `data/*.csv` | 抓取結果（gitignore，依條件自動命名） |
| `debug_result.png` | 最新結果頁截圖（gitignore） |
| `pyproject.toml` | uv 專案設定 |

> `data/`、`*.png`、`.venv` 等已在 `.gitignore`，不要 commit 抓回的資料與截圖。
