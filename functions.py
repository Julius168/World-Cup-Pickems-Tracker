import requests
import pandas as pd
import json
import os
import time

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "predictions.csv")
CACHE_PATH = os.path.join(BASE_DIR, "match_cache.json")

# ── Match IDs ────────────────────────────────────────────────────────────────

KNOCKOUT_ROUND_CSVS = {
    "Round of 32": "Round_of_32_(Responses).csv",
}

KNOCKOUT_ROUND_POINTS = {
    "Round of 32": 20,
    "Round of 16": 40,
    "Quarter Finals": 80,
    "Semi Finals": 160,
    "Third Place": 200,
    "Final": 400,
}

ROUND_OF_32_IDS = [
    "4653703","4653704","4653705","4653706","4653707","4653708",
    "4653709","4653710","4653711","4653712","4653713","4653714",
    "4653715","4653716","4653717","4653718",
]
MATCH_IDS = [
    # Group stage
    4667751, 4667752, 4667753, 4667754, 4667755, 4667756, 4667757, 4667758, 4667759, 4667760,
    4667761, 4667762, 4667763, 4667764, 4667765, 4667766, 4667767, 4667768, 4667769, 4667770,
    4667771, 4667772, 4667773, 4667774, 4667775, 4667776, 4667777, 4667778, 4667779, 4667780,
    4667781, 4667782, 4667783, 4667784, 4667785, 4667786, 4667787, 4667788, 4667789, 4667790,
    4667791, 4667792, 4667793, 4667794, 4667795, 4667796, 4667797, 4667798, 4667799, 4667800,
    4667801, 4667802, 4667803, 4667804, 4667805, 4667806, 4667807, 4667808, 4667809, 4667810,
    4667811, 4667812, 4667813, 4667814, 4667815, 4667816, 4667817, 4667818, 4667819, 4667820,
    # Round of 32
    4653703, 4653704, 4653705, 4653706, 4653707, 4653708, 4653709, 4653710,
    4653712, 4653713, 4653714, 4653715, 4653716, 4653717, 4653718,
    # Round of 16
    4653842, 4653843, 4653844, 4653845, 4653846, 4653847, 4653848, 4653849,
    # Quarter
    4653851, 4653852, 4653853, 4653854,
    # Semi
    4653855, 4653856,
    # Losers final
    4653857,
    # Final
    4653858,
]

UNDERDOG_TEAMS = ["Haiti", "Curacao", "Cape Verde"]
THIRD_PLACE_COL = "3rd place teams to go through (Select 8 based on your above choices)"

# ── CSV columns ───────────────────────────────────────────────────────────────
PLAYER_CSV_COLS = {
    "Golden Ball":  "World cup Golden Ball (MVP award)",
    "Top Scorer":   "Top Scorer",
    "Top Assister": "Top Assister",
    "Yellow Cards": "Most Yellow Cards",
    "Golden Glove": "Most Saves per 90 (minimum 180 minutes)",
}
PLAYER_API_KEYS = {
    "Golden Ball":  "rating",
    "Top Scorer":   "goals",
    "Top Assister": "goal_assist",
    "Yellow Cards": "yellow_card",
    "Golden Glove": "saves",
}

# ── Favourites & Underdogs ────────────────────────────────────────────────────
FAVOURITES = [
    "Mexico", "Czechia", "Switzerland", "Canada", "Brazil", "Morocco",
    "USA", "Turkey", "Germany", "Ecuador", "Netherlands", "Japan",
    "Belgium", "Egypt", "Spain", "Uruguay", "France", "Norway",
    "Argentina", "Austria", "Portugal", "Colombia", "England", "Croatia",
]

UNDERDOGS = [
    "South Africa", "Qatar", "Haiti", "Australia", "Curacao", "Tunisia",
    "New Zealand", "Cape Verde", "Iraq", "Jordan", "Uzbekistan", "Panama",
]
TEAM_CSV_COLS = {
    "Winning Team":         "Winning team",
    "Goals Per Match":      "Team most goals per match",
    "Least Goals Conceded": "Team least goals conceded per match",
    "Set Piece Goals":      "Most set-piece goals ",
    "Fouls Per Match":      "Fouls per match",
}
TEAM_API_KEYS = {
    "Winning Team":         "rating_team",
    "Goals Per Match":      "goals_team_match",
    "Least Goals Conceded": "goals_conceded_team_match",
    "Set Piece Goals":      "_set_piece_goals_team",
    "Fouls Per Match":      "fk_foul_lost_team",
}

