import os
import streamlit as st

def _secret(key: str, fallback: str = "") -> str:
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, fallback)

# API Keys
MOFA_API_KEY = _secret(
    "MOFA_API_KEY",
    "4a8c9a2a154141a85edbb284e8604e2b650d9697c0806cc5610ff1515d0c9297",
)

# Endpoints
ALARM_URL = "https://apis.data.go.kr/1262000/TravelAlarmService2/getTravelAlarmList2"
WARN_URL  = "https://apis.data.go.kr/1262000/TravelWarningServiceV3/getTravelWarningListV3"

# 경보 단계 메타
LEVEL_META = {
    "1": {"text": "여행 유의",  "color": "#F59E0B", "bg": "#FFFDE7", "icon": "🟡", "badge": "#FFC107"},
    "2": {"text": "여행 자제",  "color": "#F97316", "bg": "#FFF3E0", "icon": "🟠", "badge": "#F97316"},
    "3": {"text": "출국 권고",  "color": "#EF4444", "bg": "#FFEBEE", "icon": "🔴", "badge": "#EF4444"},
    "4": {"text": "여행 금지",  "color": "#7C3AED", "bg": "#F3E5F5", "icon": "🚫", "badge": "#7C3AED"},
}

RISK_COLORS = {
    "매우 높음": "#CC0000",
    "높음":     "#EF4444",
    "보통":     "#F97316",
    "낮음":     "#22C55E",
}

LEGEND = [
    ("#CC0000", "매우 높음", "강력범죄, 테러, 무장강도 등"),
    ("#EF4444", "높음",     "소매치기, 절도, 폭력 등"),
    ("#F97316", "보통",     "안전사고, 경미한 범죄 등"),
    ("#22C55E", "낮음",     "비교적 안전"),
]

DANGER_KW = [
    "사건", "사고", "범죄", "테러", "지진", "화재", "폭발", "시위", "폭력",
    "납치", "강도", "총격", "재난", "태풍", "홍수", "위험", "경보", "경고",
    "attack", "crime", "terror", "disaster", "earthquake", "flood",
    "shooting", "robbery", "warning", "arrest", "explosion", "killed", "dead",
]

BLOCKED_SOURCES = {
    "네이트", "네이버 블로그", "티스토리", "카페", "위키백과",
    "나무위키", "Nate", "Blog", "Cafe", "Wikipedia",
}
