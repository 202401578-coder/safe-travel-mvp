import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import random
import requests

st.set_page_config(
    page_title="안전여행",
    page_icon="🛡️",
    layout="wide"
)

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .alert-card {
        border-radius: 8px;
        padding: 14px 16px;
        margin: 8px 0;
    }
    .crime-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 14px;
        text-align: center;
        background: white;
        height: 100%;
    }
    .legend-dot {
        display: inline-block;
        width: 14px;
        height: 14px;
        border-radius: 50%;
        margin-right: 8px;
        vertical-align: middle;
    }
</style>
""", unsafe_allow_html=True)

# ===================== 외교부 API =====================

API_KEY = "4a8c9a2a154141a85edbb284e8604e2b650d9697c0806cc5610ff1515d0c9297"
API_URL = "https://apis.data.go.kr/1262000/TravelAlarmService2/getTravelAlarmList2"

ALARM_LEVEL_INFO = {
    "1": {"text": "여행 유의",  "color": "#FFC107", "bg": "#FFFDE7", "icon": "🟡"},
    "2": {"text": "여행 자제",  "color": "#FF9800", "bg": "#FFF3E0", "icon": "🟠"},
    "3": {"text": "출국 권고",  "color": "#F44336", "bg": "#FFEBEE", "icon": "🔴"},
    "4": {"text": "여행 금지",  "color": "#7B1FA2", "bg": "#F3E5F5", "icon": "🚫"},
}

@st.cache_data(ttl=3600)
def fetch_all_countries():
    try:
        resp = requests.get(API_URL, params={
            "serviceKey": API_KEY,
            "numOfRows": 300,
            "pageNo": 1,
        }, timeout=10)
        items = resp.json()["response"]["body"]["items"]["item"]
        countries = {}
        for item in items:
            name = item["country_nm"]
            eng  = item["country_eng_nm"]
            lvl  = item["alarm_lvl"]
            countries[name] = {
                "eng_name":    eng,
                "iso":         item["country_iso_alp2"],
                "level":       lvl,
                "level_text":  ALARM_LEVEL_INFO.get(lvl, {}).get("text", "정보 없음"),
                "level_color": ALARM_LEVEL_INFO.get(lvl, {}).get("color", "#999"),
                "level_bg":    ALARM_LEVEL_INFO.get(lvl, {}).get("bg", "#f5f5f5"),
                "level_icon":  ALARM_LEVEL_INFO.get(lvl, {}).get("icon", "⚪"),
                "continent":   item["continent_nm"],
                "region":      item["remark"],
                "flag_url":    item["flag_download_url"],
                "map_url":     item["map_download_url"],
                "dang_map_url": item["dang_map_download_url"],
            }
        return countries
    except Exception as e:
        return {}

# 도시 샘플 데이터 (바르셀로나)
CITY_INFO = {"바르셀로나": {"overall": "높음", "overall_color": "#FF4B4B", "lat": 41.3870, "lng": 2.1700,
    "districts": [
        ("고딕 지구 (Barri Gòtic)", "매우 높음", "#CC0000", "소매치기·강도 최다 발생. 야간 특히 위험"),
        ("람블라스 거리 (La Rambla)", "매우 높음", "#CC0000", "관광객 밀집, 소매치기 극심. 가방 앞으로"),
        ("엘 라발 (El Raval)", "높음", "#FF4B4B", "야간 이동 위험, 강력범죄 주의"),
        ("에이샴플라 (Eixample)", "보통", "#FFA500", "상대적으로 안전, 소매치기 주의"),
        ("바르셀로네타 (Barceloneta)", "보통", "#FFA500", "해변 도난 주의, 귀중품 보관 철저"),
        ("몬주이크 (Montjuïc)", "낮음", "#4CAF50", "비교적 안전, 야간 주의"),
    ],
    "tips": [
        "💼 가방·지갑·핸드폰은 항상 앞으로 들고 이동하세요",
        "🌙 엘 라발, 고딕 지구 야간 단독 이동 자제",
        "📱 공공장소에서 스마트폰 노출 최소화",
        "🏧 ATM 이용 시 주변을 반드시 확인하세요",
        "🎒 배낭은 앞으로 메거나 잠금장치를 사용하세요",
    ],
}}

CITY_INFO = {
    "바르셀로나": {
        "overall": "높음",
        "overall_color": "#FF4B4B",
        "lat": 41.3870,
        "lng": 2.1700,
        "districts": [
            ("고딕 지구 (Barri Gòtic)", "매우 높음", "#CC0000", "소매치기·강도 최다 발생. 야간 특히 위험"),
            ("람블라스 거리 (La Rambla)", "매우 높음", "#CC0000", "관광객 밀집, 소매치기 극심. 가방 앞으로"),
            ("엘 라발 (El Raval)", "높음", "#FF4B4B", "야간 이동 위험, 강력범죄 주의"),
            ("에이샴플라 (Eixample)", "보통", "#FFA500", "상대적으로 안전, 소매치기 주의"),
            ("바르셀로네타 (Barceloneta)", "보통", "#FFA500", "해변 도난 주의, 귀중품 보관 철저"),
            ("몬주이크 (Montjuïc)", "낮음", "#4CAF50", "비교적 안전, 야간 주의"),
        ],
        "tips": [
            "💼 가방·지갑·핸드폰은 항상 앞으로 들고 이동하세요",
            "🌙 엘 라발, 고딕 지구 야간 단독 이동 자제",
            "📱 공공장소에서 스마트폰 노출 최소화",
            "🏧 ATM 이용 시 주변을 반드시 확인하세요",
            "🎒 배낭은 앞으로 메거나 잠금장치를 사용하세요",
        ],
    }
}

ALERTS = [
    {
        "time": "14:32",
        "type": "소매치기",
        "level": "높음",
        "color": "#FF4B4B",
        "location": "람블라스 거리",
        "detail": "람블라스 거리 중앙 구간에서 소매치기 3건 신고 접수. 가방을 앞으로 메고 이동하세요.",
        "source": "Mossos d'Esquadra (카탈루냐 경찰)",
    },
    {
        "time": "13:15",
        "type": "시위/집회",
        "level": "보통",
        "color": "#FFA500",
        "location": "카탈루냐 광장",
        "detail": "카탈루냐 독립 지지 집회 예정 (18:00~21:00). 광장 일대 교통 통제 예상.",
        "source": "Barcelona Ajuntament 공식 발표",
    },
    {
        "time": "11:50",
        "type": "강력범죄",
        "level": "보통",
        "color": "#FFA500",
        "location": "엘 라발 (El Raval)",
        "detail": "엘 라발 북부에서 강도 사건 1건 발생. 야간 단독 이동 자제 권고.",
        "source": "Mossos d'Esquadra",
    },
    {
        "time": "09:20",
        "type": "교통사고",
        "level": "낮음",
        "color": "#4CAF50",
        "location": "에이샴플라 (Eixample)",
        "detail": "그라시아 거리 교통사고로 일부 구간 정체. 우회 경로 이용 권장.",
        "source": "Barcelona 교통정보센터",
    },
]

CRIME_STATS = [
    {"type": "소매치기", "emoji": "👜", "level": "높음", "color": "#FF4B4B",
     "location": "람블라스 거리, 고딕 지구", "count": 28, "unit": "건"},
    {"type": "강력범죄", "emoji": "⚠️", "level": "보통", "color": "#FFA500",
     "location": "엘 라발, 우르키나오나 주변", "count": 7, "unit": "건"},
    {"type": "시위/집회", "emoji": "📢", "level": "보통", "color": "#FFA500",
     "location": "카탈루냐 광장, 그라시아 거리", "count": 2, "unit": "건(예정)"},
    {"type": "교통/사고", "emoji": "🚗", "level": "낮음", "color": "#4CAF50",
     "location": "에이샴플라 주요 도로", "count": 4, "unit": "건"},
]

LEGEND = [
    ("#CC0000", "매우 높음", "강력범죄, 테러, 무장강도 등"),
    ("#FF4B4B", "높음", "소매치기, 절도, 폭력 등"),
    ("#FFA500", "보통", "안전사고, 경미한 범죄 등"),
    ("#4CAF50", "낮음", "비교적 안전"),
]

# ===================== 히트맵 데이터 =====================

def get_heatmap_data():
    random.seed(42)
    hotspots = [
        # La Rambla - 매우 높음
        (41.3797, 2.1738, 1.0), (41.3810, 2.1735, 0.95),
        (41.3785, 2.1741, 0.90), (41.3800, 2.1736, 0.92),
        (41.3775, 2.1745, 0.88),
        # Barri Gòtic - 매우 높음
        (41.3833, 2.1764, 0.95), (41.3825, 2.1780, 0.90),
        (41.3840, 2.1755, 0.88), (41.3820, 2.1770, 0.92),
        (41.3845, 2.1760, 0.87), (41.3830, 2.1790, 0.83),
        # Plaça de Catalunya - 높음 (관광객 밀집)
        (41.3870, 2.1700, 0.82), (41.3875, 2.1695, 0.78),
        (41.3865, 2.1705, 0.80),
        # El Raval - 높음
        (41.3795, 2.1686, 0.75), (41.3785, 2.1675, 0.80),
        (41.3800, 2.1670, 0.72), (41.3810, 2.1680, 0.78),
        (41.3775, 2.1690, 0.70),
        # Barceloneta - 보통
        (41.3793, 2.1888, 0.50), (41.3780, 2.1900, 0.45),
        (41.3800, 2.1875, 0.48),
        # Eixample - 보통~낮음
        (41.3933, 2.1619, 0.35), (41.3920, 2.1640, 0.40),
        (41.3950, 2.1600, 0.30),
        # Montjuïc - 낮음
        (41.3641, 2.1594, 0.20), (41.3620, 2.1610, 0.18),
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
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=14,
        tiles="CartoDB positron",
    )

    HeatMap(
        get_heatmap_data(),
        radius=28,
        blur=22,
        max_zoom=18,
        gradient={"0.2": "#4CAF50", "0.45": "#FFC107", "0.65": "#FF9800", "0.82": "#FF4B4B", "1.0": "#CC0000"},
    ).add_to(m)

    folium.Circle(
        location=[center_lat, center_lng],
        radius=radius_m,
        color="#1565C0",
        weight=2,
        fill=False,
        dash_array="8",
    ).add_to(m)

    folium.Marker(
        location=[center_lat, center_lng],
        tooltip="📍 카탈루냐 광장 (기준점)",
        icon=folium.Icon(color="blue", icon="info-sign"),
    ).add_to(m)

    labels = {
        "고딕 지구": (41.3833, 2.1776),
        "El Raval": (41.3800, 2.1670),
        "에이샴플라": (41.3945, 2.1619),
        "람블라스": (41.3790, 2.1730),
        "바르셀로네타": (41.3780, 2.1900),
        "몬주이크": (41.3641, 2.1594),
    }
    for name, (lat, lng) in labels.items():
        folium.Marker(
            location=[lat, lng],
            tooltip=name,
            icon=folium.DivIcon(
                html=f'<div style="font-size:11px;color:#222;background:rgba(255,255,255,0.85);'
                     f'padding:2px 6px;border-radius:4px;white-space:nowrap;font-weight:600;">{name}</div>',
                icon_size=(100, 22),
                icon_anchor=(50, 11),
            ),
        ).add_to(m)

    return m


# ===================== 헤더 =====================

col_title, col_meta = st.columns([3, 1])
with col_title:
    st.markdown("# 🛡️ 안전여행")
    st.caption("해외여행 위험 정보 종합 서비스 | 스페인 · 바르셀로나")
with col_meta:
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("📅 2024.05.20 14:35 기준")

st.divider()

# ===================== 탭 =====================

tab_a, tab_b, tab_c, tab_plan = st.tabs(
    ["🗺️ A. 국가·지역 위험 브리핑", "🔔 B. 실시간 위험 알림", "📍 C. 여행지 위험지도", "📋 기획서"]
)

# ===================== TAB A: 브리핑 =====================

with tab_a:
    st.subheader("① 국가 선택")

    with st.spinner("외교부 여행경보 데이터 불러오는 중..."):
        all_countries = fetch_all_countries()

    if not all_countries:
        st.error("API 호출 실패. 잠시 후 다시 시도해주세요.")
    else:
        country_names = sorted(all_countries.keys())
        default_idx = country_names.index("스페인") if "스페인" in country_names else 0
        country = st.selectbox(
            f"국가 선택 (전체 {len(country_names)}개국)",
            country_names,
            index=default_idx,
            label_visibility="collapsed",
        )
        info = all_countries[country]

        # 경보 배지
        st.markdown(
            f"""
            <div style="background:{info['level_bg']}; border:2px solid {info['level_color']};
                        border-radius:12px; padding:18px 24px; margin:12px 0; display:flex; align-items:center; gap:20px;">
                <img src="{info['flag_url']}" width="60" style="border-radius:4px;">
                <div>
                    <div style="font-size:22px; font-weight:bold;">{info['level_icon']} {country} ({info['eng_name']})</div>
                    <div style="margin-top:6px; font-size:15px;">
                        경보 <strong>{info['level']}단계</strong> —
                        <span style="color:{info['level_color']}; font-weight:bold;">{info['level_text']}</span>
                        &nbsp;|&nbsp; 대상 지역: {info['region']} &nbsp;|&nbsp; 대륙: {info['continent']}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 경보 단계 설명
        level_descs = {
            "1": ["여행 시 신변 안전에 유의하세요.", "특별한 위험 요소는 없으나 기본적인 주의가 필요합니다."],
            "2": ["불필요한 여행을 자제하세요.", "신변 안전에 특별히 주의하고 여행 목적을 최소화하세요."],
            "3": ["즉시 출국을 검토하세요.", "체류 중인 경우 신속히 대피 준비를 하시기 바랍니다."],
            "4": ["여행이 금지된 국가입니다.", "현지 체류자는 즉시 출국하시기 바랍니다."],
        }
        for desc in level_descs.get(info["level"], []):
            st.warning(desc) if info["level"] in ("3","4") else st.info(desc)

        # 외교부 위험지도 이미지
        with st.expander("📌 외교부 공식 위험지도 보기", expanded=False):
            st.image(info["dang_map_url"], caption=f"{country} 외교부 공식 위험지도", use_container_width=True)

        st.divider()
        st.subheader("② 도시 선택 (바르셀로나 시범)")

        # 도시는 스페인 선택 시에만 샘플 데이터 제공
        if country == "스페인":
            city = st.selectbox("도시", ["바르셀로나", "마드리드", "세비야", "발렌시아"], label_visibility="collapsed")
        else:
            city = st.selectbox("도시", ["(준비 중 — 현재 바르셀로나만 지원)"], label_visibility="collapsed")
            city = None

        if city and city in CITY_INFO:
            cinfo = CITY_INFO[city]
            with st.expander(f"⚠️ {city} 안전 브리핑 — 전체 위험도: **{cinfo['overall']}**", expanded=True):
                st.markdown(
                    f"<span style='font-size:18px; font-weight:bold; color:{cinfo['overall_color']};'>"
                    f"전체 위험도: {cinfo['overall']}</span>",
                    unsafe_allow_html=True,
                )
                st.markdown("---")
                st.markdown("**구역별 위험 수준**")
                for name, level, color, detail in cinfo["districts"]:
                    dc1, dc2, dc3 = st.columns([3, 2, 4])
                    dc1.markdown(f"**{name}**")
                    dc2.markdown(f"<span style='color:{color}; font-weight:bold;'>{level}</span>", unsafe_allow_html=True)
                    dc3.markdown(detail)
                st.markdown("---")
                st.markdown("**여행 시 주의사항**")
                for tip in cinfo["tips"]:
                    st.info(tip)