# ── API fetchers ──────────────────────────────────────────────────────────────
def fetch_groups():
    """Returns (group_standings, real_qualifiers, real_third_qualifiers)"""
    try:
        response = requests.get("https://www.fotmob.com/api/data/leagues?id=77", timeout=10)
        data = response.json()
        all_tables = data["table"][0]["data"]["tables"]
        group_standings = {}
        real_third_qualifiers = []
        for table in all_tables:
            name = table["leagueName"]
            teams = table["table"]["all"]
            if name == "Best 3rd placed teams":
                real_third_qualifiers = [t["name"] for t in teams if t.get("qualColor") == "#2AD572"]
            elif name.startswith("Grp."):
                letter = name.replace("Grp. ", "")
                group_standings[letter] = {
                    "order": [t["name"] for t in teams],
                    "full":  teams,
                }
        real_qualifiers = set()
        for letter, d in group_standings.items():
            real_qualifiers.update(d["order"][:2])
        real_qualifiers.update(real_third_qualifiers)
        return group_standings, real_qualifiers, real_third_qualifiers
    except Exception:
        return {}, set(), []


def fetch_player_stats():
    """Returns {stat_key: [topThree players]} from FotMob player stats"""
    try:
        # Change id=42 to id=77 when World Cup starts
        response = requests.get("https://www.fotmob.com/api/data/leagues?id=77", timeout=10)
        data = response.json()
        raw = data.get("stats", {}).get("players", [])
        indexed = {}
        for entry in raw:
            key = entry.get("name")
            if key:
                indexed[key] = entry.get("topThree", [])
        return indexed
    except Exception:
        return {}


def fetch_team_stats():
    """Returns {stat_key: [topThree teams]} from FotMob team stats"""
    try:
        # Change id=42 to id=77 when World Cup starts
        response = requests.get("https://www.fotmob.com/api/data/leagues?id=77", timeout=10)
        data = response.json()
        raw = data.get("stats", {}).get("teams", [])
        indexed = {}
        for entry in raw:
            key = entry.get("name")
            if key:
                indexed[key] = entry.get("topThree", [])
        return indexed
    except Exception:
        return {}


# ── Match cache ───────────────────────────────────────────────────────────────
def load_match_cache():
    """Load existing match cache from disk"""
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r") as f:
            return json.load(f)
    return {}


def save_match_cache(cache):
    """Save match cache to disk"""
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f)


def process_match(data):
    """Extract relevant stats from a single match API response"""
    result = {
        "has_shootout": False,
        "total_goals": 0,
        "biggest_deficit_winner": 0,
        "most_added_time": 0,
        "home": "",
        "away": "",
        "score": "",
    }
    try:
        general = data.get("general", {})
        if not general.get("finished", False):
            return None  # not finished, don't cache

        header = data.get("header", {})
        teams = header.get("teams", [])
        if len(teams) < 2:
            return None

        result["home"] = teams[0].get("name", "")
        result["away"] = teams[1].get("name", "")
        final_home = teams[0].get("score", 0) or 0
        final_away = teams[1].get("score", 0) or 0
        result["score"] = f"{final_home}-{final_away}"

        # Collect all goal events
        events_home = header.get("events", {}).get("homeTeamGoals", {})
        events_away = header.get("events", {}).get("awayTeamGoals", {})
        all_goal_events = []
        for goals in events_home.values():
            all_goal_events.extend(goals)
        for goals in events_away.values():
            all_goal_events.extend(goals)

        # Check for penalty shootout
        result["has_shootout"] = any(
            e.get("isPenaltyShootoutEvent", False) for e in all_goal_events
        )

        # Sort by time
        def sort_key(e):
            t = e.get("time", 0) or 0
            ot = e.get("overloadTime", 0) or 0
            return t * 100 + ot
        all_goal_events.sort(key=sort_key)

        # Count goals (excl. shootout)
        result["total_goals"] = sum(
            1 for e in all_goal_events
            if not e.get("isPenaltyShootoutEvent") and e.get("type") == "Goal"
        )

        # Biggest comeback
        max_deficit_home = 0
        max_deficit_away = 0
        for e in all_goal_events:
            if e.get("isPenaltyShootoutEvent"):
                continue
            new_score = e.get("newScore", [])
            if len(new_score) == 2:
                h, a = new_score
                max_deficit_home = max(max_deficit_home, a - h)
                max_deficit_away = max(max_deficit_away, h - a)

        if final_home > final_away:
            result["biggest_deficit_winner"] = max_deficit_home
        elif final_away > final_home:
            result["biggest_deficit_winner"] = max_deficit_away
        else:
            result["biggest_deficit_winner"] = 0

        # Most added time at 90
        content = data.get("content", {})
        mf_events = content.get("matchFacts", {}).get("events", {}).get("events", [])
        for e in mf_events:
            if e.get("type") == "AddedTime" and e.get("time") == 90:
                added = e.get("minutesAddedInput", 0) or 0
                result["most_added_time"] = max(result["most_added_time"], added)

    except Exception:
        pass

    return result


