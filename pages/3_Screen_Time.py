import plotly.express as px
import streamlit as st

from utils import (
    load_data, group_box_plot, anova_with_check, describe_anova,
    page_intro, takeaways, next_page, ALPHA,
    LIKERT_LABELS, YEAR_ORDER, HIGH_SCREEN_TIME_HOURS,
)

df = load_data()
screen = df["avg_screen_time_hours"]
SCREEN_LABEL = {"avg_screen_time_hours": "Average Screen Time (hours)"}

page_intro(
    "Screen Time",
    "How much time students spend on screens, what they use them for, when, and whether "
    "this differs between groups.",
)

# ----------------------------------------------------------------------------
# Key takeaways (computed from the data)
# ----------------------------------------------------------------------------
use_share = df["main_use"].value_counts(normalize=True)
peak_share = df["peak_time"].value_counts(normalize=True)
evening = peak_share.reindex(["Evening (6PM-10PM)", "Late night (after 10PM)"]).fillna(0).sum()
n_high = int((screen >= HIGH_SCREEN_TIME_HOURS).sum())

GROUPS = [("major_category", "Major Category", None),
          ("year", "Academic Year", YEAR_ORDER),
          ("gender", "Gender", None)]
tests = {col: anova_with_check(df, col, "avg_screen_time_hours") for col, _, _ in GROUPS}
real = [label.lower() for col, label, _ in GROUPS if tests[col]["p"] < ALPHA and not tests[col]["driven_by_high"]]
fragile = [label.lower() for col, label, _ in GROUPS if tests[col]["driven_by_high"]]

group_point = (f"Screen time differs significantly by {' and '.join(real)}." if real
               else "Screen time is broadly similar across major categories, academic years and genders.")
if fragile:
    group_point += (f" {' and '.join(fragile).capitalize()} looks different at first, but only because "
                    f"of a few {HIGH_SCREEN_TIME_HOURS}+ hour answers (likely a Type I error).")

takeaways([
    f"Students average **{screen.mean():.1f} hours a day** (median {screen.median():.1f}).",
    f"Main use: {use_share.index[0]} {use_share.iloc[0]:.0%}, then "
    f"{use_share.index[1]} {use_share.iloc[1]:.0%}.",
    f"{evening:.0%} use screens most in the evening or late at night.",
    f"{(df['check_phone_during_study'] >= 4).mean():.0%} check their phone often or very often while studying.",
    group_point,
])

c1, c2, c3 = st.columns(3)
c1.metric("Average", f"{screen.mean():.2f} hrs")
c2.metric("Median", f"{screen.median():.2f} hrs")
c3.metric("Standard deviation", f"{screen.std():.2f} hrs")  # sample SD (n-1)
c4, c5, c6 = st.columns(3)
c4.metric("Minimum", f"{screen.min():.2f} hrs")
c5.metric("Maximum", f"{screen.max():.2f} hrs")
c6.metric(f"Reporting {HIGH_SCREEN_TIME_HOURS}+ hrs/day", n_high)
st.caption(
    f"Screen time is self-reported. Values of {HIGH_SCREEN_TIME_HOURS}+ hours a day are possible but "
    "may be over-reported; the Robustness & Drivers page checks whether they change the conclusions."
)


# ----------------------------------------------------------------------------
# Usage patterns
# ----------------------------------------------------------------------------
def horizontal_counts(column, title, axis_label):
    counts = df[column].value_counts().rename_axis(column).reset_index(name="count")
    fig = px.bar(
        counts, x="count", y=column, orientation="h", title=title, text="count",
        labels={"count": "Participants", column: axis_label},
    )
    fig.update_yaxes(categoryorder="total ascending")
    st.plotly_chart(fig, width="stretch")


def likert_chart(column, title):
    counts = df[column].value_counts().reindex([1, 2, 3, 4, 5], fill_value=0)
    fig = px.bar(
        x=[LIKERT_LABELS[i] for i in counts.index], y=counts.values, title=title, text=counts.values,
        labels={"x": "Frequency", "y": "Participants"},
    )
    st.plotly_chart(fig, width="stretch")


st.header("Usage patterns")
tabs = st.tabs(["Daily screen time", "Main use", "Peak time", "Phone habits"])
with tabs[0]:
    st.plotly_chart(
        px.histogram(df, x="avg_screen_time_hours", nbins=10, title="Daily Screen Time",
                     labels=SCREEN_LABEL),
        width="stretch",
    )
with tabs[1]:
    horizontal_counts("main_use", "Main Use of Screen Time", "Main Use")
with tabs[2]:
    horizontal_counts("peak_time", "When Screens Are Used Most", "Peak Time")
with tabs[3]:
    likert_chart("check_phone_during_study", "Checking Phone While Studying")
    likert_chart("phone_during_lectures", "Phone Use During Lectures")

# ----------------------------------------------------------------------------
# Group comparisons
# ----------------------------------------------------------------------------
st.header("Group comparisons")
st.caption(
    "Box plots: the line inside each box is the median, the box covers the middle 50% of "
    "students, and dots are outliers; n is shown in each label. Very small groups (e.g. n=1) "
    "show as a single line and should not be over-interpreted."
)
tabs = st.tabs([label for _, label, _ in GROUPS] + ["Individual majors", "Major × main use"])

for tab, (col, label, order) in zip(tabs, GROUPS):
    with tab:
        st.plotly_chart(
            group_box_plot(df, col, "avg_screen_time_hours", f"Screen Time by {label}",
                           labels={**SCREEN_LABEL, col: label}, order=order,
                           sort_by_median=order is None),
            width="stretch",
        )
        st.caption(describe_anova(tests[col], "average screen time", f"{label.lower()} groups"))

with tabs[3]:
    st.plotly_chart(
        group_box_plot(df, "major", "avg_screen_time_hours", "Screen Time by Major",
                       labels={**SCREEN_LABEL, "major": "Major"}, sort_by_median=True, horizontal=True),
        width="stretch",
    )
    st.caption("Many majors have only a few students, so these are not tested statistically.")

with tabs[4]:
    selected_use = st.selectbox(
        "Filter by main use of screen time",
        ["All"] + sorted(df["main_use"].dropna().unique().tolist()),
    )
    filtered_df = df if selected_use == "All" else df[df["main_use"] == selected_use]
    if filtered_df.empty:
        st.warning("No respondents match this filter.")
    else:
        st.plotly_chart(
            group_box_plot(filtered_df, "major", "avg_screen_time_hours",
                           f"Screen Time by Major ({selected_use}, n={len(filtered_df)})",
                           labels={**SCREEN_LABEL, "major": "Major"}, sort_by_median=True, horizontal=True),
            width="stretch",
        )

    by_cat_use = (
        df.groupby(["major_category", "main_use"], as_index=False)
        .agg(avg_screen_time_hours=("avg_screen_time_hours", "mean"), n=("cgpa", "size"))
    )
    fig = px.bar(
        by_cat_use, x="major_category", y="avg_screen_time_hours", color="main_use",
        barmode="group", hover_data=["n"],
        title="Average Screen Time by Major Category and Main Use",
        labels={"major_category": "Major Category",
                "avg_screen_time_hours": "Average Screen Time (Hours)", "main_use": "Main Use"},
    )
    fig.update_layout(legend_title="Main Use", height=500)
    st.plotly_chart(fig, width="stretch")
    st.caption("Hover over a bar to see how many respondents it is based on; some combinations have only one or two.")

next_page("pages/3_Screen_Time.py")
