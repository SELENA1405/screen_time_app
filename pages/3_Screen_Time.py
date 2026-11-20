import plotly.express as px
import streamlit as st

from utils import (
    load_data, mean_ci_plot, LIKERT_LABELS, YEAR_ORDER, HIGH_SCREEN_TIME_HOURS,
)

st.title("Screen Time Dashboard")

df = load_data()
screen = df["avg_screen_time_hours"]

st.subheader("Purpose")
st.write(
    "Analyze the participants' screen time habits by examining overall usage, "
    "daily patterns, phone habits, and differences across demographic and "
    "academic groups."
)

st.header("Screen Time Metrics")

col1, col2, col3 = st.columns(3)
col1.metric("Average Screen Time", f"{screen.mean():.2f} hrs")
col2.metric("Median", f"{screen.median():.2f} hrs")
col3.metric("Standard Deviation", f"{screen.std():.2f} hrs")  # sample SD (n-1)

col4, col5, col6 = st.columns(3)
col4.metric("Minimum", f"{screen.min():.2f} hrs")
col5.metric("Maximum", f"{screen.max():.2f} hrs")
col6.metric(f"Reporting {HIGH_SCREEN_TIME_HOURS}+ hrs/day", int((screen >= HIGH_SCREEN_TIME_HOURS).sum()))

st.caption(
    "Screen time is self-reported. Values of 14+ hours a day are possible but may "
    "be over-reported; the Robustness & Drivers page checks whether they change "
    "the conclusions."
)

st.divider()

st.header("Visualizations")
st.subheader("SCREEN TIME DISTRIBUTION")

fig = px.histogram(
    df, x="avg_screen_time_hours", nbins=10,
    title="Distribution of Daily Screen Time",
    labels={"avg_screen_time_hours": "Average Screen Time (hours)"},
)
st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("USAGE PATTERNS")


def horizontal_counts(column, title, axis_label):
    counts = df[column].value_counts().rename_axis(column).reset_index(name="count")
    fig = px.bar(
        counts, x="count", y=column, orientation="h", title=title,
        labels={"count": "Participants", column: axis_label},
    )
    fig.update_yaxes(categoryorder="total ascending")
    st.plotly_chart(fig, use_container_width=True)


horizontal_counts("main_use", "Main Uses of Screen Time", "Main Use")
horizontal_counts("peak_time", "Peak Times of Screen Use", "Peak Time")

st.divider()
st.subheader("PHONE HABITS")


def likert_chart(column, title):
    counts = df[column].value_counts().reindex([1, 2, 3, 4, 5], fill_value=0)
    fig = px.bar(
        x=[LIKERT_LABELS[i] for i in counts.index], y=counts.values, title=title,
        labels={"x": "Frequency", "y": "Participants"},
    )
    st.plotly_chart(fig, use_container_width=True)


likert_chart("check_phone_during_study", "Phone Checking During Study")
likert_chart("phone_during_lectures", "Phone Use During Lectures")

st.divider()
st.header("Group Comparisons")
st.caption(
    "Dots show group means with 95% confidence intervals; n is shown in each label. "
    "Very small groups have wide or missing intervals and should not be over-interpreted."
)
st.subheader("SIMPLE COMPARISONS")

SCREEN_LABEL = {"avg_screen_time_hours": "Average Screen Time (hours)"}

st.plotly_chart(
    mean_ci_plot(df, "major", "avg_screen_time_hours", "Average Screen Time by Major",
                 labels={**SCREEN_LABEL, "major": "Major"}, sort_desc=True, horizontal=True),
    use_container_width=True,
)
st.plotly_chart(
    mean_ci_plot(df, "major_category", "avg_screen_time_hours",
                 "Average Screen Time by Major Category",
                 labels={**SCREEN_LABEL, "major_category": "Major Category"}, sort_desc=True),
    use_container_width=True,
)
st.plotly_chart(
    mean_ci_plot(df, "year", "avg_screen_time_hours", "Average Screen Time by Academic Year",
                 labels={**SCREEN_LABEL, "year": "Academic Year"}, order=YEAR_ORDER),
    use_container_width=True,
)
st.plotly_chart(
    mean_ci_plot(df, "gender", "avg_screen_time_hours", "Average Screen Time by Gender",
                 labels={**SCREEN_LABEL, "gender": "Gender"}),
    use_container_width=True,
)

st.divider()
st.subheader("COMPLEX COMPARISONS")

selected_use = st.selectbox(
    "Filter by main use of screen time",
    ["All"] + sorted(df["main_use"].dropna().unique().tolist()),
)
filtered_df = df if selected_use == "All" else df[df["main_use"] == selected_use]

if filtered_df.empty:
    st.warning("No respondents match this filter.")
else:
    st.plotly_chart(
        mean_ci_plot(filtered_df, "major", "avg_screen_time_hours",
                     f"Average Screen Time by Major ({selected_use}, n={len(filtered_df)})",
                     labels={**SCREEN_LABEL, "major": "Major"}, sort_desc=True, horizontal=True),
        use_container_width=True,
    )

by_cat_use = (
    df.groupby(["major_category", "main_use"], as_index=False)
    .agg(avg_screen_time_hours=("avg_screen_time_hours", "mean"), n=("cgpa", "size"))
)
fig = px.bar(
    by_cat_use, x="major_category", y="avg_screen_time_hours", color="main_use",
    barmode="group", hover_data=["n"],
    title="Average Screen Time by Major Category and Main Use",
    labels={
        "major_category": "Major Category",
        "avg_screen_time_hours": "Average Screen Time (Hours)",
        "main_use": "Main Use",
    },
)
fig.update_layout(legend_title="Main Use", height=500)
st.plotly_chart(fig, use_container_width=True)
st.caption("Hover over a bar to see how many respondents it is based on; some combinations have only one or two.")
