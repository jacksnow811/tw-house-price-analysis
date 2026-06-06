## 1. 繪圖基礎

- [ ] 1.1 在 `analysis.py` 抽出共用繪圖設定（Agg backend、中文字型、輸出至 `analysis/` 的 helper）
- [ ] 1.2 確認交易日期欄位已轉為可繪圖的時間型別

## 2. 單一資料集視覺化

- [ ] 2.1 實作單價趨勢折線圖（含新青安 2023-08-01 分界線），輸出 PNG
- [ ] 2.2 實作「所在樓層 vs 實坪制坪價」圖（散布或箱型）
- [ ] 2.3 實作車位價格(客制)分布圖（直方或箱型）

## 3. 多社區/多縣市比較

- [ ] 3.1 依 `來源檔`/`city`/`keyword` 分組
- [ ] 3.2 於同一張圖比較各組實坪制坪價並輸出 PNG

## 4. 驗證

- [ ] 4.1 以 `data/` 現有多個社區 CSV 實跑 `uv run analysis.py`，確認各圖正確輸出至 `analysis/`
- [ ] 4.2 封存本變更（`openspec archive add-analysis-visualization`），讓 `data-analysis` spec 納入視覺化需求
