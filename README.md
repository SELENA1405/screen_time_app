# Student Screen Time & Academic Performance

An interactive Streamlit dashboard that asks whether daily screen time is associated with
academic performance (CGPA) among 129 university students, alongside sleep, study habits,
and digital distraction.

**Live app:** https://screen-time-vs-academic-performance.streamlit.app/

Originally a group project; rebuilt and extended independently as a solo portfolio project.

## Key findings

- Students report about 8 hours of screen time a day (median 7.7).
- **No significant relationship between screen time and CGPA** (Pearson r = −0.13, p = 0.15).
  The result holds when restricted to the 58 responses backed by a screenshot (r = −0.10, p = 0.46)
  and when excluding respondents reporting 14+ hours a day (r = −0.10, p = 0.31).
- Typed screen times track screenshots closely: among 44 verified respondents who gave a daily figure, 77% were within 1 hour (r = 0.69). Five typed weekly totals because the survey said "per week".
- Older students report slightly less screen time (r = −0.25, p = 0.004).
- Screen time looks higher in Year 1 (ANOVA p = 0.024), but this comes from the 14+ hour answers
  (9 of 14 are Year 1 students); without them there is no difference (p = 0.82).
- Sleep, study hours, phone use and digital distraction show no clear association with CGPA.
- In a regression controlling for the other factors, STEM & Health Sciences students have lower
  CGPA than Business students (p = 0.007). This is exploratory because the group is small.

## What's in the app

| Page | Content |
|---|---|
| Home | Summary of findings, with an answer to each research question (computed from the data) |
| Demographics | Sample profile: gender, age, year, major, allowance |
| Screen Time | Usage patterns, phone habits, group comparisons (box plots and ANOVA) |
| Academic Performance | CGPA distribution, study and sleep habits |
| Relationships | Pearson correlations with a verified-only toggle; screen time vs CGPA by main use (social media, streaming, gaming, study & work) |
| Major Analysis | Group comparisons with ANOVA |
| Dataset & Methodology | Data collection, cleaning (150 → 129 responses), data dictionary, limitations, raw and cleaned data with CSV downloads |
| Robustness & Drivers | Sensitivity checks, correlation heatmap, multiple regression |

## Methods

- **Pearson correlation** (r) with p-values, significance level 0.05.
- **One-way ANOVA** (F-test) for differences between groups.
- **Two-sample t-test** comparing heavier and lighter screen users within each main-use group.
- **Multiple linear regression** (numpy/scipy), with a t-test for each coefficient.
- **Robustness checks**: key results repeated with verified-only answers and without 14+ hrs/day reports.
- **Box plots** for comparing distributions between groups.

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
pages/1_Home.py     Home page: summary of findings and answers to the research questions
utils.py            Data loading, ordering constants, statistics and chart helpers
pages/              One file per dashboard page (2-8)
Data/Screen_Time_Data.xlsx        Survey data with screenshot links removed
                                  - OgData_Screenshot_Removed: 150 raw survey responses
                                  - CleanedData_Screenshot_Removed: 129 cleaned rows used by the app
Data/screen_time_validation.csv   Typed vs screenshot screen time for 49 respondents (no personal links)
```
