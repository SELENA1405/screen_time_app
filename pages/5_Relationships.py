import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils import (
    load_data, pearson, correlation_section, fmt_p, strength_label, page_intro, takeaways, next_page,
    main_use_correlations, heavy_vs_light, anova_test, describe_anova, group_box_plot,
    ALPHA, HIGH_SCREEN_TIME_HOURS,
)

df = load_data()


USE_NAMES = {"Game": "gaming", "Social Media": "social media",
             "Streaming (Netflix, YouTube)": "streaming (Netflix, YouTube)",
             "Studying/Academic work": "studying or academic work"}


def use_name(use):
    """Readable lower-case name of a main-use category for use inside sentences."""
    return USE_NAMES.get(use, use.lower())


def describe_correlation_short(row):
    """One sentence on the within-group correlation for the detail tab."""
    if row["p-value"] < ALPHA:
        return (f"Across the whole group, screen time and CGPA have a {strength_label(row['r'])} "
                f"{'negative' if row['r'] < 0 else 'positive'} relationship (r = {row['r']:.2f}, "
                f"{fmt_p(row['p-value'])}).")
    return (f"Across the whole group, the correlation is not significant (r = {row['r']:.2f}, "
            f"{fmt_p(row['p-value'])}).")

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
by_use = main_use_correlations(df)
if len(by_use):
    strongest = by_use.loc[by_use["r"].abs().idxmax()]
    if by_use["Significant (p < 0.05)"].any():
        sig_uses = ", ".join(by_use.loc[by_use["Significant (p < 0.05)"], "Main use"])
        points.append(f"**By main use:** screen time is significantly related to CGPA for {sig_uses}. "
                      "See the main-use section below.")
    else:
        points.append(f"**By main use:** within no main-use group is screen time significantly related to "
                      f"CGPA. The strongest is {strongest['Main use']} (r = {strongest['r']:.2f}, "
                      f"{fmt_p(strongest['p-value'])}, n = {strongest['n']}).")
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

# ----------------------------------------------------------------------------
# Screen time and CGPA by main use
# ----------------------------------------------------------------------------
st.header("Screen time and CGPA by main use")
st.caption(
    "The survey asked for total daily screen time and each student's **main** use of it, not hours "
    "per app. So this compares students by what they mainly use screens for: for example, among "
    "students who mainly use social media, do those with more screen time have a lower CGPA? Groups "
    "with fewer than 5 students are left out."
)

if by_use.empty:
    st.warning("No main-use group has at least 5 students in this selection.")
