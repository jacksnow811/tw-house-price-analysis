## Why

本專案已能抓取實價登錄並算出「實坪制坪價」，但使用者拿到一整批成交資料後，仍答不出真正要面對的問題：「我看上的這一間，到底該出多少？」目前缺一個站在**買方**立場、把社區實價登錄 comps 轉成**具體出價策略與談判話術**的工具——這正是上談判桌時最關鍵、也最缺的一塊。

## What Changes

- 新增 Claude Code skill `/price-negotiation`（談價）：使用者給「目標物件資訊」並指定社區後，skill 讀 `data/` 內該社區的實價登錄 CSV，算出**實坪制坪價**行情，再依目標物件的樓層、景觀、車位、主建物坪數、總坪數（公設比）、屋齡、地段等條件相對 comps 調整，最後產出**對買方最有利**的報價與談判話術。
- skill **每次執行皆即時上網**（WebSearch/WebFetch）查當下區域行情與各價格因子（樓層、車位、屋齡等）的加減價幅度，作為 comps 之外的佐證與校準。
- 範圍限定**電梯大樓 / 住宅大樓**；偵測到透天、土地、店面、套房廠辦等非大樓標的時，skill 明確說明不在範圍、不硬給價。
- 固定輸出**完整報告**：comps 行情摘要、目標物件定位、三段式報價（起始出價／目標成交價／心理天花板）、壓價談判話術、物件風險提醒、區域行情比較表、資料來源，每點附 comps 或來源佐證。

## Capabilities

### New Capabilities

- `price-negotiation`: 站在買方立場，依「社區實價登錄 comps（實坪制坪價）＋即時區域行情」對指定**大樓**物件產出對買方最有利的三段式報價與談判話術的 Claude Code skill。

### Modified Capabilities

（無。本變更新增獨立能力，不改動 `data-scraping`、`data-analysis`、`housing-analysis` 既有需求。）

## Impact

- 新增：`.claude/skills/price-negotiation/SKILL.md`（skill 主體）＋ 參考檔（談價方法論、價格因子調整對照、即時查詢 playbook）。
- 相依：沿用既有 `data/*.csv`（實價登錄）與 `analysis.py` 的實坪制坪價公式；skill 需 `WebSearch`/`WebFetch`（即時行情）與讀檔／計算（讀 CSV、算統計）。
- 不改 `scraper.py`、`analysis.py` 程式邏輯，不新增 Python 套件。
- 文件：本變更封存後 `openspec/specs/` 新增 `price-negotiation` 能力；`CLAUDE.md` 檔案結構表補一列（實作時順手）。
