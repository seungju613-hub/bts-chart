# BTS "Swim" 차트 트래커 — 설치부터 배포까지 완전 가이드

> 파이썬·개발 경험 없어도 따라할 수 있습니다.
> 총 소요시간: 약 20~30분

---

## 전체 구조 한눈에 보기

```
[GitHub 저장소]
  ├── index.html          ← 사이트 화면
  ├── data/charts.json    ← 차트 순위 데이터 (자동 업데이트)
  ├── scripts/crawl_charts.py  ← 크롤링 코드
  ├── requirements.txt
  └── .github/workflows/update-charts.yml  ← 자동 실행 설정

[작동 흐름]
  매 정시 → GitHub Actions가 크롤링 실행
        → charts.json 업데이트 & 자동 커밋
        → Cloudflare Pages가 감지하여 자동 재배포
        → 크롤링 실패 시 GitHub Issue 생성 → 이메일 알림
```

---

## STEP 1: GitHub 계정 만들기

> 이미 계정이 있다면 STEP 2로 건너뛰세요.

1. https://github.com 접속
2. 오른쪽 상단 **Sign up** 클릭
3. 이메일 입력 → 비밀번호 설정 → 사용자명 입력
4. 이메일로 온 인증 코드 입력
5. 완료!

---

## STEP 2: 새 저장소(Repository) 만들기

1. GitHub 로그인 상태에서 오른쪽 상단 **+** 버튼 → **New repository** 클릭
2. 아래처럼 설정:
   - **Repository name**: `bts-chart` (원하는 이름 가능)
   - **Description**: `BTS Swim 실시간 차트 트래커` (선택사항)
   - **Public** 선택 (반드시!)
   - **Add a README file** 체크하지 않기
3. **Create repository** 클릭

---

## STEP 3: 파일 업로드하기

### 방법 A: 한번에 드래그 앤 드롭 (추천)

1. 다운로드 받은 `bts-chart.zip` 압축 해제
2. 압축 해제한 `bts-chart` 폴더 안을 열기
3. GitHub 저장소 페이지에서 **"uploading an existing file"** 링크 클릭
4. `bts-chart` 폴더 **안의 모든 파일/폴더**를 선택하여 드래그 앤 드롭
5. 하단에 **Commit changes** 클릭

⚠️ **중요!** `.github` 폴더가 보이지 않을 수 있어요.

- **Windows**: 파일 탐색기 → 상단 메뉴 "보기" → "숨긴 항목" 체크
- **Mac**: Finder에서 `Cmd + Shift + .` 키를 동시에 누르기

### 방법 B: `.github` 폴더가 안 올라갈 경우 (수동 생성)

드래그 앤 드롭으로 `.github` 폴더가 안 올라가는 경우가 있어요.
이때는 나머지 파일을 먼저 업로드한 후, 워크플로우 파일만 수동으로 만듭니다.

1. 저장소에서 **Add file** → **Create new file** 클릭
2. 파일 이름 입력란에 정확히 다음을 입력: `.github/workflows/update-charts.yml`
   (슬래시(/)를 입력하면 자동으로 폴더가 생겨요)
3. 다운로드 받은 `.github/workflows/update-charts.yml` 파일을 텍스트 에디터(메모장)로 열기
4. 내용을 전부 복사해서 GitHub 편집기에 붙여넣기
5. **Commit new file** 클릭

### 업로드 확인하기

저장소 메인 페이지에서 다음 파일들이 보이면 성공이에요:

```
📂 .github/workflows/
📂 data/
📂 scripts/
📄 index.html
📄 requirements.txt
```

---

## STEP 4: GitHub Actions 권한 설정

이 단계를 빠뜨리면 자동 크롤링이 작동하지 않아요!

1. 저장소 상단 메뉴에서 **Settings** (⚙️ 톱니바퀴) 클릭
2. 왼쪽 사이드바에서 **Actions** → **General** 클릭
3. 스크롤을 아래로 내려서 **"Workflow permissions"** 섹션 찾기
4. **"Read and write permissions"** 선택
5. 바로 아래 **"Allow GitHub Actions to create and approve pull requests"** 체크
6. **Save** 클릭

