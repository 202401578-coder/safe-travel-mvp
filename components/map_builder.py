import math
import random
import folium
from folium.plugins import HeatMap
from branca.element import MacroElement
from jinja2 import Template
from config import LEGEND, RISK_COLORS

BARCELONA_HOTSPOTS = [
    (41.3797, 2.1738, 1.0), (41.3810, 2.1735, 0.95), (41.3785, 2.1741, 0.90),
    (41.3833, 2.1764, 0.95), (41.3825, 2.1780, 0.90), (41.3840, 2.1755, 0.88),
    (41.3870, 2.1700, 0.82), (41.3875, 2.1695, 0.78),
    (41.3795, 2.1686, 0.75), (41.3785, 2.1675, 0.80), (41.3800, 2.1670, 0.72),
    (41.3793, 2.1888, 0.50), (41.3780, 2.1900, 0.45),
    (41.3933, 2.1619, 0.35), (41.3920, 2.1640, 0.40),
    (41.3641, 2.1594, 0.20),
]

BARCELONA_LABELS = {
    "고딕 지구":    (41.3833, 2.1776),
    "El Raval":    (41.3800, 2.1670),
    "에이샴플라":   (41.3945, 2.1619),
    "람블라스":     (41.3790, 2.1730),
    "바르셀로네타": (41.3780, 2.1900),
    "몬주이크":     (41.3641, 2.1594),
}


def _generate_heatmap(city_lat: float, city_lng: float, risk_level: str) -> list:
    weights = {"매우 높음": 0.92, "높음": 0.78, "보통": 0.50, "낮음": 0.22}
    n_hot   = {"매우 높음": 9,    "높음": 7,    "보통": 5,    "낮음": 3}
    base_w  = weights.get(risk_level, 0.50)
    n       = n_hot.get(risk_level, 5)

    random.seed(int((city_lat * 1000 + city_lng * 1000)) % 9999)
    hotspots = [
        (city_lat + random.uniform(-0.013, 0.013),
         city_lng + random.uniform(-0.016, 0.016),
         base_w * random.uniform(0.72, 1.0))
        for _ in range(n)
    ]
    points = []
    for lat, lng, w in hotspots:
        points.append([lat, lng, w])
        for _ in range(9):
            points.append([
                lat + random.uniform(-0.006, 0.006),
                lng + random.uniform(-0.007, 0.007),
                max(0.05, w * random.uniform(0.35, 0.82)),
            ])
    return points


def _area_offset(center_lat, center_lng, index, total, radius_m):
    angle = (360 / max(total, 1)) * index - 90
    dist  = radius_m * 0.55
    dlat  = dist * math.cos(math.radians(angle)) / 111000
    dlng  = dist * math.sin(math.radians(angle)) / (111000 * math.cos(math.radians(center_lat)))
    return center_lat + dlat, center_lng + dlng


