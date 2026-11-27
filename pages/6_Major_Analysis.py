import plotly.express as px
import streamlit as st

from utils import (
    load_data, anova_test, anova_with_check, describe_anova, page_intro, takeaways, next_page,
    ALPHA, STUDY_HOURS_ORDER, SLEEP_HOURS_ORDER,
)

df = load_data()

page_intro(
    "Major Analysis",
    "Whether CGPA, screen time, sleep, study time and self-rated performance differ between "
    "major categories.",
)

# ----------------------------------------------------------------------------
# Key takeaways (computed from the data)
# ----------------------------------------------------------------------------
counts = df["major_category"].value_counts()
small = counts[counts < 5]
cgpa_test = anova_test(df, "major_category", "cgpa")
screen_test = anova_with_check(df, "major_category", "avg_screen_time_hours")
perf_test = anova_test(df, "major_category", "academic_performance")
cgpa_means = df[df["major_category"].isin(cgpa_test["groups"])].groupby("major_category")["cgpa"].mean()


def significance_phrase(p):
    if p < ALPHA:
        return "a statistically significant difference"
    if p < 0.10:
        return "a borderline difference that is suggestive but not conclusive"
    return "no statistically significant difference"


takeaways([
    f"{len(counts)} major categories; {counts.idxmax()} is the largest ({counts.max()} students)."
    + (f" {', '.join(small.index)} has fewer than 5 students and is left out of the tests." if len(small) else ""),
    f"CGPA: {significance_phrase(cgpa_test['p'])} between categories (ANOVA p = {cgpa_test['p']:.3f}). "
    f"{cgpa_means.idxmin()} has the lowest average ({cgpa_means.min():.2f}) and "
    f"{cgpa_means.idxmax()} the highest ({cgpa_means.max():.2f}).",
    f"Screen time: {significance_phrase(screen_test['p'])} (ANOVA p = {screen_test['p']:.3f}).",
    f"Self-rated performance: {significance_phrase(perf_test['p'])} (ANOVA p = {perf_test['p']:.3f}).",
    "With groups this small, a real but modest difference could be missed (a Type II error).",
])

c1, c2, c3 = st.columns([1, 2, 1])
c1.metric("Major categories", len(counts))
c2.metric("Largest category", counts.idxmax())
c3.metric("Participants", len(df))

# ----------------------------------------------------------------------------
# Overview
# ----------------------------------------------------------------------------
st.header("Students per category")
major_counts = counts.rename_axis("major_category").reset_index(name="participants")
fig = px.bar(
    major_counts, x="major_category", y="participants", text="participants",
    title="Number of Participants by Major Category",
    labels={"major_category": "Major Category", "participants": "Number of Participants"},
)
st.plotly_chart(fig, width="stretch")


# ----------------------------------------------------------------------------
# Comparisons
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


st.header("Comparisons by major category")
tabs = st.tabs(["CGPA", "Screen time", "Sleep", "Study hours", "Self-rated performance"])

with tabs[0]:
    fig = px.box(
        df.dropna(subset=["major_category", "cgpa"]), x="major_category", y="cgpa", points="all",
        title="CGPA by Major Category",
        labels={"major_category": "Major Category", "cgpa": "CGPA"},
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(describe_anova(cgpa_test, "average CGPA", "major categories"))

with tabs[1]:
    fig = px.box(
        df.dropna(subset=["major_category", "avg_screen_time_hours"]),
        x="major_category", y="avg_screen_time_hours", points="all",
        title="Screen Time by Major Category",
        labels={"major_category": "Major Category", "avg_screen_time_hours": "Average Screen Time (Hours)"},
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(describe_anova(screen_test, "average screen time", "major categories"))

with tabs[2]:
    grouped_share("sleep_hours", SLEEP_HOURS_ORDER, "Sleep by Major Category", "Sleep Hours")
    st.caption("Bars show the percentage within each major category, so categories of different size can be compared fairly.")

with tabs[3]:
    grouped_share("study_hours_outside_class", STUDY_HOURS_ORDER,
                  "Study Hours by Major Category", "Study Hours")
    st.caption("Bars show the percentage within each major category, so categories of different size can be compared fairly.")

with tabs[4]:
    perf = (
        df.groupby("major_category")["academic_performance"].agg(["mean", "size"])
        .sort_values("mean", ascending=False).reset_index()
    )
    perf["label"] = perf["major_category"] + " (n=" + perf["size"].astype(str) + ")"
    fig = px.bar(
        perf, x="label", y="mean", text=perf["mean"].round(2),
        title="Average Self-Rated Academic Performance by Major Category",
        labels={"label": "Major Category", "mean": "Average Self-Rated Performance (1-5)"},
    )
    fig.update_yaxes(range=[0, 5])
    st.plotly_chart(fig, width="stretch")
    st.caption("Academic performance is a self-rating from 1 to 5. "
               + describe_anova(perf_test, "average self-rated performance", "major categories"))

# ----------------------------------------------------------------------------
# Summary table
# ----------------------------------------------------------------------------
st.header("Summary by category")
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
st.caption(
    "Differences between major categories describe associations within this dataset "
    "and do not establish that a student's major causes differences in academic "
    "performance, screen time, study hours, or sleep."
)

next_page("pages/6_Major_Analysis.py")
