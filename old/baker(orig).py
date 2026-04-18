import requests
from datetime import datetime, timedelta
import time

BASE_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={}"
BASE_GAME_URL = "https://statsapi.mlb.com/api/v1.1/game/{}/feed/live"


# ----------------------------
# Get completed games only
# ----------------------------
def get_games_for_date(date_str):
    data = requests.get(BASE_SCHEDULE_URL.format(date_str)).json()

    game_pks = []

    for d in data.get("dates", []):
        for g in d.get("games", []):
            if g["status"]["detailedState"] == "Final":
                game_pks.append(g["gamePk"])

    return game_pks


# ----------------------------
# Find inning + score at first pitching appearance
# (best available MLB method)
# ----------------------------
def get_entry_context(game_data, pitcher_id):
    plays = game_data["liveData"]["plays"]["allPlays"]

    inning_entered = None
    score_at_entry = None

    for play in plays:
        matchup = play.get("matchup", {})
        about = play.get("about", {})
        result = play.get("result", {})

        pid = matchup.get("pitcher")

        # normalize pitcher id (MLB is inconsistent)
        if isinstance(pid, dict):
            pid = pid.get("id")

        try:
            pid = int(pid)
            pitcher_id = int(pitcher_id)
        except:
            continue

        if pid == pitcher_id:
            if inning_entered is None:
                inning_entered = about.get("inning")

                score_at_entry = {
                    "home": result.get("homeScore"),
                    "away": result.get("awayScore")
                }
            break

    return inning_entered, score_at_entry


# ----------------------------
# Core detection logic
# ----------------------------
def get_position_player_pitching(game_pk):
    url = BASE_GAME_URL.format(game_pk)
    data = requests.get(url).json()

    box = data["liveData"]["boxscore"]["teams"]
    game_data_players = data["gameData"]["players"]

    results = []

    for side in ["home", "away"]:
        team = box[side]
        opponent = box["away"]["team"]["name"] if side == "home" else box["home"]["team"]["name"]

        for p in team["players"].values():

            pitching = p.get("stats", {}).get("pitching")

            # must have pitched in this game
            if not pitching:
                continue

            name = p["person"]["fullName"]
            player_id = p["person"]["id"]

            # exclude Shohei Ohtani
            if name == "Shohei Ohtani":
                continue

            # roster-based position check (most reliable available field)
            player_info = game_data_players.get(f"ID{player_id}", {})
            position = player_info.get("primaryPosition", {}).get("abbreviation")

            # skip real pitchers
            if position == "P":
                continue

            inning, score = get_entry_context(data, player_id)

            results.append({
                "name": name,
                "team": team["team"]["name"],
                "opponent": opponent,
                "innings_pitched": pitching.get("inningsPitched"),
                "hits": pitching.get("hits"),
                "runs": pitching.get("runs"),
                "inning_entered": inning,
                "score_at_entry": score
            })

    return results


# ----------------------------
# Season loop
# ----------------------------
def iterate_season(start_date, end_date):
    current = start_date

    while current <= end_date:
        date_str = current.strftime("%Y-%m-%d")

        print(f"\nChecking {date_str}...")

        games = get_games_for_date(date_str)

        for game_pk in games:
            try:
                results = get_position_player_pitching(game_pk)

                for r in results:
                    print("\n🚨 POSITION PLAYER PITCHED 🚨")
                    print(f"Name: {r['name']}")
                    print(f"{r['team']} vs {r['opponent']}")
                    print(f"Innings Pitched: {r['innings_pitched']}")
                    print(f"Hits Allowed: {r['hits']}")
                    print(f"Runs Allowed: {r['runs']}")
                    print(f"Inning Entered: {r['inning_entered']}")
                    print(f"Score at Entry: {r['score_at_entry']}")
                    print("-" * 50)

                time.sleep(0.25)

            except Exception as e:
                print(f"Error with game {game_pk}: {e}")

        current += timedelta(days=1)


# ----------------------------
# MAIN (THIS SEASON ONLY)
# ----------------------------
if __name__ == "__main__":
    today = datetime.today()

    season_start = datetime(today.year, 3, 20)

    iterate_season(season_start, today)