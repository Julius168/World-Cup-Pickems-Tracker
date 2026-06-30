import streamlit as st
import pandas as pd
import requests
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from functions import load_predictions

st.set_page_config(page_title="Knockouts", page_icon="⚔️", layout="wide")

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
        .round-title { font-family: 'Bebas Neue', sans-serif; font-size: 28px; letter-spacing: 4px; color: #FFD23F; text-align: center; margin: 20px 0 12px; }
        .match-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,210,63,0.15); border-radius: 12px; padding: 12px 16px; margin-bottom: 8px; }
        .match-card:hover { border-color: rgba(255,210,63,0.4); }
        .match-num { font-size: 11px; color: rgba(255,255,255,0.3); letter-spacing: 2px; text-transform: uppercase; margin-bottom: 4px; }
        .team-row { display: flex; justify-content: space-between; align-items: center; padding: 4px 0; }
        .team-name { font-family: 'Bebas Neue', sans-serif; font-size: 16px; letter-spacing: 1px; color: white; }
        .team-name-winner { color: #FFD23F; }
        .team-name-loser { color: rgba(255,255,255,0.3); }
        .score { font-family: 'Bebas Neue', sans-serif; font-size: 16px; color: #FFD23F; }
        .vs { font-size: 11px; color: rgba(255,255,255,0.3); text-align: center; }
        .person-name { font-family: 'Bebas Neue', sans-serif; font-size: 28px; letter-spacing: 4px; color: white; margin-bottom: 8px; }
        .points-box { font-family: 'Bebas Neue', sans-serif; font-size: 24px; letter-spacing: 3px; color: #FFD23F; margin-bottom: 16px; }
        .pred-correct { color: #2ad572; font-family: 'Bebas Neue', sans-serif; font-size: 14px; }
        .pred-wrong { color: #ff8080; font-family: 'Bebas Neue', sans-serif; font-size: 14px; }
        .pred-pending { color: rgba(255,255,255,0.3); font-family: 'Bebas Neue', sans-serif; font-size: 14px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="page-title">⚔️ Knockouts</h1>', unsafe_allow_html=True)

# ── Match definitions (in order) ─────────────────────────────────────────────
ROUND_OF_32_MATCHES = [
    {"num": 1,  "id": "4653703", "home": "Paraguay",             "away": "Germany"},
    {"num": 2,  "id": "4653704", "home": "France",               "away": "Sweden"},
    {"num": 3,  "id": "4653705", "home": "South Africa",         "away": "Canada"},
    {"num": 4,  "id": "4653706", "home": "Netherlands",          "away": "Morocco"},
    {"num": 5,  "id": "4653707", "home": "Portugal",             "away": "Croatia"},
    {"num": 6,  "id": "4653708", "home": "Spain",                "away": "Austria"},
    {"num": 7,  "id": "4653709", "home": "USA",                  "away": "Bosnia and Herzegovina"},
    {"num": 8,  "id": "4653710", "home": "Belgium",              "away": "Senegal"},
    {"num": 9,  "id": "4653711", "home": "Brazil",               "away": "Japan"},
    {"num": 10, "id": "4653712", "home": "Ivory Coast",          "away": "Norway"},
    {"num": 11, "id": "4653713", "home": "Mexico",               "away": "Ecuador"},
    {"num": 12, "id": "4653714", "home": "England",              "away": "DR Congo"},
    {"num": 13, "id": "4653715", "home": "Argentina",            "away": "Cape Verde"},
    {"num": 14, "id": "4653716", "home": "Australia",            "away": "Egypt"},
    {"num": 15, "id": "4653717", "home": "Switzerland",          "away": "Algeria"},
    {"num": 16, "id": "4653718", "home": "Colombia",             "away": "Ghana"},
]

ROUND_POINTS = {
    "Round of 32": 20,
    "Round of 16": 40,
    "Quarter Finals": 80,
    "Semi Finals": 160,
    "Third Place": 200,
    "Final": 400,
}

CSV_DIR = os.path.join(os.path.dirname(__file__), "..")
ROUND_CSVS = {
    "Round of 32": os.path.join(CSV_DIR, "Round_of_32_(Responses).csv"),
}

# ── Fetch match results from FotMob ──────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_knockout_results():
    results = {}
    for match in ROUND_OF_32_MATCHES:
        mid = match["id"]
        try:
            r = requests.get(f"https://www.fotmob.com/api/data/matchDetails?matchId={mid}", timeout=5)
            if r.status_code != 200:
                results[mid] = {"finished": False, "home": match["home"], "away": match["away"],
                                 "home_score": None, "away_score": None, "score_str": "", "winner": None}
                continue
            data = r.json()
            general = data.get("general", {})
            finished = general.get("finished", False)
            header = data.get("header", {})
            teams = header.get("teams", [])

            if not finished or len(teams) < 2:
                results[mid] = {"finished": finished, "home": match["home"], "away": match["away"],
                                 "home_score": None, "away_score": None, "score_str": "", "winner": None}
                continue

            home_name = teams[0].get("name", "")
            away_name = teams[1].get("name", "")
            home_score = teams[0].get("score", 0) or 0
            away_score = teams[1].get("score", 0) or 0
            status = header.get("status", {})

            winner = None
            if home_score > away_score:
                winner = home_name
            elif away_score > home_score:
                winner = away_name
            else:
                lost = status.get("whoLostOnPenalties")
                if lost:
                    winner = away_name if lost == home_name else home_name

            results[mid] = {
                "finished": finished,
                "home": home_name,
                "away": away_name,
                "home_score": home_score,
                "away_score": away_score,
                "score_str": f"{home_score} - {away_score}",
                "winner": winner,
                "penalties": bool(status.get("whoLostOnPenalties")),
            }
        except Exception:
            results[mid] = {"finished": False, "home": match["home"], "away": match["away"],
                             "home_score": None, "away_score": None, "score_str": "", "winner": None}
    return results

# ── Load knockout predictions CSVs ───────────────────────────────────────────
@st.cache_data
def load_knockout_predictions():
    all_preds = {}  # {name: {round: [pick1, pick2, ...]}}
    for round_name, csv_path in ROUND_CSVS.items():
        if not os.path.exists(csv_path):
            continue
        df = pd.read_csv(csv_path)
        num_matches = len([c for c in df.columns if c.startswith("Match")])
        for _, row in df.iterrows():
            name = str(row["Name"]).strip()
            if not name or name == "nan":
                continue
            picks = []
            for i in range(1, num_matches + 1):
                col = f"Match {i}"
                picks.append(str(row.get(col, "")).strip())
            if name not in all_preds:
                all_preds[name] = {}
            all_preds[name][round_name] = picks
    return all_preds

def score_knockout_predictions(person_preds, results):
    """Returns total points and per-match results for Round of 32."""
    total = 0
    match_results = []
    r32_picks = person_preds.get("Round of 32", [])
    for i, match in enumerate(ROUND_OF_32_MATCHES):
        pick = r32_picks[i] if i < len(r32_picks) else ""
        result = results.get(match["id"], {})
        winner = result.get("winner")
        finished = result.get("finished", False)
        if not finished:
            match_results.append((match, pick, None, 0))
        elif winner and pick:
            if pick.strip().lower() == winner.strip().lower():
                total += 20
                match_results.append((match, pick, True, 20))
            else:
                match_results.append((match, pick, False, 0))
        else:
            match_results.append((match, pick, None, 0))
    return total, match_results

def render_match_card(match, result, pick=None, correct=None, points=0):
    mid = match["id"]
    res = result.get(mid, {})
    finished = res.get("finished", False)
    home = match["home"]
    away = match["away"]
    home_score = res.get("home_score", "")
    away_score = res.get("away_score", "")
    winner = res.get("winner")

    home_class = ""
    away_class = ""
    if finished and winner:
        home_class = "team-name-winner" if winner == home else "team-name-loser"
        away_class = "team-name-winner" if winner == away else "team-name-loser"

    score_html = f'<span class="score">{home_score} - {away_score}</span>' if finished else '<span class="vs">vs</span>'
    pen_html = ' <span style="font-size:10px;color:rgba(255,210,63,0.6)">(Pen)</span>' if res.get("penalties") else ""

    pred_html = ""
    if pick is not None:
        if not finished:
            pred_html = f'<div class="pred-pending">📌 {pick}</div>'
        elif correct:
            pred_html = f'<div class="pred-correct">✅ {pick} +{points}</div>'
        else:
            pred_html = f'<div class="pred-wrong">❌ {pick}</div>'

    st.markdown(f"""
        <div class="match-card">
            <div class="match-num">Match {match["num"]}</div>
            <div class="team-row">
                <span class="team-name {home_class}">{home}</span>
                {score_html}{pen_html}
                <span class="team-name {away_class}">{away}</span>
            </div>
            {pred_html}
        </div>
    """, unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
results = fetch_knockout_results()
knockout_preds = load_knockout_predictions()

tab1, tab2 = st.tabs(["📊 Bracket", "🎯 My Picks"])

# ── Tab 1: Bracket ────────────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="round-title">Round of 32</div>', unsafe_allow_html=True)
    left_matches = ROUND_OF_32_MATCHES[:8]
    right_matches = ROUND_OF_32_MATCHES[8:]
    col_left, col_div, col_right = st.columns([5, 1, 5])

    with col_left:
        st.markdown("**Left Side**")
        for match in left_matches:
            render_match_card(match, results)

    with col_div:
        st.markdown("")

    with col_right:
        st.markdown("**Right Side**")
        for match in right_matches:
            render_match_card(match, results)

# ── Tab 2: My Picks ───────────────────────────────────────────────────────────
with tab2:
    if not knockout_preds:
        st.info("No knockout predictions loaded yet.")
    else:
        people = list(knockout_preds.keys())
        selected = st.selectbox("Select a person", people)
        person_preds = knockout_preds.get(selected, {})

        total_pts, match_results = score_knockout_predictions(person_preds, results)

        st.markdown(f'<div class="person-name">{selected}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="points-box">Round of 32 Points: {total_pts}</div>', unsafe_allow_html=True)
        st.divider()

        st.markdown('<div class="round-title">Round of 32</div>', unsafe_allow_html=True)
        col_left, col_div, col_right = st.columns([5, 1, 5])
        left_results = match_results[:8]
        right_results = match_results[8:]

        with col_left:
            for match, pick, correct, pts in left_results:
                render_match_card(match, results, pick, correct, pts)

        with col_right:
            for match, pick, correct, pts in right_results:
                render_match_card(match, results, pick, correct, pts)
