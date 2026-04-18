import requests
import json
from datetime import datetime, timedelta
import time

BASE_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={}"
BASE_GAME_URL = "https://statsapi.mlb.com/api/v1.1/game/{}/feed/live"

OHTANI_ID = 660271


def get_games_for_date(date_str):
    data = requests.get(BASE_SCHEDULE_URL.format(date_str)).json()
    games = []

    for d in data.get("dates", []):
        for g in d.get("games", []):
            if g["status"]["detailedState"] == "Final":
                games.append(g["gamePk"])

    return games


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

            if pid is None or int(pid) != int(pitcher_id):
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

    return {"inning": None, "score": None}


def get_baker_window(game_data, pitcher_id):
    plays = game_data["liveData"]["plays"]["allPlays"]
    baker_plays = []

    for play in plays:
        matchup = play.get("matchup", {})
        pid = matchup.get("pitcher")

        if isinstance(pid, dict):
            pid = pid.get("id")

        if pid and int(pid) == int(pitcher_id):
            baker_plays.append(play)

    if not baker_plays:
        return None

    return {
        "start_inning": baker_plays[0]["about"]["inning"],
        "end_inning": baker_plays[-1]["about"]["inning"],
        "plays": baker_plays
    }


def is_hit(event_type):
    return event_type in ["single", "double", "triple", "home_run"]


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

                        player_info = game_data["gameData"]["players"].get(f"ID{player_id}", {})
                        position = player_info.get("primaryPosition", {}).get("abbreviation")

                        if position == "P":
                            continue

                        entry = get_entry_context(game_data, player_id)
                        window = get_baker_window(game_data, player_id)

                        if not window:
                            continue

                        # ----------------------------
                        # VS BAKER
                        # ----------------------------
                        runs_vs_baker = 0
                        hits_vs_baker = 0

                        for play in window["plays"]:
                            result = play.get("result", {})
                            event = result.get("eventType", "")

                            if is_hit(event):
                                hits_vs_baker += 1

                            runs_vs_baker += result.get("rbi", 0)

                        # ----------------------------
                        # ENTRY / FINAL DIFF + RUN LINE
                        # ----------------------------
                        entry_score = entry["score"]
                        final_score = game_data["liveData"]["linescore"]["teams"]

                        if entry_score:
                            home_entry = entry_score.get("home", 0)
                            away_entry = entry_score.get("away", 0)

                            home_final = final_score["home"]["runs"]
                            away_final = final_score["away"]["runs"]

                            if side == "home":
                                entry_diff = home_entry - away_entry
                                final_diff = home_final - away_final
                            else:
                                entry_diff = away_entry - home_entry
                                final_diff = away_final - home_final

                            run_line = entry_diff + 0.5

                            if final_diff > run_line:
                                run_line_result = "WIN"
                            elif final_diff < run_line:
                                run_line_result = "LOSS"
                            else:
                                run_line_result = "PUSH"

                        else:
                            entry_diff = None
                            final_diff = None
                            run_line = None
                            run_line_result = None

                        # ----------------------------
                        # TEAM TOTAL VS BAKER (NEW ADDITION)
                        # ----------------------------
                        team_total_vs_baker = None

                        if entry_score:
                            if side == "home":
                                entry_runs = entry_score.get("home", 0)
                                final_runs = final_score["home"]["runs"]
                            else:
                                entry_runs = entry_score.get("away", 0)
                                final_runs = final_score["away"]["runs"]

                            team_total_vs_baker = final_runs - entry_runs

                        # ----------------------------
                        # USED BAKER
                        # ----------------------------
                        dataset.append({
                            "type": "USED_BAKER",
                            "date": date_str,
                            "team": team["team"]["name"],
                            "opponent": opponent,
                            "player_name": name,

                            "inning_entered": window["start_inning"],
                            "inning_exited": window["end_inning"],

                            "IP": pitching.get("inningsPitched"),
                            "H": pitching.get("hits"),
                            "R": pitching.get("runs"),
                            "ER": pitching.get("earnedRuns"),
                            "BB": pitching.get("baseOnBalls"),
                            "K": pitching.get("strikeOuts"),
                            "HR": pitching.get("homeRuns"),
                            "ERA": pitching.get("era"),

                            "team_hits_vs_baker": hits_vs_baker,
                            "team_runs_vs_baker": runs_vs_baker,

                            "entry_run_diff": entry_diff,
                            "final_run_diff": final_diff,
                            "run_line": run_line,
                            "run_line_result": run_line_result
                        })

                        # ----------------------------
                        # FACED BAKER
                        # ----------------------------
                        dataset.append({
                            "type": "FACED_BAKER",
                            "date": date_str,
                            "team": opponent,
                            "opponent": team["team"]["name"],

                            "inning_entered": window["start_inning"],
                            "inning_exited": window["end_inning"],

                            "team_hits_vs_baker": hits_vs_baker,
                            "team_runs_vs_baker": runs_vs_baker,

                            # NEW SAFE METRIC
                            "team_total_vs_baker": team_total_vs_baker,

                            "entry_run_diff": entry_diff,
                            "final_run_diff": final_diff,
                            "run_line": run_line,
                            "run_line_result": run_line_result
                        })

                time.sleep(0.2)

            except Exception as e:
                print(f"Error game {game_pk}: {e}")

        current += timedelta(days=1)

    return dataset


def save_json(data, filename="mlb_data.json"):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    today = datetime.today()
    start = datetime(2026, 3, 20)

    data = build_dataset(start, today)

    save_json(data)

    print(f"\nSaved {len(data)} records to mlb_data.json")