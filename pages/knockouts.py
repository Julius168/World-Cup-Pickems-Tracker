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

ROUND_OF_16_MATCHES = [
    {"num": 1, "id": "4653842", "home": "Paraguay",   "away": "France"},
    {"num": 2, "id": "4653843", "home": "Canada",     "away": "Morocco"},
    {"num": 3, "id": "4653844", "home": "Brazil",     "away": "Norway"},
    {"num": 4, "id": "4653845", "home": "Mexico",     "away": "England"},
    {"num": 5, "id": "4653846", "home": "Portugal",   "away": "Spain"},
    {"num": 6, "id": "4653847", "home": "USA",        "away": "Belgium"},
    {"num": 7, "id": "4653848", "home": "Argentina",  "away": "Egypt"},
    {"num": 8, "id": "4653849", "home": "Switzerland","away": "Colombia"},
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
    "Round of 16": os.path.join(CSV_DIR, "Round_of_16_(Responses).csv"),
}

# ── Fetch results from matchDetails ──────────────────────────────────────────
def fetch_round_results(matches):
    results = {}
    for match in matches:
        mid = match["id"]
        try:
            r = requests.get(f"https://www.fotmob.com/api/data/matchDetails?matchId={mid}", timeout=5)
            if r.status_code != 200:
                results[mid] = {"finished": False, "home": match["home"], "away": match["away"],
                                 "home_score": None, "away_score": None, "winner": None}
                continue
            data = r.json()
            general = data.get("general", {})
            finished = general.get("finished", False)
            header = data.get("header", {})
            teams = header.get("teams", [])
            if not finished or len(teams) < 2:
                results[mid] = {"finished": finished, "home": match["home"], "away": match["away"],
                                 "home_score": None, "away_score": None, "winner": None}
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
                "finished": finished, "home": home_name, "away": away_name,
                "home_score": home_score, "away_score": away_score,
                "winner": winner, "penalties": bool(status.get("whoLostOnPenalties")),
            }
        except Exception:
            results[mid] = {"finished": False, "home": match["home"], "away": match["away"],
                             "home_score": None, "away_score": None, "winner": None}
    return results

@st.cache_data(ttl=300)
def fetch_all_results():
    r32 = fetch_round_results(ROUND_OF_32_MATCHES)
    r16 = fetch_round_results(ROUND_OF_16_MATCHES)
    return {**r32, **r16}

# ── Load predictions ──────────────────────────────────────────────────────────
@st.cache_data
def load_knockout_predictions():
    
    all_preds = {}
    for round_name, csv_path in ROUND_CSVS.items():
        if not os.path.exists(csv_path):
            continue
        df = pd.read_csv(csv_path)
        num_matches = len([c for c in df.columns if c.startswith("Match")])
        for _, row in df.iterrows():
            name = str(row["Name"]).strip()
            if not name or name == "nan":
                continue
            picks = [str(row.get(f"Match {i}", "")).strip() for i in range(1, num_matches + 1)]
            if name not in all_preds:
                all_preds[name] = {}
            all_preds[name][round_name] = picks
    return all_preds



def score_round(person_preds, matches, round_name, points_per_correct, results):
    total = 0
    match_results = []
    picks = person_preds.get(round_name, [])
    for i, match in enumerate(matches):
        pick = picks[i] if i < len(picks) else ""
        res = results.get(match["id"], {})
        winner = res.get("winner")
        finished = res.get("finished", False)
        if not finished:
            match_results.append((match, pick, None, 0))
        elif winner and pick:
            if pick.strip().lower() == winner.strip().lower():
                total += points_per_correct
                match_results.append((match, pick, True, points_per_correct))
            else:
                match_results.append((match, pick, False, 0))
        else:
            match_results.append((match, pick, None, 0))
    return total, match_results

def render_match_card(match, results, pick=None, correct=None, points=0):
    mid = match["id"]
    res = results.get(mid, {})
    finished = res.get("finished", False)
    home = res.get("home", match["home"])
    away = res.get("away", match["away"])
    home_score = res.get("home_score", "")
    away_score = res.get("away_score", "")
    winner = res.get("winner")

    home_class = "team-name-winner" if (finished and winner == home) else ("team-name-loser" if (finished and winner and winner != home) else "")
    away_class = "team-name-winner" if (finished and winner == away) else ("team-name-loser" if (finished and winner and winner != away) else "")

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

def render_bracket_round(title, matches, results, match_results=None):
    st.markdown(f'<div class="round-title">{title}</div>', unsafe_allow_html=True)
    left = matches[:len(matches)//2]
    right = matches[len(matches)//2:]
    col_left, _, col_right = st.columns([5, 1, 5])
    with col_left:
        for i, match in enumerate(left):
            if match_results:
                _, pick, correct, pts = match_results[i]
                render_match_card(match, results, pick, correct, pts)
            else:
                render_match_card(match, results)
    with col_right:
        for i, match in enumerate(right):
            idx = i + len(left)
            if match_results:
                _, pick, correct, pts = match_results[idx]
                render_match_card(match, results, pick, correct, pts)
            else:
                render_match_card(match, results)

# ── Load data ─────────────────────────────────────────────────────────────────
results = fetch_all_results()
knockout_preds = load_knockout_predictions()

tab1, tab2 = st.tabs(["📊 Bracket", "🎯 My Picks"])

with tab1:
    render_bracket_round("Round of 32", ROUND_OF_32_MATCHES, results)
    render_bracket_round("Round of 16", ROUND_OF_16_MATCHES, results)

with tab2:
    if not knockout_preds:
        st.info("No knockout predictions loaded yet.")
    else:
        people = list(knockout_preds.keys())
        selected = st.selectbox("Select a person", people)
        person_preds = knockout_preds.get(selected, {})

        r32_pts, r32_results = score_round(person_preds, ROUND_OF_32_MATCHES, "Round of 32", 20, results)
        r16_pts, r16_results = score_round(person_preds, ROUND_OF_16_MATCHES, "Round of 16", 40, results)
        total_pts = r32_pts + r16_pts

        st.markdown(f'<div class="person-name">{selected}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="points-box">Total: {total_pts} &nbsp;|&nbsp; R32: {r32_pts} &nbsp;|&nbsp; R16: {r16_pts}</div>', unsafe_allow_html=True)
        st.divider()

        render_bracket_round("Round of 32", ROUND_OF_32_MATCHES, results, r32_results)
        render_bracket_round("Round of 16", ROUND_OF_16_MATCHES, results, r16_results)
