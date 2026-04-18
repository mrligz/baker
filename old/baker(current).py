import requests
import json
from datetime import datetime, timedelta
import time

BASE_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={}"
BASE_GAME_URL = "https://statsapi.mlb.com/api/v1.1/game/{}/feed/live"

OHTANI_ID = 660271


# ----------------------------
# Get completed games only
# ----------------------------
def get_games_for_date(date_str):
    data = requests.get(BASE_SCHEDULE_URL.format(date_str)).json()

    games = []

    for d in data.get("dates", []):
        for g in d.get("games", []):
            if g["status"]["detailedState"] == "Final":
                games.append(g["gamePk"])

    return games


# ----------------------------
# SAFE entry context (inning + score)
# ----------------------------
def get_entry_context(game_data, pitcher_id):
    try:
        plays = game_data["liveData"]["plays"]["allPlays"]

        for play in plays:
            matchup = play.get("matchup", {})
            about = play.get("about", {})
            result = play.get("result", {})

            pid = matchup.get("pitcher")

            if isinstance(pid, dict):
                pid = pid.get("id")

            if pid is None:
                continue

            if int(pid) != int(pitcher_id):
                continue

            return {
                "inning": about.get("inning"),
                "score": {
                    "home": result.get("homeScore"),
                    "away": result.get("awayScore")
                }
            }

    except:
        pass

    return {
        "inning": None,
        "score": None
    }


# ----------------------------
# Build dataset
# ----------------------------
def build_dataset(start_date, end_date):
    dataset = []
    current = start_date

    while current <= end_date:
        date_str = current.strftime("%Y-%m-%d")
        print(f"Processing {date_str}...")

        games = get_games_for_date(date_str)

        for game_pk in games:
            try:
                game_data = requests.get(BASE_GAME_URL.format(game_pk)).json()

                box = game_data["liveData"]["boxscore"]["teams"]

                home_team = box["home"]["team"]["name"]
                away_team = box["away"]["team"]["name"]

                # ----------------------------
                # USED BAKER (position player pitched)
                # ----------------------------
                for side in ["home", "away"]:
                    team = box[side]
                    opponent = away_team if side == "home" else home_team

                    for p in team["players"].values():

                        pitching = p.get("stats", {}).get("pitching")
                        if not pitching:
                            continue

                        player_id = p["person"]["id"]
                        name = p["person"]["fullName"]

                        if player_id == OHTANI_ID:
                            continue

                        # get position safely
                        player_info = game_data["gameData"]["players"].get(f"ID{player_id}", {})
                        position = player_info.get("primaryPosition", {}).get("abbreviation")

                        if position is None:
                            continue

                        # ONLY position players pitching
                        if position == "P":
                            continue

                        entry = get_entry_context(game_data, player_id)

                        dataset.append({
                            "type": "USED_BAKER",
                            "date": date_str,
                            "team": team["team"]["name"],
                            "opponent": opponent,
                            "player_name": name,
                            "innings": pitching.get("inningsPitched"),
                            "hits_allowed": pitching.get("hits"),
                            "runs_allowed": pitching.get("runs"),
                            "inning_entered": entry["inning"],
                            "score_at_entry": entry["score"]
                        })

                # ----------------------------
                # FACED BAKER (game-level flag)
                # ----------------------------
                for side in ["home", "away"]:
                    opp_side = "away" if side == "home" else "home"

                    opponent_players = box[opp_side]["players"]
                    team_name = box[side]["team"]["name"]
                    opponent_name = box[opp_side]["team"]["name"]

                    used_baker = False

                    for p in opponent_players.values():
                        pitching = p.get("stats", {}).get("pitching")

                        if not pitching:
                            continue

                        player_id = p["person"]["id"]

                        player_info = game_data["gameData"]["players"].get(f"ID{player_id}", {})
                        position = player_info.get("primaryPosition", {}).get("abbreviation")

                        if position and position != "P":
                            used_baker = True
                            break

                    if used_baker:
                        dataset.append({
                            "type": "FACED_BAKER",
                            "date": date_str,
                            "team": team_name,
                            "opponent": opponent_name,
                            "player_name": None,
                            "innings": None,
                            "hits_allowed": None,
                            "runs_allowed": None,
                            "inning_entered": None,
                            "score_at_entry": None,
                            "team_runs": box[side]["teamStats"]["batting"]["runs"]
                        })

                time.sleep(0.2)

            except Exception as e:
                print(f"Error game {game_pk}: {e}")

        current += timedelta(days=1)

    return dataset


# ----------------------------
# SAVE JSON
# ----------------------------
def save_json(data, filename="mlb_data.json"):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


# ----------------------------
# RUN
# ----------------------------
if __name__ == "__main__":
    today = datetime.today()
    start = datetime(today.year, 3, 20)

    data = build_dataset(start, today)

    save_json(data)

    print(f"\nSaved {len(data)} records to mlb_data.json")