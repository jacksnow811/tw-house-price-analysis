#!/usr/bin/env python3
"""price-negotiation skill 的 comps 統計工具。

給一個社區關鍵字，從 data/ 找出對應的實價登錄 CSV，算出「實坪制坪價」
（公式沿用 analysis.py：(總價 − 車位價格) ÷ 主建物坪數），輸出談價需要的
行情統計：中位數、分位區間、近期行情、各樓層帶中位數、車位均價，以及被
剔除的特殊交易。

關鍵差異（與 analysis.py）：
  - 每車均價只用「該社區內」車位獨立販售的成交計算，不跨社區平均
    （analysis.py 會合併 data/ 全部社區、跨社區平均，談單一社區會被污染）。
  - 會剔除「特殊交易」（備註含協力廠商/親友/含裝潢/急售/法拍…）與離群值，
    讓 comps 更接近正常市場行情。

注意：
  - 住宅樓層取自「樓別/樓高」（中文數字，如『八層/十四層』＝8 樓/共 14 樓）。
    「所在樓層」欄位實際是『車位』所在樓層（常為地下層），不可當住宅樓層。

用法：
    uv run python .claude/skills/price-negotiation/scripts/comps_stats.py "東都綠學"
    uv run python .../comps_stats.py "東都綠學" --years 2
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

# 備註含這些字 → 視為特殊交易，從 comps 剔除（這些不是正常市場成交）
SPECIAL_KW = [
    "協力廠商", "親友", "親屬", "親等", "員工", "關係人", "二親等",
    "含裝潢", "含家電", "含傢俱", "毛胚", "增建", "頂樓加蓋", "頂加",
    "急售", "急讓", "法拍", "拍定", "金拍", "瑕疵", "漏水", "凶宅",
    "輻射", "海砂", "贈與", "信託", "分期付款", "債務", "未含車位但價格含車位",
]
CN = {"零": 0, "一": 1, "二": 2, "兩": 2, "三": 3, "四": 4,
      "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}


def cn_to_int(s) -> int | None:
    """中文數字（1–99）轉 int；含『地下/B』或無法解析回傳 None。"""
    if s is None:
        return None
    s = str(s).strip()
    if not s or "地下" in s or "B" in s.upper():
        return None
    s = s.replace("層", "").replace("樓", "").strip()
    if s.isdigit():
        return int(s)
    if "十" not in s:
        return CN.get(s[:1])
    a, _, b = s.partition("十")
    tens = CN.get(a, 1) if a else 1
    ones = CN.get(b, 0) if b else 0
    val = tens * 10 + ones
    return val if val > 0 else None


def to_number(value) -> float:
    s = str(value).replace(",", "").strip()
    if s == "" or s.lower() == "nan":
        return float("nan")
    try:
        return float(s)
    except ValueError:
        return float("nan")


def parse_car_count(ptype: str) -> int:
    m = re.search(r"車(\d+)", str(ptype))
    return int(m.group(1)) if m else 0


def roc_to_date(date_str) -> pd.Timestamp:
    m = re.match(r"\s*(\d{2,3})/(\d{1,2})/(\d{1,2})\s*$", str(date_str))
    if not m:
        return pd.NaT
    y = int(m.group(1)) + 1911
    try:
        return pd.Timestamp(year=y, month=int(m.group(2)), day=int(m.group(3)))
    except ValueError:
        return pd.NaT


def floor_pair(s):
    """『八層/十四層』→ (8, 14)。解析失敗該位回 None。"""
    parts = str(s).split("/")
    cur = cn_to_int(parts[0]) if parts else None
    total = cn_to_int(parts[1]) if len(parts) > 1 else None
    return cur, total


def find_files(data_dir: Path, keyword: str) -> list[Path]:
    return sorted(
        p for p in data_dir.glob("*.csv")
        if not p.name.startswith("analysis_") and keyword in p.name
    )


def fmt(x) -> str:
    return "—" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.2f}"


def describe(series: pd.Series, label: str) -> None:
    s = series.dropna()
    if s.empty:
        print(f"  {label}: 無有效資料")
        return
    print(f"  {label}（n={len(s)}）："
          f"中位數 {fmt(s.median())}｜平均 {fmt(s.mean())}｜"
          f"P25 {fmt(s.quantile(.25))}｜P75 {fmt(s.quantile(.75))}｜"
          f"最低 {fmt(s.min())}｜最高 {fmt(s.max())}")


def main() -> None:
    ap = argparse.ArgumentParser(description="社區實價登錄 comps 統計（談價用）")
    ap.add_argument("keyword", help="社區關鍵字（用來比對 data/ 檔名）")
    ap.add_argument("--years", type=float, default=2.0,
                    help="『近期』定義：距最新一筆成交幾年內（預設 2）")
    ap.add_argument("--data-dir", default=None, help="資料夾（預設專案 data/）")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[4]
    data_dir = Path(args.data_dir) if args.data_dir else repo_root / "data"

    files = find_files(data_dir, args.keyword)
    if not files:
        print(f"✗ 在 {data_dir} 找不到檔名含「{args.keyword}」的 CSV。")
        print("  → 請先用 scraper.py 抓取該社區，或確認社區關鍵字／檔名。")
        raise SystemExit(2)

    frames = []
    for f in files:
        d = pd.read_csv(f, encoding="utf-8-sig", dtype=str)
        d["來源檔"] = f.name
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    print(f"社區關鍵字：{args.keyword}")
    print(f"來源檔：{', '.join(f.name for f in files)}（共 {len(df)} 筆原始資料）\n")

    # --- 計算實坪制坪價（每車均價在社區內自算） ---
    car_count = df["交易標的"].map(parse_car_count)
    parking_total = df["車位總價 (萬元)"].map(to_number)
    has_car = car_count > 0
    is_indep = has_car & parking_total.notna()

    per_spot = (parking_total[is_indep] / car_count[is_indep])
    avg_per_spot = per_spot.mean()

    car_price = pd.Series(0.0, index=df.index)
    car_price[is_indep] = parking_total[is_indep]
    is_nonindep = has_car & parking_total.isna()
    car_price[is_nonindep] = avg_per_spot * car_count[is_nonindep]

    total_price = df["總價(萬元)"].map(to_number)
    main_area = df["主建物坪數"].map(to_number)
    df["實坪制坪價"] = (total_price - car_price) / main_area
    df["主建物坪數_num"] = main_area
    df["車位數"] = car_count
    df["日期"] = df["交易日期"].map(roc_to_date)
    df["樓層"] = df["樓別/樓高"].map(lambda s: floor_pair(s)[0])
    df["總樓層"] = df["樓別/樓高"].map(lambda s: floor_pair(s)[1])

    note = df.get("備註", pd.Series("", index=df.index)).fillna("")
    df["特殊交易"] = note.map(lambda t: next((k for k in SPECIAL_KW if k in str(t)), ""))

    # 有效：實坪制坪價為正且有限、主建物坪數 > 0
    valid = df[np.isfinite(df["實坪制坪價"]) & (df["實坪制坪價"] > 0)
               & (df["主建物坪數_num"] > 0)].copy()

    special = valid[valid["特殊交易"] != ""]
    comps = valid[valid["特殊交易"] == ""].copy()

    # IQR 去離群
    q1, q3 = comps["實坪制坪價"].quantile([.25, .75])
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    outliers = comps[(comps["實坪制坪價"] < lo) | (comps["實坪制坪價"] > hi)]
    clean = comps[(comps["實坪制坪價"] >= lo) & (comps["實坪制坪價"] <= hi)].copy()

    print("=" * 64)
    print(f"有效成交 {len(valid)} 筆｜特殊交易剔除 {len(special)} 筆｜"
          f"離群剔除 {len(outliers)} 筆｜最終 comps {len(clean)} 筆")
    if avg_per_spot == avg_per_spot:  # not NaN
        print(f"社區內車位獨立販售 {int(is_indep.sum())} 筆，"
              f"平均每車價格 ≈ {avg_per_spot:.1f} 萬元")
    print("=" * 64)

    print("\n【實坪制坪價（萬元/坪）— 最終 comps】")
    describe(clean["實坪制坪價"], "全期")

    if clean["日期"].notna().any():
        latest = clean["日期"].max()
        cutoff = latest - pd.Timedelta(days=int(365 * args.years))
        recent = clean[clean["日期"] >= cutoff]
        print(f"\n【近 {args.years:g} 年（{cutoff.date()} 起，最新 {latest.date()}）】")
        describe(recent["實坪制坪價"], f"近 {args.years:g} 年")

    # 樓層帶
    print("\n【各樓層帶 實坪制坪價中位數】（樓層取自 樓別/樓高）")
    def bucket(fl):
        if fl is None or (isinstance(fl, float) and np.isnan(fl)):
            return "未知"
        fl = int(fl)
        if fl <= 3:
            return "低樓層(1-3F)"
        if fl <= 7:
            return "中低(4-7F)"
        if fl <= 12:
            return "中高(8-12F)"
        return "高樓層(13F+)"
    clean["樓層帶"] = clean["樓層"].map(bucket)
    order = ["低樓層(1-3F)", "中低(4-7F)", "中高(8-12F)", "高樓層(13F+)", "未知"]
    g = clean.groupby("樓層帶")["實坪制坪價"]
    for b in order:
        if b in g.groups:
            s = g.get_group(b)
            print(f"  {b:<14} n={len(s):<3} 中位數 {fmt(s.median())}")

    # 主建物坪數帶（坪效/小宅大宅）
    print("\n【主建物坪數分布】")
    describe(clean["主建物坪數_num"], "主建物坪數")

    # 車位
    if "車位類別" in df.columns and is_indep.any():
        print("\n【車位（獨立販售）每車價格（萬元）】")
        cc = df.loc[is_indep].copy()
        cc["每車"] = parking_total[is_indep] / car_count[is_indep]
        cc["類別"] = cc["車位類別"].map(lambda x: str(x).split("；")[0])
        for cat, s in cc.groupby("類別")["每車"]:
            print(f"  {cat:<10} n={len(s):<3} 中位數 {fmt(s.median())}｜"
                  f"區間 {fmt(s.min())}–{fmt(s.max())}")

    # 特殊交易明細
    if not special.empty:
        print("\n【已剔除的特殊交易】（談價時可當『拉低行情』的佐證，但非正常成交）")
        for _, r in special.head(10).iterrows():
            d = r["日期"].date() if pd.notna(r["日期"]) else "—"
            print(f"  {d}｜{fmt(r['實坪制坪價'])} 萬/坪｜原因：{r['特殊交易']}"
                  f"｜備註：{str(r.get('備註',''))[:30]}")

    print("\n（提醒：以上為機械統計，仍須人工檢視個別 comps 與目標物件可比性。）")


if __name__ == "__main__":
    main()
