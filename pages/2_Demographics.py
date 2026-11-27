import plotly.express as px
import streamlit as st

from utils import load_data, page_intro, takeaways, next_page, YEAR_ORDER, ALLOWANCE_ORDER

df = load_data()

page_intro(
    "Demographics",
    f"Who took part in the survey, and how evenly the {len(df)} students are spread across "
    "gender, age, academic year, major and monthly allowance.",
)

# ----------------------------------------------------------------------------
# Key takeaways (computed from the data)
# ----------------------------------------------------------------------------
gender = df["gender"].value_counts()
year = df["year"].value_counts()
category = df["major_category"].value_counts(normalize=True)
allowance = df["monthly_allowance"].value_counts(normalize=True)
under_18 = int((df["age"] < 18).sum())

takeaways([
    f"{len(df)} students: {gender.get('Female', 0)} female, {gender.get('Male', 0)} male and "
    f"{gender.get('Other', 0)} other.",
    f"Median age {df['age'].median():.0f} (range {df['age'].min()}–{df['age'].max()}). "
    f"{under_18} are under 18, which is unusual for university students; they are kept in the analysis.",
    f"{year.idxmax()} is the largest year group ({year.max()} students) and {year.idxmin()} the "
    f"smallest ({year.min()}).",
    f"{category.index[0]} is the largest major category ({category.iloc[0]:.0%}). Groups with fewer "
    "than 5 students, such as 'Other', are left out of group tests on other pages.",
    f"The most common monthly allowance is {allowance.index[0]} THB ({allowance.iloc[0]:.0%}).",
])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Participants", len(df))
c2.metric("Age range", f"{df['age'].min()} – {df['age'].max()}")
c3.metric("Median age", f"{df['age'].median():.0f}")
c4.metric("Majors represented", df["major"].nunique())


# ----------------------------------------------------------------------------
# Charts
# ----------------------------------------------------------------------------
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
        fig.update_layout(height=max(400, 30 * len(counts) + 150))
    st.plotly_chart(fig, width="stretch")


st.header("Who took part")
tabs = st.tabs(["Gender", "Age", "Academic year", "Major", "Allowance"])

with tabs[0]:
    count_chart("gender", "Gender")
    st.caption("The 'Other' group is very small, so gender comparisons elsewhere are mostly Male vs Female.")

with tabs[1]:
    st.plotly_chart(
        px.histogram(df, x="age", title="Age", labels={"age": "Age (years)"}),
        width="stretch",
    )
    if under_18:
        st.caption(f"{under_18} respondents are under 18, which is unusual for university students.")

with tabs[2]:
    count_chart("year", "Academic Year", order=YEAR_ORDER)

with tabs[3]:
    count_chart("major_category", "Major Category")
    st.caption(
        "Computing & IT is the largest category and 'Other' has only a handful of "
        "students, so category-level results should be read with group sizes in mind."
    )
    count_chart("major", "Individual Majors", horizontal=True)

with tabs[4]:
    count_chart("monthly_allowance", "Monthly Allowance (THB)", order=ALLOWANCE_ORDER)

next_page("pages/2_Demographics.py")
