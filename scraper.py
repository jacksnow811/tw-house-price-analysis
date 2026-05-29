"""
內政部不動產交易實價查詢爬蟲
網站: https://lvr.land.moi.gov.tw/

運作原理（重要）：
  網站「搜尋」按鈕不是送 AJAX，而是：
    1. 檢查 navigator.webdriver — 若為自動化瀏覽器則直接 return（不執行搜尋）
    2. 驗證必填欄位（含「交易標的」ptype，至少要勾一個）
    3. 把表單值組成 dataObj 寫入 localStorage["form-data"]
    4. location.href = "list.jsp" —— 由 list.jsp 讀 localStorage 後呈現結果
  因此本爬蟲：注入 init script 把 navigator.webdriver 偽裝成 undefined、
  勾選交易標的、再觸發按鈕，結果出現在 list.jsp 的 #price_table。
"""

import asyncio
import csv
import json
import re
from pathlib import Path
from playwright.async_api import async_playwright

# ── 查詢設定（修改這裡）─────────────────────────────────────────────────────
CONFIG = {
    "city": "台南市",        # 縣市
    "district": "仁德區",    # 鄉鎮市區（空白 = 全部）
    "keyword": "新東琚",   # 門牌/社區名稱
    "start_year": "110",     # 訂約起始年（民國）
    "start_month": "1",      # 訂約起始月
    "end_year": "115",       # 訂約結束年（民國）
    "end_month": "12",        # 訂約結束月
    "headless": True,        # True=背景執行不開瀏覽器視窗（較快）；False=開視窗，可看抓取過程
    "slow_mo": 0,            # 每個瀏覽器操作間的延遲(毫秒)，除錯時調大(如 300)可放慢觀察；0=不延遲
}

CITY_CODE = {
    "基隆市": "C", "臺北市": "A", "台北市": "A", "新北市": "F", "桃園市": "H",
    "新竹市": "O", "新竹縣": "J", "苗栗縣": "K", "臺中市": "B", "台中市": "B",
    "南投縣": "M", "彰化縣": "N", "雲林縣": "P", "嘉義市": "I",
    "嘉義縣": "Q", "臺南市": "D", "台南市": "D", "高雄市": "E", "屏東縣": "T",
    "宜蘭縣": "G", "花蓮縣": "U", "臺東縣": "V", "澎湖縣": "X",
    "金門縣": "W", "連江縣": "Z",
}

# 把 navigator.webdriver 偽裝成 undefined，否則搜尋 handler 會直接 return
STEALTH_JS = "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"


