"""實價登錄資料分析：計算「實坪制坪價」。

流程：
  1. 讀取 data/ 底下所有 CSV，合併成一個大的 pandas DataFrame。
  2. 台灣為虛坪制（公設、車位都灌進坪數與總價），故先扣除車位價格，
     再除以「主建物坪數」，得到真正的實坪單價。
  3. 輸出結果 CSV 並印出基本統計。

計算邏輯詳見 02_資料分析.md。
"""

import re
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")  # 不開視窗，直接存檔
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

# 中文字型（macOS）
matplotlib.rcParams["font.sans-serif"] = ["Arial Unicode MS", "Heiti TC"]
matplotlib.rcParams["axes.unicode_minus"] = False

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = Path(__file__).parent / "analysis"
OUTPUT_CSV = OUTPUT_DIR / "analysis_實坪制坪價.csv"
OUTPUT_PNG = OUTPUT_DIR / "trend_實坪制坪價.png"

# 新青安專案上路時間點（特殊分界線）
NEW_YOUTH_LOAN = pd.Timestamp("2023-08-01")


# ---------------------------------------------------------------------------
# 載入資料
# ---------------------------------------------------------------------------
def load_all_csv(data_dir: Path) -> pd.DataFrame:
    """讀取 data/ 底下所有 CSV（排除分析輸出檔），合併成一個 DataFrame。"""
    files = sorted(
        p for p in data_dir.glob("*.csv") if not p.name.startswith("analysis_")
    )
    if not files:
        raise FileNotFoundError(f"在 {data_dir} 找不到任何 CSV")

    frames = []
    for f in files:
        # 來源為 UTF-8-BOM；encoding="utf-8-sig" 可正確去掉 BOM
        df = pd.read_csv(f, encoding="utf-8-sig", dtype=str)
        df["來源檔"] = f.name
        frames.append(df)
        print(f"讀取 {f.name}：{len(df)} 筆")

    big = pd.concat(frames, ignore_index=True)
    print(f"合併完成：共 {len(big)} 筆、{len(files)} 個檔案")
    return big


# ---------------------------------------------------------------------------
# 欄位清洗工具
# ---------------------------------------------------------------------------
def to_number(value) -> float:
    """把含千分位逗號 / 空白的字串轉成 float；無法解析回傳 NaN。"""
    if value is None:
        return float("nan")
    s = str(value).replace(",", "").strip()
    if s == "" or s.lower() == "nan":
        return float("nan")
    try:
        return float(s)
    except ValueError:
        return float("nan")


def parse_car_count(ptype: str) -> int:
    """從「交易標的」（如 土1 建1車1）取出車位數；找不到視為 0。"""
    m = re.search(r"車(\d+)", str(ptype))
    return int(m.group(1)) if m else 0


def roc_to_ad_date(date_str) -> str:
    """民國日期（115/04/08）轉西元 yyyy/mm/dd（2026/04/08）。無法解析回傳空字串。"""
    m = re.match(r"\s*(\d{2,3})/(\d{1,2})/(\d{1,2})\s*$", str(date_str))
    if not m:
        return ""
    year = int(m.group(1)) + 1911
    return f"{year:04d}/{int(m.group(2)):02d}/{int(m.group(3)):02d}"


# ---------------------------------------------------------------------------
# 核心：計算車位平均值價格 / 車位價格(客制) / 不含車位總價 / 實坪制坪價
# ---------------------------------------------------------------------------
def add_real_price_columns(df: pd.DataFrame) -> pd.DataFrame:
    """新增客製欄位並回傳 DataFrame。

    車位價格(客制)，單位：萬元：
      - 無車位（交易標的寫 車0）          → 0
      - 車位獨立販售（車位總價(萬元)有值）→ 直接用車位總價
      - 車位非獨立販售（車位總價為空）    → 平均每車價格 × 車位數
        （平均每車價格＝所有獨立販售物件「車位平均值價格」的平均）
    """
    df = df.copy()

    # 交易日期：民國 → 西元 yyyy/mm/dd（方便 Excel 畫趨勢線）
    df["交易日期(西元)"] = df["交易日期"].map(roc_to_ad_date)

    car_count = df["交易標的"].map(parse_car_count)          # 車位數
    parking_total = df["車位總價 (萬元)"].map(to_number)      # 車位總價(萬元)
    df["車位數"] = car_count

    has_car = car_count > 0
    is_indep = has_car & parking_total.notna()               # 獨立販售
    is_nonindep = has_car & parking_total.isna()             # 非獨立販售

    # 1. 車位平均值價格 = 車位總價 ÷ 車位數（僅獨立販售物件有值）
    df["車位平均值價格"] = float("nan")
    df.loc[is_indep, "車位平均值價格"] = (
        parking_total[is_indep] / car_count[is_indep]
    )

    # 所有獨立販售物件「車位平均值價格」的平均 → 套用到非獨立販售物件
    avg_per_spot = df.loc[is_indep, "車位平均值價格"].mean()
    print(f"\n獨立販售車位：{is_indep.sum()} 筆，平均每車價格 = {avg_per_spot:.2f} 萬元")
    print(f"非獨立販售車位：{is_nonindep.sum()} 筆，改用「平均每車價格 × 車位數」估算")

    # 2. 車位價格(客制)
    df["車位價格(客制)"] = 0.0
    df.loc[is_indep, "車位價格(客制)"] = parking_total[is_indep]
    df.loc[is_nonindep, "車位價格(客制)"] = avg_per_spot * car_count[is_nonindep]

    # 3. 不含車位總價 = 總價(萬元) − 車位價格(客制)
    total_price = df["總價(萬元)"].map(to_number)
    df["不含車位總價"] = total_price - df["車位價格(客制)"]

    # 4. 實坪制坪價 = 不含車位總價 ÷ 主建物坪數
    main_area = df["主建物坪數"].map(to_number)
    df["實坪制坪價"] = df["不含車位總價"] / main_area

    return df


