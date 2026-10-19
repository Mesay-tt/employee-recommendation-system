# Streamlit UI
st.title("🤖 Employee Recommendation AI Agent")

st.write(
    "Welcome! I analyze employee performance data to identify "
    "top-performing employees based on OKR, KPI, and Manager scores."
)

st.info(
    "💡 Enter a team or department name below, and I will analyze "
    "the available performance data and recommend the top employees."
)

merged_df = load_data()

team_name_input = st.text_input(
    "🔎 Which team or department would you like me to analyze?",
    placeholder="e.g., Finance, HR, IT"
)

if team_name_input.strip():

    with st.spinner(
        f"🤖 Analyzing employee performance for {team_name_input}..."
    ):
        (
            top_employees_okr,
            top_employees_kpi,
            top_employees_manager,
            suggestions
        ) = get_best_employees(team_name_input, merged_df)

    if top_employees_okr.empty:
        st.warning(
            "I couldn't find a matching department. "
            "Please check the spelling or enter another team name."
        )

    else:
        st.success(
            f"✅ Analysis complete! Here are my top recommended "
            f"employees for the {team_name_input} department."
        )

        st.markdown(
            "### 🏆 AI Recommendation Summary"
        )

        st.write(
            f"Based on the available employee performance data, "
            f"I have identified the highest-ranked employees in "
            f"**{team_name_input}** across three performance categories."
        )

        st.caption(
            "Recommendation method: employees are ranked from "
            "highest to lowest score within each category."
        )

        st.subheader("🎯 Top Recommendations — OKR Performance")
        st.write(
            "These employees have the highest recorded average OKR scores "
            "in the selected department."
        )
        st.dataframe(
            top_employees_okr,
            use_container_width=True,
            hide_index=True
        )

        st.subheader("📊 Top Recommendations — KPI Performance")
        st.write(
            "These employees have the highest recorded average KPI scores "
            "in the selected department."
        )
        st.dataframe(
            top_employees_kpi,
            use_container_width=True,
            hide_index=True
        )

        st.subheader("👔 Top Recommendations — Manager Evaluation")
        st.write(
            "These employees have the highest recorded average manager "
            "evaluation scores in the selected department."
        )
        st.dataframe(
            top_employees_manager,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        st.caption(
            "Note: These recommendations reflect the available scores "
            "and ranking rules. They are decision-support results, "
            "not a guarantee of overall employee suitability."
        )
