# 🛡️ 안전여행

외교부 공식 데이터 기반 해외여행 안전 정보 서비스

## 주요 기능

| 탭 | 기능 |
|----|------|
| 🗺️ 국가·지역 브리핑 | 외교부 실시간 여행경보 (215개국) + 전 세계 위험 현황 대시보드 |
| 🔔 실시간 위험 알림 | 현지 뉴스 RSS 수집 + 한국어 자동 번역 |
| 📍 여행지 위험지도 | 도시별 히트맵 + Nominatim 지오코딩 (전 세계 모든 도시) |

## 실행 방법

### 1. 클론

```bash
git clone https://github.com/202401578-coder/safe-travel-mvp.git
cd safe-travel-mvp
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 실행

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속

## 프로젝트 구조

```
safe-travel-mvp/
├── app.py                   # Streamlit 메인 (UI)
├── config.py                # 설정 및 상수
├── data/
│   └── city_db.py           # 15개국 50개 도시 안전 정보 DB
├── services/
│   ├── mofa_api.py          # 외교부 API 호출
│   ├── news_service.py      # 뉴스 RSS + 번역
│   └── geo_service.py       # Nominatim 지오코딩
├── components/
│   └── map_builder.py       # Folium 지도 빌더
└── requirements.txt
```

## 사용 API / 데이터

| 출처 | 용도 | 비용 |
|------|------|------|
| 외교부 해외안전여행 API | 국가별 여행경보 실시간 데이터 | 무료 |
| Google 뉴스 RSS | 현지 안전 뉴스 수집 | 무료 |
| Google Translate (비공식) | 뉴스 제목 한국어 번역 | 무료 |
| Nominatim (OpenStreetMap) | 도시명 → 좌표 변환 | 무료 |
| Carto Voyager Tiles | 지도 타일 | 무료 |
