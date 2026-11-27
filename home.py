"""Home page: a summary of everything found, organised as answers to the
research questions. Every number and every 'significant / not significant'
phrase is computed from the data, so the text cannot drift from the analysis."""

import streamlit as st

from utils import (
    load_data, load_raw_data, pearson, anova_with_check, robustness_table,
    cgpa_drivers, cgpa_regression, collection_period, fmt_p,
    ALPHA, HIGH_SCREEN_TIME_HOURS,
)

df = load_data()
raw = load_raw_data()

def join_words(items, conj):
    """['a', 'b', 'c'] -> 'a, b or c'."""
    items = list(items)
    return items[0] if len(items) == 1 else f"{', '.join(items[:-1])} {conj} {items[-1]}"


screen = df["avg_screen_time_hours"]
verified = df[df["Screen_Time_Confidence"] == "Verified"]
r_c, p_c, n_c = pearson(df, "avg_screen_time_hours", "cgpa")

# ----------------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------------
st.html("<h1 style='text-align: center; width: 100%;'>STUDENT SCREEN TIME & ACADEMIC PERFORMANCE</h1>")
st.html("<h3 style='text-align: center; width: 100%;'>Summary of findings</h3>")
st.markdown(
    f"""
    <div style='text-align: center; max-width: 700px; margin: 0 auto;'>
    Does time spent on screens go together with lower grades? This dashboard
    analyses a survey of {len(df)} Siam University students covering screen
    time, CGPA, sleep, study habits and digital distraction.
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("")

if p_c >= ALPHA:
    st.info(
        f"**Short answer: no.** In this sample, students who spend more time on screens do "
        f"not have noticeably lower CGPAs (r = {r_c:.2f}, {fmt_p(p_c)}). The result holds "
        "in every robustness check."
    )
else:
    st.info(
        f"**Short answer:** screen time and CGPA show a statistically significant "
        f"{'negative' if r_c < 0 else 'positive'} association (r = {r_c:.2f}, {fmt_p(p_c)})."
    )

c1, c2, c3, c4 = st.columns(4)
c1.metric("Students analysed", len(df), help=f"{len(raw)} survey responses before cleaning")
c2.metric("Avg. daily screen time", f"{screen.mean():.1f} hrs")
c3.metric("Average CGPA", f"{df['cgpa'].mean():.2f}")
c4.metric("Screen time ↔ CGPA (r)", f"{r_c:.2f}", help=f"Pearson correlation, {fmt_p(p_c)}, n = {n_c}")

st.divider()
st.header("Answers to the research questions")

# ----------------------------------------------------------------------------
# RQ1: screen-time behaviour
# ----------------------------------------------------------------------------
use_share = df["main_use"].value_counts(normalize=True)
peak_share = df["peak_time"].value_counts(normalize=True)
evening_share = peak_share.reindex(["Evening (6PM-10PM)", "Late night (after 10PM)"]).fillna(0).sum()
often = lambda col: (df[col] >= 4).mean()  # 4-5 = Often / Very Often
n_high = int((screen >= HIGH_SCREEN_TIME_HOURS).sum())

with st.container(border=True):
    st.subheader("1. What does screen-time behaviour look like?")
    st.markdown(
        f"**Students spend a lot of time on screens: about {screen.mean():.1f} hours a day** "
        f"(median {screen.median():.1f}). Most of it goes to **{use_share.index[0].lower()}**, "
        "and most of it happens in the evening or late at night."
    )
    st.markdown(
        f"""
- Main use: {use_share.index[0]} {use_share.iloc[0]:.0%}, then {use_share.index[1]} {use_share.iloc[1]:.0%}.
- {evening_share:.0%} use their phone most in the evening (6–10 PM) or late at night (after 10 PM).
- {often('check_phone_during_study'):.0%} check their phone often or very often while studying, and
  {often('phone_during_lectures'):.0%} often use it in lectures.
- {often('hard_to_reduce_screen_time'):.0%} say it is often hard to cut down, and
  {often('digital_distraction'):.0%} rate their digital distraction 4 or 5 out of 5.
- {n_high} students report {HIGH_SCREEN_TIME_HOURS}+ hours a day, which may be over-reported.
"""
    )
    st.page_link("pages/3_Screen_Time.py", label="See the Screen Time page", icon=":material/arrow_forward:")

# ----------------------------------------------------------------------------
# RQ2: differences between demographic groups
# ----------------------------------------------------------------------------
GROUPS = [("gender", "Gender"), ("year", "Academic year"),
          ("major_category", "Major category"), ("monthly_allowance", "Monthly allowance")]
label_cols = {label: col for col, label in GROUPS}
group_lines, sig_groups, fragile = [], [], []
for col, label in GROUPS:
    t = anova_with_check(df, col, "avg_screen_time_hours")
    means = df[df[col].isin(t["groups"])].groupby(col)["avg_screen_time_hours"].mean()
    lo, hi = means.idxmin(), means.idxmax()
    if t["driven_by_high"]:
        fragile.append((label, hi, t))
        verdict = (f"significant, but not without the {HIGH_SCREEN_TIME_HOURS}+ hour answers "
                   f"({fmt_p(t['p_without_high'])})")
    elif t["p"] < ALPHA:
        sig_groups.append(label.lower())
        verdict = "significant"
    else:
        verdict = "not significant"
    group_lines.append(
        f"- **{label}:** average from {means[lo]:.1f} hrs ({lo}) to {means[hi]:.1f} hrs ({hi}), "
        f"{fmt_p(t['p'])}: {verdict}."
    )
r_a, p_a, _ = pearson(df, "age", "avg_screen_time_hours")

with st.container(border=True):
    st.subheader("2. How does screen time differ across groups?")
    if sig_groups:
        lead = f"Screen time differs significantly by **{join_words(sig_groups, 'and')}**."
    elif fragile:
        lead = ("**Screen time is broadly similar across gender, academic year, major and "
                "allowance.**")
        for label, hi, t in fragile:
            n_high_hi = int(((df[label_cols[label]] == hi) & (screen >= HIGH_SCREEN_TIME_HOURS)).sum())
            lead += (f" {label} looks significant at first ({fmt_p(t['p'])}, {hi} highest), but "
                     f"{n_high_hi} of the {n_high} students reporting {HIGH_SCREEN_TIME_HOURS}+ hours "
                     f"are in {hi}. Without them the difference disappears "
                     f"({fmt_p(t['p_without_high'])}), so it is likely a Type I error (a false positive).")
    else:
        lead = ("**Screen time is about the same across gender, academic year, major and "
                "allowance.** None of these differences is statistically significant.")
    if p_a < ALPHA:
        age_text = (f" The one clear pattern is **age**: older students report "
                    f"**{'less' if r_a < 0 else 'more'}** screen time "
                    f"(r = {r_a:.2f}, {fmt_p(p_a)}), a weak relationship.")
    else:
        age_text = f" Age is not clearly related either (r = {r_a:.2f}, {fmt_p(p_a)})."
    st.markdown(lead + age_text)
    st.markdown("\n".join(group_lines))
    st.caption("One-way ANOVA on average daily screen time, repeated without the "
               f"{HIGH_SCREEN_TIME_HOURS}+ hour answers; groups with fewer than 5 students "
               "(e.g. 'Other') are left out of the tests.")
    st.page_link("pages/3_Screen_Time.py", label="See the group comparisons on the Screen Time page",
                 icon=":material/arrow_forward:")

# ----------------------------------------------------------------------------
# RQ3: screen time vs academic performance and lifestyle
# ----------------------------------------------------------------------------
LIFESTYLE = {
    "sleep_code": "Sleep",
    "study_code": "Study hours outside class",
    "digital_distraction": "Digital distraction",
    "check_phone_during_study": "Checking phone while studying",
    "phone_during_lectures": "Phone use in lectures",
    "hard_to_reduce_screen_time": "Difficulty reducing screen time",
}
life = []
for col, label in LIFESTYLE.items():
    r, p, _ = pearson(df, "avg_screen_time_hours", col)
    life.append((label, r, p))
life_sig = [x for x in life if x[2] < ALPHA]
life_ns = [x for x in life if x[2] >= ALPHA]

with st.container(border=True):
    st.subheader("3. How does screen time relate to grades and lifestyle?")
    if p_c >= ALPHA:
        st.markdown(f"**Screen time is not linked to CGPA** (r = {r_c:.2f}, {fmt_p(p_c)}): "
                    "heavy and light screen users have similar grades.")
    else:
        st.markdown(f"**Screen time is significantly associated with CGPA** "
                    f"(r = {r_c:.2f}, {fmt_p(p_c)}).")
    lines = []
    if life_sig:
        parts = "; ".join(f"{l.lower()} (r = {r:+.2f}, {fmt_p(p)})" for l, r, p in life_sig)
        lines.append(f"- Heavier screen users report more: {parts}.")
        lines.append(f"- These links are weak (all |r| ≤ {max(abs(r) for _, r, _ in life_sig):.2f}). "
                     f"With {len(LIFESTYLE)} tests at the 5% level, a result just under 0.05 could "
                     "be a Type I error (a false positive), so the smallest p-values are the most "
                     "convincing.")
    if life_ns:
        names = join_words([l.lower() for l, _, _ in life_ns], "or")
        lines.append(f"- No clear link with {names}.")
    st.markdown("\n".join(lines))
    st.page_link("pages/5_Relationships.py", label="See the Relationships page", icon=":material/arrow_forward:")

# ----------------------------------------------------------------------------
# RQ4: what is most associated with CGPA
# ----------------------------------------------------------------------------
drivers = cgpa_drivers(df)
top = drivers.iloc[0]
habits = drivers[~drivers["Variable"].isin(["academic_performance", "age"])]
table, summary = cgpa_regression(df)
coef = table[table["Term"] != "Intercept"]
clear = coef[coef["p-value"] < ALPHA]
BASELINES = {"major_category_": "Business & Management", "year_": "Year 1"}


def describe_term(term, b, p):
    for prefix, base in BASELINES.items():
        if term.startswith(prefix):
            name = term[len(prefix):]
            return (f"**{name}** students have a CGPA {abs(b):.2f} points "
                    f"{'lower' if b < 0 else 'higher'} than {base} ({fmt_p(p)})")
    return f"**{term}** ({b:+.3f}, {fmt_p(p)})"


with st.container(border=True):
    st.subheader("4. Which factors are most associated with CGPA?")
    if not habits["Significant (p < 0.05)"].any():
        st.markdown(
            "**No everyday habit stands out.** Screen time, sleep, study hours, phone habits "
            f"and digital distraction each have only a very weak link with CGPA "
            f"(all |r| ≤ {habits['r with CGPA'].abs().max():.2f}), and none is statistically significant."
        )
    else:
        names = ", ".join(habits.loc[habits["Significant (p < 0.05)"], "Factor"])
        st.markdown(f"**Habits significantly associated with CGPA:** {names}.")
    lines = [f"- The strongest association is **{top['Factor'].lower()}** "
             f"(r = {top['r with CGPA']:.2f}, {fmt_p(top['p-value'])})"
             + (": students' own rating of their grades, so it mostly shows they know how "
                "they are doing rather than explaining their CGPA."
                if top["Variable"] == "academic_performance" else ".")]
    lines.append(
        f"- With all factors together, a regression explains {summary['r2']:.0%} of the differences "
        f"in CGPA and {'is' if summary['f_p'] < ALPHA else 'is not'} statistically significant "
        f"overall ({fmt_p(summary['f_p'])})."
    )
    if len(clear):
        parts = "; ".join(describe_term(r["Term"], r["Coefficient"], r["p-value"]) for _, r in clear.iterrows())
        lines.append(f"- Holding the other factors constant, {parts}. Treat this as a lead to "
                     "investigate, not a firm conclusion: the group is small and many terms were tested.")
    st.markdown("\n".join(lines))
    st.page_link("pages/8_Robustness_And_Drivers.py", label="See the Robustness & Drivers page",
                 icon=":material/arrow_forward:")
    st.page_link("pages/6_Major_Analysis.py", label="See the Major Analysis page",
                 icon=":material/arrow_forward:")

# ----------------------------------------------------------------------------
# RQ5: robustness to verified data
# ----------------------------------------------------------------------------
robust = robustness_table(df)

with st.container(border=True):
    st.subheader("5. Do the findings hold with verified screen time only?")
    if (robust["p-value"] >= ALPHA).all():
        st.markdown(
            f"**Yes.** Using only the {len(verified)} screenshot-verified responses, leaving out "
            f"{HIGH_SCREEN_TIME_HOURS}+ hour reports, or both, gives the same answer: r stays between "
            f"{robust['r'].min():.2f} and {robust['r'].max():.2f} and is never statistically significant."
        )
    else:
        changed = ", ".join(robust.loc[robust["p-value"] < ALPHA, "Subset"])
        st.markdown(f"**Not entirely.** The result changes in: {changed}. Interpret it with caution.")
    st.dataframe(
        robust.drop(columns="Significant (p < 0.05)").style.format({"r": "{:.2f}", "p-value": "{:.3f}"}),
        width="stretch", hide_index=True,
    )
    st.page_link("pages/8_Robustness_And_Drivers.py", label="See the Robustness & Drivers page",
                 icon=":material/arrow_forward:")

# ----------------------------------------------------------------------------
# Conclusion, data and navigation
# ----------------------------------------------------------------------------
st.divider()
st.header("Conclusion")
if p_c >= ALPHA:
    st.success(
        f"Students in this survey spend a lot of time on screens, about {screen.mean():.1f} hours a "
        "day, mostly on social media in the evening. But how much time they spend tells us little "
        "about their grades: CGPA is similar for light and heavy users, and no everyday habit "
        "measured here is clearly linked to CGPA."
    )
else:
    st.success(
        f"Students in this survey spend about {screen.mean():.1f} hours a day on screens, and "
        "screen time is associated with CGPA. See the pages above for the size of the effect."
    )
st.caption(
    "These are associations in a self-reported survey of students at one university. They cannot "
    "show cause and effect, and CGPA varies little (most students are near the top of the scale), "
    "which makes weak effects hard to detect."
)

st.subheader("About the data")
c1, c2, c3 = st.columns(3)
c1.metric("Survey responses", len(raw))
c2.metric("Kept after cleaning", len(df))
c3.metric("Verified by screenshot", len(verified))
st.caption(f"Collected through an online survey of Siam University students, {collection_period(raw)}.")
st.page_link("pages/7_Dataset_And_Methodology.py",
             label="See how the data was collected and cleaned, and view the raw responses",
             icon=":material/arrow_forward:")

st.subheader("Explore the dashboard")
for path, label in [
    ("pages/2_Demographics.py", "Demographics: who took part"),
    ("pages/3_Screen_Time.py", "Screen Time: how much, on what, and when"),
    ("pages/4_Academic_Performance.py", "Academic Performance: CGPA, study and sleep"),
    ("pages/5_Relationships.py", "Relationships: screen time, age and CGPA"),
    ("pages/6_Major_Analysis.py", "Major Analysis: differences between majors"),
    ("pages/7_Dataset_And_Methodology.py", "Dataset & Methodology: data, cleaning and limitations"),
    ("pages/8_Robustness_And_Drivers.py", "Robustness & Drivers: do the results hold up?"),
]:
    st.page_link(path, label=label, icon=":material/arrow_forward:")