def fetch_all_match_stats():
    """
    Loop through MATCH_IDS, use cache for completed matches,
    only fetch new/unfinished ones. Returns aggregated tournament stats.
    """
    cache = load_match_cache()
    cache_updated = False

    for match_id in MATCH_IDS:
        key = str(match_id)
        if key in cache:
            continue  # already processed and finished

        try:
            r = requests.get(
                f"https://www.fotmob.com/api/data/matchDetails?matchId={match_id}",
                timeout=5
            )
            if r.status_code != 200:
                continue
            data = r.json()
            processed = process_match(data)
            if processed is not None:  # only cache finished matches
                cache[key] = processed
                cache_updated = True
            time.sleep(0.1)
        except Exception:
            continue

    if cache_updated:
        save_match_cache(cache)

    # Aggregate
    penalty_shootouts = 0
    biggest_comeback = 0
    biggest_comeback_match = ""
    most_goals_game = 0
    most_goals_match = ""
    most_added_time = 0
    most_added_time_match = ""

    for key, m in cache.items():
        if m.get("has_shootout"):
            penalty_shootouts += 1
        if m.get("biggest_deficit_winner", 0) > biggest_comeback:
            biggest_comeback = m["biggest_deficit_winner"]
            biggest_comeback_match = f"{m['home']} vs {m['away']} ({m['score']})"
        if m.get("total_goals", 0) > most_goals_game:
            most_goals_game = m["total_goals"]
            most_goals_match = f"{m['home']} vs {m['away']} ({m['score']})"
        if m.get("most_added_time", 0) > most_added_time:
            most_added_time = m["most_added_time"]
            most_added_time_match = f"{m['home']} vs {m['away']}"

    return {
        "penalty_shootouts":      penalty_shootouts,
        "biggest_comeback":       biggest_comeback,
        "biggest_comeback_match": biggest_comeback_match,
        "most_goals_game":        most_goals_game,
        "most_goals_match":       most_goals_match,
        "most_added_time":        most_added_time,
        "most_added_time_match":  most_added_time_match,
    }


# ── CSV loader ────────────────────────────────────────────────────────────────
def load_predictions():
    """Load all predictions from CSV. Returns dict keyed by person name."""
    df = pd.read_csv(CSV_PATH)
    predictions = {}

    def get_col(col):
        normalized_col = col.strip().replace('\n', '').replace('\r', '')
        matching = [c for c in df.columns if c.strip().replace('\n', '').replace('\r', '') == normalized_col]
        return str(row[matching[0]]).strip() if matching else ""
    group_letters = "ABCDEFGHIJKL"

    for _, row in df.iterrows():
        name = row["Name"]
        group_preds = {}
        for letter in group_letters:
            def find_col(pos, l=letter):
                for col in df.columns:
                    if col.strip().startswith(f"Group {l}") and f"[{pos}]" in col:
                        return col
                return None
            group_preds[letter] = [
                str(row[find_col("First")]).strip()  if find_col("First")  else "",
                str(row[find_col("Second")]).strip() if find_col("Second") else "",
                str(row[find_col("Third")]).strip()  if find_col("Third")  else "",
                str(row[find_col("Fourth")]).strip() if find_col("Fourth") else "",
            ]

        third_str = str(row.get(THIRD_PLACE_COL, ""))
        third_groups = [g.strip().replace("Group ", "") for g in third_str.split(",") if g.strip()]
        predicted_third_teams = [group_preds[l][2] for l in third_groups if l in group_preds]

        player_picks = {cat: get_col(col) for cat, col in PLAYER_CSV_COLS.items()}
        team_picks   = {cat: get_col(col) for cat, col in TEAM_CSV_COLS.items()}

        predictions[name] = {
            "_name":                  name,
            "groups":                 group_preds,
            "third_groups":           third_groups,
            "predicted_third_teams":  predicted_third_teams,
            "player_picks":           player_picks,
            "team_picks":             team_picks,
            "zero_points_team":       get_col("Team to get 0 points in groups"),
            "underdog_points":        get_col("How many points will Haiti, Curacao and Cape Verde get combined"),
            "penalty_shootouts":      get_col("Amount of penalty shootouts"),
            "biggest_comeback":       get_col("Biggest comeback\n(Quantity of goals trailed by while eventually winning the game)"),
            "most_goals_game":        get_col("Most goals scored in a game (both teams combined including extra time)"),
            "most_added_time":        get_col("most added time at 90 \n"),
            "european_top4":          get_col("European Nations in top 4 "),
            "perfect_group":          get_col("Perfect Group stage (9 points)"),
            "fav_eliminated":         get_col("Group favourite eliminated in group stage"),
            "underdog_qualifies":     get_col("Group underdog to make it out of group stage"),
        }

    return predictions


