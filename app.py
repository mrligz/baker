import streamlit as st
import json
import pandas as pd
import requests

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(layout="wide")

# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>

.stApp {
    background: radial-gradient(circle at top, #0b1220, #070a12);
    color: #e6edf3;
}

h1 {
    font-size: 42px !important;
    font-weight: 800;
    color: #ffffff;
}

[data-testid="stMetric"] {
    background: linear-gradient(145deg, #121a2a, #0d1422);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 18px;
    border-radius: 16px;
}

/* PILL BUTTONS */
button[kind="secondary"] {
    background: linear-gradient(145deg, #121a2a, #0d1422);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 999px;
    color: #9aa4b2;
    transition: all 0.25s ease-in-out;
    font-size: 14px;
}

button[kind="secondary"]:hover {
    border: 1px solid rgba(0,180,255,0.4);
    color: #ffffff;
    transform: translateY(-2px);
}

button[kind="primary"] {
    background: rgba(0,180,255,0.20) !important;
    border: 1px solid rgba(0,180,255,0.65) !important;
    color: white !important;
    box-shadow: 0 0 16px rgba(0,180,255,0.30);
}

button[kind="primary"],
button[kind="secondary"] {
    white-space: nowrap !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 6px !important;
    padding: 8px 14px !important;
}

button img {
    height: 24px !important;
    width: 24px !important;
    object-fit: contain;
}

.team-header {
    position: sticky;
    top: 0;
    z-index: 999;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 12px 0 10px 0;
    margin-bottom: 15px;
    background: linear-gradient(180deg, #0b1220 80%, rgba(11,18,32,0));
    backdrop-filter: blur(6px);
}

.team-logo {
    width: 70px;
    height: 70px;
    object-fit: contain;
    filter: drop-shadow(0 0 10px rgba(0,180,255,0.5));
    margin-bottom: 6px;
}

.team-name1 {
    font-size: 18px;
    font-weight: 600;
    color: #e6edf3;
    letter-spacing: 0.5px;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# DATA
# ============================================================
@st.cache_data
def load_data():
    with open("mlb_data.json", "r") as f:
        return json.load(f)

df = pd.DataFrame(load_data())
df["date"] = pd.to_datetime(df["date"], errors="coerce")

# ============================================================
# TEAM MAP (ONLY ONCE)
# ============================================================
team_map = {
    "Arizona Diamondbacks": "ari",
    "Atlanta Braves": "atl",
    "Baltimore Orioles": "bal",
    "Boston Red Sox": "bos",
    "Chicago Cubs": "chc",
    "Chicago White Sox": "chw",
    "Cincinnati Reds": "cin",
    "Cleveland Guardians": "cle",
    "Colorado Rockies": "col",
    "Detroit Tigers": "det",
    "Houston Astros": "hou",
    "Kansas City Royals": "kc",
    "Los Angeles Angels": "laa",
    "Los Angeles Dodgers": "lad",
    "Miami Marlins": "mia",
    "Milwaukee Brewers": "mil",
    "Minnesota Twins": "min",
    "New York Mets": "nym",
    "New York Yankees": "nyy",
    "Oakland Athletics": "oak",
    "Philadelphia Phillies": "phi",
    "Pittsburgh Pirates": "pit",
    "San Diego Padres": "sd",
    "San Francisco Giants": "sf",
    "Seattle Mariners": "sea",
    "St. Louis Cardinals": "stl",
    "Tampa Bay Rays": "tb",
    "Texas Rangers": "tex",
    "Toronto Blue Jays": "tor",
    "Washington Nationals": "wsh",
}

def get_logo(team):
    code = team_map.get(team)
    return f"https://a.espncdn.com/i/teamlogos/mlb/500/{code}.png" if code else None

def format_team_label(team):
    if team == "All Teams":
        return "🏟️ All Teams"

    code = team_map.get(team)
    if code:
        return f"![logo]({get_logo(team)}) {team}"

    return f"⚾ {team}"

# ========================
# COLOR CARD HELPER
# ========================
def render_stat_card(label, value, pct):
    if pct >= 55:
        border = "rgba(0,255,159,0.7)"
        glow = "rgba(0,255,159,0.35)"
        color = "#00ff9f"
    elif pct <= 45:
        border = "rgba(255,77,77,0.7)"
        glow = "rgba(255,77,77,0.35)"
        color = "#ff4d4d"
    else:
        border = "rgba(255,255,255,0.08)"
        glow = "rgba(255,255,255,0)"
        color = "#9aa4b2"

    st.markdown(f"""
    <div style="
        background: linear-gradient(145deg, #121a2a, #0d1422);
        border: 1px solid {border};
        box-shadow: 0 0 12px {glow};
        padding: 18px;
        border-radius: 16px;
        text-align: center;
        min-height: 108px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    ">
        <div style="font-size: 14px; color: #9aa4b2; margin-bottom: 8px;">{label}</div>
        <div style="font-size: 28px; font-weight: 700; color: {color};">{value}</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# LIVE HELPERS
# ============================================================
LIVE_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1"
LIVE_GAME_URL = "https://statsapi.mlb.com/api/v1.1/game/{}/feed/live"

def get_live_games():
    data = requests.get(LIVE_SCHEDULE_URL, timeout=15).json()
    games = []

    for d in data.get("dates", []):
        for g in d.get("games", []):
            if g.get("status", {}).get("abstractGameState") == "Live":
                games.append({
                    "gamePk": g["gamePk"],
                    "home_team": g["teams"]["home"]["team"]["name"],
                    "away_team": g["teams"]["away"]["team"]["name"],
                })

    return games

def get_live_game_box(game_pk):
    data = requests.get(LIVE_GAME_URL.format(game_pk), timeout=15).json()

    linescore = data.get("liveData", {}).get("linescore", {})
    teams = linescore.get("teams", {})

    home = teams.get("home", {}).get("runs", 0)
    away = teams.get("away", {}).get("runs", 0)

    inning = linescore.get("currentInning")
    inning_state = linescore.get("inningState", "")
    diff = abs(home - away)

    return {
        "home_runs": home,
        "away_runs": away,
        "inning": inning,
        "inning_state": inning_state,
        "run_diff": diff,
    }

def get_previous_bakers_for_team(team_name, df):
    used = df[df["type"] == "USED_BAKER"].copy()
    team_used = used[used["team"] == team_name].copy()

    if len(team_used) == 0:
        return pd.DataFrame()

    cols = [
        "date",
        "player_name",
        "opponent",
        "IP",
        "H",
        "R",
        "ER",
        "BB",
        "K",
        "HR",
        "ERA",
    ]
    existing = [c for c in cols if c in team_used.columns]
    return team_used[existing].sort_values("date", ascending=False)

# ============================================================
# SESSION STATE
# ============================================================
if "selected_team" not in st.session_state:
    st.session_state.selected_team = "All Teams"

teams = ["All Teams"] + sorted(df["team"].dropna().unique().tolist())

# ============================================================
# HEADER
# ============================================================
st.title("⚾ MLB Baker Dashboard")

logo_url = get_logo(st.session_state.selected_team)
display_name = "MLB" if st.session_state.selected_team == "All Teams" else st.session_state.selected_team

if logo_url:
    st.markdown(f"""
<div style="text-align:center; margin-top:10px; filter: drop-shadow(0 0 12px rgba(0,180,255,0.5)); font-size:25px;">
    <img src="{logo_url}" width="120">
    <div class="team-name1">{display_name}</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# TEAM SELECTOR (FIXED - NO 1 CLICK BUG)
# ============================================================
st.markdown("### 🏟️ Select Team")

selected_team = st.session_state.selected_team

cols = st.columns(6)

for i, team in enumerate(teams):
    col = cols[i % 6]

    is_selected = st.session_state.get("selected_team", "All Teams") == team

    if col.button(
        format_team_label(team),
        key=f"team_{team}",
        use_container_width=True,
        type="primary" if is_selected else "secondary"
    ):
        if st.session_state.selected_team != team:
            st.session_state.selected_team = team
            st.rerun()

# ============================================================
# FILTER
# ============================================================
team_df = df if selected_team == "All Teams" else df[df["team"] == selected_team]

used = team_df[team_df["type"] == "USED_BAKER"].copy()
faced = team_df[team_df["type"] == "FACED_BAKER"].copy()

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Summary",
    "💰 Run Line (Used)",
    "💰 Run Line (Faced)",
    "📈 Team Total",
    "📋 Tables & Trends",
    "🔴 Live"
])

# ============================================================
# SUMMARY
# ============================================================
with tab1:
    st.header("📊 Team Summary")

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Used Baker", len(used))
    c2.metric("Faced Baker", len(faced))
    c3.metric("Runs Scored", int(faced["team_runs_vs_baker"].sum()) if len(faced) else 0)
    c4.metric("Runs Allowed", int(used["R"].sum()) if len(used) else 0)
    c5.metric("Avg Runs vs Baker", round(faced["team_runs_vs_baker"].mean(), 2) if len(faced) else 0)

    st.divider()

    st.subheader("📋 Game Logs")
    log_tab1, log_tab2 = st.tabs(["⚾ Used Baker", "🔥 Faced Baker"])

    # ============================================================
    # USED LOGS
    # ============================================================
    with log_tab1:
        if len(used) > 0:
            used_display = used.rename(columns={
                "date": "Date",
                "player_name": "Baker",
                "opponent": "Opponent",
                "inning_entered": "Inning Entered",
                "inning_exited": "Inning Exited",

                "IP": "IP",
                "H": "Hits",
                "R": "Runs",
                "ER": "ER",
                "BB": "BB",
                "K": "K",
                "HR": "HR",
                "ERA": "ERA",

                "entry_run_diff": "Entry Diff",
                "final_run_diff": "Final Diff",
                "run_line": "Run Line",
                "run_line_result": "Result"
            })

            used_display["Opponent"] = used_display["Opponent"].apply(
                lambda x: f"<img src='{get_logo(x)}' width='18' style='vertical-align:middle;margin-right:6px'> {x}"
            )
            
            used_display["Baker"] = used_display.apply(
                lambda row: f"<img src='{get_logo(row['team'])}' width='18' style='vertical-align:middle;margin-right:6px'> {row['Baker']}",
                axis=1
            )

            st.markdown(
                used_display.sort_values("Date", ascending=False)[
                    [
                        "Date",
                        "Baker",
                        "Opponent",
                        "Inning Entered",
                        "Inning Exited",

                        "IP",
                        "Hits",
                        "Runs",
                        "ER",
                        "BB",
                        "K",
                        "HR",
                        "ERA",

                        "Entry Diff",
                        "Final Diff",
                        "Run Line",
                        "Result"
                    ]].to_html(escape=False, index=False),
                unsafe_allow_html=True
            )
        else:
            st.info("No data available")

    # ============================================================
    # FACED LOGS
    # ============================================================
    with log_tab2:
        if len(faced) > 0:
            faced_display = faced.rename(columns={
                "date": "Date",
                "team": "Team",
                "opponent": "Opponent",
                "player_name": "Baker",
                "team_hits_vs_baker": "Hits",
                "team_runs_vs_baker": "Runs",
                "inning_entered": "Inning Entered",
                "inning_exited": "Inning Exited",
                "run_line": "Run Line",
                "run_line_result": "Result",
            })

            # Build Baker column FIRST, while Opponent is still plain team text
            faced_display["Baker"] = faced_display.apply(
                lambda row: f"<img src='{get_logo(row['Opponent'])}' width='18' style='vertical-align:middle;margin-right:6px'> {row['Baker']}"
                if pd.notna(row["Baker"]) else "",
                axis=1
            )

            # Then convert Team and Opponent columns to logo HTML
            faced_display["Team"] = faced_display["Team"].apply(
                lambda x: f"<img src='{get_logo(x)}' width='18' style='vertical-align:middle;margin-right:6px'> {x}"
            )

            faced_display["Opponent"] = faced_display["Opponent"].apply(
                lambda x: f"<img src='{get_logo(x)}' width='18' style='vertical-align:middle;margin-right:6px'> {x}"
            )

            st.markdown(
                faced_display.sort_values("Date", ascending=False)[[
                    "Date",
                    "Team",
                    "Opponent",
                    "Baker",
                    "Hits",
                    "Runs",
                    "Inning Entered",
                    "Inning Exited",
                    "Run Line",
                    "Result"
                ]].to_html(escape=False, index=False),
                unsafe_allow_html=True
            )
        else:
            st.info("No data available")

# ============================================================
# RUN LINE USED
# ============================================================
with tab2:
    st.subheader("💰 Run Line (Using Baker)")

    if len(used):
        total = len(used)
        win = (used["run_line_result"] == "WIN").sum()
        loss = (used["run_line_result"] == "LOSS").sum()

        win_pct = (win / total * 100) if total > 0 else 0
        loss_pct = (loss / total * 100) if total > 0 else 0

        c1, c2 = st.columns(2)

        with c1:
            render_stat_card("Win", f"{win}/{total} ({win_pct:.0f}%)", win_pct)

        with c2:
            render_stat_card("Loss", f"{loss}/{total} ({loss_pct:.0f}%)", loss_pct)

# ============================================================
# RUN LINE FACED
# ============================================================
with tab3:
    st.subheader("💰 Run Line vs Baker")

    if len(faced):
        total = len(faced)
        win = (faced["run_line_result"] == "WIN").sum()
        loss = (faced["run_line_result"] == "LOSS").sum()

        win_pct = (win / total * 100) if total > 0 else 0
        loss_pct = (loss / total * 100) if total > 0 else 0

        c1, c2 = st.columns(2)

        with c1:
            render_stat_card("Win", f"{win}/{total} ({win_pct:.0f}%)", win_pct)

        with c2:
            render_stat_card("Loss", f"{loss}/{total} ({loss_pct:.0f}%)", loss_pct)

# ============================================================
# TEAM TOTAL
# ============================================================
with tab4:
    st.subheader("💰 Team Runs vs Baker")

    if len(faced):
        total = len(faced)

        over1 = (faced["team_runs_vs_baker"] >= 1).sum()
        over2 = (faced["team_runs_vs_baker"] >= 2).sum()
        over3 = (faced["team_runs_vs_baker"] >= 3).sum()

        p1 = (over1 / total * 100) if total > 0 else 0
        p2 = (over2 / total * 100) if total > 0 else 0
        p3 = (over3 / total * 100) if total > 0 else 0

        c1, c2, c3 = st.columns(3)

        with c1:
            render_stat_card("Over 0.5", f"{over1}/{total} ({p1:.0f}%)", p1)

        with c2:
            render_stat_card("Over 1.5", f"{over2}/{total} ({p2:.0f}%)", p2)

        with c3:
            render_stat_card("Over 2.5", f"{over3}/{total} ({p3:.0f}%)", p3)
    else:
        st.info("No data available")

# ============================================================
# TRENDS
# ============================================================
with tab5:
    st.header("📈 Trends")

    if len(faced):
        st.line_chart(faced.sort_values("date").set_index("date")["team_runs_vs_baker"])

    if len(used):
        st.line_chart(used.sort_values("date").set_index("date")["R"])

# ============================================================
# LIVE
# ============================================================
with tab6:
    st.header("🔴 Live Games")

    live_games = get_live_games()

    if not live_games:
        st.info("No live MLB games right now.")
    else:
        for game in live_games:
            box = get_live_game_box(game["gamePk"])

            home_team = game["home_team"]
            away_team = game["away_team"]

            home_logo = get_logo(home_team)
            away_logo = get_logo(away_team)

            highlight = box["run_diff"] >= 8
            border = "2px solid #ff4d4d" if highlight else "1px solid rgba(255,255,255,0.08)"
            glow = "0 0 14px rgba(255,77,77,0.35)" if highlight else "none"

            st.markdown(f"""
            <div style="
                background: linear-gradient(145deg, #121a2a, #0d1422);
                border: {border};
                box-shadow: {glow};
                border-radius: 16px;
                padding: 16px;
                margin-bottom: 16px;
            ">
                <div style="display:flex; align-items:center; justify-content:space-between; gap:16px; flex-wrap:wrap;">
                    <div style="display:flex; align-items:center; gap:10px;">
                        <img src="{away_logo}" width="34">
                        <div style="font-size:18px; font-weight:700;">{away_team}</div>
                        <div style="font-size:24px; font-weight:800;">{box["away_runs"]}</div>
                    </div>

                    <div style="font-size:16px; color:#9aa4b2;">
                        {box["inning_state"]} {box["inning"] if box["inning"] else ""}
                    </div>

                    <div style="display:flex; align-items:center; gap:10px;">
                        <div style="font-size:24px; font-weight:800;">{box["home_runs"]}</div>
                        <div style="font-size:18px; font-weight:700;">{home_team}</div>
                        <img src="{home_logo}" width="34">
                    </div>
                </div>

                <div style="margin-top:10px; font-size:15px; color:{'#ff4d4d' if highlight else '#9aa4b2'}; font-weight:700;">
                    Run Differential: {box["run_diff"]}{'  •  Baker Watch' if highlight else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)

            if highlight:
                st.markdown("#### Previous Bakers")
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"**{away_team}**")
                    away_prev = get_previous_bakers_for_team(away_team, df)
                    if len(away_prev):
                        st.dataframe(away_prev, use_container_width=True, hide_index=True)
                    else:
                        st.info("No previous Bakers found.")

                with col2:
                    st.markdown(f"**{home_team}**")
                    home_prev = get_previous_bakers_for_team(home_team, df)
                    if len(home_prev):
                        st.dataframe(home_prev, use_container_width=True, hide_index=True)
                    else:
                        st.info("No previous Bakers found.")