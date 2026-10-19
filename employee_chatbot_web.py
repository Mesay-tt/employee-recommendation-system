import streamlit as st
import pandas as pd
import difflib


# --------------------------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Employee Recommendation AI Agent",
    page_icon="",
    layout="wide"
)


# --------------------------------------------------
# 2. LOAD AND MERGE EMPLOYEE DATA
# --------------------------------------------------

@st.cache_data
def load_data():

    # Load all five employee datasets
    df1 = pd.read_csv("employees (1).csv")
    df2 = pd.read_csv("employees (2).csv")
    df3 = pd.read_csv("employees (3).csv")
    df4 = pd.read_csv("employees (4).csv")
    df5 = pd.read_csv("employees (5).csv")

    # Merge the first three datasets using employee ID
    merged = df1.merge(
        df2, on="user_id", how="outer",
        suffixes=("", "_df2")
    )

    merged = merged.merge(
        df3, on="user_id", how="outer",
        suffixes=("", "_df3")
    )

    # Merge dataset 4, removing overlapping columns
    # except for user_id
    df4 = df4.drop(
        columns=[
            col for col in df4.columns
            if col in merged.columns and col != "user_id"
        ]
    )

    merged = merged.merge(
        df4, on="user_id", how="outer"
    )

    # Merge dataset 5, removing overlapping columns
    # except for user_id
    df5 = df5.drop(
        columns=[
            col for col in df5.columns
            if col in merged.columns and col != "user_id"
        ]
    )

    merged = merged.merge(
        df5, on="user_id", how="outer"
    )

    # Normalize column names in case of extra spaces
    merged.columns = merged.columns.str.strip()

    # Identify score columns by their actual names.
    # If a score appears under a suffixed name, use the
    # first available matching column as the standard one.
    score_columns = {
        "average_okr_score": [
            "average_okr_score",
            "average_okr_score_df1",
            "average_okr_score_df2",
            "average_okr_score_df3"
        ],
        "average_kpi_score": [
            "average_kpi_score",
            "average_kpi_score_df1",
            "average_kpi_score_df2",
            "average_kpi_score_df3"
        ],
        "average_manager_score": [
            "average_manager_score",
            "average_manager_score_df1",
            "average_manager_score_df2",
            "average_manager_score_df3",
            "average_manager_score_df4"
        ]
    }

    for standard_name, possible_names in score_columns.items():

        available_columns = [
            col for col in possible_names
            if col in merged.columns
        ]

        if standard_name not in merged.columns and available_columns:
            merged = merged.rename(
                columns={available_columns[0]: standard_name}
            )

    # Ensure the three score columns exist
    for col in [
        "average_okr_score",
        "average_kpi_score",
        "average_manager_score"
    ]:
        if col not in merged.columns:
            merged[col] = pd.NA

        merged[col] = pd.to_numeric(
            merged[col], errors="coerce"
        )

    # Do not automatically replace missing scores with zero.
    # Missing data should not automatically mean poor performance.

    # Clean team names
    if "team_name" in merged.columns:
        merged["team_name"] = (
            merged["team_name"]
            .astype("string")
            .str.strip()
        )

    return merged


# --------------------------------------------------
# 3. FIND AND RANK EMPLOYEES
# --------------------------------------------------

def get_best_employees(team_name, df, top_n=5):

    empty_df = pd.DataFrame()
    empty_suggestions = []

    team_name = team_name.strip().lower()

    # Required department column
    if "team_name" not in df.columns:
        return empty_df, empty_df, empty_df, empty_suggestions

    # Get the available department names
    team_names = (
        df["team_name"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
    )

    # Create lowercase names for case-insensitive matching
    normalized_names = {
        name.lower(): name for name in team_names
    }

    # Try an exact match first
    matched_team_name = normalized_names.get(team_name)

    # If there is no exact match, look for a similar name
    if matched_team_name is None:

        closest_matches = difflib.get_close_matches(
            team_name,
            list(normalized_names.keys()),
            n=1,
            cutoff=0.6
        )

        if not closest_matches:
            return empty_df, empty_df, empty_df, empty_suggestions

        matched_team_name = normalized_names[
            closest_matches[0]
        ]

    # Filter the data for the selected department
    team_df = df[
        df["team_name"].astype(str).str.strip().str.lower()
        == matched_team_name.lower()
    ].copy()

    if team_df.empty:
        return empty_df, empty_df, empty_df, empty_suggestions

    # Employee information to show in the results
    display_columns = [
        "user_id",
        "full_name",
        "year_of_service",
        "sum_tardy",
        "sum_absent"
    ]

    # Rank by OKR score
    top_employees_okr = (
        team_df.dropna(subset=["average_okr_score"])
        .sort_values(
            by="average_okr_score",
            ascending=False
        )
        .head(top_n)
    )

    # Rank by KPI score
    top_employees_kpi = (
        team_df.dropna(subset=["average_kpi_score"])
        .sort_values(
            by="average_kpi_score",
            ascending=False
        )
        .head(top_n)
    )

    # Rank by manager score
    top_employees_manager = (
        team_df.dropna(subset=["average_manager_score"])
        .sort_values(
            by="average_manager_score",
            ascending=False
        )
        .head(top_n)
    )

    # Include only columns that exist
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
        empty_suggestions
    )


