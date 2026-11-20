import pandas as pd
import plotly.express as px
import streamlit as st

from utils import load_data, HIGH_SCREEN_TIME_HOURS, DATA_PATH

st.title("Dataset & Methodology Dashboard")

df = load_data()

st.subheader("Dataset Overview")
st.write(
    f"The dataset contains **{len(df)} rows and {len(df.columns)} columns** after data "
    "cleaning (including a few columns derived during analysis). The original survey had "
    "150 responses; 129 were retained for the final analysis."
)

st.subheader("Data Collection Method")
st.write(
    "The data was collected through a student survey conducted over a 7-day period "
    "among Siam University students. The survey captured demographic characteristics, "
    "screen-time behavior, academic performance, study habits, sleep patterns, and "
    "digital distractions. Screen-time values were supported by screenshots where "
    "available, and each response was labelled **Verified** (a screenshot was provided) "
    "or **Unverified** (self-reported only)."
)

st.subheader("Dataset Source")
st.write(
    "The dataset consists of primary data collected directly from Siam University "
    "students through the survey. No external dataset was used for the main analysis."
)

st.subheader("Collection Period")
st.write(
    "Data collection was conducted over a 7-day period, during which students were "
    "invited to complete the survey."
)

# ----------------------------------------------------------------------------
st.subheader("Screen-Time Data Confidence")
conf = df["Screen_Time_Confidence"].value_counts()
c1, c2 = st.columns(2)
c1.metric("Verified (screenshot provided)", int(conf.get("Verified", 0)))
c2.metric("Unverified (self-reported only)", int(conf.get("Unverified", 0)))

# ----------------------------------------------------------------------------
st.subheader("Data Cleaning")
st.markdown(
    """
The raw survey export contained 150 responses. Questions were free text for age, CGPA and
screen time, so the answers needed cleaning before analysis:

1. **Free-text answers were converted to numbers**: for example "9h 40m" became 9.67 hours.
2. **Responses with unusable values were removed**, leaving 129. The cleaned data contains no
   CGPA above 4.0, no screen time above 24 hours a day, and no non-numeric answers.
3. **Majors were standardised** and grouped into broader major categories.
4. **Screenshots were used to check screen time.** Where a respondent uploaded a screenshot of
   their weekly screen-time report, the daily average from the screenshot replaced their typed
   answer and the response was labelled **Verified**.
"""
)
st.caption(
    "The question wording asked for hours per week, but most respondents answered with a daily "
    "figure. The analysis treats screen time as a daily average, in line with the screenshots."
)

