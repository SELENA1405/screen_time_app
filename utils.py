"""Shared data loading, ordering constants and analysis helpers for the dashboard."""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from scipy import stats

# Resolve the data file relative to this file, so the app works no matter
# which folder `streamlit run` is started from.
DATA_PATH = Path(__file__).resolve().parent / "Data" / "Screen_Time_Data.xlsx"
SHEET_NAME = "CleanedData_Screenshot_Removed"
RAW_SHEET_NAME = "OgData_Screenshot_Removed"

# --- Shared category orderings, used across pages so ordering stays consistent.
STUDY_HOURS_ORDER = ["Less than 1 hr", "1-2 hrs", "2-3 hrs", "More than 3 hrs"]
SLEEP_HOURS_ORDER = ["Less than 5 hrs", "5-6 hrs", "7-8 hrs", "8+ hrs"]
YEAR_ORDER = ["Year 1", "Year 2", "Year 3", "Year 4"]
ALLOWANCE_ORDER = ["Under 5,000", "5,000-10,000", "10,001-15,000", "15,000+"]

LIKERT_LABELS = {1: "Never", 2: "Rarely", 3: "Sometimes", 4: "Often", 5: "Very Often"}

# Screen time at or above this many hours/day is treated as a possible
# over-report in the robustness checks (it is NOT removed from the main pages).
HIGH_SCREEN_TIME_HOURS = 14

# Human-readable names for the numeric / ordinal variables.
VARIABLE_LABELS = {
    "avg_screen_time_hours": "Screen time (hrs/day)",
    "study_code": "Study hours outside class (ordinal)",
    "sleep_code": "Sleep hours (ordinal)",
    "check_phone_during_study": "Checks phone while studying",
    "phone_during_lectures": "Phone use in lectures",
    "hard_to_reduce_screen_time": "Hard to reduce screen time",
    "digital_distraction": "Digital distraction",
    "academic_performance": "Self-rated academic performance",
    "age": "Age",
    "cgpa": "CGPA",
}