---

## STEP 5: 첫 번째 크롤링 실행 (테스트)

1. 저장소 상단 메뉴에서 **Actions** 탭 클릭
2. "I understand my workflows, go ahead and enable them" 이 보이면 클릭
3. 왼쪽에서 **"차트 자동 업데이트"** 워크플로우 클릭
4. 오른쪽에 있는 **"Run workflow"** 버튼 클릭 → 한번 더 **"Run workflow"** 클릭
5. 노란색 원이 나타나면서 실행 시작!
6. 1~3분 후 결과 확인:
   - ✅ **초록색 체크** → 성공! 크롤링이 잘 작동해요.
   - ❌ **빨간색 X** → 아래 "문제 해결" 섹션 확인

성공했다면, 저장소의 `data/charts.json` 파일을 열어보세요.
순위 데이터가 들어가 있으면 완벽해요!

---

## STEP 6: Cloudflare Pages 배포 (안정적 호스팅)

### 6-1: Cloudflare 계정 만들기

1. https://dash.cloudflare.com/sign-up 접속
2. 이메일 + 비밀번호 입력하여 가입
3. 이메일 인증 완료

### 6-2: Cloudflare Pages 프로젝트 생성

1. Cloudflare 대시보드에서 왼쪽 메뉴 **"Workers & Pages"** 클릭
2. **"Create"** 버튼 클릭
3. **"Pages"** 탭 선택
4. **"Connect to Git"** 클릭

### 6-3: GitHub 연결

1. **"Connect GitHub"** 클릭
2. GitHub 로그인 팝업이 뜨면 로그인
3. **"Only select repositories"** 선택 → `bts-chart` 저장소 선택
4. **"Install & Authorize"** 클릭
5. 다시 Cloudflare로 돌아와서 `bts-chart` 저장소 선택
6. **"Begin setup"** 클릭

### 6-4: 빌드 설정

1. **Project name**: `bts-chart` (이것이 URL이 됩니다)
2. **Production branch**: `main`
3. **Framework preset**: `None` 선택
4. **Build command**: 비워두기 (빈칸으로!)
5. **Build output directory**: `/` 입력 (슬래시 하나만!)
6. **"Save and Deploy"** 클릭

### 6-5: 배포 완료 확인

1~2분 후 배포가 완료되면 URL이 생겨요:

```
https://bts-chart.pages.dev
```

이 URL로 접속하면 차트 트래커 사이트가 보여요! 🎉

---

## STEP 7: 자동 업데이트 확인

모든 셋업이 끝났어요! 이제 이런 흐름으로 자동 작동합니다:

```
매 시간 정시 (00분)
  → GitHub Actions가 자동으로 크롤링 실행
  → data/charts.json 파일 업데이트
  → GitHub에 자동 커밋 & 푸시
  → Cloudflare Pages가 변경 감지
  → 사이트 자동 재배포 (약 30초)
  → 사이트에서 새 순위 확인 가능!
```

처음 1~2시간은 Actions 탭에서 자동 실행이 잘 되는지 확인해보세요.

---

## STEP 8: 이메일 알림 설정 (크롤링 실패 시)

크롤링이 실패하면 자동으로 GitHub Issue가 생성돼요.
이메일로 알림을 받으려면:

1. GitHub → 오른쪽 상단 프로필 아이콘 → **Settings** 클릭
2. 왼쪽에서 **Notifications** 클릭
3. **"Participating, @mentions and custom"** 섹션에서 **Email** 체크
4. 저장소로 돌아가서 상단 **Watch** 버튼 클릭 → **"All Activity"** 선택

이제 크롤링이 실패하면 이런 이메일이 와요:
```
🚨 차트 크롤링 오류 발생 (2026-03-24 15:00 KST)
- 멜론 TOP100 크롤링 실패: ConnectionError
```

