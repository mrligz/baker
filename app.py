import streamlit as st
import json
import pandas as pd

st.set_page_config(layout="wide")

# ----------------------------
# LOAD DATA
# ----------------------------
with open("mlb_data.json", "r") as f:
    data = json.load(f)

df = pd.DataFrame(data)

st.title("⚾ MLB Baker Dashboard")

# ----------------------------
# CLEAN DATA
# ----------------------------
df["date"] = pd.to_datetime(df["date"], errors="coerce")

# ----------------------------
# TEAM SELECTOR
# ----------------------------
teams = sorted(df["team"].dropna().unique())
selected_team = st.selectbox("Select Team", teams)

team_df = df[df["team"] == selected_team].copy()

# ----------------------------
# FILTERS
# ----------------------------
st.sidebar.header("Filters")

type_filter = st.sidebar.selectbox(
    "Data Type",
    ["All", "USED_BAKER", "FACED_BAKER"]
)

date_filter = st.sidebar.date_input("Filter by Date", value=None)

blowout_only = st.sidebar.checkbox("Only Show Blowouts (6+ run diff)")

# ----------------------------
# APPLY FILTERS
# ----------------------------
if type_filter != "All":
    team_df = team_df[team_df["type"] == type_filter]

if date_filter:
    team_df = team_df[team_df["date"].dt.date == date_filter]

# ----------------------------
# BLOWOUT DETECTION
# ----------------------------
def get_run_diff(score):
    if isinstance(score, dict) and score.get("home") is not None:
        return abs(score["home"] - score["away"])
    return None

team_df["run_diff"] = team_df["score_at_entry"].apply(get_run_diff)

if blowout_only:
    team_df = team_df[team_df["run_diff"] >= 6]

# ----------------------------
# SPLIT DATA
# ----------------------------
used = team_df[team_df["type"] == "USED_BAKER"]
faced = team_df[team_df["type"] == "FACED_BAKER"]

# ----------------------------
# SUMMARY SECTION
# ----------------------------
st.header("📊 Team Summary")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Used Position Pitcher", len(used))
col2.metric("Faced Position Pitcher", len(faced))

col3.metric(
    "Runs Scored vs Baker",
    int(faced["team_runs"].sum()) if len(faced) > 0 else 0
)

col4.metric(
    "Runs Allowed Using Position Pitcher",
    int(used["runs_allowed"].sum()) if len(used) > 0 else 0
)



# ----------------------------
# USED Baker
# ----------------------------
st.header("⚾ Used Baker")

if len(used) > 0:
    st.dataframe(
        used.sort_values("date", ascending=False)[
            [
                "date",
                "opponent",
                "player_name",
                "innings",
                "runs_allowed",
                "hits_allowed",
                "inning_entered",
                "run_diff"
            ]
        ],
        use_container_width=True
    )
else:
    st.info("No data available")

# ----------------------------
# FACED Baker
# ----------------------------
st.header("🔥 Faced Baker")

if len(faced) > 0:
    st.dataframe(
        faced.sort_values("date", ascending=False)[
            [
                "date",
                "opponent",
                "team_runs"
            ]
        ],
        use_container_width=True
    )
else:
    st.info("No data available")
    
    # ----------------------------
# ADVANCED METRICS
# ----------------------------
st.subheader("📈 Advanced Metrics")

colA, colB, colC = st.columns(3)

if len(faced) > 0:
    colA.metric("Avg Runs vs Baker", round(faced["team_runs"].mean(), 2))

if len(used) > 0:
    colB.metric("Avg Runs Allowed (Using Them)", round(used["runs_allowed"].mean(), 2))

if len(team_df) > 0:
    colC.metric("Avg Run Diff at Entry", round(team_df["run_diff"].mean(), 2))

# ----------------------------
# CHARTS
# ----------------------------
st.header("📈 Trends")

if len(faced) > 0:
    chart_df = faced[["date", "team_runs"]].dropna().sort_values("date")
    chart_df = chart_df.set_index("date")

    st.subheader("Runs Scored vs Baker Over Time")
    st.line_chart(chart_df)

if len(used) > 0:
    chart_used = used[["date", "runs_allowed"]].dropna().sort_values("date")
    chart_used = chart_used.set_index("date")

    st.subheader("Runs Allowed When Using Baker")
    st.line_chart(chart_used)