@st.cache_data
def load_data(path: Path = DATA_PATH, sheet_name: str = SHEET_NAME) -> pd.DataFrame:
    """Load the cleaned survey sheet and tidy it once, for every page."""
    df = pd.read_excel(path, sheet_name=sheet_name)

    # Strip stray whitespace in text columns (e.g. "Computer Science " vs
    # "Computer Science" were being counted as two different majors).
    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]) or df[col].dtype == object:
            df[col] = df[col].astype("string").str.strip()

    for col in ["age", "cgpa", "avg_screen_time_hours"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Ordinal codes (0 = lowest) so categorical habits can enter correlations.
    df["study_code"] = df["study_hours_outside_class"].map(
        {v: i for i, v in enumerate(STUDY_HOURS_ORDER)}
    )
    df["sleep_code"] = df["sleep_hours"].map(
        {v: i for i, v in enumerate(SLEEP_HOURS_ORDER)}
    )
    return df


@st.cache_data
def load_raw_data(path: Path = DATA_PATH, sheet_name: str = RAW_SHEET_NAME) -> pd.DataFrame:
    """Load the raw survey export exactly as submitted (screenshot question removed)."""
    return pd.read_excel(path, sheet_name=sheet_name)


def collection_period(raw: pd.DataFrame) -> str:
    """Date range of the survey responses, e.g. '16–24 March 2026'."""
    ts = pd.to_datetime(raw["Timestamp"], errors="coerce").dropna()
    a, b = ts.min(), ts.max()
    if (a.year, a.month) == (b.year, b.month):
        return f"{a.day}–{b.day} {b:%B %Y}"
    return f"{a.day} {a:%B} – {b.day} {b:%B %Y}"


def fmt_p(p: float) -> str:
    return "p < 0.001" if p < 0.001 else f"p = {p:.3f}"


# ----------------------------------------------------------------------------
# Statistics helpers
# ----------------------------------------------------------------------------
ALPHA = 0.05  # significance level used throughout


def pearson(df: pd.DataFrame, x: str, y: str):
    """Pearson correlation on complete cases. Returns (r, p, n)."""
    d = df[[x, y]].dropna()
    r, p = stats.pearsonr(d[x].astype(float), d[y].astype(float))
    return float(r), float(p), len(d)


def strength_label(r: float) -> str:
    a = abs(r)
    if a < 0.2:
        return "very weak"
    if a < 0.4:
        return "weak"
    if a < 0.6:
        return "moderate"
    return "strong"


def describe_correlation(r: float, p: float, alpha: float = ALPHA) -> str:
    """Plain-English interpretation generated from the numbers, so the text can
    never disagree with the statistics if the data changes."""
    direction = "negative" if r < 0 else "positive"
    verdict = "is" if p < alpha else "is not"
    if abs(r) < 0.1:
        lead = "There is almost no linear relationship"
    else:
        lead = f"There is a {strength_label(r)} {direction} linear relationship"
    return (
        f"{lead} (r = {r:.2f}). It {verdict} statistically significant at the 5% level "
        f"({fmt_p(p)})."
    )


def anova_test(df: pd.DataFrame, group: str, value: str, exclude=(), min_n: int = 5):
    """One-way ANOVA: do the group means of `value` differ across `group`?

    Groups with fewer than `min_n` people (or listed in `exclude`) are left out
    because they are too small to say anything. Returns a dict with the F
    statistic, p-value, n, the groups used and those left out.
    """
    d = df[[group, value]].dropna()
    d = d[~d[group].isin(exclude)]
    counts = d[group].value_counts()
    keep = counts[counts >= min_n].index
    dropped = [g for g in counts.index if g not in keep]
    d = d[d[group].isin(keep)]
    samples = [g[value].astype(float).values for _, g in d.groupby(group)]
    f, p = stats.f_oneway(*samples)
    return {"F": float(f), "p": float(p), "n": len(d),
            "groups": sorted(keep), "dropped": dropped}


def anova_with_check(df: pd.DataFrame, group: str, value: str):
    """ANOVA on all respondents, repeated without the 14+ hrs/day screen-time
    reports, so a result driven by a few extreme answers can be flagged."""
    full = anova_test(df, group, value)
    trimmed = anova_test(df[df["avg_screen_time_hours"] < HIGH_SCREEN_TIME_HOURS], group, value)
    full["p_without_high"] = trimmed["p"]
    # Significant overall, but not once the extreme answers are removed.
    full["driven_by_high"] = full["p"] < ALPHA <= trimmed["p"]
    return full


def describe_anova(t: dict, what: str, between: str) -> str:
    """One sentence reporting an ANOVA result (with the extreme-value check, if run)."""
    text = (f"One-way ANOVA: F = {t['F']:.2f}, {fmt_p(t['p'])}. "
            f"There {'is a' if t['p'] < ALPHA else 'is no'} statistically significant difference "
            f"in {what} between {between}.")
    if t.get("driven_by_high"):
        text += (f" However, without the {HIGH_SCREEN_TIME_HOURS}+ hrs/day reports the difference "
                 f"disappears ({fmt_p(t['p_without_high'])}), so it comes from a few very high answers "
                 "and may be a Type I error (a false positive).")
    if t["dropped"]:
        text += f" Left out for having fewer than 5 people: {', '.join(t['dropped'])}."
    return text


def ols_table(df: pd.DataFrame, y: str, numeric: list, categorical: list):
    """Multiple linear regression (ordinary least squares), using numpy/scipy.

    Categorical predictors are dummy-coded against their first level
    (alphabetical). Each coefficient's p-value comes from a t-test.
    Returns (coefficient table, summary dict).
    """
    d = df[[y] + numeric + categorical].dropna()
    X = pd.get_dummies(d[numeric + categorical], columns=categorical,
                       drop_first=True, dtype=float)
    X.insert(0, "Intercept", 1.0)
    Y = d[y].astype(float).values
    A = X.values.astype(float)

    n, k = A.shape
    beta, *_ = np.linalg.lstsq(A, Y, rcond=None)
    resid = Y - A @ beta
    dof = n - k
    sigma2 = resid @ resid / dof
    se = np.sqrt(np.diag(sigma2 * np.linalg.inv(A.T @ A)))
    p_vals = 2 * stats.t.sf(np.abs(beta / se), dof)

    ss_tot = ((Y - Y.mean()) ** 2).sum()
    r2 = 1 - (resid @ resid) / ss_tot
    f_stat = (r2 / (k - 1)) / ((1 - r2) / dof)
    f_p = stats.f.sf(f_stat, k - 1, dof)

    table = pd.DataFrame({"Term": X.columns, "Coefficient": beta, "p-value": p_vals})
    summary = {"n": n, "r2": float(r2), "f_p": float(f_p)}
    return table, summary


# ----------------------------------------------------------------------------
# Shared analyses (used by both the Home page and Robustness & Drivers, so the
# summary on Home always matches the detailed page).
# ----------------------------------------------------------------------------
# Factors compared with CGPA; CGPA itself is last so it can be used in a matrix.
DRIVER_VARIABLES = [
    "avg_screen_time_hours", "study_code", "sleep_code", "check_phone_during_study",
    "phone_during_lectures", "hard_to_reduce_screen_time", "digital_distraction",
    "academic_performance", "age", "cgpa",
]

REGRESSION_TERM_LABELS = {
    "avg_screen_time_hours": "Screen time (per extra hour/day)",
    "study_code": "Study hours (per band up)",
    "sleep_code": "Sleep (per band up)",
    "digital_distraction": "Digital distraction (per point)",
    "age": "Age (per year)",
}


def robustness_table(df: pd.DataFrame) -> pd.DataFrame:
    """Screen time vs CGPA (Pearson) repeated on progressively stricter subsets."""
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
        r, p, n = pearson(subset, "avg_screen_time_hours", "cgpa")
        rows.append({"Subset": name, "n": n, "r": r, "p-value": p,
                     "Significant (p < 0.05)": p < ALPHA})
    return pd.DataFrame(rows)


def cgpa_drivers(df: pd.DataFrame) -> pd.DataFrame:
    """Pearson correlation of each factor with CGPA, strongest first."""
    rows = []
    for v in DRIVER_VARIABLES[:-1]:
        r, p, n = pearson(df, v, "cgpa")
        rows.append({"Variable": v, "Factor": VARIABLE_LABELS[v], "r with CGPA": r, "p-value": p})
    drivers = pd.DataFrame(rows)
    drivers = drivers.reindex(drivers["r with CGPA"].abs().sort_values(ascending=False).index)
    drivers = drivers.reset_index(drop=True)
    drivers["Significant (p < 0.05)"] = drivers["p-value"] < ALPHA
    return drivers


def cgpa_regression(df: pd.DataFrame):
    """Regression of CGPA on habits, age, year and major category ('Other' major excluded)."""
    reg_df = df[df["major_category"] != "Other"]
    table, summary = ols_table(
        reg_df, "cgpa",
        numeric=["avg_screen_time_hours", "study_code", "sleep_code", "digital_distraction", "age"],
        categorical=["year", "major_category"],
    )
    table["Term"] = table["Term"].replace(REGRESSION_TERM_LABELS)
    return table, summary


def main_use_correlations(df: pd.DataFrame, group_col: str = "main_use", min_n: int = 5) -> pd.DataFrame:
    """Screen time vs CGPA (Pearson) within each main-use group with at least
    `min_n` students, also repeated without the 14+ hrs/day answers."""
    rows = []
    for use, g in df.dropna(subset=["avg_screen_time_hours", "cgpa"]).groupby(group_col):
        if len(g) < min_n:
            continue
        r, p, n = pearson(g, "avg_screen_time_hours", "cgpa")
        trimmed = g[g["avg_screen_time_hours"] < HIGH_SCREEN_TIME_HOURS]
        r2, p2 = (pearson(trimmed, "avg_screen_time_hours", "cgpa")[:2]
                  if len(trimmed) >= min_n else (np.nan, np.nan))
        rows.append({
            "Main use": use, "n": n,
            "Verified": int((g["Screen_Time_Confidence"] == "Verified").sum()),
            "Avg screen time (hrs)": g["avg_screen_time_hours"].mean(),
            "Avg CGPA": g["cgpa"].mean(),
            "r": r, "p-value": p, "Significant (p < 0.05)": p < ALPHA,
            f"r without {HIGH_SCREEN_TIME_HOURS}+ hrs": r2,
            f"p without {HIGH_SCREEN_TIME_HOURS}+ hrs": p2,
        })
    return pd.DataFrame(rows).sort_values("n", ascending=False).reset_index(drop=True)


def heavy_vs_light(g: pd.DataFrame) -> dict:
    """Split a group at its median screen time and compare the CGPA of heavier and
    lighter users with a two-sample t-test (not assuming equal variances)."""
    g = g.dropna(subset=["avg_screen_time_hours", "cgpa"])
    median = g["avg_screen_time_hours"].median()
    heavy = g.loc[g["avg_screen_time_hours"] > median, "cgpa"]
    light = g.loc[g["avg_screen_time_hours"] <= median, "cgpa"]
    t, p = stats.ttest_ind(heavy, light, equal_var=False)
    return {"median": float(median), "heavy_mean": float(heavy.mean()), "light_mean": float(light.mean()),
            "n_heavy": len(heavy), "n_light": len(light), "t": float(t), "p": float(p)}


# ----------------------------------------------------------------------------
# Chart helpers
# ----------------------------------------------------------------------------
def group_box_plot(df, group, value, title, labels=None, order=None,
                   sort_by_median=False, horizontal=False):
    """Box plot of `value` for each level of `group`, with the group size in
    each label. The line in the box is the median, the box covers the middle
    50% of answers, and dots beyond the whiskers are outliers."""
    d = df[[group, value]].dropna().copy()
    counts = d[group].value_counts()
    if order is not None:
        levels = [g for g in order if g in counts.index]
    elif sort_by_median:
        levels = list(d.groupby(group)[value].median().sort_values(ascending=False).index)
    else:
        levels = sorted(counts.index)
    d = d[d[group].isin(levels)]
    names = {g: f"{g} (n={counts[g]})" for g in levels}
    d["label"] = d[group].map(names)
    cat_order = [names[g] for g in levels]
    labels = dict(labels or {})
    labels["label"] = labels.get(group, group)
    if horizontal:
        fig = px.box(d, x=value, y="label", title=title, labels=labels,
                     category_orders={"label": cat_order})
        fig.update_layout(height=max(400, 32 * len(levels) + 150))
    else:
        fig = px.box(d, x="label", y=value, title=title, labels=labels,
                     category_orders={"label": cat_order})
    return fig


def scatter_with_trend(d, x, y, title, labels):
    """Scatter plot with a straight least-squares trend line (no statsmodels)."""
    fig = px.scatter(d, x=x, y=y, title=title, labels=labels, opacity=0.7)
    slope, intercept = np.polyfit(d[x], d[y], 1)
    xs = np.array([d[x].min(), d[x].max()])
    fig.add_scatter(x=xs, y=slope * xs + intercept, mode="lines",
                    name="Linear trend", line=dict(color="crimson"))
    fig.update_layout(height=500)
    return fig


def correlation_section(df, x, y, heading, question, labels):
    """Render one Pearson correlation (metrics, scatter plot, interpretation)
    and return (r, p, n)."""
    st.subheader(heading)
    st.write(question)
    d = df[[x, y]].dropna()
    r, p, n = pearson(d, x, y)

    c1, c2, c3 = st.columns(3)
    c1.metric("Pearson's r", f"{r:.2f}")
    c2.metric("p-value", f"{p:.4f}")
    c3.metric("Sample size", n)

    st.plotly_chart(scatter_with_trend(d, x, y, heading, labels),
                    width="stretch")
    st.info("**Interpretation**\n\n" + describe_correlation(r, p))
    return r, p, n


# ----------------------------------------------------------------------------
# Page layout helpers, so every page follows the same structure:
# title + intro, key takeaways, key numbers, tabbed sections, next-page link.
# ----------------------------------------------------------------------------
PAGE_ORDER = [
    ("pages/1_Home.py", "Home"),
    ("pages/2_Demographics.py", "Demographics"),
    ("pages/3_Screen_Time.py", "Screen Time"),
    ("pages/4_Academic_Performance.py", "Academic Performance"),
    ("pages/5_Relationships.py", "Relationships"),
    ("pages/6_Major_Analysis.py", "Major Analysis"),
    ("pages/7_Dataset_And_Methodology.py", "Dataset & Methodology"),
    ("pages/8_Robustness_And_Drivers.py", "Robustness & Drivers"),
]


def page_intro(title: str, intro: str):
    """Page title (matching the sidebar) and a one-line description."""
    st.title(title)
    st.markdown(intro)


def takeaways(points):
    """'Key takeaways' box shown at the top of each page."""
    st.info("**Key takeaways**\n\n" + "\n".join(f"- {p}" for p in points),
            icon=":material/lightbulb:")


def next_page(current: str):
    """Link to the next page in the sidebar order (or back to Home on the last page)."""
    paths = [p for p, _ in PAGE_ORDER]
    i = paths.index(current)
    st.divider()
    if i + 1 < len(PAGE_ORDER):
        path, title = PAGE_ORDER[i + 1]
        st.page_link(path, label=f"Next: {title}", icon=":material/arrow_forward:")
    else:
        st.page_link("pages/1_Home.py", label="Back to Home", icon=":material/home:")
