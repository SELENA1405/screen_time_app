# Student Screen Time & Academic Performance

An interactive Streamlit dashboard that asks whether daily screen time is associated with
academic performance (CGPA) among 129 university students, alongside sleep, study habits,
and digital distraction.

**Live app:** https://screen-time-vs-academic-performance.streamlit.app/

Originally a group project; rebuilt and extended independently as a solo portfolio project.

## Key findings

- Students report about 8 hours of screen time a day (median 7.7).
- **No significant association between screen time and CGPA** (Spearman ρ = −0.12, p = 0.17).
  The result holds when restricted to the 58 responses backed by a screenshot (ρ = −0.10, p = 0.44)
  and when excluding respondents reporting 14+ hours a day (ρ = −0.10, p = 0.31).
- Typed screen times track screenshots closely: among 44 verified respondents who gave a daily figure, 77% were within 1 hour (rank correlation 0.81). Five typed weekly totals because the survey said "per week".
- Older students report slightly less screen time (ρ = −0.25, p = 0.004).
- Sleep, study hours, phone use and digital distraction show no clear association with CGPA.
- In a regression controlling for the other factors, STEM & Health Sciences students have lower
  CGPA than Business students (p = 0.007). This is exploratory because the group is small.

## What's in the app

| Page | Content |
|---|---|
| Home | Summary of findings, with an answer to each research question (computed from the data) |
| Demographics | Sample profile: gender, age, year, major, allowance |
| Screen Time | Usage patterns, phone habits, group comparisons with 95% CIs |
| Academic Performance | CGPA distribution, study and sleep habits |
| Relationships | Spearman correlations with a verified-only toggle |
| Major Analysis | Group comparisons with Kruskal-Wallis tests |
| Dataset & Methodology | Data collection, cleaning (150 → 129 responses), data dictionary, limitations, raw and cleaned data with CSV downloads |
| Robustness & Drivers | Sensitivity checks, correlation heatmap, multiple regression |

## Methods

- **Spearman rank correlation**, chosen because screen time and age contain extreme values.
- **Kruskal-Wallis test** with epsilon-squared effect size for group differences.
- **OLS regression** (numpy/scipy) with 95% confidence intervals.
- **Sensitivity analysis**: verified-only and outlier-excluded subsets.
- **Bonferroni adjustment** when ranking factors against CGPA.

## Limitations

Self-reported data from a convenience sample at one university; 71 of 129 screen-time values are
unverified; CGPA is concentrated near the top of the scale; several groups are very small; the
analysis is cross-sectional, so it shows association, not causation.

## Run it locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Project structure

```
app.py              Entry point: sidebar navigation (run this file)
home.py             Home page: summary of findings and answers to the research questions
utils.py            Data loading, ordering constants, statistics and chart helpers
pages/              One file per dashboard page
Data/Screen_Time_Data.xlsx        Survey data with screenshot links removed
                                  - OgData_Screenshot_Removed: 150 raw survey responses
                                  - CleanedData_Screenshot_Removed: 129 cleaned rows used by the app
Data/screen_time_validation.csv   Typed vs screenshot screen time for 49 respondents (no personal links)
```
