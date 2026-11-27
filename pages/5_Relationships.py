import pandas as pd
import streamlit as st

from utils import load_data, correlation_section

st.html("<h1 style='text-align: center; width: 100%;'>RELATIONSHIPS DASHBOARD</h1>")

st.write("")
st.markdown(
    """
    <div style='text-align: center; max-width: 700px; margin: 0 auto;'>
    This dashboard explores relationships between screen time, academic performance, and
    demographic factors using correlation analysis.
    </div>
    """,
    unsafe_allow_html=True,
)

st.header("Correlation Method")
st.write(
    "Spearman's rank correlation was used because the dataset contains extreme "
    "observations in screen time and age that could disproportionately influence "
    "Pearson's correlation. Spearman's correlation is less sensitive to extreme "
    "values and evaluates whether variables have a monotonic relationship."
)

df = load_data()

verified_only = st.checkbox(
    "Use only responses with verified screen time (screenshot provided)",
    value=False,
    help="Screen time is self-reported. Ticking this keeps only the respondents who "
         "also supplied a screenshot of their screen-time report.",
)
if verified_only:
    df = df[df["Screen_Time_Confidence"] == "Verified"]
st.caption(f"Analysing {len(df)} respondents.")

results = []

for x, y, heading, question, labels in [
    ("avg_screen_time_hours", "cgpa", "Screen Time vs CGPA",
     "Is average daily screen time associated with participants' CGPA?",
     {"avg_screen_time_hours": "Average Screen Time (Hours)", "cgpa": "CGPA"}),
    ("age", "cgpa", "Age vs CGPA",
     "Is age associated with academic performance?",
     {"age": "Age", "cgpa": "CGPA"}),
    ("age", "avg_screen_time_hours", "Age vs Screen Time",
     "Is age associated with average daily screen time?",
     {"age": "Age", "avg_screen_time_hours": "Average Screen Time (Hours)"}),
]:
    st.divider()
    rho, p, n = correlation_section(df, x, y, heading, question, labels)
    results.append({"Relationship": heading, "ρ": rho, "p-value": p, "n": n,
                    "Significant (p < 0.05)": p < 0.05})

# ----------------------------------------------------------------------------
# Summary and findings are generated from the results above.
# ----------------------------------------------------------------------------
st.divider()
st.subheader("Summary of Relationships")
summary = pd.DataFrame(results)
st.dataframe(
    summary.style.format({"ρ": "{:.2f}", "p-value": "{:.4f}"}),
    width="stretch", hide_index=True,
)

st.subheader("Overall Findings")
significant = summary[summary["Significant (p < 0.05)"]]
not_significant = summary[~summary["Significant (p < 0.05)"]]

lines = []
if len(significant):
    for _, r in significant.iterrows():
        lines.append(f"- **{r['Relationship']}** was statistically significant "
                     f"(ρ = {r['ρ']:.2f}, p = {r['p-value']:.4f}).")
if len(not_significant):
    names = ", ".join(not_significant["Relationship"])
    lines.append(f"- Not statistically significant: {names}.")
st.info("**Key Finding**\n\n" + "\n".join(lines))

st.caption(
    "Correlation values indicate the strength and direction of association "
    "between variables. They do not imply causation. Three tests are run on this "
    "page, so a p-value just under 0.05 would deserve extra caution."
)
