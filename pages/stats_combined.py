import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from functions import fetch_player_stats, load_predictions, score_top3_pick, PLAYER_API_KEYS

st.set_page_config(page_title="Player Stats", page_icon="📊", layout="wide")

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
        .stat-category { font-family: 'Bebas Neue', sans-serif; font-size: 22px; letter-spacing: 4px; color: #FFD23F; margin-bottom: 8px; }
        .player-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,210,63,0.15); border-radius: 12px; padding: 14px 16px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
        .player-card:hover { border-color: rgba(255,210,63,0.4); background: rgba(255,210,63,0.05); }
        .player-info { flex: 1; padding: 0 12px; }
        .player-name { font-family: 'Bebas Neue', sans-serif; font-size: 18px; letter-spacing: 2px; color: white; }
        .player-team { font-size: 12px; color: rgba(255,255,255,0.45); letter-spacing: 1px; }
        .player-value { font-family: 'Bebas Neue', sans-serif; font-size: 26px; color: #FFD23F; }
        .pick-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,210,63,0.15); border-radius: 12px; padding: 14px 16px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
        .pick-name { font-family: 'Bebas Neue', sans-serif; font-size: 18px; letter-spacing: 2px; color: white; }
        .pick-sub { font-size: 12px; color: rgba(255,255,255,0.45); letter-spacing: 1px; }
        .pick-result { font-family: 'Bebas Neue', sans-serif; font-size: 22px; color: #FFD23F; }
        .person-name { font-family: 'Bebas Neue', sans-serif; font-size: 32px; letter-spacing: 4px; color: white; margin-bottom: 16px; }
        .points-box { font-family: 'Bebas Neue', sans-serif; font-size: 28px; letter-spacing: 3px; color: #FFD23F; margin-bottom: 20px; }
        .no-data { color: rgba(255,255,255,0.3); font-size: 14px; padding: 10px 0; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="page-title">📊 Player Stats</h1>', unsafe_allow_html=True)

ICONS = {
    "Golden Ball": "⭐", "Top Scorer": "⚽", "Top Assister": "🎯",
    "Yellow Cards": "🟨", "Golden Glove": "🧤",
}

@st.cache_data(ttl=300)
def get_stats():
    return fetch_player_stats()

@st.cache_data
def get_predictions():
    return load_predictions()

def render_live(col, key, title, stats):
    medals = ["🥇", "🥈", "🥉"]
    suffix = "%" if key == "_save_percentage" else ""
    players = stats.get(key, [])
    with col:
        st.markdown(f'<div class="stat-category">{title}</div>', unsafe_allow_html=True)
        if not players:
            st.markdown('<div class="no-data">No data yet</div>', unsafe_allow_html=True)
            return
        for i, player in enumerate(players[:3]):
            name = player.get("name", "")
            team = player.get("teamName", "")
            value = player.get("value", "")
            if isinstance(value, float):
                value = f"{value:.1f}"
            st.markdown(f"""
                <div class="player-card">
                    <div style="font-size:24px;width:32px">{medals[i]}</div>
                    <div class="player-info">
                        <div class="player-name">{name}</div>
                        <div class="player-team">{team}</div>
                    </div>
                    <div class="player-value">{value}{suffix}</div>
                </div>
            """, unsafe_allow_html=True)

try:
    stats = get_stats()
except Exception as e:
    st.error(f"Failed to load stats: {e}")
    st.stop()

categories = list(PLAYER_API_KEYS.keys())
tab1, tab2 = st.tabs(["📊 Live Stats", "🎯 My Picks"])

# ── Tab 1: Live Stats ─────────────────────────────────────────────────────────
with tab1:
    cols1 = st.columns(3)
    for col, cat in zip(cols1, categories[:3]):
        render_live(col, PLAYER_API_KEYS[cat], f"{ICONS[cat]} {cat}", stats)
    st.markdown("<br>", unsafe_allow_html=True)
    _, col1, col2, _ = st.columns([0.5, 2, 2, 0.5])
    for col, cat in zip([col1, col2], categories[3:]):
        render_live(col, PLAYER_API_KEYS[cat], f"{ICONS[cat]} {cat}", stats)

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
    person_picks = all_picks[selected_person]["player_picks"]

    st.markdown(f'<div class="person-name">{selected_person}</div>', unsafe_allow_html=True)

    total_points = sum(
        score_top3_pick(person_picks.get(cat, ""), stats.get(PLAYER_API_KEYS[cat], []))[0]
        for cat in categories
    )
    st.markdown(f'<div class="points-box">Total Points: {total_points}</div>', unsafe_allow_html=True)
    st.divider()

    def render_pick_col(col, cat):
        with col:
            api_key = PLAYER_API_KEYS[cat]
            picked = person_picks.get(cat, "")
            top3 = stats.get(api_key, [])
            top3_names = [p.get("name", "") for p in top3]
            pts, result = score_top3_pick(picked, top3)
            st.markdown(f'<div class="stat-category">{ICONS[cat]} {cat}</div>', unsafe_allow_html=True)
            st.markdown(f"""
                <div class="pick-card">
                    <div style="flex:1">
                        <div class="pick-name">{picked or "—"}</div>
                        <div class="pick-sub">Top 3: {", ".join(top3_names) if top3_names else "No data"}</div>
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