---

## (선택) 커스텀 도메인 연결

`bts-chart.pages.dev` 대신 `armystream.kr` 같은 나만의 주소를 쓰고 싶다면:

### 도메인 구매

- 추천: Cloudflare Registrar (원가에 판매, 추가 수수료 없음)
- Cloudflare 대시보드 → **"Domain Registration"** → 원하는 도메인 검색 → 구매
- `.kr` 도메인: 약 15,000~20,000원/년
- `.com` 도메인: 약 12,000원/년

### 도메인 연결

1. Cloudflare → Workers & Pages → `bts-chart` 프로젝트 클릭
2. **"Custom domains"** 탭 클릭
3. **"Set up a custom domain"** 클릭
4. 구매한 도메인 입력 (예: `armystream.kr`)
5. DNS 설정이 자동으로 완료돼요!

---

## 문제 해결 FAQ

### Q: Actions에서 빨간색 ❌이 나와요

**클릭해서 로그를 확인하세요.** 흔한 원인들:

1. **"Permission denied"** → STEP 4의 권한 설정을 다시 확인
2. **크롤링 관련 에러** → 특정 사이트가 차단했거나 구조가 변경됨. Issues 탭 확인
3. **".github/workflows 파일을 찾을 수 없음"** → STEP 3의 방법 B로 파일 수동 생성

### Q: 사이트에 "데이터를 불러올 수 없습니다"가 나와요

- STEP 5의 첫 번째 크롤링이 성공했는지 확인
- `data/charts.json` 파일에 실제 데이터가 있는지 확인
- Cloudflare에서 재배포가 완료되었는지 확인

### Q: 순위가 전부 "—"으로 나와요

- 아직 곡이 차트에 진입하지 않았을 수 있어요
- `scripts/crawl_charts.py` 상단의 `TRACK_TITLE`이 정확한지 확인

### Q: 1시간마다 자동 실행이 안 돼요

- GitHub Actions의 schedule은 정확히 정시에 실행되지 않을 수 있어요 (최대 15분 지연 정상)
- Actions 탭에서 최근 실행 기록 확인

### Q: 특정 사이트 크롤링만 계속 실패해요

- 해당 사이트가 페이지 구조를 변경했을 가능성이 높아요
- Claude에게 해당 사이트 URL과 에러 메시지를 보여주면 코드 수정을 도와드릴게요

### Q: Cloudflare Pages 배포가 실패해요

- Build output directory가 `/`인지 확인
- Build command가 비어있는지 확인
- 이 사이트는 정적 HTML이라 빌드가 필요 없어요

---

## 트래킹 곡 변경하기 (나중에 컴백 시)

다른 곡으로 바꾸고 싶을 때:

1. GitHub 저장소에서 `scripts/crawl_charts.py` 파일 클릭
2. 연필 아이콘 (Edit) 클릭
3. 상단에서 아래 부분을 찾아 수정:

```python
TRACK_TITLE = "Swim"                          ← 새 곡 제목
TRACK_ARTIST_KEYWORDS = ["BTS", "방탄소년단"]  ← 아티스트명
```

4. **Commit changes** 클릭
5. 같은 방법으로 `index.html`에서 곡 제목, 이모지 등도 수정

---

## 안정성 요약

| 항목 | 상태 |
|------|------|
| 서버 다운 | Cloudflare CDN 330+ 노드 분산, 사실상 불가능 |
| 트래픽 폭증 | 대역폭 무제한, 아무리 많아도 무료 |
| DDoS 공격 | Cloudflare 자동 방어 내장 |
| SSL 인증서 | 무료 자동 발급 (HTTPS) |
| 크롤링 실패 | GitHub Issue 자동 생성 + 이메일 알림 |
| 월 비용 | 0원 (커스텀 도메인 제외) |

---

## 💜 크레딧

제작: [@bomnalcafe](https://x.com/bomnalcafe)
