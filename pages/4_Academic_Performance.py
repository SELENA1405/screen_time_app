import plotly.express as px
import streamlit as st

from utils import (
    load_data, group_box_plot, anova_test, describe_anova, ALPHA,
    page_intro, takeaways, next_page,
    STUDY_HOURS_ORDER, SLEEP_HOURS_ORDER, YEAR_ORDER,
)

df = load_data()
cgpa = df["cgpa"]
CGPA_LABEL = {"cgpa": "CGPA"}
BOX_NOTE = ("Box plots: the line inside each box is the median, the box covers the middle 50% of "
            "students, and dots are outliers; n is shown in each label.")

page_intro(
    "Academic Performance",
    "Students' CGPA, how much they study and sleep, and whether CGPA differs between these groups.",
)

# ----------------------------------------------------------------------------
# Key takeaways (computed from the data)
# ----------------------------------------------------------------------------
year_test = anova_test(df, "year", "cgpa")
study_test = anova_test(df, "study_hours_outside_class", "cgpa")
sleep_test = anova_test(df, "sleep_hours", "cgpa")
study_mode = df["study_hours_outside_class"].value_counts(normalize=True)
sleep_mode = df["sleep_hours"].value_counts(normalize=True)


def differs(test, what):
    return (f"CGPA differs significantly by {what} (p = {test['p']:.3f})." if test["p"] < ALPHA
            else f"CGPA does not differ significantly by {what} (p = {test['p']:.3f}).")


takeaways([
    f"Average CGPA is **{cgpa.mean():.2f}** (median {cgpa.median():.2f}), and "
    f"{(cgpa >= 3.5).mean():.0%} have 3.5 or higher. CGPA is bunched near the top of the scale, "
    "which makes weak effects hard to detect.",
    f"The most common study time outside class is {study_mode.index[0]} a day "
    f"({study_mode.iloc[0]:.0%}), and the most common sleep is {sleep_mode.index[0]} a night "
    f"({sleep_mode.iloc[0]:.0%}).",
    differs(year_test, "academic year"),
    differs(study_test, "study hours") + " " + differs(sleep_test, "sleep"),
])

c1, c2, c3 = st.columns(3)
c1.metric("Average CGPA", f"{cgpa.mean():.2f}")
c2.metric("Median CGPA", f"{cgpa.median():.2f}")
c3.metric("Standard deviation", f"{cgpa.std():.2f}")  # sample SD (n-1)
c4, c5, c6 = st.columns(3)
c4.metric("Minimum CGPA", f"{cgpa.min():.2f}")
c5.metric("Maximum CGPA", f"{cgpa.max():.2f}")
c6.metric("CGPA of 3.5 or higher", f"{(cgpa >= 3.5).mean():.0%}")

# ----------------------------------------------------------------------------
# CGPA
# ----------------------------------------------------------------------------
st.header("CGPA")
tabs = st.tabs(["Distribution", "By academic year", "By major category", "By major"])
with tabs[0]:
    fig = px.histogram(df, x="cgpa", nbins=8, title="CGPA Distribution", labels=CGPA_LABEL)
    fig.update_xaxes(range=[1.5, 4])
    st.plotly_chart(fig, width="stretch")
with tabs[1]:
    st.plotly_chart(
        group_box_plot(df, "year", "cgpa", "CGPA by Academic Year",
                       labels={**CGPA_LABEL, "year": "Academic Year"}, order=YEAR_ORDER),
        width="stretch",
    )
    st.caption(describe_anova(year_test, "average CGPA", "academic years"))
with tabs[2]:
    st.plotly_chart(
        group_box_plot(df, "major_category", "cgpa", "CGPA by Major Category",
                       labels={**CGPA_LABEL, "major_category": "Major Category"}, sort_by_median=True),
        width="stretch",
    )
    st.caption("See the Major Analysis page for the ANOVA across major categories.")
with tabs[3]:
    st.plotly_chart(
        group_box_plot(df, "major", "cgpa", "CGPA by Major",
                       labels={**CGPA_LABEL, "major": "Major"}, sort_by_median=True, horizontal=True),
        width="stretch",
    )
st.caption(BOX_NOTE)


# ----------------------------------------------------------------------------
# Study and sleep habits
# ----------------------------------------------------------------------------
def category_counts(column, order, title, label):
    counts = df[column].value_counts().reindex(order, fill_value=0)
    fig = px.bar(
        x=counts.index, y=counts.values, title=title, text=counts.values,
        labels={"x": label, "y": "Number of Participants"},
    )
    st.plotly_chart(fig, width="stretch")


def share_by_year(column, order, title, legend_label):
    counts = df.groupby(["year", column]).size().reset_index(name="Participants")
    counts["Percentage"] = counts.groupby("year")["Participants"].transform(lambda x: x / x.sum() * 100)
    fig = px.bar(
        counts, x="year", y="Percentage", color=column,
        category_orders={"year": YEAR_ORDER, column: order}, title=title,
        labels={"year": "Academic Year", "Percentage": "Percentage of Participants", column: legend_label},
    )
    fig.update_layout(barmode="stack", yaxis=dict(range=[0, 100], ticksuffix="%"))
    st.plotly_chart(fig, width="stretch")


st.header("Study and sleep habits")
tabs = st.tabs(["Study hours", "Sleep", "By academic year"])
with tabs[0]:
    category_counts("study_hours_outside_class", STUDY_HOURS_ORDER,
                    "Study Hours Outside Class (per day)", "Study Hours")
with tabs[1]:
    category_counts("sleep_hours", SLEEP_HOURS_ORDER, "Sleep (per night)", "Sleep Duration")
with tabs[2]:
    share_by_year("study_hours_outside_class", STUDY_HOURS_ORDER,
                  "Study Hours by Academic Year", "Study Hours")
    share_by_year("sleep_hours", SLEEP_HOURS_ORDER, "Sleep by Academic Year", "Sleep Duration")

# ----------------------------------------------------------------------------
# CGPA by study and sleep
# ----------------------------------------------------------------------------
st.header("Does CGPA differ by study or sleep?")
tabs = st.tabs(["By study hours", "By sleep"])
with tabs[0]:
    st.plotly_chart(
        group_box_plot(df, "study_hours_outside_class", "cgpa", "CGPA by Study Hours Outside Class",
                       labels={**CGPA_LABEL, "study_hours_outside_class": "Study Hours"},
                       order=STUDY_HOURS_ORDER),
        width="stretch",
    )
    st.caption(describe_anova(study_test, "average CGPA", "study-hour groups"))
with tabs[1]:
    st.plotly_chart(
        group_box_plot(df, "sleep_hours", "cgpa", "CGPA by Sleep Duration",
                       labels={**CGPA_LABEL, "sleep_hours": "Sleep Duration"}, order=SLEEP_HOURS_ORDER),
        width="stretch",
    )
    st.caption(describe_anova(sleep_test, "average CGPA", "sleep groups"))

significant = [name for name, t in [("study hours", study_test), ("sleep", sleep_test)] if t["p"] < ALPHA]
if significant:
    st.info(f"CGPA differs significantly by {' and '.join(significant)}. The **Robustness & "
            "Drivers** page checks this with correlations and a regression.")
else:
    st.info(
        "The boxes overlap heavily and neither ANOVA is significant, so there is no clear "
        "difference in CGPA across study or sleep groups. The **Robustness & Drivers** page "
        "checks this with correlations and a regression."
    )

next_page("pages/4_Academic_Performance.py")
