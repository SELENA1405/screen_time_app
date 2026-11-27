import pandas as pd
import plotly.express as px
import streamlit as st

from utils import (
    load_data, spearman, ols_table, HIGH_SCREEN_TIME_HOURS, VARIABLE_LABELS,
)

st.title("Robustness & Drivers")

df = load_data()

st.write(
    "This page asks two questions: do the main findings hold up when the less "
    "reliable data is set aside, and which factors are most strongly associated "
    "with CGPA?"
)

# ============================================================================
# 1. Robustness of screen time vs CGPA
# ============================================================================
st.header("1. Does the screen time ↔ CGPA result hold up?")
st.write(
    "Screen time is self-reported. The same Spearman correlation is repeated on "
    "subsets of the data that exclude the least trustworthy responses."
)

verified = df["Screen_Time_Confidence"] == "Verified"
plausible = df["avg_screen_time_hours"] < HIGH_SCREEN_TIME_HOURS
scenarios = {
    "All respondents": df,
    "Verified screen time only": df[verified],
    f"Excluding {HIGH_SCREEN_TIME_HOURS}+ hrs/day": df[plausible],
    f"Verified and under {HIGH_SCREEN_TIME_HOURS} hrs/day": df[verified & plausible],
}

rows = []
for name, subset in scenarios.items():
    rho, p, n = spearman(subset, "avg_screen_time_hours", "cgpa")
    rows.append({"Subset": name, "n": n, "ρ": rho, "p-value": p, "Significant (p < 0.05)": p < 0.05})
robust = pd.DataFrame(rows)

st.dataframe(
    robust.style.format({"ρ": "{:.2f}", "p-value": "{:.3f}"}),
    width="stretch", hide_index=True,
)

fig = px.bar(
    robust, x="ρ", y="Subset", orientation="h", text=robust["ρ"].round(2),
    title="Spearman ρ between screen time and CGPA, by subset",
    labels={"ρ": "Spearman's ρ"},
)
fig.update_xaxes(range=[-0.5, 0.5])
fig.update_yaxes(autorange="reversed")
st.plotly_chart(fig, width="stretch")

if (robust["p-value"] >= 0.05).all():
    st.success(
        "In every subset the association is weak and not statistically significant, "
        "so the conclusion does not depend on unverified or extreme screen-time reports."
    )
else:
    st.warning("The result changes in at least one subset, so interpret it with caution.")

# ============================================================================
# 2. Correlation heatmap + ranked drivers
# ============================================================================
st.divider()
st.header("2. Which factors are most associated with CGPA?")

variables = [
    "avg_screen_time_hours", "study_code", "sleep_code", "check_phone_during_study",
    "phone_during_lectures", "hard_to_reduce_screen_time", "digital_distraction",
    "academic_performance", "age", "cgpa",
]
nice = [VARIABLE_LABELS[v] for v in variables]
corr = df[variables].corr(method="spearman")
corr.index = nice
corr.columns = nice

fig = px.imshow(
    corr, zmin=-1, zmax=1, color_continuous_scale="RdBu_r", text_auto=".2f",
    title="Spearman correlation matrix", aspect="auto",
)
fig.update_layout(height=650)
st.plotly_chart(fig, width="stretch")
st.caption("Study and sleep are ordered bands (0 = lowest) so they can be ranked.")

predictors = [v for v in variables if v != "cgpa"]
drivers = []
for v in predictors:
    rho, p, n = spearman(df, v, "cgpa")
    drivers.append({"Factor": VARIABLE_LABELS[v], "ρ with CGPA": rho, "p-value": p})
drivers = pd.DataFrame(drivers)
drivers["|ρ|"] = drivers["ρ with CGPA"].abs()
drivers = drivers.sort_values("|ρ|", ascending=False).drop(columns="|ρ|").reset_index(drop=True)

alpha_adj = 0.05 / len(drivers)
drivers["Significant (p < 0.05)"] = drivers["p-value"] < 0.05
drivers[f"Significant after Bonferroni (p < {alpha_adj:.4f})"] = drivers["p-value"] < alpha_adj

