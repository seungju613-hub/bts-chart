"""
BTS "Swim" 차트 크롤러
- 국내: 멜론, 지니, 벅스, 플로, 바이브
- 글로벌: Spotify, Apple Music, YouTube Music
- 1시간마다 GitHub Actions에서 자동 실행됩니다.
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import sys
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

# ══════════════════════════════════════════════
#  설정: 트래킹할 곡 정보
# ══════════════════════════════════════════════
TRACK_TITLE = "Swim"
TRACK_ARTIST_KEYWORDS = ["BTS", "방탄소년단"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}

errors = []  # 에러 모은 뒤 마지막에 GitHub Issue 생성


def log(msg):
    print(f"[{datetime.now(KST).strftime('%H:%M:%S')}] {msg}")


def find_rank(rows, title_key, artist_key):
    """
    차트 행 리스트에서 곡 제목과 아티스트가 매칭되는 행의 순위를 반환.
    rows: [{"rank": int, "title": str, "artist": str}, ...]
    """
    title_lower = TRACK_TITLE.lower()
    for row in rows:
        t = row.get("title", "").strip().lower()
        a = row.get("artist", "").strip()
        if title_lower in t:
            for kw in TRACK_ARTIST_KEYWORDS:
                if kw.lower() in a.lower():
                    return row["rank"]
    return None


def calc_change(current_rank, prev_rank):
    """이전 순위 대비 변동 계산"""
    if current_rank is None:
        return "-"
    if prev_rank is None or prev_rank == "-":
        return "NEW"
    if isinstance(prev_rank, str):
        return "NEW"
    diff = prev_rank - current_rank
    return diff


# ══════════════════════════════════════════════
#  멜론 크롤링
# ══════════════════════════════════════════════

def crawl_melon_chart(chart_type="TOP100"):
    """멜론 차트 크롤링"""
    urls = {
        "TOP100": "https://www.melon.com/chart/index.htm",
        "HOT100": "https://www.melon.com/chart/hot100/index.htm",
        "일간": "https://www.melon.com/chart/day/index.htm",
        "주간": "https://www.melon.com/chart/week/index.htm",
    }
    url = urls.get(chart_type, urls["TOP100"])
    
    try:
        headers = {**HEADERS, "Referer": "https://www.melon.com/"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        rows = []
        
        # 멜론 차트 테이블 파싱
        for i, tr in enumerate(soup.select("tr.lst50, tr.lst100"), 1):
            rank_el = tr.select_one(".rank")
            title_el = tr.select_one(".ellipsis.rank01 a") or tr.select_one(".rank01 a")
            artist_el = tr.select_one(".ellipsis.rank02 a") or tr.select_one(".rank02 a")
            
            if rank_el and title_el:
                rank_text = rank_el.get_text(strip=True)
                try:
                    rank_num = int(rank_text)
                except ValueError:
                    rank_num = i
                
                rows.append({
                    "rank": rank_num,
                    "title": title_el.get_text(strip=True),
                    "artist": artist_el.get_text(strip=True) if artist_el else "",
                })
        
        rank = find_rank(rows, TRACK_TITLE, TRACK_ARTIST_KEYWORDS)
        log(f"  멜론 {chart_type}: {'#' + str(rank) if rank else '차트 밖'}")
        return rank
        
    except Exception as e:
        err_msg = f"멜론 {chart_type} 크롤링 실패: {str(e)}"
        log(f"  ❌ {err_msg}")
        errors.append(err_msg)
        return None


# ══════════════════════════════════════════════
#  지니 크롤링
# ══════════════════════════════════════════════

def crawl_genie_chart(chart_type="TOP200"):
    """지니 차트 크롤링"""
    urls = {
        "TOP200": "https://www.genie.co.kr/chart/top200",
        "일간": "https://www.genie.co.kr/chart/top200?ditc=D",
        "주간": "https://www.genie.co.kr/chart/top200?ditc=W",
    }
    url = urls.get(chart_type, urls["TOP200"])
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        rows = []
        
        for tr in soup.select("tr.list"):
            rank_el = tr.select_one(".number")
            title_el = tr.select_one(".title .ellipsis") or tr.select_one(".info .title")
            artist_el = tr.select_one(".artist .ellipsis") or tr.select_one(".info .artist")
            
            if rank_el and title_el:
                rank_text = rank_el.get_text(strip=True).split("\n")[0].strip()
                try:
                    rank_num = int(rank_text)
                except ValueError:
                    continue
                
                rows.append({
                    "rank": rank_num,
                    "title": title_el.get_text(strip=True),
                    "artist": artist_el.get_text(strip=True) if artist_el else "",
                })
        
        rank = find_rank(rows, TRACK_TITLE, TRACK_ARTIST_KEYWORDS)
        log(f"  지니 {chart_type}: {'#' + str(rank) if rank else '차트 밖'}")
        return rank
        
    except Exception as e:
        err_msg = f"지니 {chart_type} 크롤링 실패: {str(e)}"
        log(f"  ❌ {err_msg}")
        errors.append(err_msg)
        return None


# ══════════════════════════════════════════════
#  벅스 크롤링
# ══════════════════════════════════════════════

def crawl_bugs_chart(chart_type="실시간"):
    """벅스 차트 크롤링"""
    urls = {
        "실시간": "https://music.bugs.co.kr/chart",
        "일간": "https://music.bugs.co.kr/chart/track/day/total",
        "주간": "https://music.bugs.co.kr/chart/track/week/total",
    }
    url = urls.get(chart_type, urls["실시간"])
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        rows = []
        
        for tr in soup.select("table.list tr.trackList"):
            rank_el = tr.select_one(".ranking strong")
            title_el = tr.select_one(".title a") or tr.select_one("p.title a")
            artist_el = tr.select_one(".artist a")
            
            if rank_el and title_el:
                try:
                    rank_num = int(rank_el.get_text(strip=True))
                except ValueError:
                    continue
                
                rows.append({
                    "rank": rank_num,
                    "title": title_el.get_text(strip=True),
                    "artist": artist_el.get_text(strip=True) if artist_el else "",
                })
        
        rank = find_rank(rows, TRACK_TITLE, TRACK_ARTIST_KEYWORDS)
        log(f"  벅스 {chart_type}: {'#' + str(rank) if rank else '차트 밖'}")
        return rank
        
    except Exception as e:
        err_msg = f"벅스 {chart_type} 크롤링 실패: {str(e)}"
        log(f"  ❌ {err_msg}")
        errors.append(err_msg)
        return None


# ══════════════════════════════════════════════
#  플로 크롤링
# ══════════════════════════════════════════════

def crawl_flo_chart(chart_type="실시간"):
    """플로 차트 크롤링 (flo-chart.py 라이브러리 활용)"""
    try:
        from flo import ChartData as FloChartData
        chart = FloChartData()
        rows = []
        for entry in chart:
            rows.append({
                "rank": entry.rank,
                "title": entry.title,
                "artist": entry.artist,
            })
        
        rank = find_rank(rows, TRACK_TITLE, TRACK_ARTIST_KEYWORDS)
        log(f"  플로 {chart_type}: {'#' + str(rank) if rank else '차트 밖'}")
        return rank
        
    except Exception as e:
        err_msg = f"플로 {chart_type} 크롤링 실패: {str(e)}"
        log(f"  ❌ {err_msg}")
        errors.append(err_msg)
        return None


# ══════════════════════════════════════════════
#  바이브 크롤링
# ══════════════════════════════════════════════

def crawl_vibe_chart(chart_type="TOP100"):
    """바이브(네이버) 차트 크롤링 (vibe-chart.py 라이브러리 활용)"""
    try:
        from vibe import ChartData as VibeChartData
        chart = VibeChartData()
        rows = []
        for entry in chart:
            rows.append({
                "rank": entry.rank,
                "title": entry.title,
                "artist": entry.artist,
            })
        
        rank = find_rank(rows, TRACK_TITLE, TRACK_ARTIST_KEYWORDS)
        log(f"  바이브 {chart_type}: {'#' + str(rank) if rank else '차트 밖'}")
        return rank
        
    except Exception as e:
        err_msg = f"바이브 {chart_type} 크롤링 실패: {str(e)}"
        log(f"  ❌ {err_msg}")
        errors.append(err_msg)
        return None


# ══════════════════════════════════════════════
#  Spotify Charts
# ══════════════════════════════════════════════

def crawl_spotify_chart(chart_type="Korea Top 50"):
    """스포티파이 차트 (charts.spotify.com HTML 스크래핑)"""
    # Spotify Charts 페이지에서 JSON 데이터 추출 시도
    chart_urls = {
        "Korea Top 50": "https://charts.spotify.com/charts/view/regional-kr-daily/latest",
        "Global Top 50": "https://charts.spotify.com/charts/view/regional-global-daily/latest",
        "Global Viral 50": "https://charts.spotify.com/charts/view/viral-global-daily/latest",
    }
    url = chart_urls.get(chart_type, chart_urls["Korea Top 50"])
    
    try:
        resp = requests.get(url, headers={
            **HEADERS,
            "Accept": "text/html,application/xhtml+xml",
        }, timeout=15)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        rows = []
        
        # Spotify Charts 페이지의 차트 데이터 파싱
        import re
        # 페이지 내 JSON 데이터에서 차트 정보 추출 시도
        scripts = soup.find_all("script")
        for script in scripts:
            text = script.string or ""
            if "chartEntryData" in text or "trackName" in text:
                # JSON 데이터 추출
                json_match = re.search(r'\{.*"entries".*\}', text, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    for entry in data.get("entries", []):
                        rows.append({
                            "rank": entry.get("chartEntryData", {}).get("currentRank", 0),
                            "title": entry.get("trackMetadata", {}).get("trackName", ""),
                            "artist": ", ".join(
                                a.get("name", "")
                                for a in entry.get("trackMetadata", {}).get("artists", [])
                            ),
                        })
                    break
        
        # HTML 테이블/리스트 파싱 폴백
        if not rows:
            for i, item in enumerate(soup.select("[class*='ChartEntry'], [class*='chart-entry'], tr[class*='Row']"), 1):
                title_el = item.select_one("[class*='track-name'], [class*='Title'], td:nth-child(3)")
                artist_el = item.select_one("[class*='artist'], [class*='Artist'], td:nth-child(4)")
                if title_el:
                    rows.append({
                        "rank": i,
                        "title": title_el.get_text(strip=True),
                        "artist": artist_el.get_text(strip=True) if artist_el else "",
                    })
        
        if not rows:
            raise Exception("차트 데이터를 찾을 수 없음 (로그인 필요 가능성)")
        
        rank = find_rank(rows, TRACK_TITLE, TRACK_ARTIST_KEYWORDS)
        log(f"  Spotify {chart_type}: {'#' + str(rank) if rank else '차트 밖'}")
        return rank
        
    except Exception as e:
        err_msg = f"Spotify {chart_type} 크롤링 실패: {str(e)}"
        log(f"  ❌ {err_msg}")
        errors.append(err_msg)
        return None


# ══════════════════════════════════════════════
#  Apple Music Charts (RSS Feed)
# ══════════════════════════════════════════════

def crawl_apple_chart(chart_type="Korea Top 100"):
    """애플뮤직 차트 (RSS 피드)"""
    urls = {
        "Korea Top 100": "https://rss.marketingtools.apple.com/api/v2/kr/music/most-played/100/songs.json",
        "Global Top 100": "https://rss.marketingtools.apple.com/api/v2/us/music/most-played/100/songs.json",
        "Korea Daily Top 100": "https://rss.marketingtools.apple.com/api/v2/kr/music/most-played/100/songs.json",
    }
    url = urls.get(chart_type, urls["Korea Top 100"])
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        
        rows = []
        results = data.get("feed", {}).get("results", [])
        for i, item in enumerate(results, 1):
            rows.append({
                "rank": i,
                "title": item.get("name", ""),
                "artist": item.get("artistName", ""),
            })
        
        rank = find_rank(rows, TRACK_TITLE, TRACK_ARTIST_KEYWORDS)
        log(f"  Apple Music {chart_type}: {'#' + str(rank) if rank else '차트 밖'}")
        return rank
        
    except Exception as e:
        err_msg = f"Apple Music {chart_type} 크롤링 실패: {str(e)}"
        log(f"  ❌ {err_msg}")
        errors.append(err_msg)
        return None


# ══════════════════════════════════════════════
#  YouTube Music Charts
# ══════════════════════════════════════════════

def crawl_youtube_chart(chart_type="Korea Top 100"):
    """유튜브 뮤직 차트"""
    urls = {
        "Korea Top 100": "https://charts.youtube.com/charts/TopSongs/kr",
        "Global Top 100": "https://charts.youtube.com/charts/TopSongs/global",
        "Trending": "https://charts.youtube.com/charts/TrendingVideos/kr",
    }
    url = urls.get(chart_type, urls["Korea Top 100"])
    
    try:
        resp = requests.get(url, headers={
            **HEADERS,
            "Accept": "text/html",
        }, timeout=15)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        rows = []
        
        # YouTube Charts 페이지 파싱
        for i, item in enumerate(soup.select(".chart-table-row, [class*='TableRow']"), 1):
            title_el = item.select_one("[class*='title'], .title")
            artist_el = item.select_one("[class*='artist'], .artist, .subtitle")
            
            if title_el:
                rows.append({
                    "rank": i,
                    "title": title_el.get_text(strip=True),
                    "artist": artist_el.get_text(strip=True) if artist_el else "",
                })
        
        rank = find_rank(rows, TRACK_TITLE, TRACK_ARTIST_KEYWORDS)
        log(f"  YouTube Music {chart_type}: {'#' + str(rank) if rank else '차트 밖'}")
        return rank
        
    except Exception as e:
        err_msg = f"YouTube Music {chart_type} 크롤링 실패: {str(e)}"
        log(f"  ❌ {err_msg}")
        errors.append(err_msg)
        return None


# ══════════════════════════════════════════════
#  메인 실행
# ══════════════════════════════════════════════

def load_previous_data():
    """이전 차트 데이터 로드 (변동 계산용)"""
    path = os.path.join(os.path.dirname(__file__), "..", "data", "charts.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def get_prev_rank(prev_data, section, platform, chart_name):
    """이전 데이터에서 특정 차트의 순위 가져오기"""
    if not prev_data:
        return None
    try:
        charts = prev_data[section][platform]["charts"]
        return charts[chart_name]["rank"]
    except (KeyError, TypeError):
        return None


def create_github_issue(errors_list):
    """크롤링 에러 발생 시 GitHub Issue 자동 생성"""
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    
    if not token or not repo:
        log("⚠️ GitHub Token/Repo 없음 - Issue 생성 스킵")
        return
    
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M")
    title = f"🚨 차트 크롤링 오류 발생 ({now} KST)"
    
    body = f"""## 크롤링 오류 알림