else:
    st.dataframe(
        by_use.style.format({
            "Avg screen time (hrs)": "{:.1f}", "Avg CGPA": "{:.2f}", "r": "{:+.2f}", "p-value": "{:.3f}",
            f"r without {HIGH_SCREEN_TIME_HOURS}+ hrs": "{:+.2f}", f"p without {HIGH_SCREEN_TIME_HOURS}+ hrs": "{:.3f}",
        }, na_rep="–"),
        width="stretch", hide_index=True,
    )

    uses = list(by_use["Main use"])
    tabs = st.tabs(["All groups together", "One group in detail", "CGPA by main use"])

    with tabs[0]:
        d = df[df["main_use"].isin(uses)].dropna(subset=["avg_screen_time_hours", "cgpa"])
        fig = px.scatter(
            d, x="avg_screen_time_hours", y="cgpa", color="main_use", opacity=0.7,
            category_orders={"main_use": uses},
            title="Screen Time vs CGPA, by Main Use",
            labels={"avg_screen_time_hours": "Average Screen Time (Hours)", "cgpa": "CGPA",
                    "main_use": "Main Use"},
        )
        colors = {t.name: t.marker.color for t in fig.data}
        for use in uses:
            g = d[d["main_use"] == use]
            slope, intercept = np.polyfit(g["avg_screen_time_hours"], g["cgpa"], 1)
            xs = np.array([g["avg_screen_time_hours"].min(), g["avg_screen_time_hours"].max()])
            fig.add_scatter(x=xs, y=slope * xs + intercept, mode="lines", showlegend=False,
                            line=dict(color=colors.get(use), width=3), hoverinfo="skip")
        fig.update_layout(height=520)
        st.plotly_chart(fig, width="stretch")
        st.caption("Each line is the straight-line trend for one group. A line sloping down means "
                   "heavier screen users in that group tend to have a lower CGPA.")

    with tabs[1]:
        use = st.selectbox("Main use", uses)
        g = df[df["main_use"] == use]
        row = by_use[by_use["Main use"] == use].iloc[0]
        hl = heavy_vs_light(g)
        c1, c2, c3 = st.columns(3)
        c1.metric("Students", int(row["n"]))
        c2.metric("Pearson's r", f"{row['r']:+.2f}")
        c3.metric("p-value", f"{row['p-value']:.3f}")
        st.markdown(
            f"**Heavier vs lighter users.** Splitting {use_name(use)} users at their median screen time "
            f"({hl['median']:.1f} hrs/day):"
        )
        c4, c5, c6 = st.columns(3)
        c4.metric(f"Avg CGPA, more than {hl['median']:.1f} hrs", f"{hl['heavy_mean']:.2f}",
                  help=f"n = {hl['n_heavy']}")
        c5.metric(f"Avg CGPA, {hl['median']:.1f} hrs or less", f"{hl['light_mean']:.2f}",
                  help=f"n = {hl['n_light']}")
        c6.metric("t-test p-value", f"{hl['p']:.3f}", help="Two-sample t-test, not assuming equal variances")
        diff = hl["heavy_mean"] - hl["light_mean"]
        st.info(
            f"Among students who mainly use screens for {use_name(use)}, heavier users have an average CGPA "
            f"{abs(diff):.2f} points {'lower' if diff < 0 else 'higher'} than lighter users. This "
            f"difference {'is' if hl['p'] < ALPHA else 'is not'} statistically significant "
            f"({fmt_p(hl['p'])}). "
            + describe_correlation_short(row)
        )

    with tabs[2]:
        st.plotly_chart(
            group_box_plot(df[df["main_use"].isin(uses)], "main_use", "cgpa", "CGPA by Main Use",
                           labels={"cgpa": "CGPA", "main_use": "Main Use"}, sort_by_median=True),
            width="stretch",
        )
        st.caption(describe_anova(anova_test(df, "main_use", "cgpa"), "average CGPA", "main-use groups"))

    sig = by_use[by_use["Significant (p < 0.05)"]]
    strongest = by_use.loc[by_use["r"].abs().idxmax()]
    trim_col = f"p without {HIGH_SCREEN_TIME_HOURS}+ hrs"
    if len(sig):
        verdict = (f"Screen time is significantly related to CGPA among students who mainly use screens "
                   f"for {', '.join(use_name(u) for u in sig['Main use'])}.")
    else:
        verdict = "Within no main-use group is screen time significantly related to CGPA."
    detail = (f" The strongest relationship is for {use_name(strongest['Main use'])} "
              f"(r = {strongest['r']:.2f}, {fmt_p(strongest['p-value'])}), but it is based on only "
              f"{strongest['n']} students")
    if not np.isnan(strongest[trim_col]):
        detail += (f", and without the {HIGH_SCREEN_TIME_HOURS}+ hour answers it becomes "
                   f"r = {strongest[f'r without {HIGH_SCREEN_TIME_HOURS}+ hrs']:.2f} "
                   f"({fmt_p(strongest[trim_col])})")
    detail += (". With groups this small, a real effect could be missed (a Type II error), so the "
               "result for small groups should be treated as a lead, not a conclusion.")
    st.info(verdict + detail)

st.caption(
    "Correlation values show the strength and direction of a relationship; they do not imply "
    "causation. Many tests are run on this page, so a p-value just under 0.05 could be a "
    "Type I error (a false positive)."
)

next_page("pages/5_Relationships.py")