async def run():
    cfg = CONFIG
    fname = build_filename(cfg)         # 依查詢條件自動命名
    out = Path("data") / fname          # 所有抓回的 CSV 都放在 data/ 資料夾
    records: list[dict] = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=cfg["headless"], slow_mo=cfg["slow_mo"])
        ctx = await browser.new_context(viewport={"width": 1920, "height": 1080}, locale="zh-TW")
        await ctx.add_init_script(STEALTH_JS)
        page = await ctx.new_page()

        print("[*] 開啟網站...")
        await page.goto("https://lvr.land.moi.gov.tw/", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(1500)

        frame = next((f for f in page.frames if "index.jsp" in f.url), page.main_frame)

        # ── 填寫條件 ──────────────────────────────────────────────────────────
        city_val = CITY_CODE.get(cfg["city"], "")
        if not city_val:
            print(f"[!] 未知縣市：{cfg['city']}")
            await browser.close()
            return
        print(f"[*] 縣市：{cfg['city']}")
        await frame.select_option("#p_city", value=city_val)
        await page.wait_for_timeout(1500)  # 等鄉鎮市區 AJAX 載入

        if cfg["district"]:
            print(f"[*] 鄉鎮市區：{cfg['district']}")
            await frame.select_option("#p_town", label=cfg["district"])
            await page.wait_for_timeout(400)

        if cfg["keyword"]:
            print(f"[*] 門牌/社區名稱：{cfg['keyword']}")
            await frame.fill("#p_build", cfg["keyword"])

        print(f"[*] 訂約日期：{cfg['start_year']}/{cfg['start_month']} ～ "
              f"{cfg['end_year']}/{cfg['end_month']}")
        await frame.select_option("#p_startY", value=cfg["start_year"])
        await frame.select_option("#p_startM", value=cfg["start_month"])
        await frame.select_option("#p_endY",   value=cfg["end_year"])
        await frame.select_option("#p_endM",   value=cfg["end_month"])

        # 交易標的（ptype）為必填，全部勾選
        await frame.evaluate(
            """() => document.querySelectorAll("input[name='ptype']")
                        .forEach(e => { if (!e.checked) e.click(); })"""
        )

        # ── 送出查詢（觸發 button[go_type=list] 的 handler）─────────────────────
        print("[*] 送出查詢...")
        await frame.evaluate(
            """() => document.querySelector('button[go_type="list"]').click()"""
        )

        # 等待 list.jsp frame 出現並讀到結果表
        lf = await wait_for_list_frame(page, timeout=20000)
        if lf is None:
            print("[!] 沒有導向 list.jsp，可能查無資料或被攔截")
            await page.screenshot(path="debug_result.png", full_page=True)
            await browser.close()
            save_csv(records, out)
            return

        print(f"[*] 結果頁：{lf.url}")
        # 等 #price_table 有資料列
        try:
            await lf.wait_for_function(
                """() => {
                    const t = document.querySelector('#price_table tbody');
                    return t && t.querySelectorAll('tr').length > 0;
                }""",
                timeout=15000,
            )
        except Exception:
            print("[!] #price_table 未在時間內出現資料")

        await page.wait_for_timeout(1000)
        total = await read_total_count(lf)
        if total:
            print(f"[*] 網站回報共 {total} 筆")

        # ── 逐頁擷取＋抓明細（#price_table 為 DataTable，每頁只 render 約 15 列，
        #    且只有當頁列才有「明細」按鈕，故必須一頁抓完再換下一頁）──────────
        records = []
        page_num = 1
        while True:
            page_records = await extract_price_table(lf)
            print(f"[*] 第 {page_num} 頁：擷取 {len(page_records)} 筆基本資料")
            await enrich_with_details(page, lf, page_records)
            records.extend(page_records)
            if not await goto_next_page(page, lf):
                break
            page_num += 1

        print(f"[*] 共 {page_num} 頁，累計 {len(records)} 筆")
        if total and len(records) != total:
            print(f"[!] 注意：抓到 {len(records)} 筆與網站回報 {total} 筆不一致，請檢查")

        await lf.evaluate("() => 0")  # 確保 frame 仍存活
        await page.screenshot(path="debug_result.png", full_page=True)
        await browser.close()

    # 在每筆最前面補上查詢條件欄位（city / district / keyword）
    lead = {"city": cfg["city"], "district": cfg["district"], "keyword": cfg["keyword"]}
    records = [{**lead, **r} for r in records]

    save_csv(records, out)
    print(f"\n[完成] 共 {len(records)} 筆，已儲存至 {out.resolve()}")


async def wait_for_list_frame(page, timeout=20000):
    """輪詢等待出現 list.jsp 的 frame。"""
    waited = 0
    step = 500
    while waited < timeout:
        lf = next((f for f in page.frames if "list.jsp" in f.url), None)
        if lf:
            return lf
        await page.wait_for_timeout(step)
        waited += step
    return None


async def read_total_count(frame):
    """讀 DataTable 的資訊列（#price_table_info，如
    「顯示 1 至 15 筆 (查詢結果 : 311 筆)」）取出總筆數，用來和實際抓到的筆數
    比對驗證。讀不到回 None。"""
    try:
        txt = await frame.evaluate(
            "() => { const e=document.querySelector('#price_table_info');"
            " return e ? e.innerText : ''; }"
        )
    except Exception:
        return None
    # 取「查詢結果 : N 筆」的 N；相容舊版「共 N 筆」寫法
    m = re.search(r"查詢結果\s*[:：]\s*([\d,]+)\s*筆", txt or "") \
        or re.search(r"共\s*([\d,]+)\s*筆", txt or "")
    return int(m.group(1).replace(",", "")) if m else None


async def goto_next_page(page, frame) -> bool:
    """換到 #price_table 的下一頁。

    結果表是 jQuery DataTable，下一頁按鈕為 <li id="price_table_next">（即網頁上的
    「>」），到最後一頁時會多一個 `disabled` class。回傳是否成功換頁（最後一頁回 False）。
    """
    # 最後一頁（或找不到按鈕）→ 沒有下一頁
    disabled = await frame.evaluate(
        "() => { const li=document.querySelector('#price_table_next');"
        " return !li || li.classList.contains('disabled'); }"
    )
    if disabled:
        return False

    # 記住目前第一列文字，點「>」後等它變化，確認新頁已 render 完成
    prev = await frame.evaluate(
        "() => { const tr=document.querySelector('#price_table tbody tr');"
        " return tr ? tr.innerText : ''; }"
    )
    await frame.evaluate(
        "() => { const li=document.querySelector('#price_table_next');"
        " const a=li.querySelector('a') || li; a.click(); }"
    )
    try:
        await frame.wait_for_function(
            """(prev) => {
                const tr = document.querySelector('#price_table tbody tr');
                return tr && tr.innerText !== prev;
            }""",
            arg=prev,
            timeout=10000,
        )
    except Exception:
        print("  [!] 換頁後表格未在時間內更新，停止換頁")
        return False
    await page.wait_for_timeout(400)
    return True


DETAIL_FIELDS = ["主建物坪數", "陽台坪數", "車位類別", "車位價格", "車位面積", "所在樓層"]


async def enrich_with_details(page, lf, records: list[dict]):
    """逐筆點『明細』按鈕，攔截 /QueryPrice/detail/ 的 JSON，補上細部欄位。

    回應 JSON 結構：
      buildlist: {"主建物":坪, "陽台":坪, ...}
      r: [{r2:車位類別, r3:車位價格, r4:車位面積, r6:所在樓層}, ...]
    以門牌（地段位置或門牌）對應回 records，確保不會錯位。
    """
    # 先把每筆預設補空欄位（避免有些列抓不到時 CSV 缺欄）
    for r in records:
        for k in DETAIL_FIELDS:
            r.setdefault(k, "")

    by_door = {r.get("地段位置或門牌", "").strip(): r for r in records}
    btns = lf.locator("#price_table tbody button.detail")
    n = await btns.count()
    print(f"[*] 明細按鈕 {n} 個，逐筆抓取細部資料...")

    for i in range(n):
        btn = btns.nth(i)
        # 找出該列門牌（在 record key 中的那一格）
        cells = await btn.locator("xpath=ancestor::tr[1]").locator("td").all_inner_texts()
        door = next((c.replace("\n", " ").strip() for c in cells
                     if c.replace("\n", " ").strip() in by_door), "")
        rec = by_door.get(door)

        try:
            async with page.expect_response(
                lambda r: "/QueryPrice/detail/" in r.url, timeout=15000
            ) as ri:
                await btn.click(timeout=10000)
            resp = await ri.value
            j = json.loads(await resp.text())
        except Exception as e:
            msg = str(e).splitlines()[0]
            print(f"  [{i+1}/{n}] 門牌={door or '(未知)'} 明細失敗：{msg}")
            await close_detail_modal(page, lf)
            continue

        bl = j.get("buildlist", {}) or {}
        cars = j.get("r", []) or []
        detail = {
            "主建物坪數": bl.get("主建物", ""),
            "陽台坪數": bl.get("陽台", ""),
            "車位類別": "；".join(str(c.get("r2", "")) for c in cars if c.get("r2")),
            "車位價格": "；".join(str(c.get("r3", "")) for c in cars if c.get("r3")),
            "車位面積": "；".join(str(c.get("r4", "")) for c in cars if c.get("r4")),
            "所在樓層": "；".join(str(c.get("r6", "")) for c in cars if c.get("r6")),
        }
        target = rec if rec is not None else (records[i] if i < len(records) else None)
        if target is not None:
            target.update(detail)
        print(f"  [{i+1}/{n}] {door}　主建物={detail['主建物坪數']} 陽台={detail['陽台坪數']} "
              f"車位=[{detail['車位類別']} | {detail['車位價格']} | {detail['車位面積']} | {detail['所在樓層']}]")

        # 明細是彈出 modal（#detailModalCenter），必須關掉才能點下一筆
        await close_detail_modal(page, lf)


async def close_detail_modal(page, frame):
    """關閉明細 modal 並等待遮罩消失。

    重點：要先等 modal 完全開啟（含動畫）再強制關閉，否則在動畫途中關閉會被
    Bootstrap 的 transition 事件覆寫，導致 modal 仍停留、擋住下一筆點擊。
    """
    # 1. 等 modal 真的進入 show 狀態（動畫開始）
    try:
        await frame.wait_for_function(
            "() => { const m=document.querySelector('#detailModalCenter');"
            " return m && m.classList.contains('show'); }",
            timeout=4000,
        )
    except Exception:
        pass
    await page.wait_for_timeout(350)  # 等開啟動畫結束，避免關閉被覆寫

    # 2. 強制關閉（按鈕 + Escape + 直接移除狀態），最多重試數次
    for _ in range(8):
        still = await frame.evaluate(
            "() => { const m=document.querySelector('#detailModalCenter');"
            " return !!(m && m.classList.contains('show')); }"
        )
        if not still:
            break
        await frame.evaluate(
            """() => {
                const m = document.querySelector('#detailModalCenter');
                if (m) {
                    const b = m.querySelector('[data-dismiss="modal"], button.close, .close');
                    if (b) b.click();
                    m.classList.remove('show');
                    m.style.display = 'none';
                }
                document.body.classList.remove('modal-open');
                document.querySelectorAll('.modal-backdrop, .blockUI, .blockOverlay')
                    .forEach(el => el.remove());
            }"""
        )
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(200)

    # 3. 最終確認遮罩都清乾淨
    try:
        await frame.wait_for_function(
            """() => {
                const m = document.querySelector('#detailModalCenter');
                const open = m && m.classList.contains('show');
                const block = document.querySelector('.blockUI, .blockOverlay, .modal-backdrop');
                return !open && !block;
            }""",
            timeout=4000,
        )
    except Exception:
        pass


async def extract_price_table(frame) -> list[dict]:
    """從 list.jsp 的 #price_table 擷取資料列。"""
    data = await frame.evaluate(
        r"""() => {
            const tbl = document.querySelector('#price_table');
            if (!tbl) return {headers: [], rows: []};
            const norm = s => (s || '').replace(/\s+/g, ' ').trim();
            const headers = Array.from(tbl.querySelectorAll('thead th'))
                .map(th => norm(th.innerText));
            const rows = [];
            tbl.querySelectorAll('tbody tr').forEach(tr => {
                const cells = Array.from(tr.querySelectorAll('td'))
                    .map(td => norm(td.innerText));
                // 跳過完全空白或「無資料」列
                if (cells.length && cells.some(c => c && c !== '無資料')) {
                    rows.push(cells);
                }
            });
            return {headers, rows};
        }"""
    )
    headers = data["headers"]
    # 去掉非資料欄（功能、分享、全選、備註的按鈕欄維持空字串即可）
    records = []
    for cells in data["rows"]:
        if not any(cells):
            continue
        rec = {}
        for i, val in enumerate(cells):
            key = headers[i] if i < len(headers) and headers[i] else f"col{i}"
            rec[key] = val
        records.append(rec)
    return records


def build_filename(cfg) -> str:
    """依查詢條件自動產生檔名，例如：台南市_仁德區_東都綠學_11503-11505.csv"""
    sm = f"{int(cfg['start_month']):02d}"
    em = f"{int(cfg['end_month']):02d}"
    parts = [
        cfg["city"],
        cfg["district"] or "全區",
        cfg["keyword"] or "全部",
        f"{cfg['start_year']}{sm}-{cfg['end_year']}{em}",
    ]
    name = "_".join(parts)
    name = re.sub(r'[\\/:*?"<>|\s]', "", name)  # 去掉檔名不合法字元
    return name + ".csv"


def save_csv(records: list[dict], path: Path):
    if not records:
        print("[!] 無資料可存")
        return
    path.parent.mkdir(parents=True, exist_ok=True)  # 確保 data/ 存在
    keys, seen = [], set()
    for r in records:
        for k in r:
            if k not in seen:
                keys.append(k)
                seen.add(k)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(records)


if __name__ == "__main__":
    asyncio.run(run())
