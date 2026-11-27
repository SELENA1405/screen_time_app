"""Entry point: sets up the sidebar navigation and runs the selected page.

Run with `streamlit run app.py`. Each page lives in its own file; the URL paths
are fixed so existing links to individual pages keep working.
"""

import streamlit as st

st.set_page_config(page_title="Student Screen Time & Academic Performance")

pages = [
    st.Page("home.py", title="Home", default=True),
    st.Page("pages/2_Demographics.py", title="Demographics", url_path="Demographics"),
    st.Page("pages/3_Screen_Time.py", title="Screen Time", url_path="Screen_Time"),
    st.Page("pages/4_Academic_Performance.py", title="Academic Performance",
            url_path="Academic_Performance"),
    st.Page("pages/5_Relationships.py", title="Relationships", url_path="Relationships"),
    st.Page("pages/6_Major_Analysis.py", title="Major Analysis", url_path="Major_Analysis"),
    st.Page("pages/7_Dataset_And_Methodology.py", title="Dataset & Methodology",
            url_path="Dataset_And_Methodology"),
    st.Page("pages/8_Robustness_And_Drivers.py", title="Robustness & Drivers",
            url_path="Robustness_And_Drivers"),
]

st.navigation(pages).run()
