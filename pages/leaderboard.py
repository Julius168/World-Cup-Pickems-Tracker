import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from functions import (
    load_predictions, fetch_groups, fetch_player_stats,
    fetch_team_stats, fetch_all_match_stats, compute_all_points, UNDERDOG_TEAMS
)

st.set_page_config(page_title="Leaderboard", page_icon="🥇", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.cdnfonts.com/css/bebas-neue');

        [data-testid="stAppViewContainer"] { background-color: #0a1628; }
        [data-testid="stSidebar"] { background-color: #071020; }
        [data-testid="stSidebar"] span { color: white !important; font-size: 16px; letter-spacing: 1px; }
        [data-testid="stSidebar"] li:hover span { color: #FFD23F !important; }
        [data-testid="stSidebar"] li[aria-selected="true"] span { color: #FFD23F !important; }
        [data-testid="stSidebar"] li[aria-selected="true"] { background-color: rgba(255, 210, 63, 0.15); border-radius: 8px; }

        .page-title {
            font-family: 'Bebas Neue', sans-serif;
            font-size: 60px;
            letter-spacing: 6px;
            color: #FFD23F !important;
            text-align: center;
            margin-bottom: 40px;
        }
        .rank-card {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,210,63,0.15);
            border-radius: 14px;
            padding: 20px 24px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 20px;
        }
        .rank-card:hover {
            border-color: rgba(255,210,63,0.45);
            background: rgba(255,210,63,0.05);
        }
        .rank-card-gold   { border-color: #FFD23F; background: rgba(255,210,63,0.08); }
        .rank-card-silver { border-color: #C0C0C0; background: rgba(192,192,192,0.05); }
        .rank-card-bronze { border-color: #CD7F32; background: rgba(205,127,50,0.05); }
        .rank-number {
            font-family: 'Bebas Neue', sans-serif;
            font-size: 40px;
            color: rgba(255,255,255,0.2);
            width: 48px;
            text-align: center;
        }
        .rank-name {
            font-family: 'Bebas Neue', sans-serif;
            font-size: 28px;
            letter-spacing: 3px;
            color: white;
            flex: 1;
        }
        .rank-total {
            font-family: 'Bebas Neue', sans-serif;
            font-size: 40px;
            color: #FFD23F;
        }
        .rank-sub {
            font-size: 12px;
            color: rgba(255,255,255,0.4);
            letter-spacing: 1px;
        }
        .section-title {
            font-family: 'Bebas Neue', sans-serif;
            font-size: 22px;
            letter-spacing: 4px;
            color: #FFD23F;
            margin: 24px 0 8px;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="page-title">🥇 Leaderboard</h1>', unsafe_allow_html=True)

# ── Load all data ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_live_data():
    group_standings, real_qualifiers, real_third = fetch_groups()
    player_stats = fetch_player_stats()
    team_stats   = fetch_team_stats()
    return group_standings, real_qualifiers, player_stats, team_stats

@st.cache_data(ttl=3600)
def load_match_data():
    return fetch_all_match_stats()

@st.cache_data
def load_all_predictions():
    return load_predictions()

try:
    predictions = load_all_predictions()
except FileNotFoundError:
    st.error("predictions.csv not found.")
    st.stop()

with st.spinner("Loading live data..."):
    group_standings, real_qualifiers, player_stats, team_stats = load_live_data()

with st.spinner("Loading match data..."):
    match_stats = load_match_data()

# Build flat group_data dict for zero points scoring
group_data = {}
for letter, d in group_standings.items():
    for t in d["full"]:
        group_data[t["name"]] = {"pts": t["pts"], "played": t["played"]}

# ── Compute points for everyone ───────────────────────────────────────────────
all_breakdowns = {}
for name, person in predictions.items():
    all_breakdowns[name] = compute_all_points(
        person, group_standings, real_qualifiers,
        group_data, player_stats, team_stats, match_stats
    )

# Sort by total
sorted_players = sorted(all_breakdowns.items(), key=lambda x: x[1]["TOTAL"], reverse=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["🏆 Rankings", "📊 Breakdown"])

medals = ["🥇", "🥈", "🥉"]
card_classes = ["rank-card-gold", "rank-card-silver", "rank-card-bronze"]

# ── Tab 1: Rankings ───────────────────────────────────────────────────────────
with tab1:
    for i, (name, breakdown) in enumerate(sorted_players):
        total = breakdown["TOTAL"]
        medal = medals[i] if i < 3 else ""
        card_class = card_classes[i] if i < 3 else ""
        rank_num = "" if i < 3 else str(i + 1)

        # Build mini breakdown string
        group_pts  = breakdown.get("Groups (Quali)", 0) + breakdown.get("Groups (Exact)", 0)
        player_pts = sum(v for k, v in breakdown.items() if k.startswith("Player:"))
        team_pts   = sum(v for k, v in breakdown.items() if k.startswith("Team:"))
        special_pts = sum(v for k, v in breakdown.items() if k.startswith("Special:"))

        st.markdown(f"""
            <div class="rank-card {card_class}">
                <div class="rank-number">{medal or rank_num}</div>
                <div style="flex:1">
                    <div class="rank-name">{name}</div>
                    <div class="rank-sub">
                        Groups: {group_pts} &nbsp;|&nbsp;
                        Players: {player_pts} &nbsp;|&nbsp;
                        Teams: {team_pts} &nbsp;|&nbsp;
                        Special: {special_pts}
                    </div>
                </div>
                <div class="rank-total">{total}</div>
            </div>
        """, unsafe_allow_html=True)

# ── Tab 2: Breakdown ──────────────────────────────────────────────────────────
with tab2:
    if not sorted_players:
        st.write("No data yet.")
    else:
        # Build a dataframe with all categories as columns
        rows = []
        for name, breakdown in sorted_players:
            row = {"Name": name}
            row.update({k: v for k, v in breakdown.items()})
            rows.append(row)

        df = pd.DataFrame(rows).set_index("Name")

        # Reorder: TOTAL first
        cols = ["TOTAL"] + [c for c in df.columns if c != "TOTAL"]
        df = df[cols]

        # Rename columns for display
        df.columns = [c.replace("Groups ", "Grp ").replace("Player: ", "").replace("Team: ", "").replace("Special: ", "") for c in df.columns]

        st.dataframe(
            df.style.highlight_max(axis=0, color="rgba(255,210,63,0.3)"),
            use_container_width=True,
        )
