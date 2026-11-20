import plotly.express as px
import streamlit as st

from utils import (
    load_data, mean_ci_plot, kruskal_test,
    STUDY_HOURS_ORDER, SLEEP_HOURS_ORDER, YEAR_ORDER,
)

st.title("Academic Performance Dashboard")

df = load_data()
cgpa = df["cgpa"]

st.subheader("Purpose")
st.write(
    "Analyze the academic performance and study-related habits of the "
    "participants, focusing on CGPA, study hours, sleep hours, and academic "
    "performance patterns across different groups."
)

st.header("Academic Performance Metrics")

col1, col2, col3 = st.columns(3)
col1.metric("Average CGPA", f"{cgpa.mean():.2f}")
col2.metric("Median CGPA", f"{cgpa.median():.2f}")
col3.metric("Standard Deviation", f"{cgpa.std():.2f}")  # sample SD (n-1)

col4, col5, col6 = st.columns(3)
col4.metric("Minimum CGPA", f"{cgpa.min():.2f}")
col5.metric("Maximum CGPA", f"{cgpa.max():.2f}")
col6.metric("CGPA of 3.5 or higher", f"{(cgpa >= 3.5).mean():.0%}")

st.caption(
    "CGPA is bunched toward the top of the scale (it cannot exceed 4.0). This "
    "limited spread makes it harder for any factor to show a strong association "
    "with CGPA."
)

st.divider()
st.header("Visualizations")
st.subheader("CGPA DISTRIBUTION")

fig = px.histogram(df, x="cgpa", nbins=8, title="CGPA Distribution", labels={"cgpa": "CGPA"})
fig.update_xaxes(range=[1.5, 4])
st.plotly_chart(fig, use_container_width=True)

st.caption("Dots show mean CGPA with 95% confidence intervals; n is shown in each label.")
CGPA_LABEL = {"cgpa": "Average CGPA"}

st.plotly_chart(
    mean_ci_plot(df, "year", "cgpa", "Average CGPA by Academic Year",
                 labels={**CGPA_LABEL, "year": "Academic Year"}, order=YEAR_ORDER),
    use_container_width=True,
)
year_test = kruskal_test(df, "year", "cgpa")
st.caption(
    f"Kruskal-Wallis test across academic years: H = {year_test['H']:.2f}, "
    f"p = {year_test['p']:.3f}, ε² = {year_test['eps2']:.3f}."
)

st.plotly_chart(
    mean_ci_plot(df, "major", "cgpa", "Average CGPA by Major",
                 labels={**CGPA_LABEL, "major": "Major"}, sort_desc=True, horizontal=True),
    use_container_width=True,
)
st.plotly_chart(
    mean_ci_plot(df, "major_category", "cgpa", "Average CGPA by Major Category",
                 labels={**CGPA_LABEL, "major_category": "Major Category"}, sort_desc=True),
    use_container_width=True,
)
st.caption("See the Major Analysis page for a formal test of CGPA across major categories.")

st.divider()
st.subheader("STUDY AND SLEEP HABITS")


def category_counts(column, order, title, label):
    counts = df[column].value_counts().reindex(order, fill_value=0)
    fig = px.bar(
        x=counts.index, y=counts.values, title=title, text=counts.values,
        labels={"x": label, "y": "Number of Participants"},
    )
    st.plotly_chart(fig, use_container_width=True)


category_counts("study_hours_outside_class", STUDY_HOURS_ORDER,
                "Study Hours Outside Class", "Study Hours")
category_counts("sleep_hours", SLEEP_HOURS_ORDER, "Sleep Duration", "Sleep Duration")


def share_by_year(column, order, title, legend_label):
    counts = df.groupby(["year", column]).size().reset_index(name="Participants")
    counts["Percentage"] = counts.groupby("year")["Participants"].transform(
        lambda x: x / x.sum() * 100
    )
    fig = px.bar(
        counts, x="year", y="Percentage", color=column,
        category_orders={"year": YEAR_ORDER, column: order}, title=title,
        labels={"year": "Academic Year", "Percentage": "Percentage of Participants", column: legend_label},
    )
    fig.update_layout(barmode="stack", yaxis=dict(range=[0, 100], ticksuffix="%"))
    st.plotly_chart(fig, use_container_width=True)


share_by_year("study_hours_outside_class", STUDY_HOURS_ORDER,
              "Study Hours by Academic Year", "Study Hours")
share_by_year("sleep_hours", SLEEP_HOURS_ORDER,
              "Sleep Hours by Academic Year", "Sleep Duration")

st.divider()
st.subheader("CGPA BY STUDY AND SLEEP HABITS")
st.plotly_chart(
    mean_ci_plot(df, "study_hours_outside_class", "cgpa", "Average CGPA by Study Hours Outside Class",
                 labels={**CGPA_LABEL, "study_hours_outside_class": "Study Hours"},
                 order=STUDY_HOURS_ORDER),
    use_container_width=True,
)
st.plotly_chart(
    mean_ci_plot(df, "sleep_hours", "cgpa", "Average CGPA by Sleep Duration",
                 labels={**CGPA_LABEL, "sleep_hours": "Sleep Duration"}, order=SLEEP_HOURS_ORDER),
    use_container_width=True,
)
st.info(
    "The confidence intervals overlap heavily, so there is no clear difference in "
    "CGPA across study or sleep groups. The **Robustness & Drivers** page tests this "
    "formally with correlations and a regression."
)