# ---------------------------------------------------------------------------
# 繪圖：交易日期 vs 實坪制坪價 趨勢線（含新青安分界紅線）
# ---------------------------------------------------------------------------
def plot_trend(df: pd.DataFrame) -> None:
    """畫散布 + 趨勢線，並在新青安上路日（2023/08）標一條垂直紅線。"""
    plot = df.copy()
    plot["日期"] = pd.to_datetime(
        plot["交易日期(西元)"], format="%Y/%m/%d", errors="coerce"
    )
    plot = plot.dropna(subset=["日期", "實坪制坪價"]).sort_values("日期")
    if plot.empty:
        print("無有效資料可繪圖，略過")
        return

    fig, ax = plt.subplots(figsize=(12, 6))

    # 散布點
    ax.scatter(plot["日期"], plot["實坪制坪價"], s=18, alpha=0.5,
               color="#1f77b4", label="各筆成交")

    # 趨勢線（一次線性回歸）
    x_num = mdates.date2num(plot["日期"])
    coef = np.polyfit(x_num, plot["實坪制坪價"], 1)
    ax.plot(plot["日期"], np.polyval(coef, x_num),
            color="#ff7f0e", linewidth=2, label="趨勢線（線性）")

    # 新青安分界紅線
    ax.axvline(NEW_YOUTH_LOAN, color="red", linestyle="--", linewidth=2)
    ymax = plot["實坪制坪價"].max()
    ax.text(NEW_YOUTH_LOAN, ymax, "  新青安上路 2023/08",
            color="red", va="top", ha="left", fontweight="bold")

    ax.set_title("實坪制坪價 趨勢（交易日期）")
    ax.set_xlabel("交易日期")
    ax.set_ylabel("實坪制坪價（萬元/坪）")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUTPUT_PNG, dpi=150)
    plt.close(fig)
    print(f"已輸出趨勢圖：{OUTPUT_PNG}")

    # 順帶印出新青安前後的平均，方便比對
    before = plot.loc[plot["日期"] < NEW_YOUTH_LOAN, "實坪制坪價"]
    after = plot.loc[plot["日期"] >= NEW_YOUTH_LOAN, "實坪制坪價"]
    print(f"  新青安前（< 2023/08）：{len(before)} 筆，平均 {before.mean():.2f}")
    print(f"  新青安後（>=2023/08）：{len(after)} 筆，平均 {after.mean():.2f}")


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def main() -> None:
    df = load_all_csv(DATA_DIR)
    df = add_real_price_columns(df)

    OUTPUT_DIR.mkdir(exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"\n已輸出：{OUTPUT_CSV}")

    valid = df["實坪制坪價"].dropna()
    print("\n=== 實坪制坪價（萬元/坪）統計 ===")
    print(f"有效筆數：{len(valid)} / {len(df)}")
    if not valid.empty:
        print(f"  平均：{valid.mean():.2f}")
        print(f"  中位數：{valid.median():.2f}")
        print(f"  最小 / 最大：{valid.min():.2f} / {valid.max():.2f}")

    print("\n=== 對照：原始單價(虛坪) vs 實坪制坪價 前 5 筆 ===")
    cols = ["交易標的", "總價(萬元)", "車位價格(客制)", "不含車位總價",
            "主建物坪數", "單價 (萬元/坪)", "實坪制坪價"]
    print(df[cols].head().to_string(index=False))

    print("\n=== 趨勢圖 ===")
    plot_trend(df)


if __name__ == "__main__":
    main()