# ── Scoring functions ─────────────────────────────────────────────────────────
def score_groups(person, group_standings, real_qualifiers):
    """Returns (results_dict, quali_points, exact_points)"""
    predicted_qualifiers = set()
    for letter, teams in person["groups"].items():
        predicted_qualifiers.update(teams[:2])
    predicted_qualifiers.update(person["predicted_third_teams"])

    quali_points = 0
    exact_points = 0
    results = {}

    for letter, predicted in person["groups"].items():
        actual = group_standings.get(letter, {}).get("order", [])
        results[letter] = []
        for i, team in enumerate(predicted):
            if not actual:
                results[letter].append((team, "⬜ —", 0))
                continue
            tq = 20 if (team in real_qualifiers and team in predicted_qualifiers) else 0
            te = 10 if (len(actual) > i and actual[i] == team) else 0
            total = tq + te
            quali_points += tq
            exact_points += te
            if total == 30:   status = "⭐ +30"
            elif total == 20: status = "✅ +20"
            elif total == 10: status = "⭐ +10"
            else:             status = "❌ +0"
            results[letter].append((team, status, total))

    return results, quali_points, exact_points


def score_top3_pick(picked, top3_entries, points_map={1: 50, 2: 20, 3: 10}):
    """Score a single pick against a top3 list, handling ties by value."""
    if not picked or not top3_entries:
        return 0, "⬜ —"
    seen_values = []
    for p in top3_entries:
        v = p.get("value")
        if v not in seen_values:
            seen_values.append(v)
    value_to_rank = {}
    rank = 1
    for v in seen_values:
        value_to_rank[v] = rank
        count = sum(1 for p in top3_entries if p.get("value") == v)
        rank += count
    for player in top3_entries:
        if player.get("name", "") == picked:
            true_rank = value_to_rank.get(player.get("value"), 99)
            pts = points_map.get(true_rank, 0)
            if pts > 0:
                return pts, f"{'⭐' if true_rank == 1 else '✅'} +{pts}"
            return 0, "❌ +0"
    return 0, "❌ +0"


def score_range(picked_str, actual):
    """Score a range/exact number pick. Returns (points, result_str)"""
    try:
        picked_str = str(picked_str).strip()
        if "-" in picked_str:
            low, high = [int(x.strip()) for x in picked_str.split("-")]
        else:
            low = high = int(picked_str)
        if low <= actual <= high:
            icon = "⭐" if low == high else "✅"
            return 50, f"{icon} +50"
        return 0, f"❌ +0 (actual: {actual})"
    except Exception:
        return 0, "⬜ —"


def score_zero_points_team(picked_team, group_data):
    """Score the 'team to get 0 points' pick."""
    info = group_data.get(picked_team, {})
    actual_pts = info.get("pts", None)
    played = info.get("played", 0)
    if actual_pts is None:
        return 0, "⬜ Not found"
    if played < 3:
        return 0, f"⏳ {actual_pts} pts ({played}/3)"
    if actual_pts == 0:
        return 50, "⭐ +50"
    return 0, f"❌ +0 (got {actual_pts} pts)"



