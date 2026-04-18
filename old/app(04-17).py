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
# SPLIT DATA
# ----------------------------
used = team_df[team_df["type"] == "USED_BAKER"]
faced = team_df[team_df["type"] == "FACED_BAKER"]
if "team_total_vs_baker" not in faced.columns:
    faced["team_total_vs_baker"] = None


# ============================================================
# TABS (ONLY STRUCTURE CHANGE)
# ============================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Summary",
    "💰 Run Line (Used)",
    "💰 Run Line (Faced)",
    "📈 Team Total",
    "📋 Tables & Trends"
])

# ============================================================
# TAB 1 - SUMMARY
# ============================================================
with tab1:

    st.header("📊 Team Summary")

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Used Baker", len(used))
    col2.metric("Faced Baker", len(faced))

    col3.metric(
        "Runs Scored vs Baker",
        int(faced["team_runs_vs_baker"].sum()) if len(faced) > 0 else 0
    )

    col4.metric(
        "Runs Allowed Using Baker",
        int(used["R"].sum()) if len(used) > 0 else 0
    )

    col5.metric(
        "Avg Team Total vs Baker",
        round(faced["team_total_vs_baker"].mean(), 2) if len(faced) > 0 else 0
    )

    st.divider()

# ========================================================
# 🔽 GAME LOGS (NESTED TABS INSIDE SUMMARY ONLY)
# ========================================================

    st.subheader("📋 Game Logs")

    log_tab1, log_tab2 = st.tabs(["⚾ Used Baker", "🔥 Faced Baker"])

# ----------------------------
# USED BAKER LOGS
# ----------------------------
with log_tab1:

    if len(used) > 0:

        used_display = used.rename(columns={
            "date": "Date",
            "opponent": "Opponent",
            "player_name": "Player",
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

        st.dataframe(
            used_display.sort_values("Date", ascending=False)[
                [
                    "Date",
                    "Opponent",
                    "Player",
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
                ]
            ],
            use_container_width=True
        )

    else:
        st.info("No data available")

# ----------------------------
# FACED BAKER LOGS
# ----------------------------
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

        st.dataframe(
            faced_display.sort_values("Date", ascending=False)[
                [
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
                ]
            ],
            use_container_width=True
        )

    else:
        st.info("No data available")


# ============================================================
# TAB 2 - RUN LINE (USED BAKER)
# ============================================================
with tab2:

    st.subheader("💰 Run Line Performance (Using Baker)")

    if len(used) > 0 and "run_line_result" in used.columns:

        total_games = len(used)

        win = (used["run_line_result"] == "WIN").sum()
        loss = (used["run_line_result"] == "LOSS").sum()
        push = (used["run_line_result"] == "PUSH").sum()

        win_rate = (win / total_games) * 100
        loss_rate = (loss / total_games) * 100
        push_rate = (push / total_games) * 100

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Win Rate",
            f"{win}/{total_games} ({win_rate:.2f}%)"
        )

        c2.metric(
            "Loss Rate",
            f"{loss}/{total_games} ({loss_rate:.2f}%)"
        )

        c3.metric(
            "Push Rate",
            f"{push}/{total_games} ({push_rate:.2f}%)"
        )


# ============================================================
# TAB 3 - RUN LINE (FACED BAKER)
# ============================================================
with tab3:

    st.subheader("💰 Run Line vs Baker")

    if len(faced) > 0 and "run_line_result" in faced.columns:

        total_games = len(faced)

        win = (faced["run_line_result"] == "WIN").sum()
        loss = (faced["run_line_result"] == "LOSS").sum()
        push = (faced["run_line_result"] == "PUSH").sum()

        win_rate = (win / total_games) * 100
        loss_rate = (loss / total_games) * 100
        push_rate = (push / total_games) * 100

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Win Rate",
            f"{win}/{total_games} ({win_rate:.2f}%)"
        )

        c2.metric(
            "Loss Rate",
            f"{loss}/{total_games} ({loss_rate:.2f}%)"
        )

        c3.metric(
            "Push Rate",
            f"{push}/{total_games} ({push_rate:.2f}%)"
        )


# ============================================================
# TAB 4 - TEAM TOTAL (UNCHANGED LOGIC)
# ============================================================
with tab4:

    st.subheader("💰 Team Total vs Baker")

    if len(faced) > 0 and "team_total_vs_baker" in faced.columns:

        total_games = len(faced)

        over_0_5_wins = (faced["team_total_vs_baker"] >= 1).sum()
        over_0_5_losses = total_games - over_0_5_wins
        over_0_5_rate = (over_0_5_wins / total_games) * 100

        over_2_5_wins = (faced["team_total_vs_baker"] >= 3).sum()
        over_2_5_losses = total_games - over_2_5_wins
        over_2_5_rate = (over_2_5_wins / total_games) * 100

        over_3_5_wins = (faced["team_total_vs_baker"] >= 4).sum()
        over_3_5_losses = total_games - over_3_5_wins
        over_3_5_rate = (over_3_5_wins / total_games) * 100

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Over 0.5 Runs",
            f"{over_0_5_wins}/{total_games} ({over_0_5_rate:.2f}%)"
        )

        c2.metric(
            "Over 2.5 Runs",
            f"{over_2_5_wins}/{total_games} ({over_2_5_rate:.2f}%)"
        )

        c3.metric(
            "Over 3.5 Runs",
            f"{over_3_5_wins}/{total_games} ({over_3_5_rate:.2f}%)"
        )


# ============================================================
# TAB 5 - TABLES + TRENDS (UNCHANGED)
# ============================================================
with tab5:



    st.header("📈 Trends")

    if len(faced) > 0:
        chart_df = faced.rename(columns={
            "team_runs_vs_baker": "Runs vs Baker"
        })[["date", "Runs vs Baker"]].dropna().sort_values("date")

        chart_df = chart_df.set_index("date")

        st.line_chart(chart_df)

    if len(used) > 0:
        chart_used = used.rename(columns={
            "R": "Runs Allowed"
        })[["date", "Runs Allowed"]].dropna().sort_values("date")

        chart_used = chart_used.set_index("date")

        st.line_chart(chart_used)