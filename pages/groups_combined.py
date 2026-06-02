import streamlit as st
import pandas as pd
import sys
import os
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from functions import fetch_groups, load_predictions, score_groups

st.set_page_config(page_title="Groups", page_icon="🌍", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.cdnfonts.com/css/bebas-neue');
        [data-testid="stAppViewContainer"] { background-color: #0a1628; }
        [data-testid="stSidebar"] { background-color: #071020; }
        [data-testid="stSidebar"] span { color: white !important; font-size: 16px; letter-spacing: 1px; }
        [data-testid="stSidebar"] li:hover span { color: #FFD23F !important; }
        [data-testid="stSidebar"] li[aria-selected="true"] span { color: #FFD23F !important; }
        [data-testid="stSidebar"] li[aria-selected="true"] { background-color: rgba(255, 210, 63, 0.15); border-radius: 8px; }
        .page-title { font-family: 'Bebas Neue', sans-serif; font-size: 60px; letter-spacing: 6px; color: #FFD23F !important; text-align: center; margin-bottom: 20px; }
        .group-title { font-family: 'Bebas Neue', sans-serif; font-size: 22px; letter-spacing: 4px; color: #FFD23F; margin-bottom: 4px; }
        .person-name { font-family: 'Bebas Neue', sans-serif; font-size: 32px; letter-spacing: 4px; color: white; margin-bottom: 16px; }
        .points-box { font-family: 'Bebas Neue', sans-serif; font-size: 28px; letter-spacing: 3px; color: #FFD23F; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="page-title">🌍 Groups</h1>', unsafe_allow_html=True)

@st.cache_data(ttl=300)
def get_groups():
    return fetch_groups()

@st.cache_data
def get_predictions():
    return load_predictions()

group_standings, real_qualifiers, real_third_qualifiers = get_groups()

tab1, tab2 = st.tabs(["📊 Standings", "🎯 Predictions"])

# ── Tab 1: Standings ──────────────────────────────────────────────────────────
with tab1:
    groups = list(group_standings.items())
    grid_rows = [groups[i:i+3] for i in range(0, len(groups), 3)]
    for grid_row in grid_rows:
        cols = st.columns(3)
        for col, (letter, data) in zip(cols, grid_row):
            teams = data["full"]
            rows_data = []
            for t in teams:
                gs, gc = t["scoresStr"].split("-")
                rows_data.append({
                    "Team": t["name"], "MP": t["played"], "Pts": t["pts"],
                    "W": t["wins"], "D": t["draws"], "L": t["losses"],
                    "GS": int(gs), "GC": int(gc),
                })
            df = pd.DataFrame(rows_data)
            with col:
                st.markdown(f'<div class="group-title">Group {letter}</div>', unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="group-title">🏅 Best 3rd Place Teams</div>', unsafe_allow_html=True)

    response = requests.get("https://www.fotmob.com/api/data/leagues?id=77")
    data = response.json()
    all_tables = data["table"][0]["data"]["tables"]
    third_table = next((t for t in all_tables if t["leagueName"] == "Best 3rd placed teams"), None)

    if third_table:
        teams = third_table["table"]["all"]
        rows_data = []
        for t in teams:
            gs, gc = t["scoresStr"].split("-")
            rows_data.append({
                "Team": t["name"],
                "MP":   t["played"],
                "Pts":  t["pts"],
                "W":    t["wins"],
                "D":    t["draws"],
                "L":    t["losses"],
                "GS":   int(gs),
                "GC":   int(gc),
                "Qual": "✅" if t.get("qualColor") == "#2AD572" else "",
            })
        df = pd.DataFrame(rows_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

# ── Tab 2: Predictions ────────────────────────────────────────────────────────
with tab2:
    try:
        predictions = get_predictions()
    except FileNotFoundError:
        st.error("predictions.csv not found.")
        st.stop()
    except KeyError as e:
        st.error(f"Column not found in CSV: {e}")
        st.stop()

    people = list(predictions.keys())
    selected_person = st.selectbox("Select a person", people)
    person = predictions[selected_person]

    st.markdown(f'<div class="person-name">{selected_person}</div>', unsafe_allow_html=True)

    results, quali_points, exact_points = score_groups(person, group_standings, real_qualifiers)
    total = quali_points + exact_points

    st.markdown(f'<div class="points-box">Total: {total} &nbsp;|&nbsp; Quali: {quali_points} &nbsp;|&nbsp; Exact: {exact_points}</div>', unsafe_allow_html=True)
    st.divider()

    group_letters = list(person["groups"].keys())
    positions = ["1st", "2nd", "3rd", "4th"]
    grid_rows = [group_letters[i:i+3] for i in range(0, len(group_letters), 3)]
    for grid_row in grid_rows:
        cols = st.columns(3)
        for col, letter in zip(cols, grid_row):
            rows_data = []
            for i, (team, status, pts) in enumerate(results[letter]):
                rows_data.append({"Pos": positions[i], "Team": team, "Result": status})
            df = pd.DataFrame(rows_data)
            with col:
                st.markdown(f'<div class="group-title">Group {letter}</div>', unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True, hide_index=True)
