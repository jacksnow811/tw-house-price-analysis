## MODIFIED Requirements

### Requirement: 自動分頁完整抓取

系統 SHALL 自動處理 list.jsp 結果的 DataTable 分頁，抓取**所有頁**的列，而非僅 DOM 內當前頁。系統 SHALL 讀取網站回報的「共 N 筆」，並在抓取完成後驗證實際抓到的筆數與 N 一致；若不一致 SHALL 明確發出警告/錯誤，避免靜默漏抓。

#### Scenario: 多頁結果完整抓取

- **WHEN** 查詢結果超過單頁顯示量（DataTable 分頁）
- **THEN** 系統換頁（或載入全部）逐頁抓取所有列
- **AND** 輸出 CSV 的列數等於網站回報的「共 N 筆」

#### Scenario: 筆數不一致時告警

- **WHEN** 抓取完成後實際筆數與「共 N 筆」不符
- **THEN** 系統發出明確警告/錯誤，提示資料可能不完整

## RENAMED Requirements

- FROM: `### Requirement: 結果筆數驗證（已知限制）`
- TO: `### Requirement: 自動分頁完整抓取`
