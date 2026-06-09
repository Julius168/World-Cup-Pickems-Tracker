import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from functions import (
    fetch_groups, load_predictions, fetch_all_match_stats,
    score_range, score_zero_points_team, score_perfect_group,
    score_fav_eliminated, score_underdog_qualifies,
    UNDERDOG_TEAMS, FAVOURITES, UNDERDOGS
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
        .team-pill-red { display: inline-block; background: rgba(255,80,80,0.1); border: 1px solid rgba(255,80,80,0.3); border-radius: 20px; padding: 4px 12px; margin: 4px; font-size: 13px; color: #ff8080; }
        .team-pill-green { display: inline-block; background: rgba(42,213,114,0.1); border: 1px solid rgba(42,213,114,0.3); border-radius: 20px; padding: 4px 12px; margin: 4px; font-size: 13px; color: #2ad572; }
        .person-name { font-family: 'Bebas Neue', sans-serif; font-size: 32px; letter-spacing: 4px; color: white; margin-bottom: 16px; }
        .pick-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,210,63,0.15); border-radius: 12px; padding: 14px 16px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
        .pick-name { font-family: 'Bebas Neue', sans-serif; font-size: 18px; letter-spacing: 2px; color: white; }
        .pick-sub { font-size: 12px; color: rgba(255,255,255,0.45); letter-spacing: 1px; }
        .pick-result { font-family: 'Bebas Neue', sans-serif; font-size: 22px; color: #FFD23F; }
        .points-box { font-family: 'Bebas Neue', sans-serif; font-size: 28px; letter-spacing: 3px; color: #FFD23F; margin-bottom: 20px; }
        .section-header { font-family: 'Bebas Neue', sans-serif; font-size: 26px; letter-spacing: 4px; color: white; margin: 24px 0 12px; }
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

# Flat group_data
group_data = {}
for letter, d in group_standings.items():
    for t in d["full"]:
        group_data[t["name"]] = {"pts": t["pts"], "played": t["played"],
                                  "wins": t["wins"], "qualColor": t.get("qualColor")}

# Underdog combined points
underdog_pts = {t: group_data.get(t, {}).get("pts", 0) for t in UNDERDOG_TEAMS}
combined_pts = sum(underdog_pts.values())
zero_pt_teams = [n for n, i in group_data.items() if i["pts"] == 0 and i["played"] > 0]

# Perfect group: teams with 3 wins in 3 games
perfect_teams = [n for n, i in group_data.items() if i["played"] == 3 and i["wins"] == 3]

# Favourites eliminated (played 3, not qualified)
favs_eliminated = [f for f in FAVOURITES if f in group_data
                   and group_data[f]["played"] == 3
                   and group_data[f].get("qualColor") != "#2AD572"]

# Underdogs qualified
underdogs_qualified = [u for u in UNDERDOGS if u in real_qualifiers]

# European nations in top 4
european_top4_actual = 0

with st.spinner("Loading match data..."):
    match_stats = get_match_stats()

tab1, tab2 = st.tabs(["📊 Live Data", "🎯 My Picks"])

def render_pick(col, title, picked, actual_str, result):
    with col:
        pts_val, res = result
        st.markdown(f'<div class="category-title">{title}</div>', unsafe_allow_html=True)
        st.markdown(f"""
            <div class="pick-card">
                <div style="flex:1">
                    <div class="pick-name">{picked or "—"}</div>
                    <div class="pick-sub">{actual_str}</div>
                </div>
                <div class="pick-result">{res}</div>
            </div>
        """, unsafe_allow_html=True)

# ── Tab 1: Live Data ──────────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-header">Group Stage</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="category-title">🌍 Underdog Combined Points</div>', unsafe_allow_html=True)
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

    with col3:
        st.markdown('<div class="category-title">🌟 Perfect Group Stage</div>', unsafe_allow_html=True)
        st.markdown(f"""
            <div class="info-card">
                <div class="big-number">{len(perfect_teams)}</div>
                <div class="sub-label">Teams with 3W from 3</div>
                <div style="margin-top:12px">
                    {"".join([f'<span class="team-pill-green">{t}</span>' for t in perfect_teams]) if perfect_teams else '<span style="color:rgba(255,255,255,0.3)">None yet</span>'}
                </div>
            </div>
        """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="category-title">💀 Favourites Eliminated</div>', unsafe_allow_html=True)
        st.markdown(f"""
            <div class="info-card">
                <div class="big-number">{len(favs_eliminated)}</div>
                <div class="sub-label">Favourites knocked out in groups</div>
                <div style="margin-top:12px">
                    {"".join([f'<span class="team-pill-red">{t}</span>' for t in favs_eliminated]) if favs_eliminated else '<span style="color:rgba(255,255,255,0.3)">None yet</span>'}
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="category-title">🚀 Underdogs Qualified</div>', unsafe_allow_html=True)
        st.markdown(f"""
            <div class="info-card">
                <div class="big-number">{len(underdogs_qualified)}</div>
                <div class="sub-label">Underdogs through to knockout stage</div>
                <div style="margin-top:12px">
                    {"".join([f'<span class="team-pill-green">{t}</span>' for t in underdogs_qualified]) if underdogs_qualified else '<span style="color:rgba(255,255,255,0.3)">None yet</span>'}
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">Tournament Stats</div>', unsafe_allow_html=True)
    col1, col2, col3, col4, col5 = st.columns(5)

    for col, icon, label, key, sub in [
        (col1, "🇪🇺", "In Top 4",   "european_top4",    "EU Nations in semis"),
        (col2, "🥅", "Penalty Shootouts", "penalty_shootouts", "Total so far"),
        (col3, "💪", "Biggest Comeback",  "biggest_comeback",  match_stats["biggest_comeback_match"] or "—"),
        (col4, "⚽", "Most Goals Game",   "most_goals_game",   match_stats["most_goals_match"] or "—"),
        (col5, "⏱️", "Most Added Time",   "most_added_time",   match_stats["most_added_time_match"] or "—"),
    ]:
        actual = european_top4_actual if key == "european_top4" else match_stats.get(key, 0)
        with col:
            st.markdown(f'<div class="category-title">{icon} {label}</div>', unsafe_allow_html=True)
            st.markdown(f"""
                <div class="info-card">
                    <div class="big-number">{actual}</div>
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

    # Score all — use .get() everywhere to avoid KeyErrors
    zp_pts,  zp_res  = score_zero_points_team(person.get("zero_points_team", ""), group_data)
    ud_pts,  ud_res  = score_range(person.get("underdog_points", ""), combined_pts)
    pg_pts,  pg_res  = score_perfect_group(person.get("perfect_group", ""), group_standings)
    fe_pts,  fe_res  = score_fav_eliminated(person.get("fav_eliminated", ""), group_standings)
    uq_pts,  uq_res  = score_underdog_qualifies(person.get("underdog_qualifies", ""), group_standings, real_qualifiers)
    eu_pts,  eu_res  = score_range(person.get("european_top4", ""), european_top4_actual)
    ps_pts,  ps_res  = score_range(person.get("penalty_shootouts", ""), match_stats["penalty_shootouts"])
    bc_pts,  bc_res  = score_range(person.get("biggest_comeback", ""),  match_stats["biggest_comeback"])
    mg_pts,  mg_res  = score_range(person.get("most_goals_game", ""),   match_stats["most_goals_game"])
    at_pts,  at_res  = score_range(person.get("most_added_time", ""),   match_stats["most_added_time"])

    total = zp_pts + ud_pts + pg_pts + fe_pts + uq_pts + eu_pts + ps_pts + bc_pts + mg_pts + at_pts
    st.markdown(f'<div class="points-box">Total Points: {total}</div>', unsafe_allow_html=True)
    st.divider()

    st.markdown('<div class="section-header">Group Stage</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    render_pick(col1, "🌍 Underdog Combined Pts", person.get("underdog_points", "—"), f"Current: {combined_pts}", (ud_pts, ud_res))
    render_pick(col2, "❌ Team to Get 0 Points",  person.get("zero_points_team", "—"),
                f"{group_data.get(person.get('zero_points_team', ''), {}).get('pts', '?')} pts", (zp_pts, zp_res))
    render_pick(col3, "🌟 Perfect Group Stage",   person.get("perfect_group", "—"),
                f"Teams with 3W/3: {', '.join(perfect_teams) or 'None yet'}", (pg_pts, pg_res))

    col1, col2 = st.columns(2)
    render_pick(col1, "💀 Favourite Eliminated",  person.get("fav_eliminated", "—"),
                f"Eliminated so far: {', '.join(favs_eliminated) or 'None yet'}", (fe_pts, fe_res))
    render_pick(col2, "🚀 Underdog Qualifies",    person.get("underdog_qualifies", "—"),
                f"Qualified: {', '.join(underdogs_qualified) or 'None yet'}", (uq_pts, uq_res))

    st.markdown('<div class="section-header">Tournament Stats</div>', unsafe_allow_html=True)
    col1, col2, col3, col4, col5 = st.columns(5)
    render_pick(col1, "🇪🇺 European Top 4",       person.get("european_top4", "—"),    f"Current: {european_top4_actual}", (eu_pts, eu_res))
    render_pick(col2, "🥅 Penalty Shootouts",     person.get("penalty_shootouts", "—"), f"Current: {match_stats['penalty_shootouts']}", (ps_pts, ps_res))
    render_pick(col3, "💪 Biggest Comeback",      person.get("biggest_comeback", "—"),  f"Current: {match_stats['biggest_comeback']}", (bc_pts, bc_res))
    render_pick(col4, "⚽ Most Goals Game",        person.get("most_goals_game", "—"),   f"Current: {match_stats['most_goals_game']}", (mg_pts, mg_res))
    render_pick(col5, "⏱️ Most Added Time",        person.get("most_added_time", "—"),   f"Current: {match_stats['most_added_time']} min", (at_pts, at_res))
