import streamlit as st

from utils import load_data, spearman, HIGH_SCREEN_TIME_HOURS

st.set_page_config(page_title="Student Screen Time & Academic Performance", layout="wide")

df = load_data()

st.html("<h1 style='text-align: center; width: 100%;'>STUDENT SCREEN TIME & ACADEMIC PERFORMANCE</h1>")
st.html("<h3 style='text-align: center; width: 100%;'>Student Digital Habits Analysis</h3>")

st.write("")
st.markdown(
    f"""
    <div style='text-align: center; max-width: 700px; margin: 0 auto;'>
    An interactive dashboard exploring whether screen time is associated with
    academic performance among {len(df)} Siam University students, alongside
    sleep, study habits, and digital distraction.
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")
st.info(
    "Use the sidebar to navigate. Start with **Relationships** for the core "
    "analysis, then **Robustness & Drivers** to see whether the findings hold up."
)

# ----------------------------------------------------------------------------
# Headline numbers are computed from the data, not typed in by hand.
# ----------------------------------------------------------------------------
rho_c, p_c, n_c = spearman(df, "avg_screen_time_hours", "cgpa")
rho_a, p_a, _ = spearman(df, "age", "avg_screen_time_hours")
verified = df[df["Screen_Time_Confidence"] == "Verified"]
rho_v, p_v, n_v = spearman(verified, "avg_screen_time_hours", "cgpa")

st.subheader("Key Findings")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Respondents", len(df))
c2.metric("Average daily screen time", f"{df['avg_screen_time_hours'].mean():.1f} hrs")
c3.metric("Average CGPA", f"{df['cgpa'].mean():.2f}")
c4.metric("Screen time ↔ CGPA (ρ)", f"{rho_c:.2f}", help=f"p = {p_c:.3f}, n = {n_c}")

st.markdown(
    f"""
- Students report about **{df['avg_screen_time_hours'].mean():.1f} hours** of screen time a day
  (median {df['avg_screen_time_hours'].median():.1f}).
- **No significant link between screen time and CGPA** was found
  (ρ = {rho_c:.2f}, p = {p_c:.2f}). The result is similar using only the
  {n_v} responses backed by a screenshot (ρ = {rho_v:.2f}, p = {p_v:.2f}).
- Older students tend to report **less** screen time (ρ = {rho_a:.2f}, p = {p_a:.3f}),
  a weak but statistically significant association.
- Screen time is self-reported, and {int((df['avg_screen_time_hours'] >= HIGH_SCREEN_TIME_HOURS).sum())}
  respondents report {HIGH_SCREEN_TIME_HOURS}+ hours a day, so results should be read
  with caution. See **Dataset & Methodology** for limitations.
"""
)

st.subheader("Research Questions")
st.markdown(
    """
1. What does screen-time behavior look like among participants?
2. How does screen time differ across demographic groups?
3. How does screen time relate to academic performance and lifestyle factors?
4. Which factors are most strongly associated with academic performance?
5. Do the findings remain similar when restricted to verified screen-time responses?
"""
)
