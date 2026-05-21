import requests
import streamlit as st


@st.cache_data(ttl=86400)
def geocode_city(city_query: str, country_eng: str = "") -> dict | None:
    try:
        q    = f"{city_query}, {country_eng}" if country_eng else city_query
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": q, "format": "json", "limit": 1, "addressdetails": 1},
            headers={"User-Agent": "SafeTravel-MVP/1.0"},
            timeout=8,
        )
        results = resp.json()
        if not results:
            return None
        r   = results[0]
        adr = r.get("address", {})
        return {
            "lat":      float(r["lat"]),
            "lng":      float(r["lon"]),
            "display":  r.get("display_name", city_query),
            "city_eng": adr.get("city") or adr.get("town") or adr.get("county") or city_query,
        }
    except Exception:
        return None
