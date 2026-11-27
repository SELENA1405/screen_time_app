import plotly.express as px
import streamlit as st

from utils import (
    load_data, mean_ci_plot, kruskal_test,
    STUDY_HOURS_ORDER, SLEEP_HOURS_ORDER,
)

st.title("Major Analysis Dashboard")

df = load_data()

st.subheader("Purpose")
st.write(
    "Analyze how academic performance and study-related habits differ across "
    "major categories, focusing on CGPA, screen time, sleep hours, study hours, "
    "and academic performance."
)

# ----------------------------------------------------------------------------
st.header("Major Overview")

counts = df["major_category"].value_counts()
col1, col2, col3 = st.columns(3)
col1.metric("Major Categories", df["major_category"].nunique())
col2.metric("Largest Major Category", counts.idxmax())
col3.metric("Participants", len(df))

major_counts = counts.rename_axis("major_category").reset_index(name="participants")
fig = px.bar(
    major_counts, x="major_category", y="participants", text="participants",
    title="Number of Participants by Major Category",
    labels={"major_category": "Major Category", "participants": "Number of Participants"},
)
st.plotly_chart(fig, width="stretch")

small = counts[counts < 5]
if len(small):
    st.warning(
        f"{', '.join(small.index)} ha{'s' if len(small) == 1 else 've'} fewer than 5 "
        "respondents, so it is left out of the statistical tests below."
    )

# ----------------------------------------------------------------------------
st.header("CGPA by Major Category")

fig = px.box(
    df.dropna(subset=["major_category", "cgpa"]), x="major_category", y="cgpa", points="all",
    title="CGPA Distribution by Major Category",
    labels={"major_category": "Major Category", "cgpa": "CGPA"},
)
st.plotly_chart(fig, width="stretch")

cgpa_test = kruskal_test(df, "major_category", "cgpa")
means = df[df["major_category"].isin(cgpa_test["groups"])].groupby("major_category")["cgpa"].mean()
verdict = "a statistically significant" if cgpa_test["p"] < 0.05 else "no statistically significant"
st.info(
    f"**Kruskal-Wallis test** across {', '.join(cgpa_test['groups'])} "
    f"(n = {cgpa_test['n']}): H = {cgpa_test['H']:.2f}, p = {cgpa_test['p']:.3f}, "
    f"ε² = {cgpa_test['eps2']:.3f}. There is {verdict} difference in CGPA between "
    f"categories. **{means.idxmin()}** has the lowest mean CGPA ({means.min():.2f}) and "
    f"**{means.idxmax()}** the highest ({means.max():.2f})."
)

# ----------------------------------------------------------------------------
st.header("Screen Time by Major Category")

fig = px.box(
    df.dropna(subset=["major_category", "avg_screen_time_hours"]),
    x="major_category", y="avg_screen_time_hours", points="all",
    title="Screen Time Distribution by Major Category",
    labels={"major_category": "Major Category", "avg_screen_time_hours": "Average Screen Time (Hours)"},
)
st.plotly_chart(fig, width="stretch")

screen_test = kruskal_test(df, "major_category", "avg_screen_time_hours")
verdict = "a statistically significant" if screen_test["p"] < 0.05 else "no statistically significant"
st.info(
    f"**Kruskal-Wallis test**: H = {screen_test['H']:.2f}, p = {screen_test['p']:.3f}, "
    f"ε² = {screen_test['eps2']:.3f}. There is {verdict} difference in screen time "
    "between major categories."
)


# ----------------------------------------------------------------------------
def grouped_share(column, order, title, legend_label):
    """Percentage of each major category in each ordered habit category."""
    d = df.dropna(subset=["major_category", column])
    table = d.groupby(["major_category", column]).size().reset_index(name="participants")
    table["percentage"] = table.groupby("major_category")["participants"].transform(
        lambda x: x / x.sum() * 100
    )
    fig = px.bar(
        table, x="major_category", y="percentage", color=column, barmode="group",
        category_orders={column: order}, hover_data=["participants"], title=title,
        labels={"major_category": "Major Category", "percentage": "% of Major Category",
                column: legend_label},
    )
    fig.update_layout(yaxis=dict(ticksuffix="%"))
    st.plotly_chart(fig, width="stretch")


st.header("Sleep Hours by Major Category")
grouped_share("sleep_hours", SLEEP_HOURS_ORDER, "Sleep Hours by Major Category", "Sleep Hours")
st.caption("Bars show the percentage within each major category, so categories of different size can be compared fairly.")

st.header("Study Hours by Major Category")
grouped_share("study_hours_outside_class", STUDY_HOURS_ORDER,
              "Study Hours by Major Category", "Study Hours")
st.caption("Bars show the percentage within each major category, so categories of different size can be compared fairly.")

# ----------------------------------------------------------------------------
st.header("Academic Performance by Major Category")
st.caption("Academic performance is a self-rating from 1 to 5. Dots show means with 95% confidence intervals.")
st.plotly_chart(
    mean_ci_plot(df, "major_category", "academic_performance",
                 "Average Self-Rated Academic Performance by Major Category",
                 labels={"academic_performance": "Average Self-Rated Performance (1-5)",
                         "major_category": "Major Category"},
                 sort_desc=True),
    width="stretch",
)

# ----------------------------------------------------------------------------
st.header("Major Category Summary")

summary = (
    df.groupby("major_category")
    .agg(
        Participants=("major_category", "size"),
        Average_CGPA=("cgpa", "mean"),
        Average_Screen_Time=("avg_screen_time_hours", "mean"),
    )
    .reset_index()
    .sort_values("Participants", ascending=False)
    .rename(columns={
        "major_category": "Major Category",
        "Average_CGPA": "Average CGPA",
        "Average_Screen_Time": "Average Screen Time (Hours)",
    })
)
st.dataframe(summary.round(2), width="stretch", hide_index=True)

# ----------------------------------------------------------------------------
st.header("Overall Findings")


def significance_phrase(p):
    if p < 0.05:
        return "a statistically significant difference"
    if p < 0.10:
        return "a borderline difference that is suggestive but not conclusive"
    return "no statistically significant difference"


st.write(
    f"Between major categories there is {significance_phrase(cgpa_test['p'])} in CGPA "
    f"(Kruskal-Wallis p = {cgpa_test['p']:.3f}, effect size ε² = {cgpa_test['eps2']:.3f}) and "
    f"{significance_phrase(screen_test['p'])} in screen time (p = {screen_test['p']:.3f}). "
    "With groups this small, these tests have limited power to detect modest differences."
)
st.caption(
    "Differences between major categories describe associations within this dataset "
    "and do not establish that a student's major causes differences in academic "
    "performance, screen time, study hours, or sleep."
)