# ===================== TAB B: 실시간 알림 =====================

with tab_b:
    st.subheader("🔔 바르셀로나 실시간 위험 알림")
    st.caption("현지 경찰청·언론사 데이터 기반 시뮬레이션 | 최근 업데이트: 14:35")

    col_filter, col_count = st.columns([2, 1])
    with col_filter:
        level_filter = st.selectbox("위험도 필터", ["전체", "높음", "보통", "낮음"], label_visibility="collapsed")
    with col_count:
        filtered = ALERTS if level_filter == "전체" else [a for a in ALERTS if a["level"] == level_filter]
        st.metric("알림 건수", f"{len(filtered)}건")

    for alert in filtered:
        st.markdown(
            f"""
            <div class="alert-card" style="border-left: 5px solid {alert['color']}; background:#fafafa;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                    <span style="font-weight:700; font-size:15px;">{alert['type']}</span>
                    <span style="background:{alert['color']}; color:white; padding:2px 10px;
                                 border-radius:12px; font-size:12px; font-weight:bold;">{alert['level']}</span>
                </div>
                <div style="color:#666; font-size:12px; margin-bottom:6px;">
                    🕐 오늘 {alert['time']} &nbsp;|&nbsp; 📍 {alert['location']}
                </div>
                <div style="margin-bottom:6px;">{alert['detail']}</div>
                <div style="color:#999; font-size:11px;">출처: {alert['source']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown("**알림 수신 설정 (시뮬레이션)**")
    s1, s2 = st.columns(2)
    with s1:
        st.toggle("현재 위치 기반 알림", value=True)
        st.toggle("방문 예정지 알림", value=True)
    with s2:
        st.slider("알림 반경 (km)", 0.5, 5.0, 1.0, 0.5)
        st.multiselect(
            "알림 유형 선택",
            ["소매치기", "강력범죄", "시위/집회", "교통사고", "재난"],
            default=["소매치기", "강력범죄", "재난"],
        )

# ===================== TAB C: 위험지도 =====================

with tab_c:
    # 헤더
    ch1, ch2 = st.columns([3, 2])
    with ch1:
        st.subheader("📍 여행지 위험지도")
        st.caption("현재 위치 기준 반경 위험도 시각화")
    with ch2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("🇪🇸 **스페인 · 바르셀로나**  \n📌 기준점: 카탈루냐 광장 (Plaça de Catalunya)")

    # 반경 선택
    radius_map = {"500m": 500, "1km": 1000, "2km": 2000, "3km": 3000}
    radius_label = st.radio("반경 설정", list(radius_map.keys()), index=1, horizontal=True)
    radius_m = radius_map[radius_label]

    # 지도 + 정보 패널
    col_map, col_info = st.columns([3, 2])

    with col_map:
        cinfo = CITY_INFO["바르셀로나"]
        m = build_map(cinfo["lat"], cinfo["lng"], radius_m)
        st_folium(m, width=None, height=500, returned_objects=[])

    with col_info:
        # 전체 위험도
        st.markdown("#### 전체 위험도 요약")
        st.markdown(
            f"""
            <div style="background:#fff5f5; border:2px solid #FF4B4B; border-radius:10px;
                        padding:16px; margin-bottom:12px;">
                <div style="font-size:20px; font-weight:bold; color:#FF4B4B;">⚠️ 높음</div>
                <div style="margin-top:8px; font-size:13px; color:#444;">
                    소매치기, 강력범죄 주의.<br>
                    특히 람블라스 거리, 고딕 지구 주의.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 범례
        st.markdown("#### 위험도 범례")
        for color, level, desc in LEGEND:
            st.markdown(
                f"""<div style="margin:6px 0; display:flex; align-items:center;">
                    <span style="display:inline-block; width:14px; height:14px; border-radius:50%;
                                 background:{color}; margin-right:10px; flex-shrink:0;"></span>
                    <span><strong>{level}</strong> — <span style="color:#666; font-size:13px;">{desc}</span></span>
                </div>""",
                unsafe_allow_html=True,
            )

        st.divider()

        # 기준점 정보
        st.markdown("#### 지도 기준점 정보")
        st.markdown(
            """
            <div style="background:#f0f4ff; border-radius:8px; padding:12px; font-size:13px;">
                📍 <strong>카탈루냐 광장</strong> (Plaça de Catalunya)<br>
                <span style="color:#666;">이 지점을 기준으로 선택한 반경 내<br>위험도를 시각화합니다.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 하단 범죄 통계
    st.divider()
    st.markdown(f"**위험 유형별 주요 발생 정보 ({radius_label} 반경, 최근 7일)**")
    cols = st.columns(4)
    for i, stat in enumerate(CRIME_STATS):
        with cols[i]:
            st.markdown(
                f"""
                <div class="crime-card" style="border-top: 4px solid {stat['color']};">
                    <div style="font-size:24px;">{stat['emoji']}</div>
                    <div style="font-weight:700; font-size:14px; margin-top:4px;">{stat['type']}</div>
                    <div style="color:{stat['color']}; font-weight:bold; font-size:13px; margin:4px 0;">
                        {stat['level']}
                    </div>
                    <div style="color:#666; font-size:11px; margin-bottom:8px;">{stat['location']}</div>
                    <div style="font-size:26px; font-weight:bold; color:#222;">{stat['count']}</div>
                    <div style="color:#999; font-size:11px;">{stat['unit']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ===================== TAB 기획서 =====================

with tab_plan:
    try:
        with open("안전여행_기획서.md", "r", encoding="utf-8") as f:
            plan_text = f.read()
        st.markdown(plan_text)
    except FileNotFoundError:
        st.error("기획서 파일(안전여행_기획서.md)을 찾을 수 없습니다.")

# ===================== 푸터 =====================
st.divider()
st.caption(
    "데이터 출처: 외교부 해외안전여행, 현지 뉴스 시뮬레이션 데이터 (최근 업데이트: 2024.05.20 14:35)  \n"
    "※ 본 정보는 참고용이며 실제 상황과 다를 수 있습니다."
)
