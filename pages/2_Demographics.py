import plotly.express as px
import streamlit as st

from utils import load_data, YEAR_ORDER, ALLOWANCE_ORDER

st.title("Demographics Dashboard")

df = load_data()

st.subheader("Purpose")
st.write(
    f"Establish the demographic profile of the {len(df)} respondents and evaluate "
    "how evenly the dataset represents different majors, academic years, age "
    "groups, and genders."
)

st.header("Participant Overview")
st.write(
    "This section gives an overview of the participants: gender, age, academic "
    "year, major/faculty, and monthly allowance. It establishes the composition "
    "of the sample and gives context for interpreting the analysis that follows."
)

st.subheader("Participant Profile")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Participants", len(df))
col2.metric("Age Range", f"{df['age'].min()} – {df['age'].max()}")
col3.metric("Median Age", f"{df['age'].median():.0f}")
col4.metric("Majors Represented", df["major"].nunique())

under_18 = int((df["age"] < 18).sum())
if under_18:
    st.caption(
        f"Note: {under_18} respondents are under 18, which is unusual for university "
        "students. They are kept in the analysis."
    )

st.divider()
st.header("Visualizations")


def count_chart(column, title, order=None, horizontal=False):
    """Bar chart of respondent counts per category, with an optional fixed order."""
    counts = df[column].value_counts().rename_axis(column).reset_index(name="Participants")
    if order:
        counts[column] = counts[column].astype(str)
        counts = counts.set_index(column).reindex(order, fill_value=0).reset_index()
    kwargs = dict(x="Participants", y=column, orientation="h") if horizontal else dict(x=column, y="Participants")
    fig = px.bar(counts, title=title, text="Participants", **kwargs)
    if horizontal:
        fig.update_yaxes(categoryorder="total ascending")
    st.plotly_chart(fig, use_container_width=True)


st.subheader("Gender Distribution")
count_chart("gender", "Gender Distribution")
st.caption("The 'Other' group is very small, so gender comparisons elsewhere are mostly Male vs Female.")

st.subheader("Age Distribution")
st.plotly_chart(px.histogram(df, x="age", title="Age Distribution"), use_container_width=True)

st.subheader("Academic Year Distribution")
count_chart("year", "Academic Year Distribution", order=YEAR_ORDER)

st.subheader("Major Distribution")
count_chart("major", "Major Distribution", horizontal=True)

st.subheader("Major Category Distribution")
count_chart("major_category", "Major Category Distribution")
st.caption(
    "Computing & IT is the largest category and 'Other' has only a handful of "
    "students, so category-level results should be read with group sizes in mind."
)

st.subheader("Monthly Allowance Distribution")
count_chart("monthly_allowance", "Monthly Allowance Distribution", order=ALLOWANCE_ORDER)
