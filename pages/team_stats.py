import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from functions import fetch_team_stats, load_predictions, score_top3_pick, TEAM_API_KEYS

st.set_page_config(page_title="Team Stats", page_icon="🏟️", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.cdnfonts.com/css/bebas-neue');
        [data-testid="stAppViewContainer"] { background-color: #0a1628; }
        [data-testid="stSidebar"] { background-color: #071020; }
        [data-testid="stSidebar"] span { color: white !important; font-size: 16px; letter-spacing: 1px; }
        [data-testid="stSidebar"] li:hover span { color: #FFD23F !important; }
        [data-testid="stSidebar"] li[aria-selected="true"] span { color: #FFD23F !important; }
        [data-testid="stSidebar"] li[aria-selected="true"] { background-color: rgba(255, 210, 63, 0.15); border-radius: 8px; }
        .page-title { font-family: 'Bebas Neue', sans-serif; font-size: 60px; letter-spacing: 6px; color: #FFD23F !important; text-align: center; margin-bottom: 40px; }
        .category-title { font-family: 'Bebas Neue', sans-serif; font-size: 22px; letter-spacing: 4px; color: #FFD23F; margin-bottom: 8px; }
        .team-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,210,63,0.15); border-radius: 12px; padding: 14px 16px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
        .team-card:hover { border-color: rgba(255,210,63,0.4); background: rgba(255,210,63,0.05); }
        .team-name { font-family: 'Bebas Neue', sans-serif; font-size: 18px; letter-spacing: 2px; color: white; }
        .team-value { font-family: 'Bebas Neue', sans-serif; font-size: 26px; color: #FFD23F; }
        .pick-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,210,63,0.15); border-radius: 12px; padding: 14px 16px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
        .pick-name { font-family: 'Bebas Neue', sans-serif; font-size: 18px; letter-spacing: 2px; color: white; }
        .pick-sub { font-size: 12px; color: rgba(255,255,255,0.45); letter-spacing: 1px; }
        .pick-result { font-family: 'Bebas Neue', sans-serif; font-size: 22px; color: #FFD23F; }
        .person-name { font-family: 'Bebas Neue', sans-serif; font-size: 32px; letter-spacing: 4px; color: white; margin-bottom: 16px; }
        .points-box { font-family: 'Bebas Neue', sans-serif; font-size: 28px; letter-spacing: 3px; color: #FFD23F; margin-bottom: 20px; }
        .no-data { color: rgba(255,255,255,0.3); font-size: 14px; padding: 10px 0; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="page-title">🏟️ Team Stats</h1>', unsafe_allow_html=True)

ICONS = {
    "Winning Team": "🏆", "Goals Per Match": "⚽",
    "Least Goals Conceded": "🛡️", "Set Piece Goals": "🎯", "Fouls Per Match": "🟨",
}

def get_value_medals(entries):
    """Build value->medal mapping handling ties by value."""
    seen_values = []
    for p in entries:
        v = p.get("value")
        if v not in seen_values:
            seen_values.append(v)
    medal_map = {0: "🥇", 1: "🥈", 2: "🥉"}
    return {v: medal_map.get(i, "") for i, v in enumerate(seen_values)}

@st.cache_data(ttl=300)
def get_stats():
    return fetch_team_stats()

@st.cache_data
def get_predictions():
    return load_predictions()

def render_live_category(col, category, stats):
    api_key = TEAM_API_KEYS[category]
    icon = ICONS[category]
    teams = stats.get(api_key, [])
    with col:
        st.markdown(f'<div class="category-title">{icon} {category}</div>', unsafe_allow_html=True)
        if not teams:
            st.markdown('<div class="no-data">No data yet</div>', unsafe_allow_html=True)
            return
        value_medals = get_value_medals(teams[:3])
        for team in teams[:3]:
            name = team.get("name", "")
            value = team.get("value", "")
            medal = value_medals.get(value, "")
            if isinstance(value, float):
                value = f"{value:.1f}"
            st.markdown(f"""
                <div class="team-card">
                    <div style="font-size:24px;width:32px">{medal}</div>
                    <div style="flex:1;padding:0 12px"><div class="team-name">{name}</div></div>
                    <div class="team-value">{value}</div>
                </div>
            """, unsafe_allow_html=True)

try:
    stats = get_stats()
except Exception as e:
    st.error(f"Failed to load stats: {e}")
    st.stop()

categories = list(TEAM_API_KEYS.keys())
tab1, tab2 = st.tabs(["📊 Live Stats", "🎯 My Picks"])

# ── Tab 1: Live Stats ─────────────────────────────────────────────────────────
with tab1:
    cols1 = st.columns(3)
    for col, cat in zip(cols1, categories[:3]):
        render_live_category(col, cat, stats)
    st.markdown("<br>", unsafe_allow_html=True)
    _, col1, col2, _ = st.columns([0.5, 2, 2, 0.5])
    for col, cat in zip([col1, col2], categories[3:]):
        render_live_category(col, cat, stats)

# ── Tab 2: My Picks ───────────────────────────────────────────────────────────
with tab2:
    try:
        all_picks = get_predictions()
    except FileNotFoundError:
        st.error("predictions.csv not found.")
        st.stop()
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        st.stop()

    people = list(all_picks.keys())
    selected_person = st.selectbox("Select a person", people)
    person_picks = all_picks[selected_person]["team_picks"]

    st.markdown(f'<div class="person-name">{selected_person}</div>', unsafe_allow_html=True)

    total_points = sum(
        score_top3_pick(person_picks.get(cat, ""), stats.get(TEAM_API_KEYS[cat], []))[0]
        for cat in categories
    )
    st.markdown(f'<div class="points-box">Total Points: {total_points}</div>', unsafe_allow_html=True)
    st.divider()

    def render_pick_col(col, cat):
        with col:
            api_key = TEAM_API_KEYS[cat]
            picked = person_picks.get(cat, "")
            top3 = stats.get(api_key, [])
            top3_names = [t.get("name", "") for t in top3]
            pts, result = score_top3_pick(picked, top3)
            st.markdown(f'<div class="category-title">{ICONS[cat]} {cat}</div>', unsafe_allow_html=True)
            st.markdown(f"""
                <div class="pick-card">
                    <div style="flex:1">
                        <div class="pick-name">{picked or "—"}</div>
                        <div class="pick-sub">Current top 3: {", ".join(top3_names) if top3_names else "No data"}</div>
                    </div>
                    <div class="pick-result">{result}</div>
                </div>
            """, unsafe_allow_html=True)

    cols1 = st.columns(3)
    for col, cat in zip(cols1, categories[:3]):
        render_pick_col(col, cat)
    st.markdown("<br>", unsafe_allow_html=True)
    _, col1, col2, _ = st.columns([0.5, 2, 2, 0.5])
    for col, cat in zip([col1, col2], categories[3:]):
        render_pick_col(col, cat)