**발생 시각**: {now} KST
**오류 건수**: {len(errors_list)}건

### 오류 상세

"""
    for i, err in enumerate(errors_list, 1):
        body += f"{i}. `{err}`\n"
    
    body += """
### 조치 방법

1. 해당 사이트에 직접 접속하여 페이지 구조가 변경되었는지 확인
2. `scripts/crawl_charts.py`의 해당 크롤링 함수 수정
3. 수정 후 Actions 탭에서 수동 실행하여 테스트

> 이 Issue는 자동 생성되었습니다.
"""
    
    try:
        resp = requests.post(
            f"https://api.github.com/repos/{repo}/issues",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
            },
            json={
                "title": title,
                "body": body,
                "labels": ["bug", "crawling-error"],
            },
            timeout=15,
        )
        if resp.status_code == 201:
            log(f"✅ GitHub Issue 생성 완료: {resp.json().get('html_url')}")
        else:
            log(f"⚠️ GitHub Issue 생성 실패: {resp.status_code}")
    except Exception as e:
        log(f"⚠️ GitHub Issue 생성 실패: {e}")


def main():
    log("=" * 50)
    log("BTS 'Swim' 차트 크롤링 시작")
    log("=" * 50)
    
    prev_data = load_previous_data()
    
    # ── 국내 차트 크롤링 ──
    log("\n📌 국내 차트 수집 중...")
    
    domestic = {}
    
    # 멜론
    log("  [멜론]")
    melon_charts = {}
    for ct in ["TOP100", "HOT100", "일간", "주간"]:
        rank = crawl_melon_chart(ct)
        prev = get_prev_rank(prev_data, "domestic", "melon", ct)
        melon_charts[ct] = {
            "rank": rank if rank else "-",
            "change": calc_change(rank, prev),
        }
    # HOT100 발매30일/100일은 같은 HOT100 페이지에서 구분이 어려우므로 HOT100 결과 공유
    melon_charts["HOT100 발매 30일"] = melon_charts.get("HOT100", {"rank": "-", "change": "-"})
    melon_charts["HOT100 발매 100일"] = melon_charts.get("HOT100", {"rank": "-", "change": "-"})
    
    domestic["melon"] = {
        "name": "멜론", "letter": "M", "bgClass": "bg-melon",
        "representative": "TOP100",
        "charts": melon_charts,
        "chartMeta": {
            "TOP100": "실시간 종합 (매시 갱신)",
            "HOT100": "인기도 종합 차트",
            "HOT100 발매 30일": "발매 30일 이내 인기곡",
            "HOT100 발매 100일": "발매 100일 이내 인기곡",
            "일간": "일간 종합 차트",
            "주간": "주간 종합 차트",
        }
    }
    
    # 지니
    log("  [지니]")
    genie_charts = {}
    for ct in ["TOP200", "일간", "주간"]:
        rank = crawl_genie_chart(ct)
        prev = get_prev_rank(prev_data, "domestic", "genie", ct)
        genie_charts[ct] = {"rank": rank if rank else "-", "change": calc_change(rank, prev)}
    
    domestic["genie"] = {
        "name": "지니", "letter": "G", "bgClass": "bg-genie",
        "representative": "TOP200",
        "charts": genie_charts,
        "chartMeta": {
            "TOP200": "실시간 종합 (매시 갱신)",
            "일간": "일간 종합 차트",
            "주간": "주간 종합 차트",
        }
    }
    
    # 벅스
    log("  [벅스]")
    bugs_charts = {}
    for ct in ["실시간", "일간", "주간"]:
        rank = crawl_bugs_chart(ct)
        prev = get_prev_rank(prev_data, "domestic", "bugs", ct)
        bugs_charts[ct] = {"rank": rank if rank else "-", "change": calc_change(rank, prev)}
    
    domestic["bugs"] = {
        "name": "벅스", "letter": "B", "bgClass": "bg-bugs",
        "representative": "실시간",
        "charts": bugs_charts,
        "chartMeta": {
            "실시간": "실시간 인기 차트 (매시 갱신)",
            "일간": "일간 종합 차트",
            "주간": "주간 종합 차트",
        }
    }
    
    # 플로
    log("  [플로]")
    flo_charts = {}
    for ct in ["실시간", "일간"]:
        rank = crawl_flo_chart(ct)
        prev = get_prev_rank(prev_data, "domestic", "flo", ct)
        flo_charts[ct] = {"rank": rank if rank else "-", "change": calc_change(rank, prev)}
    
    domestic["flo"] = {
        "name": "플로", "letter": "F", "bgClass": "bg-flo",
        "representative": "실시간",
        "charts": flo_charts,
        "chartMeta": {
            "실시간": "실시간 차트 (매시 갱신)",
            "일간": "일간 종합 차트",
        }
    }
    
    # 바이브
    log("  [바이브]")
    vibe_charts = {}
    for ct in ["TOP100", "급상승"]:
        rank = crawl_vibe_chart(ct)
        prev = get_prev_rank(prev_data, "domestic", "vibe", ct)
        vibe_charts[ct] = {"rank": rank if rank else "-", "change": calc_change(rank, prev)}
    
    domestic["vibe"] = {
        "name": "바이브", "letter": "V", "bgClass": "bg-vibe",
        "representative": "TOP100",
        "charts": vibe_charts,
        "chartMeta": {
            "TOP100": "국내 인기 종합 차트",
            "급상승": "국내 급상승 차트",
        }
    }
    
    # ── 글로벌 차트 ──
    log("\n📌 글로벌 차트 수집 중...")
    
    global_charts = {}
    
    # Spotify
    log("  [Spotify]")
    spotify_charts = {}
    for ct in ["Korea Top 50", "Global Top 50", "Global Viral 50"]:
        rank = crawl_spotify_chart(ct)
        prev = get_prev_rank(prev_data, "global", "spotify", ct)
        spotify_charts[ct] = {"rank": rank if rank else "-", "change": calc_change(rank, prev)}
    
    global_charts["spotify"] = {
        "name": "Spotify", "letter": "S", "bgClass": "bg-spotify",
        "representative": "Korea Top 50",
        "charts": spotify_charts,
        "chartMeta": {
            "Korea Top 50": "한국 지역 인기 50곡",
            "Global Top 50": "전 세계 인기 50곡",
            "Global Viral 50": "전 세계 바이럴 50곡",
        }
    }
    
    # Apple Music
    log("  [Apple Music]")
    apple_charts = {}
    for ct in ["Korea Top 100", "Global Top 100"]:
        rank = crawl_apple_chart(ct)
        prev = get_prev_rank(prev_data, "global", "apple", ct)
        apple_charts[ct] = {"rank": rank if rank else "-", "change": calc_change(rank, prev)}
    
    global_charts["apple"] = {
        "name": "Apple Music", "letter": "♫", "bgClass": "bg-apple",
        "representative": "Korea Top 100",
        "charts": apple_charts,
        "chartMeta": {
            "Korea Top 100": "한국 인기 100곡",
            "Global Top 100": "전 세계 인기 100곡",
        }
    }
    
    # YouTube Music
    log("  [YouTube Music]")
    yt_charts = {}
    for ct in ["Korea Top 100", "Global Top 100", "Trending"]:
        rank = crawl_youtube_chart(ct)
        prev = get_prev_rank(prev_data, "global", "youtube", ct)
        yt_charts[ct] = {"rank": rank if rank else "-", "change": calc_change(rank, prev)}
    
    global_charts["youtube"] = {
        "name": "YouTube Music", "letter": "Y", "bgClass": "bg-youtube",
        "representative": "Korea Top 100",
        "charts": yt_charts,
        "chartMeta": {
            "Korea Top 100": "한국 인기 100곡",
            "Global Top 100": "전 세계 인기 100곡",
            "Trending": "급상승 인기곡",
        }
    }
    
    # ── JSON 저장 ──
    result = {
        "lastUpdated": datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
        "song": TRACK_TITLE,
        "artist": "BTS (방탄소년단)",
        "domestic": domestic,
        "global": global_charts,
    }
    
    out_path = os.path.join(os.path.dirname(__file__), "..", "data", "charts.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    log(f"\n✅ 데이터 저장 완료: data/charts.json")
    
    # ── 에러 처리 ──
    if errors:
        log(f"\n⚠️ {len(errors)}건의 오류 발생 - GitHub Issue 생성 중...")
        create_github_issue(errors)
        # 일부 실패해도 성공한 데이터는 저장되므로 exit(0)
        # 전체 실패 시에만 exit(1)
        total_charts = 0
        failed_charts = len(errors)
        for p in domestic.values():
            total_charts += len(p["charts"])
        for p in global_charts.values():
            total_charts += len(p["charts"])
        
        if failed_charts >= total_charts:
            log("❌ 전체 크롤링 실패!")
            sys.exit(1)
        else:
            log(f"⚠️ 일부 실패 ({failed_charts}/{total_charts}) - 성공 데이터는 반영됨")
    else:
        log("\n🎉 모든 차트 크롤링 성공!")


if __name__ == "__main__":
    main()
