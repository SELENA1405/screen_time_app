import pandas as pd
import streamlit as st

from utils import (
    load_data, pearson, correlation_section, fmt_p, strength_label, page_intro, takeaways, next_page,
    ALPHA, HIGH_SCREEN_TIME_HOURS,
)

df = load_data()

page_intro(
    "Relationships",
    "How strongly screen time, age and CGPA move together, measured with Pearson's correlation (r).",
)

with st.expander("How to read r and p-values"):
    st.write(
        "Pearson's correlation coefficient (r) measures how strongly two variables move "
        "together in a straight line, from -1 (perfect negative) to +1 (perfect positive). "
        "The p-value tests whether r differs from zero; results with p < 0.05 are called "
        "statistically significant. Pearson's r can be pulled by a few extreme values, so the "
        f"**Robustness & Drivers** page repeats the key result without the {HIGH_SCREEN_TIME_HOURS}+ "
        "hrs/day answers. A correlation shows association, not cause and effect."
    )

verified_only = st.checkbox(
    "Use only responses with verified screen time (screenshot provided)",
    value=False,
    help="Screen time is self-reported. Ticking this keeps only the respondents who "
         "also supplied a screenshot of their screen-time report.",
)
if verified_only:
    df = df[df["Screen_Time_Confidence"] == "Verified"]

PAIRS = [
    ("avg_screen_time_hours", "cgpa", "Screen Time vs CGPA",
     "Is average daily screen time associated with participants' CGPA?",
     {"avg_screen_time_hours": "Average Screen Time (Hours)", "cgpa": "CGPA"}),
    ("age", "cgpa", "Age vs CGPA",
     "Is age associated with academic performance?",
     {"age": "Age", "cgpa": "CGPA"}),
    ("age", "avg_screen_time_hours", "Age vs Screen Time",
     "Is age associated with average daily screen time?",
     {"age": "Age", "avg_screen_time_hours": "Average Screen Time (Hours)"}),
]

# ----------------------------------------------------------------------------
# Key takeaways and summary (computed before the detail tabs)
# ----------------------------------------------------------------------------
results = []
for x, y, heading, _, _ in PAIRS:
    r, p, n = pearson(df, x, y)
    results.append({"Relationship": heading, "r": r, "p-value": p, "n": n,
                    "Significant (p < 0.05)": p < ALPHA})
summary = pd.DataFrame(results)

points = []
for _, row in summary.iterrows():
    if row["Significant (p < 0.05)"]:
        direction = "negative" if row["r"] < 0 else "positive"
        points.append(f"**{row['Relationship']}:** a {strength_label(row['r'])} {direction} relationship that is statistically "
                      f"significant (r = {row['r']:.2f}, {fmt_p(row['p-value'])}).")
    else:
        points.append(f"**{row['Relationship']}:** no significant relationship "
                      f"(r = {row['r']:.2f}, {fmt_p(row['p-value'])}).")
points.append(f"Based on {len(df)} respondents"
              + (" with screenshot-verified screen time." if verified_only else "."))
takeaways(points)

st.dataframe(
    summary.style.format({"r": "{:.2f}", "p-value": "{:.4f}"}),
    width="stretch", hide_index=True,
)

# ----------------------------------------------------------------------------
# Each relationship in detail
# ----------------------------------------------------------------------------
st.header("Each relationship in detail")
tabs = st.tabs([heading for _, _, heading, _, _ in PAIRS])
for tab, (x, y, heading, question, labels) in zip(tabs, PAIRS):
    with tab:
        correlation_section(df, x, y, heading, question, labels)

st.caption(
    "Correlation values show the strength and direction of a relationship; they do not imply "
    "causation. Three tests are run on this page, so a p-value just under 0.05 could be a "
    "Type I error (a false positive)."
)

next_page("pages/5_Relationships.py")