# ----------------------------------------------------------------------------
st.subheader("How accurate were self-reported screen times?")
VALIDATION_PATH = DATA_PATH.parent / "screen_time_validation.csv"
if VALIDATION_PATH.exists():
    val = pd.read_csv(VALIDATION_PATH)
    weekly_sized = val[val["reported_hours"] > 24]
    daily = val[val["reported_hours"] <= 24].copy()
    daily["error"] = daily["reported_hours"] - daily["screenshot_hours"]
    rho = daily["reported_hours"].corr(daily["screenshot_hours"], method="spearman")

    st.write(
        "For respondents who supplied a screenshot, the typed answer can be compared with the "
        "screenshot value. This shows how much to trust the unverified answers."
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pairs compared", len(val))
    c2.metric("Within 1 hour", f"{(daily['error'].abs() <= 1).mean():.0%}",
              help="Share of daily-range answers within one hour of the screenshot")
    c3.metric("Rank correlation", f"{rho:.2f}")
    c4.metric("Weekly-sized answers (>24h)", len(weekly_sized))

    fig = px.scatter(
        daily, x="screenshot_hours", y="reported_hours", hover_data=["reported_text"],
        title="Reported vs screenshot daily screen time (hours)",
        labels={"screenshot_hours": "Screenshot value (hrs/day)", "reported_hours": "Typed answer (hrs/day)"},
    )
    top = float(max(daily["screenshot_hours"].max(), daily["reported_hours"].max()))
    fig.add_scatter(x=[0, top], y=[0, top], mode="lines", name="Perfect agreement",
                    line=dict(dash="dash", color="grey"))
    st.plotly_chart(fig, use_container_width=True)

    st.info(
        f"Among the {len(daily)} daily-range answers, typed values track the screenshots closely "
        f"(rank correlation {rho:.2f}, mean error {daily['error'].mean():+.2f} hrs, median "
        f"{daily['error'].median():+.2f}). {len(weekly_sized)} respondents typed weekly totals "
        f"(for example {', '.join(weekly_sized['reported_text'].head(3))}) because the question said "
        "'per week'; for verified respondents these were replaced by the screenshot value. Unverified "
        "respondents may contain similar slips, which is a limitation. Only respondents who chose to "
        "upload a screenshot are compared, so the result may not represent everyone."
    )

# ----------------------------------------------------------------------------
st.subheader("Data Dictionary")
dictionary = pd.DataFrame(
    [
        ("gender", "Self-reported gender (Male / Female / Other)"),
        ("age", "Age in years"),
        ("year", "Academic year (Year 1 to Year 4)"),
        ("major", "Student's major as reported"),
        ("major_category", "Majors grouped into broader categories (derived)"),
        ("monthly_allowance", "Monthly allowance band"),
        ("screen_time_hours / screen_time_minutes", "Reported daily screen time, split into hours and minutes"),
        ("avg_screen_time_hours", "Daily screen time in hours (hours + minutes / 60)"),
        ("Screen_Time_Confidence", "Verified if a screenshot was provided, otherwise Unverified"),
        ("main_use", "Main use of screen time"),
        ("peak_time", "Time of day with the most screen use"),
        ("check_phone_during_study", "How often the student checks their phone while studying (1 = Never to 5 = Very Often)"),
        ("phone_during_lectures", "How often the student uses their phone in lectures (1 to 5)"),
        ("hard_to_reduce_screen_time", "How hard it is to reduce screen time (1 to 5)"),
        ("cgpa", "Cumulative grade point average (4.0 scale)"),
        ("sleep_hours", "Typical nightly sleep, in bands"),
        ("academic_performance", "Self-rated academic performance (1 to 5)"),
        ("study_hours_outside_class", "Daily study time outside class, in bands"),
        ("digital_distraction", "Self-rated digital distraction (1 to 5)"),
        ("study_code / sleep_code", "Ordinal codes (0 = lowest band) for study and sleep bands (derived)"),
    ],
    columns=["Column", "Description"],
)
st.dataframe(dictionary, use_container_width=True, hide_index=True)

# ----------------------------------------------------------------------------
st.subheader("Limitations")
high = df["avg_screen_time_hours"] >= HIGH_SCREEN_TIME_HOURS
n_high = int(high.sum())
n_high_verified = int((high & (df["Screen_Time_Confidence"] == "Verified")).sum())
n_minor = int((df["age"] < 18).sum())
st.markdown(
    f"""
- **Self-reported data.** Screen time, sleep, study hours and academic performance are
  reported by the students themselves and may be inaccurate. Only {int(conf.get('Verified', 0))} of
  {len(df)} screen-time values are backed by a screenshot.
- **Question wording.** The survey asked for hours per week, but answers were treated as a daily
  average. Verified respondents' values come from screenshots; unverified answers may include
  weekly-style slips.
- **Very high values.** {n_high} respondents report {HIGH_SCREEN_TIME_HOURS}+ hours a day, and
  {n_high_verified} of them are confirmed by a screenshot. The Robustness & Drivers page checks
  that the conclusions do not depend on these values.
- **Convenience sample from one university.** Results describe these {len(df)} students and
  should not be generalised to all students.
- **Small groups.** Some majors and the "Other" gender and major categories have very few
  respondents, so comparisons involving them are unreliable.
- **Limited CGPA variation.** CGPA is concentrated near the top of the scale, which makes
  weak associations harder to detect.
- **Unusual ages.** {n_minor} respondents are under 18, which is unexpected for university students.
- **Association, not causation.** The analysis is cross-sectional, so it cannot show that
  screen time causes any change in academic performance.
- **Multiple tests.** Many hypothesis tests are run across the dashboard; an isolated
  p-value just below 0.05 may arise by chance.
"""
)

st.subheader("Dataset Preview")
st.dataframe(df, use_container_width=True)
