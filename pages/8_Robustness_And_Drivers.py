import plotly.express as px
import streamlit as st

from utils import (
    load_data, robustness_table, cgpa_drivers, cgpa_regression,
    DRIVER_VARIABLES, VARIABLE_LABELS, ALPHA, fmt_p,
    page_intro, takeaways, next_page,
)

df = load_data()

page_intro(
    "Robustness & Drivers",
    "Does the main finding hold up when the less reliable answers are set aside, and which "
    "factors are most strongly linked to CGPA?",
)

# ----------------------------------------------------------------------------
# All analyses first, so the takeaways and the tabs use the same numbers
# ----------------------------------------------------------------------------
robust = robustness_table(df)
robust_ok = bool((robust["p-value"] >= ALPHA).all())
drivers = cgpa_drivers(df).drop(columns="Variable")
top = drivers.iloc[0]
n_sig = int(drivers["Significant (p < 0.05)"].sum())

table, summary = cgpa_regression(df)
PRETTY = {"year_": "Year: {} (vs Year 1)",
          "major_category_": "Major: {} (vs Business & Management)"}


def pretty_term(term):
    for prefix, fmt in PRETTY.items():
        if term.startswith(prefix):
            return fmt.format(term[len(prefix):])
    return term


table["Term"] = table["Term"].map(pretty_term)
table["Significant (p < 0.05)"] = table["p-value"] < ALPHA
coef = table[table["Term"] != "Intercept"].copy()
clear = coef[coef["Significant (p < 0.05)"]]
model_sig = "is" if summary["f_p"] < ALPHA else "is not"

takeaways([
    ("**The main finding holds.** " if robust_ok else "**The main finding is not stable.** ")
    + f"Screen time vs CGPA stays between r = {robust['r'].min():.2f} and {robust['r'].max():.2f} "
    f"across all four subsets" + (", and is never significant." if robust_ok else "."),
    f"The factor most linked to CGPA is {top['Factor'].lower()} (r = {top['r with CGPA']:.2f}), "
    "students' own rating of their grades. Everyday habits show no clear link.",
    f"The regression explains {summary['r2']:.0%} of the variation in CGPA and {model_sig} significant "
    f"overall ({fmt_p(summary['f_p'])})."
    + (f" Only {', '.join(clear['Term'])} is significant (exploratory)." if len(clear) else ""),
])

tabs = st.tabs(["1 · Does the result hold up?", "2 · Factors linked to CGPA", "3 · Regression"])

# ============================================================================
# 1. Robustness of screen time vs CGPA
# ============================================================================
with tabs[0]:
    st.subheader("Does the screen time ↔ CGPA result hold up?")
    st.write(
        "Screen time is self-reported. The same Pearson correlation is repeated on "
        "subsets of the data that leave out the least trustworthy responses."
    )
    st.dataframe(
        robust.style.format({"r": "{:.2f}", "p-value": "{:.3f}"}),
        width="stretch", hide_index=True,
    )
    fig = px.bar(
        robust, x="r", y="Subset", orientation="h", text=robust["r"].round(2),
        title="Pearson's r between screen time and CGPA, by subset",
        labels={"r": "Pearson's r"},
    )
    fig.update_xaxes(range=[-0.5, 0.5])
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, width="stretch")
    if robust_ok:
        st.success(
            "In every subset the relationship is weak and not statistically significant, "
            "so the conclusion does not depend on unverified or extreme screen-time reports."
        )
    else:
        st.warning("The result changes in at least one subset, so interpret it with caution.")

# ============================================================================
# 2. Correlation heatmap + ranked drivers
# ============================================================================
with tabs[1]:
    st.subheader("Which factors are most associated with CGPA?")
    st.dataframe(
        drivers.style.format({"r with CGPA": "{:.2f}", "p-value": "{:.3f}"}),
        width="stretch", hide_index=True,
    )
    fig = px.bar(
        drivers, x="r with CGPA", y="Factor", orientation="h",
        title="Pearson's r with CGPA", text=drivers["r with CGPA"].round(2),
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(range=[-0.5, 0.5])
    st.plotly_chart(fig, width="stretch")
    st.info(
        f"The strongest association is **{top['Factor']}** (r = {top['r with CGPA']:.2f}, "
        f"{fmt_p(top['p-value'])}). Self-rated performance is partly a subjective version of CGPA, "
        "so it is not an independent driver. Screen time, sleep, study hours and distraction show "
        f"no clear association with CGPA. {len(drivers)} factors are tested here, and each test at "
        "the 5% level has a 5% chance of a false positive (a Type I error), so a single result just "
        f"below 0.05 should be read with caution. {n_sig} of {len(drivers)} factors have p < 0.05."
    )

    with st.expander("Correlation matrix of all factors"):
        nice = [VARIABLE_LABELS[v] for v in DRIVER_VARIABLES]
        corr = df[DRIVER_VARIABLES].corr(method="pearson")
        corr.index = nice
        corr.columns = nice
        fig = px.imshow(
            corr, zmin=-1, zmax=1, color_continuous_scale="RdBu_r", text_auto=".2f",
            title="Pearson correlation matrix", aspect="auto",
        )
        fig.update_layout(height=650)
        st.plotly_chart(fig, width="stretch")
        st.caption("Study and sleep are ordered bands, coded 0 (lowest) upwards so they can be correlated.")

# ============================================================================
# 3. Regression
# ============================================================================
with tabs[2]:
    st.subheader("Multiple regression: CGPA")
    st.write(
        "A multiple linear regression estimates how each factor relates to CGPA while "
        "holding the others constant. The 'Other' major category (very few students) is "
        "left out. Year and major category are compared with Year 1 and Business & "
        "Management. Each coefficient's p-value tests whether it differs from zero."
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Respondents used", summary["n"])
    c2.metric("R²", f"{summary['r2']:.3f}", help="Share of the variation in CGPA the model explains")
    c3.metric("Model p-value (F-test)", f"{summary['f_p']:.3f}")

    st.dataframe(
        table.style.format({"Coefficient": "{:+.3f}", "p-value": "{:.3f}"}),
        width="stretch", hide_index=True,
    )

    coef["Result"] = coef["Significant (p < 0.05)"].map({True: "p < 0.05", False: "Not significant"})
    fig = px.bar(
        coef, x="Coefficient", y="Term", orientation="h", color="Result",
        text=coef["Coefficient"].round(2),
        color_discrete_map={"p < 0.05": "#c0392b", "Not significant": "#95a5a6"},
        title="Regression coefficients (change in CGPA)",
    )
    fig.add_vline(x=0, line_color="grey")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, width="stretch")

    if len(clear):
        parts = ", ".join(f"{r['Term']} ({r['Coefficient']:+.2f}, {fmt_p(r['p-value'])})"
                          for _, r in clear.iterrows())
        clear_text = (f"Only {parts} is significant at the 5% level. "
                      "Treat it as a lead to investigate, not a firm conclusion: the group is small, "
                      "it overlaps with other variables such as academic year, and many terms were tested.")
    else:
        clear_text = "No single factor is significant at the 5% level."
    st.info(
        f"The model explains {summary['r2']:.1%} of the variation in CGPA and {model_sig} "
        f"statistically significant overall ({fmt_p(summary['f_p'])}). {clear_text} Screen time "
        "itself is not clearly associated with CGPA once the other factors are held constant."
    )

next_page("pages/8_Robustness_And_Drivers.py")
