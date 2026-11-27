import pandas as pd
import plotly.express as px
import streamlit as st

from utils import (
    load_data, load_raw_data, collection_period, HIGH_SCREEN_TIME_HOURS, DATA_PATH,
    SHEET_NAME, RAW_SHEET_NAME, page_intro, takeaways, next_page,
)


df = load_data()
raw = load_raw_data()

# Raw survey columns are named "<number>. <question>"; index them by number.
Q = {c.split(".")[0].strip(): c for c in raw.columns if c.split(".")[0].strip().isdigit()}
DERIVED = ["study_code", "sleep_code"]  # added by the app in utils.load_data
n_clean_cols = len(df.columns) - len(DERIVED)

page_intro(
    "Dataset & Methodology",
    "Where the data came from, how it was cleaned, what each column means, which statistical "
    "methods were used, and the raw and cleaned data themselves.",
)

# ----------------------------------------------------------------------------
# Key takeaways (computed from the data)
# ----------------------------------------------------------------------------
n_verified = int((df["Screen_Time_Confidence"] == "Verified").sum())
_val_path = DATA_PATH.parent / "screen_time_validation.csv"
_within = None
if _val_path.exists():
    _v = pd.read_csv(_val_path)
    _v = _v[_v["reported_hours"] <= 24]
    _within = ((_v["reported_hours"] - _v["screenshot_hours"]).abs() <= 1).mean()
points = [
    f"{len(raw)} survey responses were collected ({collection_period(raw)}); {len(df)} were kept "
    f"after cleaning and {len(raw) - len(df)} were removed, mostly for unusable CGPA answers.",
    f"{n_verified} of {len(df)} screen-time values ({n_verified / len(df):.0%}) are backed by a screenshot.",
]
if _within is not None:
    points.append(f"Where both exist, {_within:.0%} of typed daily answers are within 1 hour of the "
                  "screenshot, so self-reports are mostly reliable.")
points.append("Main methods: Pearson correlation, one-way ANOVA and multiple regression, with "
              "p < 0.05 as the significance level.")
takeaways(points)

tabs = st.tabs(['Overview', 'Cleaning', 'Data dictionary', 'Methods & limitations', 'View the data'])

