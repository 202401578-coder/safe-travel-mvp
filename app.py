import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import random
import requests
import feedparser
from urllib.parse import quote

st.set_page_config(page_title="안전여행", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .alert-card { border-radius: 8px; padding: 14px 16px; margin: 8px 0; }
    .crime-card { border: 1px solid #e0e0e0; border-radius: 10px; padding: 14px;
                  text-align: center; background: white; height: 100%; }
</style>
""", unsafe_allow_html=True)

# ===================== API 설정 =====================

API_KEY   = "4a8c9a2a154141a85edbb284e8604e2b650d9697c0806cc5610ff1515d0c9297"
ALARM_URL = "https://apis.data.go.kr/1262000/TravelAlarmService2/getTravelAlarmList2"
WARN_URL  = "https://apis.data.go.kr/1262000/TravelWarningServiceV3/getTravelWarningListV3"

LEVEL_META = {
    "1": {"text": "여행 유의", "color": "#F59E0B", "bg": "#FFFDE7", "icon": "🟡"},
    "2": {"text": "여행 자제", "color": "#F97316", "bg": "#FFF3E0", "icon": "🟠"},
    "3": {"text": "출국 권고", "color": "#EF4444", "bg": "#FFEBEE", "icon": "🔴"},
    "4": {"text": "여행 금지", "color": "#7C3AED", "bg": "#F3E5F5", "icon": "🚫"},
}

DANGER_KW = ["사건", "사고", "범죄", "테러", "지진", "화재", "폭발", "시위", "폭력",
             "납치", "강도", "총격", "재난", "태풍", "홍수", "위험", "경보", "경고",
             "attack", "crime", "terror", "disaster", "earthquake", "flood",
             "shooting", "robbery", "warning", "arrest", "explosion"]

# ===================== 도시 DB =====================

CITY_DB = {
    "스페인": {
        "바르셀로나": {
            "eng": "Barcelona", "lat": 41.3870, "lng": 2.1700,
            "risk": "높음", "risk_color": "#EF4444",
            "tips": ["💼 람블라스·고딕 지구 소매치기 극심 — 가방 앞으로",
                     "🌙 엘 라발 야간 단독 이동 자제",
                     "📱 공공장소 스마트폰 노출 최소화",
                     "🏧 ATM 이용 시 주변 반드시 확인"],
            "areas": [("고딕 지구 (Barri Gòtic)", "매우 높음", "#CC0000", "소매치기·강도 최다"),
                      ("람블라스 거리 (La Rambla)", "매우 높음", "#CC0000", "관광객 밀집, 소매치기 극심"),
                      ("엘 라발 (El Raval)", "높음", "#EF4444", "야간 이동 위험"),
                      ("에이샴플라 (Eixample)", "보통", "#F97316", "소매치기 주의"),
                      ("바르셀로네타", "보통", "#F97316", "해변 도난 주의")],
        },
        "마드리드": {
            "eng": "Madrid", "lat": 40.4168, "lng": -3.7038,
            "risk": "보통", "risk_color": "#F97316",
            "tips": ["🚇 지하철·버스 소매치기 주의",
                     "🌙 라바피에스 야간 주의",
                     "💳 ATM 카드 스키밍 주의"],
            "areas": [("라바피에스", "높음", "#EF4444", "치안 취약"),
                      ("그란비아", "보통", "#F97316", "소매치기"),
                      ("레티로 공원", "낮음", "#22C55E", "비교적 안전")],
        },
        "세비야": {
            "eng": "Seville", "lat": 37.3886, "lng": -5.9823,
            "risk": "낮음", "risk_color": "#22C55E",
            "tips": ["🌞 여름 극심한 더위 주의 (40°C 이상)", "💼 관광지 소매치기 주의"],
            "areas": [("산타크루스", "보통", "#F97316", "소매치기"),
                      ("트리아나", "낮음", "#22C55E", "안전")],
        },
        "발렌시아": {
            "eng": "Valencia", "lat": 39.4699, "lng": -0.3763,
            "risk": "낮음", "risk_color": "#22C55E",
            "tips": ["🚲 자전거 도난 주의", "🏖️ 해변 귀중품 보관"],
            "areas": [("구시가지", "낮음", "#22C55E", "안전"),
                      ("비아로자", "보통", "#F97316", "소매치기 주의")],
        },
    },
    "프랑스": {
        "파리": {
            "eng": "Paris", "lat": 48.8566, "lng": 2.3522,
            "risk": "높음", "risk_color": "#EF4444",
            "tips": ["🚇 지하철 소매치기 매우 빈번 — 특히 1·4호선",
                     "🗼 에펠탑·루브르 주변 사기꾼 주의",
                     "🌙 북역(Gare du Nord) 야간 주의",
                     "✉️ 청원서·팔찌 강매 사기 조심"],
            "areas": [("몽마르트", "높음", "#EF4444", "소매치기"),
                      ("북역 일대", "높음", "#EF4444", "야간 위험"),
                      ("에펠탑 주변", "높음", "#EF4444", "사기 다발"),
                      ("마레 지구", "보통", "#F97316", "소매치기")],
        },
        "니스": {
            "eng": "Nice", "lat": 43.7102, "lng": 7.2620,
            "risk": "보통", "risk_color": "#F97316",
            "tips": ["🏖️ 해변 소지품 도난 주의", "🌙 구시가지 야간 주의"],
            "areas": [("구시가지", "보통", "#F97316", "소매치기"),
                      ("해변", "보통", "#F97316", "도난")],
        },
        "마르세유": {
            "eng": "Marseille", "lat": 43.2965, "lng": 5.3698,
            "risk": "높음", "risk_color": "#EF4444",
            "tips": ["🌙 북부 지역 야간 이동 절대 금지",
                     "🎒 배낭 앞으로 메기",
                     "🚇 대중교통 소매치기 주의"],
            "areas": [("북부 지역", "매우 높음", "#CC0000", "야간 출입 자제"),
                      ("노아유", "높음", "#EF4444", "치안 취약"),
                      ("구 항구", "보통", "#F97316", "소매치기")],
        },
    },
    "이탈리아": {
        "로마": {
            "eng": "Rome", "lat": 41.9028, "lng": 12.4964,
            "risk": "높음", "risk_color": "#EF4444",
            "tips": ["🚇 지하철 A·B선 소매치기 극심",
                     "👜 식당 의자에 가방 걸지 않기",
                     "📸 콜로세움 주변 가짜 검표원 주의",
                     "💳 현금 분산 보관"],
            "areas": [("테르미니역 주변", "높음", "#EF4444", "소매치기·사기"),
                      ("콜로세움", "높음", "#EF4444", "사기"),
                      ("트레비 분수", "높음", "#EF4444", "소매치기"),
                      ("트라스테베레", "보통", "#F97316", "야간 주의")],
        },
        "밀라노": {
            "eng": "Milan", "lat": 45.4642, "lng": 9.1900,
            "risk": "보통", "risk_color": "#F97316",
            "tips": ["🚇 지하철 소매치기 주의",
                     "🛍️ 가짜 명품 구매 주의",
                     "🌙 중앙역 야간 주의"],
            "areas": [("중앙역", "높음", "#EF4444", "소매치기"),
                      ("두오모", "보통", "#F97316", "관광객 사기")],
        },
        "피렌체": {
            "eng": "Florence", "lat": 43.7696, "lng": 11.2558,
            "risk": "낮음", "risk_color": "#22C55E",
            "tips": ["👜 가방 앞으로 메기", "🌙 산타크로체 야간 주의"],
            "areas": [("산 로렌초 시장", "보통", "#F97316", "소매치기"),
                      ("우피치 주변", "낮음", "#22C55E", "안전")],
        },
    },
    "일본": {
        "도쿄": {
            "eng": "Tokyo", "lat": 35.6762, "lng": 139.6503,
            "risk": "낮음", "risk_color": "#22C55E",
            "tips": ["🌊 지진·쓰나미 대피 경로 사전 확인",
                     "🍶 가부키초 야간 바가지 주의",
                     "🎪 신주쿠 가부키초 환락가 주의"],
            "areas": [("가부키초", "보통", "#F97316", "바가지·야간 주의"),
                      ("롯폰기", "보통", "#F97316", "외국인 대상 사기"),
                      ("나머지 지역", "낮음", "#22C55E", "매우 안전")],
        },
        "오사카": {
            "eng": "Osaka", "lat": 34.6937, "lng": 135.5023,
            "risk": "낮음", "risk_color": "#22C55E",
            "tips": ["🌊 난카이 대지진 대비", "🌙 닛폰바시 야간 주의"],
            "areas": [("닛폰바시", "보통", "#F97316", "야간 주의"),
                      ("나머지", "낮음", "#22C55E", "안전")],
        },
        "교토": {
            "eng": "Kyoto", "lat": 35.0116, "lng": 135.7681,
            "risk": "낮음", "risk_color": "#22C55E",
            "tips": ["🌊 지진 대피 경로 확인", "🚲 자전거 도로 주의"],
            "areas": [("기온", "낮음", "#22C55E", "매우 안전"),
                      ("아라시야마", "낮음", "#22C55E", "안전")],
        },
    },
    "태국": {
        "방콕": {
            "eng": "Bangkok", "lat": 13.7563, "lng": 100.5018,
            "risk": "보통", "risk_color": "#F97316",
            "tips": ["🛺 툭툭 바가지 주의",
                     "💎 보석 사기 주의 (사기꾼이 도와주는 척 접근)",
                     "🌙 카오산 로드 소매치기",
                     "🚕 미터기 없는 택시 이용 자제"],
            "areas": [("카오산 로드", "높음", "#EF4444", "소매치기·바가지"),
                      ("왓포 주변", "보통", "#F97316", "사기"),
                      ("실롬", "낮음", "#22C55E", "비교적 안전")],
        },
        "푸켓": {
            "eng": "Phuket", "lat": 7.9519, "lng": 98.3381,
            "risk": "보통", "risk_color": "#F97316",
            "tips": ["🏖️ 적기(Red Flag) 해변 수영 금지",
                     "🛵 오토바이 렌탈 사고 주의",
                     "🌊 우기 이안류 주의"],
            "areas": [("파통 비치", "보통", "#F97316", "소매치기·바가지"),
                      ("올드타운", "낮음", "#22C55E", "안전")],
        },
        "치앙마이": {
            "eng": "Chiang Mai", "lat": 18.7883, "lng": 98.9853,
            "risk": "낮음", "risk_color": "#22C55E",
            "tips": ["🛵 오토바이 사고 주의", "🌙 나이트 바자 소매치기 주의"],
            "areas": [("올드시티", "낮음", "#22C55E", "안전"),
                      ("나이트 바자", "보통", "#F97316", "소매치기")],
        },
    },
    "베트남": {
        "하노이": {
            "eng": "Hanoi", "lat": 21.0285, "lng": 105.8542,
            "risk": "보통", "risk_color": "#F97316",
            "tips": ["🛵 오토바이 날치기 주의 — 가방 차도 반대편으로",
                     "🚕 가짜 택시 주의 (Grab 앱 이용 권장)",
                     "💳 ATM 카드 복제 주의"],
            "areas": [("호안끼엠 호수", "보통", "#F97316", "소매치기"),
                      ("구시가지", "보통", "#F97316", "날치기")],
        },
        "호찌민": {
            "eng": "Ho Chi Minh City", "lat": 10.8231, "lng": 106.6297,
            "risk": "보통", "risk_color": "#F97316",
            "tips": ["🛵 오토바이 날치기 극심 — 가방 끈 잡아채기",
                     "🌙 팜응우라오 야간 소매치기",
                     "💳 가짜 ATM 주의"],
            "areas": [("팜응우라오", "높음", "#EF4444", "소매치기"),
                      ("벤탄 시장", "높음", "#EF4444", "날치기"),
                      ("1군", "보통", "#F97316", "주의")],
        },
        "다낭": {
            "eng": "Da Nang", "lat": 16.0544, "lng": 108.2022,
            "risk": "낮음", "risk_color": "#22C55E",
            "tips": ["🏖️ 해변 귀중품 보관", "🛵 오토바이 사고 주의"],
            "areas": [("미케 비치", "낮음", "#22C55E", "안전"),
                      ("한강", "낮음", "#22C55E", "안전")],
        },
    },
    "영국": {
        "런던": {
            "eng": "London", "lat": 51.5074, "lng": -0.1278,
            "risk": "보통", "risk_color": "#F97316",
            "tips": ["🚇 지하철 소매치기 주의",
                     "🌙 브릭스턴·펙엄 야간 주의",
                     "🛴 전동킥보드 날치기 주의"],
            "areas": [("브릭스턴", "높음", "#EF4444", "야간 위험"),
                      ("피카딜리", "보통", "#F97316", "소매치기"),
                      ("사우스워크", "보통", "#F97316", "소매치기")],
        },
        "에든버러": {
            "eng": "Edinburgh", "lat": 55.9533, "lng": -3.1883,
            "risk": "낮음", "risk_color": "#22C55E",
            "tips": ["🌧️ 기상 변화 대비 (방수 재킷 필수)"],
            "areas": [("구시가지", "낮음", "#22C55E", "안전"),
                      ("로열 마일", "낮음", "#22C55E", "안전")],
        },
    },
    "미국": {
        "뉴욕": {
            "eng": "New York", "lat": 40.7128, "lng": -74.0060,
            "risk": "보통", "risk_color": "#F97316",
            "tips": ["🌙 할렘·사우스 브롱크스 야간 주의",
                     "🚇 심야 지하철 이용 자제",
                     "📱 스마트폰 날치기 주의"],
            "areas": [("할렘", "높음", "#EF4444", "야간 주의"),
                      ("브롱크스 남부", "높음", "#EF4444", "야간 주의"),
                      ("맨해튼 미드타운", "보통", "#F97316", "소매치기")],
        },
        "로스앤젤레스": {
            "eng": "Los Angeles", "lat": 34.0522, "lng": -118.2437,
            "risk": "보통", "risk_color": "#F97316",
            "tips": ["🚗 차량 내 귀중품 절대 방치 금지",
                     "🌙 스키드 로우 야간 접근 금지",
                     "🔫 총기 관련 사고 주의"],
            "areas": [("스키드 로우", "매우 높음", "#CC0000", "노숙자·마약 밀집"),
                      ("컴튼", "높음", "#EF4444", "야간 위험"),
                      ("산타모니카", "낮음", "#22C55E", "안전")],
        },
        "라스베이거스": {
            "eng": "Las Vegas", "lat": 36.1699, "lng": -115.1398,
            "risk": "보통", "risk_color": "#F97316",
            "tips": ["🎰 도박 중독 주의",
                     "🌙 스트립 외곽 야간 주의",
                     "💊 음료 주의 (약물 투입 사례)"],
            "areas": [("더 스트립", "보통", "#F97316", "소매치기"),
                      ("프리몬트", "보통", "#F97316", "야간 주의")],
        },
    },
    "독일": {
        "베를린": {
            "eng": "Berlin", "lat": 52.5200, "lng": 13.4050,
            "risk": "낮음", "risk_color": "#22C55E",
            "tips": ["🚇 지하철 소매치기 주의", "🌙 노이쾰른 야간 주의"],
            "areas": [("노이쾰른", "보통", "#F97316", "야간 주의"),
                      ("알렉산더플라츠", "보통", "#F97316", "소매치기")],
        },
        "뮌헨": {
            "eng": "Munich", "lat": 48.1351, "lng": 11.5820,
            "risk": "낮음", "risk_color": "#22C55E",
            "tips": ["🍺 옥토버페스트 기간 소매치기 급증", "🚇 지하철 소매치기 주의"],
            "areas": [("중앙역", "보통", "#F97316", "소매치기"),
                      ("마리엔플라츠", "낮음", "#22C55E", "안전")],
        },
    },
    "터키": {
        "이스탄불": {
            "eng": "Istanbul", "lat": 41.0082, "lng": 28.9784,
            "risk": "높음", "risk_color": "#EF4444",
            "tips": ["👞 구두 닦이 사기 주의",
                     "🍵 차이 초대 사기 주의",
                     "💳 환전소 바가지 주의",
                     "⚠️ 테러 위협 지속 경계"],
            "areas": [("술탄아흐메트", "높음", "#EF4444", "사기·소매치기"),
                      ("탁심 광장", "보통", "#F97316", "야간 주의"),
                      ("그랜드 바자르", "높음", "#EF4444", "사기")],
        },
        "안탈리아": {
            "eng": "Antalya", "lat": 36.8969, "lng": 30.7133,
            "risk": "보통", "risk_color": "#F97316",
            "tips": ["🏖️ 해변 귀중품 주의", "💳 환전소 확인 후 이용"],
            "areas": [("칼레이치", "낮음", "#22C55E", "안전"),
                      ("해변", "보통", "#F97316", "도난 주의")],
        },
    },
    "그리스": {
        "아테네": {
            "eng": "Athens", "lat": 37.9838, "lng": 23.7275,
            "risk": "보통", "risk_color": "#F97316",
            "tips": ["🚇 지하철 소매치기 주의",
                     "🌙 오모니아 광장 야간 주의",
                     "💊 약물 관련 지역 주의"],
            "areas": [("오모니아", "높음", "#EF4444", "야간 주의"),
                      ("모나스티라키", "보통", "#F97316", "소매치기"),
                      ("아크로폴리스", "낮음", "#22C55E", "안전")],
        },
        "산토리니": {
            "eng": "Santorini", "lat": 36.3932, "lng": 25.4615,
            "risk": "낮음", "risk_color": "#22C55E",
            "tips": ["🌊 절벽 낙하 사고 주의", "🛵 오토바이 사고 주의"],
            "areas": [("피라", "낮음", "#22C55E", "안전"),
                      ("오이아", "낮음", "#22C55E", "안전")],
        },
    },
    "포르투갈": {
        "리스본": {
            "eng": "Lisbon", "lat": 38.7169, "lng": -9.1399,
            "risk": "보통", "risk_color": "#F97316",
            "tips": ["🚃 트램 28번 소매치기 극심",
                     "🌙 마르팀 모니스 야간 주의",
                     "🎒 배낭 앞으로 메기"],
            "areas": [("알파마", "보통", "#F97316", "소매치기"),
                      ("바이샤", "보통", "#F97316", "소매치기"),
                      ("벨렘", "낮음", "#22C55E", "안전")],
        },
        "포르투": {
            "eng": "Porto", "lat": 41.1579, "lng": -8.6291,
            "risk": "낮음", "risk_color": "#22C55E",
            "tips": ["🍷 관광지 소매치기 주의"],
            "areas": [("히베이라", "낮음", "#22C55E", "안전"),
                      ("세 성당", "낮음", "#22C55E", "안전")],
        },
    },
    "호주": {
        "시드니": {
            "eng": "Sydney", "lat": -33.8688, "lng": 151.2093,
            "risk": "낮음", "risk_color": "#22C55E",
            "tips": ["🌊 해변 이안류 주의 — 노란 깃발 사이 수영",
                     "☀️ 자외선 매우 강함 — 자외선 차단제 필수",
                     "🐍 야외 활동 시 뱀·거미 주의"],
            "areas": [("킹스 크로스", "보통", "#F97316", "야간 주의"),
                      ("시티 센터", "낮음", "#22C55E", "안전")],
        },
        "멜버른": {
            "eng": "Melbourne", "lat": -37.8136, "lng": 144.9631,
            "risk": "낮음", "risk_color": "#22C55E",
            "tips": ["🌦️ 하루에 사계절 — 겉옷 필수"],
            "areas": [("CBD", "낮음", "#22C55E", "안전"),
                      ("세인트 킬다", "보통", "#F97316", "야간 주의")],
        },
    },
    "싱가포르": {
        "싱가포르": {
            "eng": "Singapore", "lat": 1.3521, "lng": 103.8198,
            "risk": "낮음", "risk_color": "#22C55E",
            "tips": ["🚭 공공장소 흡연 시 벌금",
                     "🍬 껌 반입 금지",
                     "✈️ 약물 반입 시 사형"],
            "areas": [("전체 지역", "낮음", "#22C55E", "아시아 최안전 도시 중 하나")],
        },
    },
    "대만": {
        "타이베이": {
            "eng": "Taipei", "lat": 25.0330, "lng": 121.5654,
            "risk": "낮음", "risk_color": "#22C55E",
            "tips": ["🌊 지진·태풍 대비", "🛵 오토바이 사고 주의"],
            "areas": [("완화", "낮음", "#22C55E", "안전"),
                      ("시먼딩", "낮음", "#22C55E", "안전")],
        },
    },
}

LEGEND = [
    ("#CC0000", "매우 높음", "강력범죄, 테러, 무장강도 등"),
    ("#EF4444", "높음",   "소매치기, 절도, 폭력 등"),
    ("#F97316", "보통",   "안전사고, 경미한 범죄 등"),
    ("#22C55E", "낮음",   "비교적 안전"),
]

CRIME_STATS = [
    {"type": "소매치기", "emoji": "👜", "level": "높음", "color": "#EF4444",
     "location": "람블라스 거리, 고딕 지구", "count": 28, "unit": "건"},
    {"type": "강력범죄", "emoji": "⚠️", "level": "보통", "color": "#F97316",
     "location": "엘 라발, 우르키나오나 주변", "count": 7, "unit": "건"},
    {"type": "시위/집회", "emoji": "📢", "level": "보통", "color": "#F97316",
     "location": "카탈루냐 광장, 그라시아 거리", "count": 2, "unit": "건(예정)"},
    {"type": "교통/사고", "emoji": "🚗", "level": "낮음", "color": "#22C55E",
     "location": "에이샴플라 주요 도로", "count": 4, "unit": "건"},
]

# ===================== API 함수 =====================

@st.cache_data(ttl=3600)
def fetch_all_countries():
    try:
        resp = requests.get(ALARM_URL, params={
            "serviceKey": API_KEY, "numOfRows": 300, "pageNo": 1,
        }, timeout=10)
        items = resp.json()["response"]["body"]["items"]["item"]
        result = {}
        for item in items:
            meta = LEVEL_META.get(item["alarm_lvl"], {"text": "정보없음", "color": "#999", "bg": "#f5f5f5", "icon": "⚪"})
            result[item["country_nm"]] = {
                "eng_name": item["country_eng_nm"],
                "iso":      item["country_iso_alp2"],
                "level":    item["alarm_lvl"],
                "level_text":  meta["text"],
                "level_color": meta["color"],
                "level_bg":    meta["bg"],
                "level_icon":  meta["icon"],
                "continent":   item["continent_nm"],
                "region":      item["remark"],
                "flag_url":    item["flag_download_url"],
                "dang_map_url": item["dang_map_download_url"],
            }
        return result
    except Exception:
        return {}


@st.cache_data(ttl=3600)
def fetch_warning_detail(country_name):
    try:
        resp = requests.get(WARN_URL, params={
            "serviceKey": API_KEY, "numOfRows": 300, "pageNo": 1,
        }, timeout=10)
        items = resp.json()["response"]["body"]["items"]["item"]
        for item in items:
            if item["country_name"] == country_name:
                return item
        return None
    except Exception:
        return None


BLOCKED_SOURCES = {"네이트", "네이버 블로그", "티스토리", "카페", "위키백과",
                   "나무위키", "Nate", "Blog", "Cafe", "Wikipedia"}

@st.cache_data(ttl=600)
def fetch_safety_news(country_name, country_eng, city_name, city_eng):
    try:
        # 도시명 기준으로 검색 (국가보다 구체적)
        query = f"{city_eng} OR {city_name} safety crime incident warning"
        url = f"https://news.google.com/rss/search?q={quote(query)}&hl=en&gl=US&ceid=US:en"
        feed = feedparser.parse(url)

        articles = []
        location_terms = {country_name.lower(), country_eng.lower(),
                          city_name.lower(), city_eng.lower()}

        for entry in feed.entries[:40]:
            title   = entry.get("title", "")
            source  = entry.get("source", {}).get("title", "")
            title_l = title.lower()

            # 신뢰도 낮은 출처 제외
            if any(b.lower() in source.lower() for b in BLOCKED_SOURCES):
                continue

            # 도시 또는 국가 언급 필수
            has_location = any(t in title_l for t in location_terms)
            if not has_location:
                continue

            # 안전 관련 키워드 필수
            has_danger = any(kw.lower() in title_l for kw in DANGER_KW)
            if not has_danger:
                continue

            articles.append({
                "title":  title,
                "link":   entry.get("link", "#"),
                "pub":    entry.get("published", ""),
                "source": source or "뉴스",
            })

        return articles[:10]
    except Exception:
        return []


# ===================== 지도 함수 =====================

def get_heatmap_data():
    random.seed(42)
    hotspots = [
        (41.3797, 2.1738, 1.0), (41.3810, 2.1735, 0.95), (41.3785, 2.1741, 0.90),
        (41.3833, 2.1764, 0.95), (41.3825, 2.1780, 0.90), (41.3840, 2.1755, 0.88),
        (41.3870, 2.1700, 0.82), (41.3875, 2.1695, 0.78),
        (41.3795, 2.1686, 0.75), (41.3785, 2.1675, 0.80), (41.3800, 2.1670, 0.72),
        (41.3793, 2.1888, 0.50), (41.3780, 2.1900, 0.45),
        (41.3933, 2.1619, 0.35), (41.3920, 2.1640, 0.40),
        (41.3641, 2.1594, 0.20),
    ]
    points = []
    for lat, lng, w in hotspots:
        points.append([lat, lng, w])
        for _ in range(7):
            dlat = random.uniform(-0.005, 0.005)
            dlng = random.uniform(-0.005, 0.005)
            points.append([lat + dlat, lng + dlng, max(0.1, w * random.uniform(0.4, 0.85))])
    return points


def build_map(center_lat, center_lng, radius_m):
    m = folium.Map(location=[center_lat, center_lng], zoom_start=14, tiles="CartoDB positron")
    HeatMap(get_heatmap_data(), radius=28, blur=22, max_zoom=18,
            gradient={"0.2": "#22C55E", "0.45": "#FFC107", "0.65": "#F97316",
                      "0.82": "#EF4444", "1.0": "#CC0000"}).add_to(m)
    folium.Circle(location=[center_lat, center_lng], radius=radius_m,
                  color="#1565C0", weight=2, fill=False, dash_array="8").add_to(m)
    folium.Marker(location=[center_lat, center_lng], tooltip="📍 카탈루냐 광장 (기준점)",
                  icon=folium.Icon(color="blue", icon="info-sign")).add_to(m)
    for name, (lat, lng) in {"고딕 지구": (41.3833, 2.1776), "El Raval": (41.3800, 2.1670),
                              "에이샴플라": (41.3945, 2.1619), "람블라스": (41.3790, 2.1730),
                              "바르셀로네타": (41.3780, 2.1900)}.items():
        folium.Marker(location=[lat, lng], tooltip=name,
                      icon=folium.DivIcon(
                          html=f'<div style="font-size:11px;color:#222;background:rgba(255,255,255,0.85);'
                               f'padding:2px 6px;border-radius:4px;white-space:nowrap;font-weight:600;">{name}</div>',
                          icon_size=(100, 22), icon_anchor=(50, 11))).add_to(m)
    return m


# ===================== 세션 상태 초기화 =====================

if "selected_country" not in st.session_state:
    st.session_state.selected_country = "스페인"
if "selected_country_eng" not in st.session_state:
    st.session_state.selected_country_eng = "Spain"
if "selected_city" not in st.session_state:
    st.session_state.selected_city = "바르셀로나"

# ===================== 헤더 =====================

col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("# 🛡️ 안전여행")
    st.caption("해외여행 위험 정보 종합 서비스")
with col_h2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.info(f"📍 현재 선택: **{st.session_state.selected_country}** · {st.session_state.selected_city}")

st.divider()

tab_a, tab_b, tab_c, tab_plan = st.tabs(
    ["🗺️ A. 국가·지역 위험 브리핑", "🔔 B. 실시간 위험 알림", "📍 C. 여행지 위험지도", "📋 기획서"]
)

# ===================== TAB A =====================

with tab_a:
    with st.spinner("외교부 여행경보 데이터 불러오는 중..."):
        all_countries = fetch_all_countries()

    if not all_countries:
        st.error("API 호출에 실패했습니다. 잠시 후 다시 시도해주세요.")
        st.stop()

    country_names = sorted(all_countries.keys())

    # --- ① 국가 선택 (검색 + 드롭다운) ---
    st.subheader("① 국가 선택")
    search = st.text_input("🔍 국가 검색 (한글 또는 영어)", placeholder="예: 스페인, Japan, France...")

    if search.strip():
        s = search.strip().lower()
        filtered = [n for n in country_names
                    if s in n.lower() or s in all_countries[n]["eng_name"].lower()]
    else:
        filtered = country_names

    if not filtered:
        st.warning("검색 결과가 없습니다.")
        st.stop()

    default_idx = filtered.index("스페인") if "스페인" in filtered else 0
    country = st.selectbox(
        f"국가 선택 (전체 {len(country_names)}개국 중 {len(filtered)}개)",
        filtered, index=default_idx, label_visibility="collapsed"
    )

    # 세션 업데이트
    st.session_state.selected_country = country
    st.session_state.selected_country_eng = all_countries[country]["eng_name"]

    info = all_countries[country]

    # 경보 배지
    st.markdown(
        f"""<div style="background:{info['level_bg']};border:2px solid {info['level_color']};
            border-radius:12px;padding:18px 24px;margin:12px 0;display:flex;align-items:center;gap:20px;">
            <img src="{info['flag_url']}" width="60" style="border-radius:4px;">
            <div>
                <div style="font-size:22px;font-weight:bold;">
                    {info['level_icon']} {country} ({info['eng_name']})
                </div>
                <div style="margin-top:6px;font-size:15px;">
                    경보 <strong>{info['level']}단계</strong> —
                    <span style="color:{info['level_color']};font-weight:bold;">{info['level_text']}</span>
                    &nbsp;|&nbsp; 대상: {info['region']} &nbsp;|&nbsp; 대륙: {info['continent']}
                </div>
            </div>
        </div>""", unsafe_allow_html=True
    )

    # 지역별 세부 경보 (TravelWarningServiceV3)
    detail = fetch_warning_detail(country)
    if detail:
        st.markdown("**지역별 세부 경보 현황**")
        warn_rows = [
            ("🟡 여행유의", detail.get("attention"),      detail.get("attention_note"),      detail.get("attention_partial")),
            ("🟠 여행자제", detail.get("control"),        detail.get("control_note"),        detail.get("control_partial")),
            ("🔴 출국권고", detail.get("limita"),         detail.get("limita_note"),         detail.get("limita_partial")),
            ("🚫 여행금지", detail.get("ban_yna"),        detail.get("ban_note"),            detail.get("ban_yn_partial")),
        ]
        has_any = False
        for label, full, note, partial in warn_rows:
            if full or partial:
                has_any = True
                region_text = note or (partial.replace("(일부)", "일부 지역") if partial else "")
                st.markdown(f"- {label}: **{region_text}**")
        if not has_any:
            st.markdown("- 별도 세부 경보 없음 (국가 전체 동일 단계)")

    # 경보 단계 안내
    level_desc = {
        "1": "여행 시 신변 안전에 유의하세요. 특별한 위험 요소는 없으나 기본 주의가 필요합니다.",
        "2": "불필요한 여행을 자제하세요. 신변 안전에 특별히 주의하세요.",
        "3": "즉시 출국을 검토하세요. 체류 중인 경우 신속히 대피를 준비하세요.",
        "4": "여행이 금지된 국가입니다. 현지 체류자는 즉시 출국하세요.",
    }.get(info["level"], "")

    if level_desc:
        if info["level"] in ("3", "4"):
            st.warning(level_desc)
        else:
            st.info(level_desc)

    with st.expander("📌 외교부 공식 위험지도 보기", expanded=False):
        st.image(info["dang_map_url"], caption=f"{country} 외교부 공식 위험지도", use_container_width=True)

    st.divider()

    # --- ② 도시 선택 ---
    st.subheader("② 도시 선택")

    if country in CITY_DB:
        city_list = list(CITY_DB[country].keys())
        city = st.selectbox("도시", city_list, label_visibility="collapsed")
        st.session_state.selected_city = city
        cinfo = CITY_DB[country][city]

        with st.expander(
            f"⚠️ {city} ({cinfo['eng']}) 안전 브리핑 — 전체 위험도: **{cinfo['risk']}**",
            expanded=True
        ):
            st.markdown(
                f"<span style='font-size:18px;font-weight:bold;color:{cinfo['risk_color']};'>"
                f"전체 위험도: {cinfo['risk']}</span>",
                unsafe_allow_html=True
            )
            st.markdown("---")

            # 구역별 위험 수준
            if cinfo.get("areas"):
                st.markdown("**구역별 위험 수준**")
                for area_name, area_level, area_color, area_detail in cinfo["areas"]:
                    c1, c2, c3 = st.columns([3, 2, 4])
                    c1.markdown(f"**{area_name}**")
                    c2.markdown(
                        f"<span style='color:{area_color};font-weight:bold;'>{area_level}</span>",
                        unsafe_allow_html=True
                    )
                    c3.markdown(area_detail)

            st.markdown("---")
            st.markdown("**여행 시 주의사항**")
            for tip in cinfo.get("tips", []):
                st.info(tip)

    else:
        city_input = st.text_input("방문 예정 도시 입력 (직접 입력)", placeholder="예: 카이로, Cairo")
        if city_input:
            st.session_state.selected_city = city_input
        st.info("ℹ️ 해당 국가의 도시별 상세 정보는 준비 중입니다. 외교부 공식 위험지도를 참고해주세요.")

# ===================== TAB B =====================

with tab_b:
    sel_country = st.session_state.selected_country
    sel_eng     = st.session_state.selected_country_eng
    sel_city    = st.session_state.selected_city

    st.subheader(f"🔔 실시간 위험 알림 — {sel_country} · {sel_city}")
    st.caption("Google 뉴스 RSS 기반 실시간 수집 | 위험 키워드 자동 필터링")

    col_b1, col_b2 = st.columns([2, 1])
    with col_b1:
        st.markdown(
            f"<div style='background:#EFF6FF;border-radius:8px;padding:10px 14px;font-size:13px;'>"
            f"📍 <strong>A탭에서 선택한 여행지</strong>: {sel_country} · {sel_city}<br>"
            f"<span style='color:#666;'>A탭에서 국가/도시를 변경하면 알림도 자동 업데이트됩니다.</span>"
            f"</div>", unsafe_allow_html=True
        )

    with col_b2:
        if st.button("🔄 뉴스 새로고침", use_container_width=True):
            st.cache_data.clear()

    st.markdown("---")

    # 도시 영문명 조회
    city_eng = ""
    if sel_country in CITY_DB and sel_city in CITY_DB[sel_country]:
        city_eng = CITY_DB[sel_country][sel_city].get("eng", sel_city)
    else:
        city_eng = sel_city

    # 실시간 뉴스
    with st.spinner(f"{sel_city} 관련 안전 뉴스 수집 중..."):
        news_items = fetch_safety_news(sel_country, sel_eng, sel_city, city_eng)

    if news_items:
        st.markdown(f"**{sel_city} ({city_eng}) 관련 최신 안전 뉴스 ({len(news_items)}건)**")
        for i, article in enumerate(news_items):
            level_color = "#EF4444" if any(kw in article["title"] for kw in ["테러", "폭발", "총격", "사망", "attack", "terror", "shooting"]) \
                else "#F97316" if any(kw in article["title"] for kw in ["사건", "사고", "범죄", "시위", "crime"]) \
                else "#F59E0B"
            level_text = "높음" if level_color == "#EF4444" else "보통" if level_color == "#F97316" else "주의"
            st.markdown(
                f"""<div class="alert-card" style="border-left:5px solid {level_color};background:#fafafa;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                        <span style="font-weight:700;font-size:14px;">{article['title']}</span>
                        <span style="background:{level_color};color:white;padding:2px 8px;
                              border-radius:12px;font-size:11px;font-weight:bold;white-space:nowrap;margin-left:8px;">
                              {level_text}</span>
                    </div>
                    <div style="color:#999;font-size:11px;">
                        📰 {article['source']} &nbsp;|&nbsp; 🕐 {article['pub'][:16] if article['pub'] else ''}
                        &nbsp;|&nbsp; <a href="{article['link']}" target="_blank">원문 보기 →</a>
                    </div>
                </div>""", unsafe_allow_html=True
            )
    else:
        st.info(f"현재 {sel_country} 관련 긴급 안전 뉴스가 없습니다.")

    st.divider()

    # 알림 설정 (기획서 B 서비스 기능 시뮬레이션)
    st.markdown("**📳 알림 수신 설정**")
    s1, s2 = st.columns(2)
    with s1:
        st.toggle("현재 위치 기반 알림 (GPS)", value=True)
        st.toggle(f"방문 예정지 알림 ({sel_city})", value=True)
    with s2:
        st.slider("알림 반경 (km)", 0.5, 5.0, 1.0, 0.5)
        st.multiselect("알림 유형",
                       ["소매치기", "강력범죄", "시위/집회", "교통사고", "재난/자연재해", "테러"],
                       default=["소매치기", "강력범죄", "재난/자연재해", "테러"])

# ===================== TAB C =====================

with tab_c:
    ch1, ch2 = st.columns([3, 2])
    with ch1:
        st.subheader("📍 여행지 위험지도")
        st.caption("현재 위치 기준 반경 위험도 시각화")
    with ch2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("🇪🇸 **스페인 · 바르셀로나**  \n📌 기준점: 카탈루냐 광장 (Plaça de Catalunya)")

    radius_map = {"500m": 500, "1km": 1000, "2km": 2000, "3km": 3000}
    radius_label = st.radio("반경 설정", list(radius_map.keys()), index=1, horizontal=True)
    radius_m = radius_map[radius_label]

    col_map, col_info = st.columns([3, 2])

    with col_map:
        m = build_map(41.3870, 2.1700, radius_m)
        st_folium(m, width=None, height=500, returned_objects=[])

    with col_info:
        st.markdown("#### 전체 위험도 요약")
        st.markdown(
            """<div style="background:#fff5f5;border:2px solid #EF4444;border-radius:10px;
                padding:16px;margin-bottom:12px;">
                <div style="font-size:20px;font-weight:bold;color:#EF4444;">⚠️ 높음</div>
                <div style="margin-top:8px;font-size:13px;color:#444;">
                    소매치기, 강력범죄 주의.<br>특히 람블라스 거리, 고딕 지구 주의.
                </div>
            </div>""", unsafe_allow_html=True
        )
        st.markdown("#### 위험도 범례")
        for color, level, desc in LEGEND:
            st.markdown(
                f"""<div style="margin:6px 0;display:flex;align-items:center;">
                    <span style="display:inline-block;width:14px;height:14px;border-radius:50%;
                                 background:{color};margin-right:10px;flex-shrink:0;"></span>
                    <span><strong>{level}</strong> — <span style="color:#666;font-size:13px;">{desc}</span></span>
                </div>""", unsafe_allow_html=True
            )
        st.divider()
        st.markdown("#### 지도 기준점")
        st.markdown(
            """<div style="background:#f0f4ff;border-radius:8px;padding:12px;font-size:13px;">
                📍 <strong>카탈루냐 광장</strong> (Plaça de Catalunya)<br>
                <span style="color:#666;">선택 반경 내 위험도를 시각화합니다.</span>
            </div>""", unsafe_allow_html=True
        )

    st.divider()
    st.markdown(f"**위험 유형별 주요 발생 정보 ({radius_label} 반경, 최근 7일)**")
    cols = st.columns(4)
    for i, stat in enumerate(CRIME_STATS):
        with cols[i]:
            st.markdown(
                f"""<div class="crime-card" style="border-top:4px solid {stat['color']};">
                    <div style="font-size:24px;">{stat['emoji']}</div>
                    <div style="font-weight:700;font-size:14px;margin-top:4px;">{stat['type']}</div>
                    <div style="color:{stat['color']};font-weight:bold;font-size:13px;margin:4px 0;">{stat['level']}</div>
                    <div style="color:#666;font-size:11px;margin-bottom:8px;">{stat['location']}</div>
                    <div style="font-size:26px;font-weight:bold;color:#222;">{stat['count']}</div>
                    <div style="color:#999;font-size:11px;">{stat['unit']}</div>
                </div>""", unsafe_allow_html=True
            )

# ===================== TAB 기획서 =====================

with tab_plan:
    try:
        with open("안전여행_기획서.md", "r", encoding="utf-8") as f:
            st.markdown(f.read())
    except FileNotFoundError:
        st.error("기획서 파일을 찾을 수 없습니다.")

# ===================== 푸터 =====================

st.divider()
st.caption(
    "데이터 출처: 외교부 해외안전여행 API, Google 뉴스 RSS (실시간) | "
    "위험지도: 바르셀로나 샘플 데이터  \n"
    "※ 본 정보는 참고용이며 실제 상황과 다를 수 있습니다."
)
