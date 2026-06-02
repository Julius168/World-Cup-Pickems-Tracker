import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from functions import (
    fetch_groups, load_predictions, fetch_all_match_stats,
    score_range, score_zero_points_team, UNDERDOG_TEAMS
)

st.set_page_config(page_title="Special Picks", page_icon="🎲", layout="wide")

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
        .category-title { font-family: 'Bebas Neue', sans-serif; font-size: 20px; letter-spacing: 3px; color: #FFD23F; margin-bottom: 8px; }
        .info-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,210,63,0.15); border-radius: 12px; padding: 18px 20px; margin-bottom: 12px; }
        .info-card:hover { border-color: rgba(255,210,63,0.4); background: rgba(255,210,63,0.05); }
        .big-number { font-family: 'Bebas Neue', sans-serif; font-size: 52px; color: #FFD23F; line-height: 1; }
        .sub-label { font-size: 12px; color: rgba(255,255,255,0.45); letter-spacing: 2px; text-transform: uppercase; margin-top: 4px; }
        .team-pill { display: inline-block; background: rgba(255,210,63,0.1); border: 1px solid rgba(255,210,63,0.3); border-radius: 20px; padding: 4px 12px; margin: 4px; font-size: 13px; color: white; }
        .person-name { font-family: 'Bebas Neue', sans-serif; font-size: 32px; letter-spacing: 4px; color: white; margin-bottom: 16px; }
        .pick-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,210,63,0.15); border-radius: 12px; padding: 14px 16px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
        .pick-name { font-family: 'Bebas Neue', sans-serif; font-size: 18px; letter-spacing: 2px; color: white; }
        .pick-sub { font-size: 12px; color: rgba(255,255,255,0.45); letter-spacing: 1px; }
        .pick-result { font-family: 'Bebas Neue', sans-serif; font-size: 22px; color: #FFD23F; }
        .points-box { font-family: 'Bebas Neue', sans-serif; font-size: 28px; letter-spacing: 3px; color: #FFD23F; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="page-title">🎲 Special Picks</h1>', unsafe_allow_html=True)

@st.cache_data(ttl=300)
def get_groups():
    return fetch_groups()

@st.cache_data(ttl=3600)
def get_match_stats():
    return fetch_all_match_stats()

@st.cache_data
def get_predictions():
    return load_predictions()

group_standings, real_qualifiers, _ = get_groups()

# Flat group_data for zero points scoring
group_data = {}
for letter, d in group_standings.items():
    for t in d["full"]:
        group_data[t["name"]] = {"pts": t["pts"], "played": t["played"]}

# Underdog combined points
underdog_pts = {t: group_data.get(t, {}).get("pts", 0) for t in UNDERDOG_TEAMS}
combined_pts = sum(underdog_pts.values())
zero_pt_teams = [n for n, i in group_data.items() if i["pts"] == 0 and i["played"] > 0]

with st.spinner("Loading match data..."):
    match_stats = get_match_stats()

tab1, tab2 = st.tabs(["📊 Live Data", "🎯 My Picks"])

def render_pick(col, title, picked, actual_str, pts, result):
    with col:
        st.markdown(f'<div class="category-title">{title}</div>', unsafe_allow_html=True)
        st.markdown(f"""
            <div class="pick-card">
                <div style="flex:1">
                    <div class="pick-name">{picked or "—"}</div>
                    <div class="pick-sub">{actual_str}</div>
                </div>
                <div class="pick-result">{result}</div>
            </div>
        """, unsafe_allow_html=True)

# ── Tab 1: Live Data ──────────────────────────────────────────────────────────
with tab1:
    st.markdown("### Group Stage")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="category-title">🌍 Haiti, Curacao & Cape Verde — Combined Points</div>', unsafe_allow_html=True)
        st.markdown(f"""
            <div class="info-card">
                <div class="big-number">{combined_pts}</div>
                <div class="sub-label">Combined points so far</div>
                <div style="margin-top:12px">
                    {"".join([f'<span class="team-pill">{t}: {underdog_pts[t]} pts</span>' for t in UNDERDOG_TEAMS])}
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="category-title">❌ Teams With 0 Points</div>', unsafe_allow_html=True)
        st.markdown(f"""
            <div class="info-card">
                <div class="big-number">{len(zero_pt_teams)}</div>
                <div class="sub-label">Teams on 0 points (having played)</div>
                <div style="margin-top:12px">
                    {"".join([f'<span class="team-pill">{t}</span>' for t in zero_pt_teams]) if zero_pt_teams else '<span style="color:rgba(255,255,255,0.3)">None yet</span>'}
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("### Tournament Stats")
    col1, col2, col3, col4 = st.columns(4)

    for col, icon, label, key, sub in [
        (col1, "🥅", "Penalty Shootouts", "penalty_shootouts", "Total so far"),
        (col2, "💪", "Biggest Comeback",   "biggest_comeback",  match_stats["biggest_comeback_match"] or "—"),
        (col3, "⚽", "Most Goals in Game", "most_goals_game",   match_stats["most_goals_match"] or "—"),
        (col4, "⏱️", "Most Added Time",    "most_added_time",   match_stats["most_added_time_match"] or "—"),
    ]:
        with col:
            st.markdown(f'<div class="category-title">{icon} {label}</div>', unsafe_allow_html=True)
            st.markdown(f"""
                <div class="info-card">
                    <div class="big-number">{match_stats[key]}</div>
                    <div class="sub-label">{sub}</div>
                </div>
            """, unsafe_allow_html=True)

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
    person = all_picks[selected_person]

    st.markdown(f'<div class="person-name">{selected_person}</div>', unsafe_allow_html=True)

    # Score everything
    zp_pts, zp_res   = score_zero_points_team(person["zero_points_team"], group_data)
    ud_pts, ud_res   = score_range(person["underdog_points"], combined_pts)
    ps_pts, ps_res   = score_range(person["penalty_shootouts"], match_stats["penalty_shootouts"])
    bc_pts, bc_res   = score_range(person["biggest_comeback"],  match_stats["biggest_comeback"])
    mg_pts, mg_res   = score_range(person["most_goals_game"],   match_stats["most_goals_game"])
    at_pts, at_res   = score_range(person["most_added_time"],   match_stats["most_added_time"])

    total = zp_pts + ud_pts + ps_pts + bc_pts + mg_pts + at_pts
    st.markdown(f'<div class="points-box">Total Points: {total}</div>', unsafe_allow_html=True)
    st.divider()

    st.markdown("### Group Stage")
    col1, col2 = st.columns(2)
    render_pick(col1, "🌍 Underdog Combined Points", person["underdog_points"], f"Current total: {combined_pts}", ud_pts, ud_res)
    render_pick(col2, "❌ Team to Get 0 Points",     person["zero_points_team"],
                f"{group_data.get(person['zero_points_team'], {}).get('pts', '?')} pts", zp_pts, zp_res)

    st.markdown("### Tournament Stats")
    col1, col2, col3, col4 = st.columns(4)
    render_pick(col1, "🥅 Penalty Shootouts", person["penalty_shootouts"], f"Current: {match_stats['penalty_shootouts']}", ps_pts, ps_res)
    render_pick(col2, "💪 Biggest Comeback",  person["biggest_comeback"],  f"Current: {match_stats['biggest_comeback']}", bc_pts, bc_res)
    render_pick(col3, "⚽ Most Goals Game",   person["most_goals_game"],   f"Current: {match_stats['most_goals_game']}", mg_pts, mg_res)
    render_pick(col4, "⏱️ Most Added Time",   person["most_added_time"],   f"Current: {match_stats['most_added_time']} min", at_pts, at_res)