with tabs[0]:
    st.subheader("Dataset Overview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Survey responses (raw)", len(raw))
    c2.metric("Kept after cleaning", len(df))
    c3.metric("Removed during cleaning", len(raw) - len(df))
    st.markdown(
        f"""
    The data file `{DATA_PATH.name}` has two sheets:

    - **Raw survey responses** (`{RAW_SHEET_NAME}`): {len(raw)} responses exactly as submitted,
      with a timestamp and {len(Q)} survey questions. The screenshot upload question (Q7) has been
      removed to protect respondents' privacy.
    - **Cleaned data** (`{SHEET_NAME}`): the {len(df)} responses kept for analysis, in
      {n_clean_cols} columns. Every page of this dashboard uses this sheet. The app adds
      {len(DERIVED)} more columns ({", ".join(DERIVED)}) when it loads the data.

    Both sheets can be viewed and downloaded in the **View the data** tab.
    """
    )

    st.subheader("Data Collection Method")
    st.write(
        "The data was collected through an online survey of Siam University students. "
        "The survey captured demographic characteristics, "
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
    ts = pd.to_datetime(raw["Timestamp"], errors="coerce").dropna()
    first_week = (ts < ts.min().normalize() + pd.Timedelta(days=7)).mean()
    st.write(
        f"Responses were submitted between **{collection_period(raw)}**. "
        f"{first_week:.0%} of them arrived within the first 7 days."
    )

    st.subheader("Screen-Time Data Confidence")
    conf = df["Screen_Time_Confidence"].value_counts()
    c1, c2 = st.columns(2)
    c1.metric("Verified (screenshot provided)", int(conf.get("Verified", 0)))
    c2.metric("Unverified (self-reported only)", int(conf.get("Unverified", 0)))

with tabs[1]:
    st.subheader("Data Cleaning")

    # Problems visible in the raw answers, counted directly from the raw sheet.
    cgpa_num = pd.to_numeric(raw[Q["13"]], errors="coerce")
    n_cgpa_text = int(cgpa_num.isna().sum())
    n_cgpa_high = int((cgpa_num > 4).sum())
    screen_txt = raw[Q["6"]].astype("string").str.strip()
    n_screen_blank = int((~screen_txt.str.contains(r"\d", na=False)).sum())
    n_age_text = int(pd.to_numeric(raw[Q["2"]], errors="coerce").isna().sum())
    n_major_spellings = raw[Q["4"]].astype("string").str.strip().nunique()

    st.markdown(
        f"""
    Age, CGPA, major and screen time were typed as free text, so the raw answers needed cleaning
    before analysis. In the raw data:

    - **{n_cgpa_text}** CGPA answers are not numbers (for example "-", "idk" or "Not yet"), and
      **{n_cgpa_high}** {'is' if n_cgpa_high == 1 else 'are'} above the 4.0 maximum.
    - **{n_screen_blank}** screen-time answers contain no number at all, and others are written in many
      formats ("7h 46m", "around 5h", "6-7 h.").
    - **{n_age_text}** age answer{'' if n_age_text == 1 else 's'} {'is' if n_age_text == 1 else 'are'} not a number.
    - The major question has **{n_major_spellings}** different spellings.

    The cleaning steps were:

    1. **Responses that could not be used were removed**: {len(raw)} responses became {len(df)}
       ({len(raw) - len(df)} removed). The cleaned data contains no CGPA above 4.0, no screen time
       above 24 hours a day, and no non-numeric answers.
    2. **Free-text answers were converted to numbers**: for example "7h 46m" became 7.77 hours.
    3. **Majors were standardised** into {df["major"].nunique()} majors and grouped into
       {df["major_category"].nunique()} broader categories.
    4. **Screenshots were used to check screen time.** Where a respondent uploaded a screenshot of
       their weekly screen-time report, the daily average from the screenshot replaced their typed
       answer and the response was labelled **Verified**. The screenshot links have since been
       removed from both sheets.
    """
    )
    st.caption(
        "The question wording asked for hours per week, but most respondents answered with a daily "
        "figure. The analysis treats screen time as a daily average, in line with the screenshots."
    )

    st.subheader("How accurate were self-reported screen times?")
    VALIDATION_PATH = DATA_PATH.parent / "screen_time_validation.csv"
    if VALIDATION_PATH.exists():
        val = pd.read_csv(VALIDATION_PATH)
        weekly_sized = val[val["reported_hours"] > 24]
        daily = val[val["reported_hours"] <= 24].copy()
        daily["error"] = daily["reported_hours"] - daily["screenshot_hours"]
        r_val = daily["reported_hours"].corr(daily["screenshot_hours"], method="pearson")

        st.write(
            "For respondents who supplied a screenshot, the typed answer can be compared with the "
            "screenshot value. This shows how much to trust the unverified answers."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Pairs compared", len(val))
        c2.metric("Within 1 hour", f"{(daily['error'].abs() <= 1).mean():.0%}",
                  help="Share of daily-range answers within one hour of the screenshot")
        c3.metric("Correlation (r)", f"{r_val:.2f}")
        c4.metric("Weekly totals typed", len(weekly_sized), help="Answers above 24 hours, i.e. a weekly total")

        fig = px.scatter(
            daily, x="screenshot_hours", y="reported_hours", hover_data=["reported_text"],
            title="Reported vs screenshot daily screen time (hours)",
            labels={"screenshot_hours": "Screenshot value (hrs/day)", "reported_hours": "Typed answer (hrs/day)"},
        )
        top = float(max(daily["screenshot_hours"].max(), daily["reported_hours"].max()))
        fig.add_scatter(x=[0, top], y=[0, top], mode="lines", name="Perfect agreement",
                        line=dict(dash="dash", color="grey"))
        st.plotly_chart(fig, width="stretch")

        st.info(
            f"Among the {len(daily)} daily-range answers, typed values track the screenshots closely "
            f"(Pearson's r = {r_val:.2f}, mean error {daily['error'].mean():+.2f} hrs, median "
            f"{daily['error'].median():+.2f}). {len(weekly_sized)} respondents typed weekly totals "
            f"(for example {', '.join(weekly_sized['reported_text'].head(3))}) because the question said "
            "'per week'; for verified respondents these were replaced by the screenshot value. Unverified "
            "respondents may contain similar slips, which is a limitation. Only respondents who chose to "
            "upload a screenshot are compared, so the result may not represent everyone."
        )

with tabs[2]:
    st.subheader("Data Dictionary")
    st.write("Columns of the cleaned data, and the survey question each one comes from.")


    def question(n):
        """Survey question text for question number n, as worded in the raw data."""
        col = Q.get(str(n))
        return f"Q{n}. " + " ".join(col.split(".", 1)[1].split()) if col else ""


    dictionary = pd.DataFrame(
        [
            ("gender", "Self-reported gender (Male / Female / Other)", question(1)),
            ("age", "Age in years", question(2)),
            ("year", "Academic year (Year 1 to Year 4)", question(3)),
            ("major", "Major, standardised from the typed answer", question(4)),
            ("major_category", "Majors grouped into broader categories", "Derived from major"),
            ("monthly_allowance", "Monthly allowance band (THB)", question(5)),
            ("avg_screen_time_hours", "Average daily screen time in hours (from the screenshot if verified)",
             question(6)),
            ("hour (h) / minnutes (m)", "avg_screen_time_hours split into whole hours and minutes",
             "Derived from avg_screen_time_hours"),
            ("Screen_Time_Confidence", "Verified if a screenshot was provided, otherwise Unverified",
             "Q7. Screenshot upload (removed for privacy)"),
            ("main_use", "Main use of screen time", question(8)),
            ("peak_time", "Time of day with the most screen use", question(9)),
            ("check_phone_during_study", "1 = Never to 5 = Very Often", question(10)),
            ("phone_during_lectures", "1 = Never to 5 = Very Often", question(11)),
            ("hard_to_reduce_screen_time", "1 = Never to 5 = Very Often", question(12)),
            ("cgpa", "Cumulative grade point average (4.0 scale)", question(13)),
            ("sleep_hours", "Typical nightly sleep, in bands", question(14)),
            ("academic_performance", "Self-rated academic performance (1 to 5)", question(15)),
            ("study_hours_outside_class", "Daily study time outside class, in bands", question(16)),
            ("digital_distraction", "Self-rated digital distraction (1 to 5)", question(17)),
            ("study_code / sleep_code", "Ordinal codes (0 = lowest band) for study and sleep bands",
             "Added by the app"),
        ],
        columns=["Column", "Description", "Source"],
    )
    st.table(dictionary.set_index("Column"))

with tabs[3]:
    st.subheader("Statistical Methods")
    st.markdown(
        """
    - **Pearson's correlation (r)** measures how strongly two numeric variables move together in a
      straight line, from -1 to +1. Its p-value tests whether r differs from zero. Ordered answers
      (1-5 ratings, and the sleep and study bands coded 0, 1, 2, 3) are treated as numbers.
    - **One-way ANOVA** compares the average of a variable across three or more groups (for example
      academic years) using an F-test. Groups with fewer than 5 students are left out.
    - **Multiple linear regression** estimates each factor's link with CGPA while holding the others
      constant. Each coefficient is tested with a t-test.
    - **Significance level.** A result is called statistically significant when p < 0.05. Because
      screen time includes some very high answers, key results are also repeated without the
      14+ hrs/day reports and with screenshot-verified answers only (see **Robustness & Drivers**).
    - **Box plots** show the median (line), the middle 50% of answers (box) and outliers (dots).
    """
    )

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
    - **Multiple tests.** Many hypothesis tests are run across the dashboard. Each test at the 5%
      level has a 5% chance of a false positive (a Type I error), so an isolated p-value just below
      0.05 may arise by chance.
    - **Small groups and power.** With small groups, a real but modest difference may not reach
      significance (a Type II error), so "not significant" does not prove there is no difference.
    """
    )

with tabs[4]:
    st.subheader("View the Data")
    tab_clean, tab_raw = st.tabs([f"Cleaned data ({len(df)} rows)", f"Raw survey responses ({len(raw)} rows)"])

    with tab_clean:
        st.caption("The data used by every page, including the columns the app adds.")
        st.dataframe(df, width="stretch")
        st.download_button(
            "Download cleaned data (CSV)", df.to_csv(index=False).encode("utf-8-sig"),
            file_name="screen_time_cleaned.csv", mime="text/csv",
        )

    with tab_raw:
        st.caption(
            "Responses exactly as submitted, before any cleaning. The screenshot upload "
            "question (Q7) has been removed to protect respondents' privacy."
        )
        raw_view = raw.rename(columns=lambda c: " ".join(str(c).split()))
        # Free-text columns mix numbers and text (e.g. CGPA "3.5" and "idk"); show them as text.
        for col in raw_view.columns:
            if raw_view[col].dtype == object:
                raw_view[col] = raw_view[col].astype("string")
        st.dataframe(raw_view, width="stretch")
        st.download_button(
            "Download raw responses (CSV)", raw_view.to_csv(index=False).encode("utf-8-sig"),
            file_name="screen_time_raw.csv", mime="text/csv",
        )

next_page("pages/7_Dataset_And_Methodology.py")