# --------------------------------------------------
# 4. STREAMLIT USER INTERFACE
# --------------------------------------------------

st.title(" Employee Recommendation AI Agent")

st.write(
    "Welcome! I analyze employee performance data to identify "
    "top-performing employees based on OKR, KPI, and manager scores."
)

st.info(
    "Enter a team or department name below. "
    "I will analyze the available performance data and "
    "recommend the highest-ranked employees."
)

# Load employee information
try:
    merged_df = load_data()

except Exception as error:
    st.error(
        "I couldn't load the employee datasets. "
        "Please check that all five CSV files are in the "
        "correct project folder and that their columns are valid."
    )

    st.exception(error)
    st.stop()


# Check for required columns
if "team_name" not in merged_df.columns:
    st.error(
        "The employee dataset does not contain a 'team_name' column. "
        "Please check your CSV files and merge settings."
    )
    st.stop()


# User input
team_name_input = st.text_input(
    "🔎 Which team or department would you like me to analyze?",
    placeholder="Enter a department name..."
)


# Analyze when the user enters a department
if team_name_input.strip():

    with st.spinner(
        f"Analyzing employee performance for "
        f"{team_name_input.strip()}..."
    ):

        (
            top_employees_okr,
            top_employees_kpi,
            top_employees_manager,
            suggestions
        ) = get_best_employees(
            team_name_input,
            merged_df
        )

    # No matching employees found
    if (
        top_employees_okr.empty
        and top_employees_kpi.empty
        and top_employees_manager.empty
    ):

        st.warning(
            "I couldn't find usable performance scores for this "
            "department. Please check the department name and "
            "the available employee data."
        )

    else:

        # Recommendation introduction
        st.success(
            f"✅ Analysis complete! Here are the top-ranked "
            f"employees for the {team_name_input.strip()} department."
        )

        st.subheader("AI Recommendation Summary")

        st.write(
            "I compared employee scores within the selected department "
            "and ranked employees separately in three categories: "
            "OKR performance, KPI performance, and manager evaluation."
        )

        st.caption(
            "Ranking method: highest available score first. "
            "Up to five employees are displayed in each category."
        )

        # OKR results
        st.subheader("Top Recommendations — OKR Performance")

        st.write(
            "These employees have the highest available average "
            "OKR scores in this department."
        )

        if top_employees_okr.empty:
            st.info("No usable OKR scores are available.")

        else:
            st.dataframe(
                top_employees_okr,
                use_container_width=True,
                hide_index=True
            )

        # KPI results
        st.subheader("Top Recommendations — KPI Performance")

        st.write(
            "These employees have the highest available average "
            "KPI scores in this department."
        )

        if top_employees_kpi.empty:
            st.info("No usable KPI scores are available.")

        else:
            st.dataframe(
                top_employees_kpi,
                use_container_width=True,
                hide_index=True
            )

        # Manager results
        st.subheader("Top Recommendations — Manager Evaluation")

        st.write(
            "These employees have the highest available manager "
            "evaluation scores in this department."
        )

        if top_employees_manager.empty:
            st.info("No usable manager scores are available.")

        else:
            st.dataframe(
                top_employees_manager,
                use_container_width=True,
                hide_index=True
            )

        # Closing note
        st.divider()

        st.caption(
            "Note: These rankings reflect the available recorded scores "
            "and programmed ranking rules. They support decision-making "
            "but do not guarantee overall employee suitability. "
            "Review the underlying data before making employment decisions."
        )
