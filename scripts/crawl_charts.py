"""
BTS "ARIRANG" 차트 크롤러 — 다중 곡 트래킹
- 트래킹 곡: Swim, Body to Body
- 국내: 멜론, 지니, 벅스, 플로, 바이브
- 글로벌: Apple Music (Spotify/YouTube 연동 준비 중)
- 1시간마다 GitHub Actions에서 자동 실행됩니다.
"""

import requests
from bs4 import BeautifulSoup
import json, os, sys, re
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

# ══════════════════════════════════════════════
#  설정: 트래킹할 곡 정보 (여러 곡 가능)
# ══════════════════════════════════════════════
TRACKS = [
    {"title": "Swim",         "emoji": "🌊"},
    {"title": "Body to Body", "emoji": "💃"},
]
ARTIST_KEYWORDS = ["BTS", "방탄소년단"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}
errors = []

def log(msg):
    print(f"[{datetime.now(KST).strftime('%H:%M:%S')}] {msg}")

def find_rank_in_rows(rows, title, artist_keywords):
    title_lower = title.lower()
    for row in rows:
        t = row.get("title", "").strip().lower()
        a = row.get("artist", "").strip()
        if title_lower in t:
            for kw in artist_keywords:
                if kw.lower() in a.lower():
                    return row["rank"]
    return None

def calc_change(current_rank, prev_rank):
    if current_rank is None:
        return "-"
    if prev_rank is None or prev_rank == "-" or isinstance(prev_rank, str):
        return "NEW"
    return prev_rank - current_rank


# ══════════════════════════════════════════════
#  각 플랫폼 크롤링 — rows 리스트 반환
# ══════════════════════════════════════════════

