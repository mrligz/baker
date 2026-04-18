import streamlit as st
import json
import pandas as pd

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
# TEAM SELECTOR
# ============================================================
st.markdown("### 🏟️ Select Team")

cols = st.columns(6)

for i, team in enumerate(teams):
    col = cols[i % 6]
    is_selected = st.session_state.selected_team == team

    if col.button(
        format_team_label(team),
        key=f"team_{team}",
        use_container_width=True,
        type="primary" if is_selected else "secondary"
    ):
        st.session_state.selected_team = team

selected_team = st.session_state.selected_team

# ============================================================
# FILTER
# ============================================================
team_df = df if selected_team == "All Teams" else df[df["team"] == selected_team]

used = team_df[team_df["type"] == "USED_BAKER"]
faced = team_df[team_df["type"] == "FACED_BAKER"]

if "team_total_vs_baker" not in faced.columns:
    faced["team_total_vs_baker"] = None

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Summary",
    "💰 Run Line (Used)",
    "💰 Run Line (Faced)",
    "📈 Team Total",
    "📋 Tables & Trends"
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
    c5.metric("Avg Total", round(faced["team_total_vs_baker"].mean(), 2) if len(faced) else 0)

    st.divider()

    st.subheader("📋 Game Logs")
    log_tab1, log_tab2 = st.tabs(["⚾ Used Baker", "🔥 Faced Baker"])

# ============================================================
# USED LOGS
# ============================================================
with log_tab1:
    if len(used):
        used_display = used.sort_values("date", ascending=False)
        st.dataframe(used_display)
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
            "team_hits_vs_baker": "Hits",
            "team_runs_vs_baker": "Runs",
            "inning_entered": "Inning Entered",
            "inning_exited": "Inning Exited",
            "run_line": "Run Line",
            "run_line_result": "Result",
            "team_total_vs_baker": "Team Total vs Baker",
        })

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
                "Hits",
                "Runs",
                "Team Total vs Baker",
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
        push = (used["run_line_result"] == "PUSH").sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("Win", f"{win}/{total}")
        c2.metric("Loss", f"{loss}/{total}")
        c3.metric("Push", f"{push}/{total}")

# ============================================================
# RUN LINE FACED
# ============================================================
with tab3:
    st.subheader("💰 Run Line vs Baker")

    if len(faced):
        total = len(faced)
        win = (faced["run_line_result"] == "WIN").sum()
        loss = (faced["run_line_result"] == "LOSS").sum()
        push = (faced["run_line_result"] == "PUSH").sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("Win", f"{win}/{total}")
        c2.metric("Loss", f"{loss}/{total}")
        c3.metric("Push", f"{push}/{total}")

# ============================================================
# TEAM TOTAL
# ============================================================
with tab4:
    st.subheader("💰 Team Total vs Baker")

    if len(faced):
        total = len(faced)

        over1 = (faced["team_total_vs_baker"] >= 1).sum()
        over3 = (faced["team_total_vs_baker"] >= 3).sum()
        over4 = (faced["team_total_vs_baker"] >= 4).sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("Over 0.5", f"{over1}/{total}")
        c2.metric("Over 2.5", f"{over3}/{total}")
        c3.metric("Over 3.5", f"{over4}/{total}")

# ============================================================
# TRENDS
# ============================================================
with tab5:
    st.header("📈 Trends")

    if len(faced):
        st.line_chart(faced.sort_values("date").set_index("date")["team_runs_vs_baker"])

    if len(used):
        st.line_chart(used.sort_values("date").set_index("date")["R"])