st.subheader("Factors ranked by strength of association with CGPA")
st.dataframe(
    drivers.style.format({"ρ with CGPA": "{:.2f}", "p-value": "{:.3f}"}),
    width="stretch", hide_index=True,
)

fig = px.bar(
    drivers, x="ρ with CGPA", y="Factor", orientation="h",
    title="Spearman ρ with CGPA", text=drivers["ρ with CGPA"].round(2),
)
fig.update_yaxes(autorange="reversed")
fig.update_xaxes(range=[-0.5, 0.5])
st.plotly_chart(fig, width="stretch")

top = drivers.iloc[0]
st.info(
    f"{len(drivers)} factors are tested, so a Bonferroni-adjusted threshold of {alpha_adj:.4f} is "
    f"shown as well. The strongest association is **{top['Factor']}** "
    f"(ρ = {top['ρ with CGPA']:.2f}, p = {top['p-value']:.3f}). Self-rated performance is "
    "partly a subjective version of CGPA, so it is not an independent driver. "
    "Screen time, sleep, study hours and distraction show no clear association with CGPA."
)

# ============================================================================
# 3. Regression
# ============================================================================
st.divider()
st.header("3. Multiple regression: CGPA")
st.write(
    "A linear regression estimates the association of each factor with CGPA while "
    "holding the others constant. The 'Other' major category (very few students) is "
    "excluded. Coefficients are compared against the first level of each categorical "
    "variable (Year 1; Business & Management)."
)

reg_df = df[df["major_category"] != "Other"]
table, summary = ols_table(
    reg_df, "cgpa",
    numeric=["avg_screen_time_hours", "study_code", "sleep_code", "digital_distraction", "age"],
    categorical=["year", "major_category"],
)
nice_terms = {
    "avg_screen_time_hours": "Screen time (per extra hour/day)",
    "study_code": "Study hours (per band up)",
    "sleep_code": "Sleep (per band up)",
    "digital_distraction": "Digital distraction (per point)",
    "age": "Age (per year)",
}
table["Term"] = table["Term"].replace(nice_terms)

c1, c2, c3 = st.columns(3)
c1.metric("Respondents used", summary["n"])
c2.metric("R²", f"{summary['r2']:.3f}", help=f"Adjusted R² = {summary['adj_r2']:.3f}")
c3.metric("Model F-test p-value", f"{summary['f_p']:.3f}")

st.dataframe(
    table.style.format({
        "Coefficient": "{:.3f}", "Std. error": "{:.3f}", "CI low": "{:.3f}",
        "CI high": "{:.3f}", "p-value": "{:.3f}",
    }),
    width="stretch", hide_index=True,
)

coef = table[table["Term"] != "Intercept"]
fig = px.scatter(
    coef, x="Coefficient", y="Term",
    error_x=coef["CI high"] - coef["Coefficient"],
    error_x_minus=coef["Coefficient"] - coef["CI low"],
    title="Regression coefficients with 95% confidence intervals",
)
fig.add_vline(x=0, line_dash="dash", line_color="grey")
fig.update_yaxes(autorange="reversed")
st.plotly_chart(fig, width="stretch")

model_sig = "is" if summary["f_p"] < 0.05 else "is not"
clear = coef[(coef["CI low"] > 0) | (coef["CI high"] < 0)]
if len(clear):
    parts = ", ".join(f"{r['Term']} ({r['Coefficient']:+.2f}, p = {r['p-value']:.3f})"
                      for _, r in clear.iterrows())
    clear_text = (f"Only {parts} has a 95% confidence interval that excludes zero. "
                  "Treat it as a lead to investigate, not a firm conclusion: the group is small, "
                  "it overlaps with other variables such as academic year, and many terms were tested.")
else:
    clear_text = "Every confidence interval includes zero, so no single factor is clearly associated with CGPA."
st.info(
    f"The model explains {summary['r2']:.1%} of the variation in CGPA (adjusted R² = "
    f"{summary['adj_r2']:.1%}) and {model_sig} statistically significant overall "
    f"(p = {summary['f_p']:.3f}). {clear_text} Screen time itself is not clearly "
    "associated with CGPA once the other factors are held constant."
)
