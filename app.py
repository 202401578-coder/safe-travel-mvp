import streamlit as st
from streamlit_folium import st_folium

from config import LEGEND
from data.city_db import CITY_DB
from services.mofa_api import fetch_all_countries, fetch_warning_detail, fetch_global_stats
from services.news_service import fetch_safety_news, translate_to_korean
from services.geo_service import geocode_city
from components.map_builder import build_city_map, get_city_crime_stats

# ── 페이지 설정 ───────────────────────────────────────────────────
st.set_page_config(
    page_title="안전여행",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── 전역 CSS ─────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');

  html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
  .block-container { padding: 1.5rem 2rem 2rem; max-width: 1400px; }

  /* 헤더 */
  .app-header {
    background: linear-gradient(135deg, #0f2942 0%, #1a4a7a 100%);
    border-radius: 16px; padding: 24px 32px; margin-bottom: 24px;
    display: flex; align-items: center; justify-content: space-between;
    box-shadow: 0 4px 20px rgba(15,41,66,0.3);
  }
  .app-title { color: white; font-size: 28px; font-weight: 700; margin: 0; }
  .app-subtitle { color: rgba(255,255,255,0.7); font-size: 14px; margin-top: 4px; }
  .app-badge {
    background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.3);
    border-radius: 20px; padding: 6px 16px; color: white; font-size: 13px;
  }

  /* 카드 */
  .stat-card {
    background: white; border-radius: 12px; padding: 20px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08); border: 1px solid #f0f0f0;
    text-align: center; transition: transform 0.2s;
  }
  .stat-card:hover { transform: translateY(-2px); box-shadow: 0 4px 20px rgba(0,0,0,0.12); }
  .stat-number { font-size: 36px; font-weight: 700; line-height: 1.1; }
  .stat-label  { font-size: 13px; color: #666; margin-top: 4px; }

  /* 경보 뱃지 */
  .level-badge {
    display: inline-block; padding: 4px 12px; border-radius: 20px;
    font-size: 12px; font-weight: 700; color: white;
  }

  /* 알림 카드 */
  .news-card {
    background: #fafafa; border-radius: 10px; padding: 14px 16px;
    margin: 8px 0; border-left: 4px solid;
    transition: box-shadow 0.2s;
  }
  .news-card:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.1); }

  /* 범죄 통계 카드 */
  .crime-card {
    background: white; border-radius: 12px; padding: 18px;
    text-align: center; border: 1px solid #f0f0f0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  }

  /* 구역 행 */
  .area-row {
    display: flex; align-items: center; padding: 8px 12px;
    background: #f8f9fa; border-radius: 8px; margin: 4px 0;
  }

  /* 팁 박스 */
  .tip-box {
    background: #EFF6FF; border-left: 3px solid #3B82F6;
    border-radius: 6px; padding: 10px 14px; margin: 4px 0;
    font-size: 14px;
  }

  /* 국가 배지 */
  .country-card {
    background: white; border-radius: 12px; padding: 16px 20px;
    border: 2px solid; margin: 12px 0;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  }

  /* 탭 스타일 */
  .stTabs [data-baseweb="tab-list"] { gap: 4px; }
  .stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0; padding: 10px 20px;
    font-weight: 500; font-size: 14px;
  }

  /* 섹션 헤더 */
  .section-header {
    font-size: 18px; font-weight: 700; color: #1a1a2e;
    margin: 20px 0 12px; display: flex; align-items: center; gap: 8px;
  }

  /* 여행금지 국가 리스트 */
  .ban-country {
    display: inline-flex; align-items: center; gap: 6px;
    background: #FFF5F5; border: 1px solid #FED7D7;
    border-radius: 8px; padding: 4px 10px; margin: 3px;
    font-size: 13px;
  }

  /* 분리선 개선 */
  hr { border-color: #f0f0f0; margin: 16px 0; }

  /* 숨기기 */
  #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── 세션 상태 ─────────────────────────────────────────────────────
defaults = {
    "selected_country":     "스페인",
    "selected_country_eng": "Spain",
    "selected_city":        "바르셀로나",
    "city_lat":             41.3870,
    "city_lng":             2.1700,
    "city_eng":             "Barcelona",
    "city_risk":            "높음",
    "city_risk_color":      "#EF4444",
    "city_areas":           [],
    "city_tips":            [],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── 헤더 ─────────────────────────────────────────────────────────
sel_c = st.session_state.selected_country
sel_city = st.session_state.selected_city
st.markdown(
    f"""<div class="app-header">
        <div>
            <div class="app-title">🛡️ 안전여행</div>
            <div class="app-subtitle">외교부 공식 데이터 기반 해외여행 안전 정보 서비스</div>
        </div>
        <div class="app-badge">📍 {sel_c} &nbsp;·&nbsp; {sel_city}</div>
    </div>""",
    unsafe_allow_html=True,
)

# ── 탭 ───────────────────────────────────────────────────────────
tab_a, tab_b, tab_c, tab_plan = st.tabs([
    "🗺️  국가·지역 브리핑",
    "🔔  실시간 위험 알림",
    "📍  여행지 위험지도",
    "📋  기획서",
])

# ════════════════════════════════════════════════════════════════
# TAB A — 국가·지역 위험 브리핑
# ════════════════════════════════════════════════════════════════
with tab_a:
    with st.spinner("외교부 여행경보 데이터 불러오는 중..."):
        all_countries = fetch_all_countries()
        global_stats  = fetch_global_stats()

    if not all_countries:
        st.error("API 호출에 실패했습니다. 잠시 후 다시 시도해주세요.")
        st.stop()

    # ── 글로벌 현황 대시보드 ──────────────────────────────────────
    st.markdown('<div class="section-header">🌐 전 세계 여행경보 현황</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    stats_data = [
        (c1, len(global_stats.get("ban", [])),      "🚫 여행금지", "#7C3AED", "#F3E5F5"),
        (c2, len(global_stats.get("limita", [])),   "🔴 출국권고", "#EF4444", "#FFEBEE"),
        (c3, len(global_stats.get("control", [])),  "🟠 여행자제", "#F97316", "#FFF3E0"),
        (c4, len(global_stats.get("attention", [])), "🟡 여행유의", "#F59E0B", "#FFFDE7"),
    ]
    for col, count, label, color, bg in stats_data:
        with col:
            st.markdown(
                f"""<div class="stat-card" style="border-top: 4px solid {color};">
                    <div class="stat-number" style="color:{color};">{count}</div>
                    <div class="stat-label">{label}</div>
                    <div style="font-size:11px;color:#999;margin-top:2px;">개국</div>
                </div>""",
                unsafe_allow_html=True,
            )

    # 여행금지 국가 목록
    ban_list = global_stats.get("ban", [])
    if ban_list:
        st.markdown("**🚫 현재 여행금지 국가**")
        html = "".join(
            f'<span class="ban-country">'
            f'<img src="{c["flag"]}" height="14" style="border-radius:2px;"> {c["name"]}'
            f'</span>'
            for c in ban_list
        )
        st.markdown(f'<div style="margin:8px 0 16px;">{html}</div>', unsafe_allow_html=True)

    st.divider()

    # ── ① 국가 선택 ──────────────────────────────────────────────
    st.markdown('<div class="section-header">① 국가 선택</div>', unsafe_allow_html=True)

    country_names = sorted(all_countries.keys())
    search = st.text_input(
        "🔍 국가 검색",
        placeholder="예: 스페인, Japan, France...",
        label_visibility="collapsed",
    )
    filtered = (
        [n for n in country_names
         if search.strip().lower() in n.lower()
         or search.strip().lower() in all_countries[n]["eng_name"].lower()]
        if search.strip() else country_names
    )
    if not filtered:
        st.warning("검색 결과가 없습니다.")
        st.stop()

    default_idx = filtered.index("스페인") if "스페인" in filtered else 0
    country = st.selectbox(
        f"국가 ({len(filtered)}개)",
        filtered, index=default_idx,
        label_visibility="collapsed",
    )
    st.session_state.selected_country     = country
    st.session_state.selected_country_eng = all_countries[country]["eng_name"]
    info = all_countries[country]

    # 여행금지 강조 배너
    if info["level"] in ("3", "4"):
        st.error(f"{'🚫 여행금지 국가입니다. 방문을 즉시 중단하세요.' if info['level']=='4' else '🔴 출국권고 국가입니다. 즉시 출국을 검토하세요.'}")

    # 국가 카드
    st.markdown(
        f"""<div class="country-card" style="border-color:{info['level_color']};">
            <div style="display:flex;align-items:center;gap:16px;">
                <img src="{info['flag_url']}" height="48" style="border-radius:6px;box-shadow:0 2px 6px rgba(0,0,0,0.15);">
                <div style="flex:1;">
                    <div style="font-size:20px;font-weight:700;">{country}
                        <span style="font-size:15px;color:#666;font-weight:400;">({info['eng_name']})</span>
                    </div>
                    <div style="margin-top:6px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
                        <span class="level-badge" style="background:{info['level_badge']};">
                            {info['level_icon']} {info['level']}단계 · {info['level_text']}
                        </span>
                        <span style="color:#888;font-size:13px;">대상: {info['region']}</span>
                        <span style="color:#888;font-size:13px;">대륙: {info['continent']}</span>
                    </div>
                </div>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    # 지역별 세부 경보
    detail = fetch_warning_detail(country)
    if detail:
        warn_rows = [
            ("🟡 여행유의", detail.get("attention_note") or detail.get("attention_partial", "")),
            ("🟠 여행자제", detail.get("control_note")   or detail.get("control_partial", "")),
            ("🔴 출국권고", detail.get("limita_note")    or detail.get("limita_partial", "")),
            ("🚫 여행금지", detail.get("ban_note")       or detail.get("ban_yn_partial", "")),
        ]
        visible = [(l, r) for l, r in warn_rows if r]
        if visible:
            with st.expander("📌 지역별 세부 경보 현황", expanded=True):
                for label, region in visible:
                    st.markdown(f"**{label}** — {region}")

    level_msg = {
        "1": ("info", "여행 시 신변 안전에 유의하세요. 기본 안전 수칙을 지키면 비교적 안전합니다."),
        "2": ("warning", "불필요한 여행을 자제하세요. 신변 안전에 특별히 주의하세요."),
        "3": ("error", "즉시 출국을 검토하세요. 현지 대사관에 즉시 연락하세요."),
        "4": ("error", "여행이 금지된 국가입니다. 현지 체류자는 즉시 출국하세요."),
    }.get(info["level"])
    if level_msg:
        getattr(st, level_msg[0])(level_msg[1])

    with st.expander("🗺️ 외교부 공식 위험지도", expanded=False):
        st.image(info["dang_map_url"], caption=f"{country} 외교부 공식 위험지도", use_container_width=True)

    st.divider()

    # ── ② 도시 선택 ──────────────────────────────────────────────
    st.markdown('<div class="section-header">② 도시 선택</div>', unsafe_allow_html=True)

    country_risk_map = {"1": ("낮음", "#22C55E"), "2": ("보통", "#F97316"),
                        "3": ("높음", "#EF4444"), "4": ("매우 높음", "#CC0000")}
    fallback_risk, fallback_color = country_risk_map.get(info["level"], ("보통", "#F97316"))

    db_cities = list(CITY_DB.get(country, {}).keys())
    col_sel, col_txt = st.columns([1, 1])

    with col_sel:
        if db_cities:
            chosen = st.selectbox("DB 도시", db_cities + ["✏️ 직접 입력"], label_visibility="visible")
        else:
            chosen = "✏️ 직접 입력"
            st.caption("해당 국가는 상세 DB 미보유")

    with col_txt:
        custom_input = st.text_input(
            "도시 직접 입력 (한글·영어)",
            placeholder="예: 빌바오, Bilbao, Cairo",
        )

    city_query = custom_input.strip() or (chosen if chosen != "✏️ 직접 입력" else "")

    if city_query:
        st.session_state.selected_city = city_query
        use_db = (not custom_input.strip()) and city_query in CITY_DB.get(country, {})

        if use_db:
            cinfo = CITY_DB[country][city_query]
            st.session_state.update({
                "city_lat": cinfo["lat"], "city_lng": cinfo["lng"],
                "city_eng": cinfo.get("eng", city_query),
                "city_risk": cinfo["risk"], "city_risk_color": cinfo["risk_color"],
                "city_areas": cinfo.get("areas", []), "city_tips": cinfo.get("tips", []),
            })
            risk_col = cinfo["risk_color"]
            with st.expander(
                f"⚠️ {city_query} ({cinfo['eng']}) — 위험도: {cinfo['risk']}",
                expanded=True,
            ):
                st.markdown(
                    f"<span style='font-size:17px;font-weight:700;color:{risk_col};'>"
                    f"전체 위험도: {cinfo['risk']}</span>",
                    unsafe_allow_html=True,
                )
                if cinfo.get("areas"):
                    st.markdown("**구역별 위험 수준**")
                    for aname, alvl, acol, adet in cinfo["areas"]:
                        st.markdown(
                            f"""<div class="area-row">
                                <div style="flex:1;font-size:13px;"><b>{aname}</b>
                                <span style="color:#888;"> — {adet}</span></div>
                                <span class="level-badge" style="background:{acol};font-size:11px;">{alvl}</span>
                            </div>""",
                            unsafe_allow_html=True,
                        )
                if cinfo.get("tips"):
                    st.markdown("**여행 시 주의사항**")
                    for tip in cinfo["tips"]:
                        st.markdown(f'<div class="tip-box">{tip}</div>', unsafe_allow_html=True)
        else:
            with st.spinner(f"'{city_query}' 위치 검색 중..."):
                geo = geocode_city(city_query, all_countries[country]["eng_name"])
            if geo:
                st.session_state.update({
                    "city_lat": geo["lat"], "city_lng": geo["lng"],
                    "city_eng": geo["city_eng"],
                    "city_risk": fallback_risk, "city_risk_color": fallback_color,
                    "city_areas": [], "city_tips": [],
                })
                st.success(f"📍 위치 확인: **{geo['display'].split(',')[0]}** (위도 {geo['lat']:.4f}, 경도 {geo['lng']:.4f})")
                lvl_tips = {
                    "1": ["✅ 기본 안전 수칙을 지키세요.", "📱 귀중품 관리에 주의하세요.", "🏥 여행자 보험 가입 권장"],
                    "2": ["⚠️ 꼭 필요한 경우에만 방문하세요.", "📞 대사관 연락처를 저장하세요.", "🏥 여행자 보험 필수 가입"],
                    "3": ["🔴 즉시 출국을 검토하세요.", "🚨 한국 대사관에 즉시 연락하세요."],
                    "4": ["🚫 여행 금지 국가입니다.", "🚨 영사콜센터 (+82-2-3210-0404) 즉시 연락"],
                }
                with st.expander(f"⚠️ {city_query} — 위험도: {fallback_risk} (국가 경보 기반)", expanded=True):
                    for tip in lvl_tips.get(info["level"], []):
                        st.markdown(f'<div class="tip-box">{tip}</div>', unsafe_allow_html=True)
            else:
                st.warning("위치를 찾을 수 없습니다. 영어 도시명으로 다시 시도해보세요.")
    else:
        st.caption("위에서 도시를 선택하거나 직접 입력하면 상세 정보가 표시됩니다.")


# ════════════════════════════════════════════════════════════════
# TAB B — 실시간 위험 알림
# ════════════════════════════════════════════════════════════════
with tab_b:
    sel_country = st.session_state.selected_country
    sel_eng     = st.session_state.selected_country_eng
    sel_city    = st.session_state.selected_city
    city_eng    = CITY_DB.get(sel_country, {}).get(sel_city, {}).get("eng", sel_city)

    hdr1, hdr2 = st.columns([3, 1])
    with hdr1:
        st.markdown(
            f'<div class="section-header">🔔 실시간 위험 알림</div>'
            f'<p style="color:#888;font-size:13px;margin-top:-8px;">'
            f'현지 뉴스 RSS 실시간 수집 · 한국어 자동 번역 | '
            f'<b>{sel_country} · {sel_city}</b> ({city_eng})</p>',
            unsafe_allow_html=True,
        )
    with hdr2:
        if st.button("🔄 새로고침", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    st.markdown(
        f"""<div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:10px;
            padding:10px 16px;font-size:13px;margin-bottom:16px;">
            📍 <b>A탭 선택 여행지</b>: {sel_country} · {sel_city} ({city_eng}) &nbsp;|&nbsp;
            <span style="color:#888;">A탭에서 변경하면 자동 업데이트됩니다.</span>
        </div>""",
        unsafe_allow_html=True,
    )

    with st.spinner("현지 안전 뉴스 수집 중..."):
        news_items = fetch_safety_news(sel_country, sel_eng, sel_city, city_eng)

    HIGH_KW = {"terror","attack","shooting","explosion","killed","dead","bomb","hostage"}
    MID_KW  = {"crime","robbery","arrest","protest","theft","scam","warning","incident"}

    if news_items:
        st.markdown(f"**{sel_city} 최신 안전 뉴스 ({len(news_items)}건) — 한국어 번역**")
        for article in news_items:
            orig    = article["title"]
            title_l = orig.lower()
            if any(k in title_l for k in HIGH_KW):
                lc, lt = "#EF4444", "높음"
            elif any(k in title_l for k in MID_KW):
                lc, lt = "#F97316", "보통"
            else:
                lc, lt = "#F59E0B", "주의"

            ko_title = translate_to_korean(orig)
            st.markdown(
                f"""<div class="news-card" style="border-color:{lc};">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                        <span style="font-weight:600;font-size:14px;line-height:1.5;flex:1;">{ko_title}</span>
                        <span class="level-badge" style="background:{lc};margin-left:10px;flex-shrink:0;">{lt}</span>
                    </div>
                    <div style="color:#aaa;font-size:11px;font-style:italic;margin-top:3px;">{orig}</div>
                    <div style="color:#999;font-size:11px;margin-top:6px;">
                        📰 {article['source']} &nbsp;|&nbsp;
                        🕐 {article['pub'][:16] if article['pub'] else ''} &nbsp;|&nbsp;
                        <a href="{article['link']}" target="_blank" style="color:#3B82F6;">원문 보기 →</a>
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )
    else:
        st.success(f"✅ 현재 {sel_city}({city_eng}) 관련 긴급 안전 뉴스가 없습니다.")

    st.divider()
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


# ════════════════════════════════════════════════════════════════
# TAB C — 여행지 위험지도
# ════════════════════════════════════════════════════════════════
with tab_c:
    sel_country = st.session_state.selected_country
    sel_city    = st.session_state.selected_city
    city_lat    = st.session_state.city_lat
    city_lng    = st.session_state.city_lng
    city_eng    = st.session_state.city_eng
    risk_lvl    = st.session_state.city_risk
    risk_col    = st.session_state.city_risk_color
    city_areas  = st.session_state.city_areas

    risk_bg = {"매우 높음": "#FFF0F0", "높음": "#FFF5F5", "보통": "#FFFBF0", "낮음": "#F0FFF4"}.get(risk_lvl, "#fff")
    risk_msg = {"매우 높음": "강력범죄·테러 위협. 방문을 재고하세요.",
                "높음":     "소매치기·강력범죄 주의. 야간 단독 이동 자제.",
                "보통":     "기본 안전 수칙 준수 시 비교적 안전합니다.",
                "낮음":     "비교적 안전한 도시입니다."}.get(risk_lvl, "")

    # 헤더 행
    mh1, mh2 = st.columns([3, 2])
    with mh1:
        st.markdown(
            f'<div class="section-header">📍 {sel_city} ({city_eng}) 위험지도</div>'
            f'<p style="color:#888;font-size:13px;margin-top:-8px;">{sel_country} · 위험도 히트맵 시각화</p>',
            unsafe_allow_html=True,
        )
    with mh2:
        radius_map   = {"500m": 500, "1km": 1000, "2km": 2000, "3km": 3000}
        radius_label = st.radio("반경", list(radius_map.keys()), index=1, horizontal=True)
        radius_m     = radius_map[radius_label]

    col_map, col_info = st.columns([3, 2])

    with col_map:
        m = build_city_map(sel_city, city_lat, city_lng, risk_lvl, radius_m, areas=city_areas)
        st_folium(m, width=None, height=520, returned_objects=[])

    with col_info:
        # 위험도 요약
        st.markdown(
            f"""<div style="background:{risk_bg};border:2px solid {risk_col};
                border-radius:12px;padding:16px 20px;margin-bottom:14px;">
                <div style="font-size:22px;font-weight:700;color:{risk_col};">⚠️ {risk_lvl}</div>
                <div style="font-size:13px;color:#555;margin-top:6px;">{risk_msg}</div>
            </div>""",
            unsafe_allow_html=True,
        )

        # 구역별 위험도
        if city_areas:
            st.markdown("**구역별 위험도**")
            for aname, alvl, acol, adet in city_areas:
                st.markdown(
                    f"""<div class="area-row" style="border-left:4px solid {acol};">
                        <div style="flex:1;font-size:12px;">
                            <b>{aname.split("(")[0].strip()}</b><br>
                            <span style="color:#888;">{adet}</span>
                        </div>
                        <span class="level-badge" style="background:{acol};font-size:11px;">{alvl}</span>
                    </div>""",
                    unsafe_allow_html=True,
                )
            st.markdown("")

        # 범례
        st.markdown("**위험도 범례**")
        for color, level, desc in LEGEND:
            st.markdown(
                f"""<div style="display:flex;align-items:center;margin:5px 0;">
                    <span style="display:inline-block;width:12px;height:12px;border-radius:50%;
                                 background:{color};margin-right:10px;flex-shrink:0;"></span>
                    <span style="font-size:13px;"><b>{level}</b>
                    <span style="color:#777;"> — {desc}</span></span>
                </div>""",
                unsafe_allow_html=True,
            )

        st.divider()
        st.markdown(
            f"""<div style="background:#F0F4FF;border-radius:8px;padding:12px;font-size:13px;">
                📍 <b>{sel_city}</b> ({city_eng})<br>
                <span style="color:#666;">A탭에서 도시 변경 시 자동 업데이트됩니다.</span>
            </div>""",
            unsafe_allow_html=True,
        )

    # 하단 범죄 통계
    st.divider()
    st.markdown(f"**{sel_city} 위험 유형별 발생 현황 ({radius_label} 반경, 추정치)**")
    crime_stats = get_city_crime_stats({
        "risk": risk_lvl, "lat": city_lat, "lng": city_lng
    })
    cols = st.columns(4)
    for i, s in enumerate(crime_stats):
        with cols[i]:
            st.markdown(
                f"""<div class="crime-card" style="border-top:4px solid {s['color']};">
                    <div style="font-size:26px;">{s['emoji']}</div>
                    <div style="font-weight:700;font-size:14px;margin-top:6px;">{s['type']}</div>
                    <span class="level-badge" style="background:{s['color']};font-size:11px;margin:6px 0;display:inline-block;">{s['level']}</span>
                    <div style="font-size:28px;font-weight:700;color:#1a1a2e;">{s['count']}</div>
                    <div style="color:#999;font-size:11px;">건 (최근 7일)</div>
                </div>""",
                unsafe_allow_html=True,
            )


# ════════════════════════════════════════════════════════════════
# TAB 기획서
# ════════════════════════════════════════════════════════════════
with tab_plan:
    try:
        with open("안전여행_기획서.md", "r", encoding="utf-8") as f:
            st.markdown(f.read())
    except FileNotFoundError:
        st.error("기획서 파일을 찾을 수 없습니다.")

# ── 푸터 ─────────────────────────────────────────────────────────
st.markdown(
    """<div style="text-align:center;padding:20px;color:#aaa;font-size:12px;margin-top:16px;">
        데이터 출처: 외교부 해외안전여행 API · Google 뉴스 RSS · OpenStreetMap<br>
        ※ 본 정보는 참고용이며 실제 상황과 다를 수 있습니다.
    </div>""",
    unsafe_allow_html=True,
)
