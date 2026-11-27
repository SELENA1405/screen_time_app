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


# ----------------------------------------------------------------------------
# Statistics helpers
# ----------------------------------------------------------------------------
def spearman(df: pd.DataFrame, x: str, y: str):
    """Spearman correlation on complete cases. Returns (rho, p, n)."""
    d = df[[x, y]].dropna()
    rho, p = stats.spearmanr(d[x], d[y])
    return float(rho), float(p), len(d)


def strength_label(rho: float) -> str:
    a = abs(rho)
    if a < 0.2:
        return "very weak"
    if a < 0.4:
        return "weak"
    if a < 0.6:
        return "moderate"
    return "strong"


def describe_correlation(rho: float, p: float, alpha: float = 0.05) -> str:
    """Plain-English interpretation generated from the numbers, so the text can
    never disagree with the statistics if the data changes."""
    direction = "negative" if rho < 0 else "positive"
    verdict = "was" if p < alpha else "was not"
    if abs(rho) < 0.1:
        lead = "There is almost no monotonic association"
    else:
        lead = f"There is a {strength_label(rho)} {direction} association"
    return (
        f"{lead} (ρ = {rho:.2f}). The association {verdict} statistically "
        f"significant (p = {p:.4f})."
    )


def kruskal_test(df: pd.DataFrame, group: str, value: str, exclude=(), min_n: int = 5):
    """Kruskal-Wallis test of `value` across the levels of `group`.

    Groups with fewer than `min_n` observations (or listed in `exclude`) are
    dropped because they are too small to say anything. Returns a dict with
    H, p, epsilon-squared (effect size), n, the groups used and those dropped.
    """
    d = df[[group, value]].dropna()
    d = d[~d[group].isin(exclude)]
    counts = d[group].value_counts()
    keep = counts[counts >= min_n].index
    dropped = [g for g in counts.index if g not in keep]
    d = d[d[group].isin(keep)]
    samples = [g[value].values for _, g in d.groupby(group)]
    h, p = stats.kruskal(*samples)
    n = len(d)
    eps2 = h * (n + 1) / (n**2 - 1)
    return {"H": float(h), "p": float(p), "eps2": float(eps2), "n": n,
            "groups": sorted(keep), "dropped": dropped}


def ols_table(df: pd.DataFrame, y: str, numeric: list, categorical: list):
    """Ordinary least squares with 95% CIs, using only numpy/scipy.

    Categorical predictors are dummy-coded against their first level
    (alphabetical). Returns (coefficient table, summary dict).
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
    t_vals = beta / se
    p_vals = 2 * stats.t.sf(np.abs(t_vals), dof)
    crit = stats.t.ppf(0.975, dof)

    ss_tot = ((Y - Y.mean()) ** 2).sum()
    r2 = 1 - (resid @ resid) / ss_tot
    adj_r2 = 1 - (1 - r2) * (n - 1) / dof
    f_stat = (r2 / (k - 1)) / ((1 - r2) / dof)
    f_p = stats.f.sf(f_stat, k - 1, dof)

    table = pd.DataFrame({
        "Term": X.columns,
        "Coefficient": beta,
        "Std. error": se,
        "CI low": beta - crit * se,
        "CI high": beta + crit * se,
        "p-value": p_vals,
    })
    summary = {"n": n, "r2": float(r2), "adj_r2": float(adj_r2),
               "f_p": float(f_p)}
    return table, summary


# ----------------------------------------------------------------------------
# Chart helpers
# ----------------------------------------------------------------------------
def mean_ci_table(df, group, value, order=None, sort_desc=False):
    """Mean, SD, n and 95% CI half-width of `value` per level of `group`."""
    g = df.groupby(group)[value].agg(["mean", "std", "count"]).reset_index()
    sem = g["std"] / np.sqrt(g["count"])
    crit = stats.t.ppf(0.975, (g["count"] - 1).clip(lower=1))
    g["ci"] = np.where(g["count"] > 1, crit * sem, np.nan)
    if order is not None:
        g[group] = pd.Categorical(g[group], categories=order, ordered=True)
        g = g.sort_values(group).dropna(subset=[group])
        g[group] = g[group].astype(str)
    elif sort_desc:
        g = g.sort_values("mean", ascending=False)
    g["label"] = g[group].astype(str) + " (n=" + g["count"].astype(str) + ")"
    return g


def mean_ci_plot(df, group, value, title, labels=None, order=None,
                 sort_desc=False, horizontal=False):
    """Dot-and-whisker chart: group means with 95% confidence intervals and the
    group size in each label. Honest about small groups (n=1 has no whisker)."""
    g = mean_ci_table(df, group, value, order=order, sort_desc=sort_desc)
    labels = dict(labels or {})
    labels.update({"mean": labels.get(value, value), "label": labels.get(group, group)})
    if horizontal:
        fig = px.scatter(g, x="mean", y="label", error_x="ci", title=title, labels=labels)
        fig.update_yaxes(categoryorder="array", categoryarray=list(g["label"])[::-1])
    else:
        fig = px.scatter(g, x="label", y="mean", error_y="ci", title=title, labels=labels)
    fig.update_traces(marker=dict(size=11))
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
    """Render one Spearman analysis (metrics, scatter plot, interpretation)
    and return (rho, p, n)."""
    st.subheader(heading)
    st.write(question)
    d = df[[x, y]].dropna()
    rho, p, n = spearman(d, x, y)

    c1, c2, c3 = st.columns(3)
    c1.metric("Spearman's ρ", f"{rho:.2f}")
    c2.metric("p-value", f"{p:.4f}")
    c3.metric("Sample size", n)

    st.plotly_chart(scatter_with_trend(d, x, y, heading, labels),
                    width="stretch")
    st.info("**Interpretation**\n\n" + describe_correlation(rho, p))
    return rho, p, n