def crawl_melon(chart_type="TOP100"):
    urls = {"TOP100": "https://www.melon.com/chart/index.htm",
            "HOT100": "https://www.melon.com/chart/hot100/index.htm",
            "일간": "https://www.melon.com/chart/day/index.htm",
            "주간": "https://www.melon.com/chart/week/index.htm"}
    url = urls.get(chart_type, urls["TOP100"])
    try:
        resp = requests.get(url, headers={**HEADERS, "Referer": "https://www.melon.com/"}, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        rows = []
        for i, tr in enumerate(soup.select("tr.lst50, tr.lst100"), 1):
            rank_el = tr.select_one(".rank")
            title_el = tr.select_one(".ellipsis.rank01 a") or tr.select_one(".rank01 a")
            artist_el = tr.select_one(".ellipsis.rank02 a") or tr.select_one(".rank02 a")
            if rank_el and title_el:
                try: rank_num = int(rank_el.get_text(strip=True))
                except ValueError: rank_num = i
                rows.append({"rank": rank_num, "title": title_el.get_text(strip=True),
                             "artist": artist_el.get_text(strip=True) if artist_el else ""})
        return rows
    except Exception as e:
        errors.append(f"멜론 {chart_type} 크롤링 실패: {e}")
        log(f"  ❌ 멜론 {chart_type} 실패: {e}")
        return []

def crawl_genie(chart_type="TOP200"):
    urls = {"TOP200": "https://www.genie.co.kr/chart/top200"}
    url = urls.get(chart_type, urls["TOP200"])
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        rows = []
        for song in soup.select("table tbody tr"):
            rank_el = song.select_one("td.number, .number")
            title_el = song.select_one("a.title.ellipsis, a.title, td.info a.title, [class*='title'] a")
            artist_el = song.select_one("a.artist.ellipsis, a.artist, td.info a.artist, [class*='artist'] a")
            if rank_el and title_el:
                match = re.search(r'(\d+)', rank_el.get_text())
                if not match: continue
                rank_num = int(match.group(1))
                if rank_num > 200: continue
                rows.append({"rank": rank_num, "title": title_el.get_text(strip=True),
                             "artist": artist_el.get_text(strip=True) if artist_el else ""})
        return rows
    except Exception as e:
        errors.append(f"지니 {chart_type} 크롤링 실패: {e}")
        log(f"  ❌ 지니 {chart_type} 실패: {e}")
        return []

def crawl_bugs(chart_type="실시간"):
    try:
        from bugs import ChartData as BugsChartData
        chart = BugsChartData()
        return [{"rank": e.rank, "title": e.title, "artist": e.artist} for e in chart]
    except Exception as e:
        errors.append(f"벅스 {chart_type} 크롤링 실패: {e}")
        log(f"  ❌ 벅스 {chart_type} 실패: {e}")
        return []

def crawl_flo(chart_type="실시간"):
    try:
        from flo import ChartData as FloChartData
        chart = FloChartData()
        return [{"rank": e.rank, "title": e.title, "artist": e.artist} for e in chart]
    except Exception as e:
        errors.append(f"플로 {chart_type} 크롤링 실패: {e}")
        log(f"  ❌ 플로 {chart_type} 실패: {e}")
        return []

def crawl_vibe(chart_type="TOP100"):
    try:
        from vibe import ChartData as VibeChartData
        chart = VibeChartData()
        return [{"rank": e.rank, "title": e.title, "artist": e.artist} for e in chart]
    except Exception as e:
        errors.append(f"바이브 {chart_type} 크롤링 실패: {e}")
        log(f"  ❌ 바이브 {chart_type} 실패: {e}")
        return []

def crawl_apple(chart_type="Korea Top 100"):
    urls = {"Korea Top 100": "https://rss.marketingtools.apple.com/api/v2/kr/music/most-played/100/songs.json",
            "Global Top 100": "https://rss.marketingtools.apple.com/api/v2/us/music/most-played/100/songs.json"}
    url = urls.get(chart_type, urls["Korea Top 100"])
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        results = resp.json().get("feed", {}).get("results", [])
        return [{"rank": i, "title": item.get("name", ""), "artist": item.get("artistName", "")}
                for i, item in enumerate(results, 1)]
    except Exception as e:
        errors.append(f"Apple Music {chart_type} 크롤링 실패: {e}")
        log(f"  ❌ Apple Music {chart_type} 실패: {e}")
        return []


# ══════════════════════════════════════════════
#  유틸리티
# ══════════════════════════════════════════════

def load_previous_data():
    path = os.path.join(os.path.dirname(__file__), "..", "data", "charts.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def get_prev_rank(prev_data, song_title, section, platform, chart_name):
    if not prev_data: return None
    try:
        for s in prev_data.get("songs", []):
            if s["title"] == song_title:
                return s[section][platform]["charts"][chart_name]["rank"]
    except (KeyError, TypeError): pass
    return None

def create_github_issue(errors_list):
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo: return
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M")
    body = f"## 크롤링 오류 알림\n\n**발생 시각**: {now} KST\n**오류 건수**: {len(errors_list)}건\n\n### 오류 상세\n\n"
    for i, err in enumerate(errors_list, 1):
        body += f"{i}. `{err}`\n"
    body += "\n> 이 Issue는 자동 생성되었습니다."
    try:
        requests.post(f"https://api.github.com/repos/{repo}/issues",
            headers={"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"},
            json={"title": f"🚨 차트 크롤링 오류 발생 ({now} KST)", "body": body, "labels": ["bug", "crawling-error"]},
            timeout=15)
    except: pass


# ══════════════════════════════════════════════
#  플랫폼 정의
# ══════════════════════════════════════════════

DOMESTIC_PLATFORMS = {
    "melon":  {"name": "멜론",  "letter": "M", "bgClass": "bg-melon",  "crawl": crawl_melon,
               "chart_types": ["TOP100"], "representative": "TOP100",
               "chartMeta": {"TOP100": "실시간 종합 (매시 갱신)"}},
    "genie":  {"name": "지니",  "letter": "G", "bgClass": "bg-genie",  "crawl": crawl_genie,
               "chart_types": ["TOP200"], "representative": "TOP200",
               "chartMeta": {"TOP200": "실시간 종합 (매시 갱신)"}},
    "bugs":   {"name": "벅스",  "letter": "B", "bgClass": "bg-bugs",   "crawl": crawl_bugs,
               "chart_types": ["실시간"], "representative": "실시간",
               "chartMeta": {"실시간": "실시간 인기 차트 (매시 갱신)"}},
    "flo":    {"name": "플로",  "letter": "F", "bgClass": "bg-flo",    "crawl": crawl_flo,
               "chart_types": ["실시간"], "representative": "실시간",
               "chartMeta": {"실시간": "실시간 차트 (매시 갱신)"}},
    "vibe":   {"name": "바이브", "letter": "V", "bgClass": "bg-vibe",  "crawl": crawl_vibe,
               "chart_types": ["TOP100"], "representative": "TOP100",
               "chartMeta": {"TOP100": "국내 인기 종합 차트"}},
}

GLOBAL_PLATFORMS = {
    "apple":  {"name": "Apple Music", "letter": "♫", "bgClass": "bg-apple", "crawl": crawl_apple,
               "chart_types": ["Korea Top 100", "Global Top 100"], "representative": "Korea Top 100",
               "chartMeta": {"Korea Top 100": "한국 인기 100곡", "Global Top 100": "전 세계 인기 100곡"}},
}


# ══════════════════════════════════════════════
#  메인 실행
# ══════════════════════════════════════════════

def main():
    log("=" * 50)
    log(f"BTS 차트 크롤링 시작 — 트래킹 곡: {', '.join(t['title'] for t in TRACKS)}")
    log("=" * 50)

    prev_data = load_previous_data()
    songs_result = []

    for track in TRACKS:
        title = track["title"]
        emoji = track["emoji"]
        log(f"\n🎵 [{title}] 순위 수집 중...")

        # ── 국내 ──
        domestic = {}
        for key, pf in DOMESTIC_PLATFORMS.items():
            charts = {}
            for ct in pf["chart_types"]:
                log(f"  [{pf['name']}] {ct}")
                rows = pf["crawl"](ct)
                rank = find_rank_in_rows(rows, title, ARTIST_KEYWORDS)
                prev = get_prev_rank(prev_data, title, "domestic", key, ct)
                charts[ct] = {"rank": rank if rank else "-", "change": calc_change(rank, prev)}
                log(f"    {title}: {'#' + str(rank) if rank else '차트 밖'}")
            domestic[key] = {
                "name": pf["name"], "letter": pf["letter"], "bgClass": pf["bgClass"],
                "representative": pf["representative"], "charts": charts, "chartMeta": pf["chartMeta"],
            }

        # ── 글로벌 ──
        global_charts = {}
        for key, pf in GLOBAL_PLATFORMS.items():
            charts = {}
            for ct in pf["chart_types"]:
                log(f"  [{pf['name']}] {ct}")
                rows = pf["crawl"](ct)
                rank = find_rank_in_rows(rows, title, ARTIST_KEYWORDS)
                prev = get_prev_rank(prev_data, title, "global", key, ct)
                charts[ct] = {"rank": rank if rank else "-", "change": calc_change(rank, prev)}
                log(f"    {title}: {'#' + str(rank) if rank else '차트 밖'}")
            global_charts[key] = {
                "name": pf["name"], "letter": pf["letter"], "bgClass": pf["bgClass"],
                "representative": pf["representative"], "charts": charts, "chartMeta": pf["chartMeta"],
            }

        # Spotify / YouTube — 연동 준비 중
        global_charts["spotify"] = {
            "name": "Spotify", "letter": "S", "bgClass": "bg-spotify",
            "representative": "Korea Top 50", "coming_soon": True,
            "charts": {"Korea Top 50": {"rank": "-", "change": "-"}},
            "chartMeta": {"Korea Top 50": "연동 준비 중"}}
        global_charts["youtube"] = {
            "name": "YouTube Music", "letter": "Y", "bgClass": "bg-youtube",
            "representative": "Korea Top 100", "coming_soon": True,
            "charts": {"Korea Top 100": {"rank": "-", "change": "-"}},
            "chartMeta": {"Korea Top 100": "연동 준비 중"}}

        songs_result.append({
            "title": title, "emoji": emoji,
            "domestic": domestic, "global": global_charts,
        })

    # ── JSON 저장 ──
    result = {
        "lastUpdated": datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
        "artist": "BTS (방탄소년단)",
        "songs": songs_result,
    }
    out_path = os.path.join(os.path.dirname(__file__), "..", "data", "charts.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    log(f"\n✅ 데이터 저장 완료: data/charts.json")

    if errors:
        log(f"\n⚠️ {len(errors)}건의 오류 발생")
        create_github_issue(errors)
    else:
        log("\n🎉 모든 차트 크롤링 성공!")


if __name__ == "__main__":
    main()