def build_city_map(city_name: str, city_lat: float, city_lng: float,
                   risk_level: str, radius_m: int, areas: list = None) -> folium.Map:
    areas     = areas or []
    badge_col = RISK_COLORS.get(risk_level, "#F97316")
    lat_d     = (radius_m / 111000) * 2.2
    lng_d     = (radius_m / (111000 * math.cos(math.radians(city_lat)))) * 2.2

    m = folium.Map(
        location=[city_lat, city_lng],
        zoom_start=14,
        tiles="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; CARTO',
        min_zoom=12,
        max_zoom=18,
    )

    # 히트맵
    if city_name == "바르셀로나":
        random.seed(42)
        pts = []
        for lat, lng, w in BARCELONA_HOTSPOTS:
            pts.append([lat, lng, w])
            for _ in range(7):
                pts.append([lat + random.uniform(-0.005, 0.005),
                             lng + random.uniform(-0.005, 0.005),
                             max(0.1, w * random.uniform(0.4, 0.85))])
    else:
        pts = _generate_heatmap(city_lat, city_lng, risk_level)

    HeatMap(pts, radius=30, blur=24, max_zoom=18,
            gradient={"0.2": "#22C55E", "0.45": "#FFC107",
                      "0.65": "#F97316", "0.82": "#EF4444", "1.0": "#CC0000"}).add_to(m)

    # 반경 원
    r_txt = f"반경 {radius_m // 1000}km" if radius_m >= 1000 else f"반경 {radius_m}m"
    folium.Circle(
        location=[city_lat, city_lng], radius=radius_m,
        color="#1565C0", weight=2, fill=True,
        fill_color="#1565C0", fill_opacity=0.04,
        dash_array="8", tooltip=r_txt,
    ).add_to(m)

    # 기준점 마커
    popup_html = (
        f'<div style="font-family:sans-serif;padding:4px;min-width:150px;">'
        f'<b style="font-size:14px;">📍 {city_name}</b><br>'
        f'<span style="color:{badge_col};font-weight:bold;">위험도: {risk_level}</span><br>'
        f'<span style="color:#888;font-size:12px;">{r_txt} 기준</span></div>'
    )
    folium.Marker(
        location=[city_lat, city_lng],
        tooltip=f"📍 {city_name} — 위험도: {risk_level}",
        popup=folium.Popup(popup_html, max_width=200),
        icon=folium.Icon(color="blue", icon="info-sign"),
    ).add_to(m)

    # 구역 레이블
    if city_name == "바르셀로나":
        labels = BARCELONA_LABELS
        for name, (lat, lng) in labels.items():
            folium.Marker(
                location=[lat, lng], tooltip=name,
                icon=folium.DivIcon(
                    html=(f'<div style="font-size:11px;color:#222;background:rgba(255,255,255,0.92);'
                          f'padding:3px 7px;border-radius:5px;white-space:nowrap;font-weight:700;'
                          f'box-shadow:0 1px 4px rgba(0,0,0,0.2);">{name}</div>'),
                    icon_size=(120, 24), icon_anchor=(60, 12),
                ),
            ).add_to(m)
    elif areas:
        for i, (aname, alvl, acol, _) in enumerate(areas[:8]):
            alat, alng = _area_offset(city_lat, city_lng, i, len(areas), radius_m)
            short = aname.split("(")[0].strip()
            folium.Marker(
                location=[alat, alng], tooltip=f"{short} — {alvl}",
                icon=folium.DivIcon(
                    html=(f'<div style="font-size:11px;color:#fff;background:{acol};opacity:0.92;'
                          f'padding:3px 7px;border-radius:5px;white-space:nowrap;font-weight:700;'
                          f'box-shadow:0 1px 4px rgba(0,0,0,0.25);">{short}</div>'),
                    icon_size=(120, 24), icon_anchor=(60, 12),
                ),
            ).add_to(m)

    # 지도 내 한국어 범례
    legend_macro = MacroElement()
    legend_macro._template = Template(
        "{% macro script(this, kwargs) %}\n"
        "var legend = L.control({position: 'bottomleft'});\n"
        "legend.onAdd = function(map) {\n"
        "  var div = L.DomUtil.create('div');\n"
        "  div.style.cssText = 'background:rgba(255,255,255,0.95);padding:10px 14px;"
        "border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.18);"
        "font-size:12px;line-height:2;pointer-events:none;';\n"
        "  div.innerHTML = '<b style=\"font-size:13px;display:block;margin-bottom:2px;\">위험도 범례</b>'\n"
        "    + '<span style=\"color:#CC0000;font-size:15px;\">●</span>&nbsp; 매우 높음<br>'\n"
        "    + '<span style=\"color:#EF4444;font-size:15px;\">●</span>&nbsp; 높음<br>'\n"
        "    + '<span style=\"color:#F97316;font-size:15px;\">●</span>&nbsp; 보통<br>'\n"
        "    + '<span style=\"color:#22C55E;font-size:15px;\">●</span>&nbsp; 낮음';\n"
        "  return div;\n"
        "};\n"
        "legend.addTo({{ this._parent.get_name() }});\n"
        "{% endmacro %}"
    )
    legend_macro.add_to(m)

    # 위험도 뱃지
    badge_macro = MacroElement()
    badge_macro._template = Template(
        "{% macro script(this, kwargs) %}\n"
        "var badge = L.control({position: 'topright'});\n"
        "badge.onAdd = function(map) {\n"
        "  var div = L.DomUtil.create('div');\n"
        f"  div.style.cssText = 'background:{badge_col};color:white;"
        "padding:7px 14px;border-radius:8px;font-weight:bold;"
        "font-size:13px;box-shadow:0 2px 8px rgba(0,0,0,0.25);pointer-events:none;';\n"
        f"  div.innerHTML = '⚠&nbsp; {city_name} &nbsp;·&nbsp; {risk_level}';\n"
        "  return div;\n"
        "};\n"
        "badge.addTo({{ this._parent.get_name() }});\n"
        "{% endmacro %}"
    )
    badge_macro.add_to(m)

    m.fit_bounds([[city_lat - lat_d, city_lng - lng_d],
                  [city_lat + lat_d, city_lng + lng_d]])
    return m


def get_city_crime_stats(city_data: dict) -> list:
    mult = {"매우 높음": 4.0, "높음": 2.5, "보통": 1.4, "낮음": 0.6}.get(
        city_data.get("risk", "보통"), 1.4)
    random.seed(int(abs(city_data.get("lat", 0) * 1000)) % 9999)
    result = []
    for name, emoji, base in [("소매치기","👜",14),("강력범죄","⚠️",4),("시위/집회","📢",2),("교통/사고","🚗",6)]:
        count = max(0, int(base * mult * random.uniform(0.75, 1.30)))
        level = "높음" if count >= 20 else "보통" if count >= 8 else "낮음"
        color = RISK_COLORS["높음"] if level == "높음" else RISK_COLORS["보통"] if level == "보통" else RISK_COLORS["낮음"]
        result.append({"type": name, "emoji": emoji, "level": level, "color": color, "count": count})
    return result
