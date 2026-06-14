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


# --- 景觀對內／對外（讀 remark/，用「地段位置或門牌」比對） ---
_SIDE_OUT = {"對外", "外", "朝外", "面外", "對外戶", "外觀戶"}
_SIDE_IN = {"對內", "內", "朝內", "面內", "中庭", "對內戶", "中庭戶"}


def norm_side(s) -> str | None:
    """把使用者寫的側別正規化成『對外』/『對內』；無法判斷回 None。"""
    s = str(s).strip()
    if s in _SIDE_OUT:
        return "對外"
    if s in _SIDE_IN:
        return "對內"
    return None


def find_remark_file(remark_dir: Path, keyword: str):
    """在 remark/ 找檔名含社區關鍵字的備註檔（排除 README 與 _/. 開頭）。"""
    if not remark_dir.exists():
        return None
    cands = [p for p in remark_dir.glob("*")
             if p.is_file() and keyword in p.stem
             and not p.name.startswith(("README", "_", "."))]
    cands.sort(key=lambda p: (p.stem != keyword, len(p.stem)))
    return cands[0] if cands else None


def parse_remark(path: Path) -> list[tuple[str, str, str]]:
    """讀備註檔 → [(側別, 地址關鍵字, 說明)]。

    格式：一行一條『側別 | 地址關鍵字 | 說明』；# 開頭或無 | 的行＝註解。
    也容忍 markdown 表格（前後空欄與 --- 分隔列會被略過）。
    """
    rules: list[tuple[str, str, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8-sig")
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "|" not in line:
            continue
        parts = [c.strip() for c in line.split("|") if c.strip() != ""]
        if len(parts) < 2:
            continue
        side = norm_side(parts[0])
        if side is None:                              # 表頭或非規則列
            continue
        pattern = parts[1]
        if not pattern or set(pattern) <= set("-:"):  # markdown 分隔列
            continue
        note = parts[2] if len(parts) > 2 else ""
        rules.append((side, pattern, note))
    return rules


def match_specificity(pattern: str, address: str) -> int | None:
    """比對單條規則的地址關鍵字，回傳『特異度』或 None(沒命中)。

    地址關鍵字可用『&』（或全形『＆』）串接多段，代表 address 需『同時包含』
    全部子字串（AND）。常用於「號」與「之X 戶別」中間夾著樓層、無法用單一連續
    字串鎖定時（例『段１６號 & 之５』＝門牌同時含『段１６號』與『之５』）。

    特異度 ＝ 命中各子字串的長度和（數字越大越精確，供『較精確者優先』排序）；
    任一子字串不在 address → None。單一子字串時行為等同舊版 `pattern in address`。
    """
    parts = [p.strip() for p in re.split(r"[&＆]", pattern) if p.strip()]
    if not parts:
        return None
    total = 0
    for p in parts:
        if p not in address:
            return None
        total += len(p)
    return total


def classify_side(address, rules) -> str | None:
    """用地址比對規則 → 『對外』/『對內』/『未知』(衝突)/None(沒命中)。

    採『較精確（特異度較大）優先』；同特異度但側別相異 → 『未知』(衝突)。
    """
    a = str(address)
    if not a or a.lower() == "nan":
        return None
    best_len, best_side, conflict = -1, None, False
    for side, pattern, _ in rules:
        if not pattern:
            continue
        spec = match_specificity(pattern, a)
        if spec is None:
            continue
        if spec > best_len:
            best_len, best_side, conflict = spec, side, False
        elif spec == best_len and side != best_side:
            conflict = True
    if best_side is None:
        return None
    return "未知" if conflict else best_side


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
    ap.add_argument("--remark-dir", default=None,
                    help="景觀備註資料夾（預設專案 remark/）")
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

    # 景觀：對外 / 對內（依 remark/，用地段位置或門牌比對）
    remark_dir = Path(args.remark_dir) if args.remark_dir else repo_root / "remark"
    print("\n【景觀：對外 vs 對內】（依 remark/ 規則，用地段位置或門牌比對）")
    rf = find_remark_file(remark_dir, args.keyword)
    if rf is None:
        print(f"  （未在 {remark_dir} 找到含「{args.keyword}」的景觀備註，未分組。）")
        print(f"  → 可建立 {remark_dir / (args.keyword + '.md')}；格式見 remark/README.md。")
    else:
        rules = parse_remark(rf)
        addr_col = next((c for c in clean.columns if "門牌" in c), None)
        if not rules:
            print(f"  （{rf.name} 無可用規則；格式見 remark/README.md。）")
        elif addr_col is None:
            print("  （comps 找不到『地段位置或門牌』欄，無法比對地址。）")
        else:
            clean["景觀側"] = clean[addr_col].map(lambda a: classify_side(a, rules))
            out = clean[clean["景觀側"] == "對外"]["實坪制坪價"].dropna()
            inn = clean[clean["景觀側"] == "對內"]["實坪制坪價"].dropna()
            unknown = clean[~clean["景觀側"].isin(["對外", "對內"])]
            print(f"  來源：{rf.name}（{len(rules)} 條規則）")
            describe(out, "對外")
            describe(inn, "對內")
            print(f"  未分類（未知／規則沒命中）：{len(unknown)} 筆")
            if not out.empty and not inn.empty:
                diff = out.median() - inn.median()
                pct = (out.median() / inn.median() - 1) * 100 if inn.median() else float("nan")
                print(f"  → 對外溢價：中位數高 {fmt(diff)} 萬/坪，約 {pct:+.0f}%"
                      f"（對外 {fmt(out.median())} vs 對內 {fmt(inn.median())}）")
                if min(len(out), len(inn)) < 5:
                    print("  ※ 兩組樣本偏少，溢價僅供參考、信心較低。")
                print("  ※ 溢價可能與樓層／棟別混淆 → 請對照各樓層帶兩側中位數：")
                for b in order:
                    sub = clean[clean["樓層帶"] == b]
                    so = sub[sub["景觀側"] == "對外"]["實坪制坪價"].dropna()
                    si = sub[sub["景觀側"] == "對內"]["實坪制坪價"].dropna()
                    if len(so) or len(si):
                        print(f"    {b:<14} 對外 {fmt(so.median())}(n={len(so)})"
                              f"｜對內 {fmt(si.median())}(n={len(si)})")
            else:
                print("  → 對外或對內其一無有效 comps，無法算溢價（資料不足）。")
            if len(unknown):
                samples = [a for a in unknown[addr_col].dropna().unique()
                           if str(a).strip()][:8]
                if samples:
                    print("  未命中規則的門牌（可據此補 remark）：")
                    for a in samples:
                        print(f"    - {a}")

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
