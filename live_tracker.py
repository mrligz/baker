import requests
import time
import joblib

MODEL = joblib.load("model.pkl")

LIVE_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1"
GAME_URL = "https://statsapi.mlb.com/api/v1.1/game/{}/feed/live"

# ----------------------------
# GET LIVE GAMES
# ----------------------------
def get_live_games():
    r = requests.get(LIVE_SCHEDULE_URL)
    data = r.json()

    games = []

    for date in data.get("dates", []):
        for game in date.get("games", []):
            state = game["status"]["abstractGameState"]

            if state == "Live":
                games.append({
                    "gamePk": game["gamePk"],
                    "home": game["teams"]["home"]["team"]["name"],
                    "away": game["teams"]["away"]["team"]["name"]
                })

    return games


# ----------------------------
# GET LIVE GAME STATE
# ----------------------------
def get_game_state(game):
    r = requests.get(GAME_URL.format(game["gamePk"]))
    data = r.json()

    try:
        linescore = data["liveData"]["linescore"]

        home_runs = linescore["teams"]["home"]["runs"]
        away_runs = linescore["teams"]["away"]["runs"]

        inning = linescore.get("currentInning", 1)

        run_diff = abs(home_runs - away_runs)
        total_runs = home_runs + away_runs

        # count pitchers (fatigue proxy)
        pitcher_count = 0
        for side in ["home", "away"]:
            players = data["liveData"]["boxscore"]["teams"][side]["players"]

            for p in players.values():
                if p.get("stats", {}).get("pitching"):
                    pitcher_count += 1

        return {
            "home": game["home"],
            "away": game["away"],
            "inning": inning,
            "run_diff": run_diff,
            "total_runs": total_runs,
            "pitcher_count": pitcher_count
        }

    except:
        return None


# ----------------------------
# PREDICT BAKER
# ----------------------------
def predict_baker(state):
    X = [[
        state["total_runs"],
        state["run_diff"],
        state["inning"],
        state["pitcher_count"]
    ]]

    pred = MODEL.predict(X)[0]
    prob = MODEL.predict_proba(X)[0][1]

    return pred, prob


# ----------------------------
# MAIN LOOP
# ----------------------------
def run_tracker():
    print("🚀 Live Baker Tracker Started...\n")

    seen_alerts = set()

    while True:
        games = get_live_games()

        for game in games:
            state = get_game_state(game)

            if not state:
                continue

            pred, prob = predict_baker(state)

            game_id = f"{state['away']} @ {state['home']}"

            # 🔥 ALERT CONDITIONS
            if pred == 1 and prob > 0.65 and state["inning"] >= 6:
                alert_key = f"{game_id}_{state['inning']}"

                if alert_key not in seen_alerts:
                    seen_alerts.add(alert_key)

                    print("\n🚨 BAKER ALERT 🚨")
                    print(f"Game: {game_id}")
                    print(f"Inning: {state['inning']}")
                    print(f"Run Diff: {state['run_diff']}")
                    print(f"Total Runs: {state['total_runs']}")
                    print(f"Pitchers Used: {state['pitcher_count']}")
                    print(f"Probability: {round(prob*100,1)}%")
                    print("-" * 40)

        time.sleep(30)  # refresh every 30 seconds


if __name__ == "__main__":
    run_tracker()