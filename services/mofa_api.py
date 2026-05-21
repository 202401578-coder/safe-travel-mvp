import requests
import streamlit as st
from config import MOFA_API_KEY, ALARM_URL, WARN_URL, LEVEL_META


@st.cache_data(ttl=3600)
def fetch_all_countries() -> dict:
    try:
        resp = requests.get(
            ALARM_URL,
            params={"serviceKey": MOFA_API_KEY, "numOfRows": 300, "pageNo": 1},
            timeout=10,
        )
        items = resp.json()["response"]["body"]["items"]["item"]
        result = {}
        for item in items:
            meta = LEVEL_META.get(item["alarm_lvl"], {
                "text": "정보없음", "color": "#999", "bg": "#f5f5f5", "icon": "⚪", "badge": "#999"
            })
            result[item["country_nm"]] = {
                "eng_name":    item["country_eng_nm"],
                "iso":         item["country_iso_alp2"],
                "level":       item["alarm_lvl"],
                "level_text":  meta["text"],
                "level_color": meta["color"],
                "level_bg":    meta["bg"],
                "level_icon":  meta["icon"],
                "level_badge": meta["badge"],
                "continent":   item["continent_nm"],
                "region":      item["remark"],
                "flag_url":    item["flag_download_url"],
                "dang_map_url": item["dang_map_download_url"],
            }
        return result
    except Exception:
        return {}


@st.cache_data(ttl=3600)
def fetch_warning_detail(country_name: str) -> dict | None:
    try:
        resp = requests.get(
            WARN_URL,
            params={"serviceKey": MOFA_API_KEY, "numOfRows": 300, "pageNo": 1},
            timeout=10,
        )
        items = resp.json()["response"]["body"]["items"]["item"]
        return next((i for i in items if i["country_name"] == country_name), None)
    except Exception:
        return None


@st.cache_data(ttl=3600)
def fetch_global_stats() -> dict:
    """TravelWarningServiceV3 기반 전 세계 경보 현황"""
    try:
        resp = requests.get(
            WARN_URL,
            params={"serviceKey": MOFA_API_KEY, "numOfRows": 300, "pageNo": 1},
            timeout=10,
        )
        items = resp.json()["response"]["body"]["items"]["item"]

        stats = {"ban": [], "limita": [], "control": [], "attention": [], "total": len(items)}

        for item in items:
            entry = {"name": item["country_name"], "flag": item.get("img_url", "")}
            if item.get("ban_yna") or item.get("ban_yn_partial"):
                stats["ban"].append(entry)
            elif item.get("limita") or item.get("limita_partial"):
                stats["limita"].append(entry)
            elif item.get("control") or item.get("control_partial"):
                stats["control"].append(entry)
            elif item.get("attention") or item.get("attention_partial"):
                stats["attention"].append(entry)

        return stats
    except Exception:
        return {}
