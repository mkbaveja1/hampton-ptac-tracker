import streamlit as st
import pandas as pd
from supabase import create_client, Client

st.set_page_config(page_title = "PTAC Pro Tracker Console", page_icon = "/Users/mannatbaveja/hampton-ptac-tracker/hamptonlogo.png", layout = "wide")
if "supabase" not in st.session_state:
    url: str = st.secrets["supabase"]["url"]
    key: str = st.secrets["supabase"]["key"]
    supabase: Client = create_client(url, key)

#moving navigation to the top
nav_cols = st.columns([1.5, 3.5])
with nav_cols[0]:
    st.markdown(
        """
        <div style= 'display: flex; align-items: center; gap: 12px; margin-top: -5px;'>
            <div style= 'background-color: #2563eb; padding: 8px; border-radius: 10px; color: white; font-weight: bold;'>🏨</div>
            <div>
                <h1 style= 'font-size: 18px; font-weight: 900; margin: 0; line-height: 1; color: #0f172a;'>PTAC Pro Tracker</h1>
                <span style= 'font-size: 10px; color: #64748b; font-weight: bold; tracking: uppercase;'>Console Management System</span>
            </div>
        </div>
        """,
        unsafe_allow_html = True
    )
    

page_map = {
    "🏨 Hotel Operations View": {
        "Dashboard Grid": st.Page("views/dashboard.py", title = "Dashboard Grid", icon = "📊", default = True),
        "Directory List": st.Page("views/directory.py", title = "Directory List", icon = "📋"),
        "Smart QR Scanner": st.Page("views/scanner.py", title = "Smart QR Tag Scanner", icon = "📸"),
        "Avery Labels": st.Page("views/avery.py", title = "Avery Label Sheet Printer", icon = "🖨️"),
        "Spending Audits": st.Page("views/analytics.py", title = "Spending & PM Audits", icon = "💰"),
    },
    "🛠️ Contractor Portals": {
        "Doyle Tech Portal": st.Page("views/doyle.py", title = "Doyle Tech Portal", icon = "🔧"),
    }
}

#setting defaults
if"current_category" not in st.session_state:
    st.session_state.current_category = "🏨 Hotel Operations View"

if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard Grid"

with nav_cols[1]:

    #this is the main categories (hotel operations view and contractor portal)
    selected_category = st.segmented_control(
        label = "System Mode", 
        options = list(page_map.keys()),
        default = st.session_state.current_category,
        label_visibility = "collapsed"
    )

    if selected_category and selected_category != st.session_state.current_category:
        st.session_state.current_category = selected_category
        st.session_state.current_page = list(page_map[selected_category].keys())[0]
        st.rerun()

st.write(" ")
available_pages = page_map[st.session_state.current_category]        #this is for the sub-dictionary

selected_page = st.segmented_control(
    label = "Sub-Navigation Pages",
    options = list(available_pages.keys()),
    default = st.session_state.current_page,
    label_visibility = "collapsed"
)

if selected_page and selected_page != st.session_state.current_page:
    st.session_state.current_page = selected_page
    st.rerun()


st.markdown("<hr style = 'margin-top: 5px; margin-bottom: 20px; border-color: #e2e8f0;'>", unsafe_allow_html = True)
target_page_obj = page_map[st.session_state.current_category][st.session_state.current_page]

pg = st.navigation([target_page_obj], position="hidden")
pg.run()