def score_perfect_group(picked_team, group_standings):
    """Score perfect group stage pick - team won all 3 games."""
    if not picked_team:
        return 0, "⬜ —"
    for letter, data in group_standings.items():
        for t in data["full"]:
            if t["name"] == picked_team:
                if t["played"] < 3:
                    return 0, f"⏳ {t['wins']}W/{t['played']} played"
                if t["wins"] == 3:
                    return 50, "⭐ +50"
                return 0, f"❌ +0 ({t['wins']}W in 3)"
    return 0, "⬜ Not found"


def score_fav_eliminated(picked_team, group_standings):
    """Score favourite eliminated pick."""
    if not picked_team:
        return 0, "⬜ —"
    # Extract just team name if format is 'Team (Group X)'
    team_name = picked_team.split(" (Group")[0].strip()
    for letter, data in group_standings.items():
        for t in data["full"]:
            if t["name"] == team_name:
                if t["played"] < 3:
                    return 0, f"⏳ {t['played']}/3 played"
                eliminated = not t.get("qualColor")
                if eliminated:
                    return 50, "⭐ +50"
                return 0, "❌ +0 (qualified)"
    return 0, "⬜ Not found"


def score_underdog_qualifies(picked_team, group_standings, real_qualifiers):
    """Score underdog qualifies pick."""
    if not picked_team:
        return 0, "⬜ —"
    team_name = picked_team.split(" (Group")[0].strip()
    for letter, data in group_standings.items():
        for t in data["full"]:
            if t["name"] == team_name:
                if t["played"] < 3:
                    return 0, f"⏳ {t['played']}/3 played"
                if t.get("qualColor"):
                    return 50, "⭐ +50"
                return 0, "❌ +0 (eliminated)"
    return 0, "⬜ Not found"



def load_knockout_predictions_for_scoring():
    """Load all knockout CSVs, return {name: {round: [picks]}}"""
    all_preds = {}
    for round_name, filename in KNOCKOUT_ROUND_CSVS.items():
        csv_path = os.path.join(BASE_DIR, filename)
        if not os.path.exists(csv_path):
            continue
        df = pd.read_csv(csv_path)
        num_matches = len([c for c in df.columns if c.startswith("Match")])
        for _, row in df.iterrows():
            name = str(row.get("Name", "")).strip()
            if not name or name == "nan":
                continue
            picks = [str(row.get(f"Match {i}", "")).strip() for i in range(1, num_matches + 1)]
            if name not in all_preds:
                all_preds[name] = {}
            all_preds[name][round_name] = picks
    return all_preds



def fetch_knockout_results():
    try:
        r = requests.get("https://www.fotmob.com/api/data/leagues?id=77", timeout=10)
        data = r.json()
        matches_raw = data.get("matches", {}).get("allMatches", [])
        results = {}
        for m in matches_raw:
            if m.get("round") == "1/16":
                mid = str(m["id"])
                status = m.get("status", {})
                finished = status.get("finished", False)
                score_str = status.get("scoreStr", "")
                home_name = m.get("home", {}).get("name", "")
                away_name = m.get("away", {}).get("name", "")
                winner = None
                home_score = None
                away_score = None
                if finished and score_str:
                    try:
                        parts = score_str.split(" - ")
                        home_score = int(parts[0].strip())
                        away_score = int(parts[1].strip())
                        if home_score > away_score:
                            winner = home_name
                        elif away_score > home_score:
                            winner = away_name
                        else:
                            # Draw — check penalty shootout
                            lost = status.get("whoLostOnPenalties")
                            if lost:
                                winner = away_name if lost == home_name else home_name
                    except:
                        pass
                results[mid] = {
                    "finished": finished,
                    "home": home_name,
                    "away": away_name,
                    "home_score": home_score,
                    "away_score": away_score,
                    "score_str": score_str,
                    "winner": winner,
                }
        return results
    except Exception as e:
        return {}
    
def fetch_knockout_results_for_scoring():
    """Fetch Round of 32 results from FotMob for scoring purposes."""
    try:
        r = requests.get("https://www.fotmob.com/api/data/leagues?id=77", timeout=10)
        data = r.json()
        matches_raw = data.get("fixtures", {}).get("allMatches", [])
        results = {}
        for m in matches_raw:
            if m.get("round") == "1/16":
                mid = str(m["id"])
                status = m.get("status", {})
                finished = status.get("finished", False)
                score_str = status.get("scoreStr", "")
                home_name = m.get("home", {}).get("name", "")
                away_name = m.get("away", {}).get("name", "")
                winner = None
                if finished and score_str:
                    try:
                        parts = score_str.split(" - ")
                        hs, as_ = int(parts[0].strip()), int(parts[1].strip())
                        if hs > as_:
                            winner = home_name
                        elif as_ > hs:
                            winner = away_name
                        else:
                            lost = status.get("whoLostOnPenalties")
                            if lost:
                                winner = away_name if lost == home_name else home_name
                    except:
                        pass
                results[mid] = {"finished": finished, "home": home_name, "away": away_name, "winner": winner}
        return results
    except:
        return {}

