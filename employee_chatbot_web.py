import streamlit as st
import pandas as pd
import difflib

# Load your merged dataset
@st.cache_data
def load_data():
    # Load all five employee datasets
    df1 = pd.read_csv("employees (1).csv")
    df2 = pd.read_csv("employees (2).csv")
    df3 = pd.read_csv("employees (3).csv")
    df4 = pd.read_csv("employees (4).csv")
    df5 = pd.read_csv("employees (5).csv")

    # Merge datasets on user_id
    merged = df1.merge(df2, on="user_id", how="outer")
    merged = merged.merge(df3, on="user_id", how="outer")

    # Drop conflicting columns from df4 and merge
    df4 = df4.drop(
        columns=[
            col for col in df4.columns
            if col in merged.columns and col != "user_id"
        ]
    )
    merged = merged.merge(df4, on="user_id", how="outer")

    # Drop conflicting columns from df5 and merge
    df5 = df5.drop(
        columns=[
            col for col in df5.columns
            if col in merged.columns and col != "user_id"
        ]
    )
    merged = merged.merge(df5, on="user_id", how="outer")

    # Rename columns for consistency
    merged = merged.rename(columns={
        "average_okr_score_df1": "average_okr_score",
        "average_kpi_score_df2": "average_kpi_score",
        "average_manager_score_df4": "average_manager_score",
    })

    # Fill missing scores with 0
    for col in [
        "average_okr_score",
        "average_kpi_score",
        "average_manager_score"
    ]:
        if col in merged.columns:
            merged[col] = merged[col].fillna(0)

    return merged


# Core recommendation function
def get_best_employees(team_name, df, top_n=5):
    team_name = team_name.strip().lower()

    # Return four values consistently
    empty_df = pd.DataFrame()
    empty_suggestions = []

    if "team_name" not in df.columns:
        return empty_df, empty_df, empty_df, empty_suggestions

    # Remove missing team names and normalize capitalization
    team_names = (
        df["team_name"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
    )

    normalized_names = {
        name.lower(): name for name in team_names
    }

    # Exact match first
    matched_team_name = normalized_names.get(team_name)

    # Try fuzzy matching if exact match fails
    if matched_team_name is None:
        closest_matches = difflib.get_close_matches(
            team_name,
            list(normalized_names.keys()),
            n=1,
            cutoff=0.6
        )

        if not closest_matches:
            return empty_df, empty_df, empty_df, empty_suggestions

        matched_team_name = normalized_names[closest_matches[0]]

    # Get employees from the matched team
    team_df = df[
        df["team_name"].astype(str).str.strip().str.lower()
        == matched_team_name.lower()
    ].copy()

    if team_df.empty:
        return empty_df, empty_df, empty_df, empty_suggestions

    # Columns to display
    display_columns = [
        "user_id",
        "full_name",
        "year_of_service",
        "sum_tardy",
        "sum_absent"
    ]

    # Rank by OKR score
    team_df_sorted_okr = team_df.sort_values(
        by="average_okr_score", ascending=False
    )
    top_employees_okr = team_df_sorted_okr.head(top_n)

    # Rank by KPI score
    team_df_sorted_kpi = team_df.sort_values(
        by="average_kpi_score", ascending=False
    )
    top_employees_kpi = team_df_sorted_kpi.head(top_n)

    # Rank by Manager score
    team_df_sorted_manager = team_df.sort_values(
        by="average_manager_score", ascending=False
    )
    top_employees_manager = team_df_sorted_manager.head(top_n)

    # Keep only columns that exist in the data
    okr_columns = [
        col for col in display_columns + ["average_okr_score"]
        if col in team_df.columns
    ]
    kpi_columns = [
        col for col in display_columns + ["average_kpi_score"]
        if col in team_df.columns
    ]
    manager_columns = [
        col for col in display_columns + ["average_manager_score"]
        if col in team_df.columns
    ]

    return (
        top_employees_okr[okr_columns],
        top_employees_kpi[kpi_columns],
        top_employees_manager[manager_columns],
        []
    )


# Streamlit UI
st.title("💼 Employee Recommendation Chatbot")
st.write(
    "Enter a team or department name to get top-performing employees "
    "based on OKR, KPI, and Manager scores."
)

merged_df = load_data()

team_name_input = st.text_input(
    "Enter the team or department name:"
)

if team_name_input.strip():
    (
        top_employees_okr,
        top_employees_kpi,
        top_employees_manager,
        suggestions
    ) = get_best_employees(team_name_input, merged_df)

    if top_employees_okr.empty:
        st.warning("No department with that name.")
    else:
        st.success(
            f"Top employees in department '{team_name_input}':"
        )

        st.subheader("Top Employees Ranked by Average OKR Score")
        st.dataframe(top_employees_okr, use_container_width=True)

        st.subheader("Top Employees Ranked by Average KPI Score")
        st.dataframe(top_employees_kpi, use_container_width=True)

        st.subheader("Top Employees Ranked by Average Manager Score")
        st.dataframe(top_employees_manager, use_container_width=True)