def score_knockout_total(person_name):
    """Returns total knockout points for a person across all rounds."""
    ko_preds = load_knockout_predictions_for_scoring()
    ko_results = fetch_knockout_results_for_scoring()
    person_preds = ko_preds.get(person_name, {})
    total = 0

    r32_picks = person_preds.get("Round of 32", [])
    r32_match_ids = ROUND_OF_32_IDS
    for i, mid in enumerate(r32_match_ids):
        pick = r32_picks[i] if i < len(r32_picks) else ""
        res = ko_results.get(mid, {})
        winner = res.get("winner")
        if winner and pick and pick.strip().lower() == winner.strip().lower():
            total += 20

    return total

def compute_all_points(person, group_standings, real_qualifiers,
                       group_data, player_stats, team_stats, match_stats):
    """
    Compute full points breakdown for one person.
    Returns dict of category -> points.
    """
    breakdown = {}

    # Groups
    _, quali_pts, exact_pts = score_groups(person, group_standings, real_qualifiers)
    breakdown["Groups (Quali)"] = quali_pts
    breakdown["Groups (Exact)"] = exact_pts

    # Player picks
    for cat, api_key in PLAYER_API_KEYS.items():
        picked = person["player_picks"].get(cat, "")
        top3 = player_stats.get(api_key, [])
        pts, _ = score_top3_pick(picked, top3)
        breakdown[f"Player: {cat}"] = pts

    # Team picks
    for cat, api_key in TEAM_API_KEYS.items():
        picked = person["team_picks"].get(cat, "")
        top3 = team_stats.get(api_key, [])
        pts, _ = score_top3_pick(picked, top3)
        breakdown[f"Team: {cat}"] = pts

    # Special: zero points team
    flat_group = {name: {"pts": d["full"][i]["pts"], "played": d["full"][i]["played"]}
                  for name, d in group_standings.items()
                  for i, t in enumerate(d["full"])
                  for name in [t["name"]]}
    pts, _ = score_zero_points_team(person["zero_points_team"], flat_group)
    breakdown["Special: 0 Pts Team"] = pts

    # Special: underdog combined points
    underdog_pts_total = sum(
        next((t["pts"] for t in d["full"] if t["name"] == team), 0)
        for name, d in group_standings.items()
        for team in UNDERDOG_TEAMS
        if any(t["name"] == team for t in d["full"])
    )
    pts, _ = score_range(person["underdog_points"], underdog_pts_total)
    breakdown["Special: Underdog Pts"] = pts

    # Special: match stats
    for field, label in [
        ("penalty_shootouts", "Special: Penalty Shootouts"),
        ("biggest_comeback",  "Special: Biggest Comeback"),
        ("most_goals_game",   "Special: Most Goals Game"),
        ("most_added_time",   "Special: Most Added Time"),
    ]:
        pts, _ = score_range(person[field], match_stats.get(field, 0))
        breakdown[label] = pts

    # Special: european top 4
    pts, _ = score_range(person.get("european_top4", ""), 0)
    breakdown["Special: European Top 4"] = pts

    # Special: perfect group stage
    pts, _ = score_perfect_group(person.get("perfect_group", ""), group_standings)
    breakdown["Special: Perfect Group"] = pts

    # Special: favourite eliminated
    pts, _ = score_fav_eliminated(person.get("fav_eliminated", ""), group_standings)
    breakdown["Special: Fav Eliminated"] = pts

    # Special: underdog qualifies
    pts, _ = score_underdog_qualifies(person.get("underdog_qualifies", ""), group_standings, real_qualifiers)
    breakdown["Special: Underdog Qualifies"] = pts

    # Knockout predictions
    ko_pts = score_knockout_total(person.get("_name", ""))
    breakdown["Knockouts"] = ko_pts

    breakdown["TOTAL"] = sum(breakdown.values())
    return breakdown
