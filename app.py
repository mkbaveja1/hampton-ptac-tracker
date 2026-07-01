import streamlit as st
from supabase import create_client, Client

st.set_page_config(page_title="PTAC Pro Tracker Console", page_icon="🏨", layout="wide")


def load_supabase_secrets():
    try:
        supabase_secrets = st.secrets["supabase"]
        url = supabase_secrets["url"]
        key = supabase_secrets["key"]
    except (KeyError, TypeError):
        st.error("Supabase secrets are not configured.")
        st.markdown(
            """
            Add secrets in **Streamlit Community Cloud → Manage app → Settings → Secrets**
            (or in local `.streamlit/secrets.toml`):

            ```toml
            [supabase]
            url = "https://YOUR-PROJECT.supabase.co"
            key = "YOUR_SUPABASE_ANON_OR_SERVICE_KEY"

            [app]
            base_url = "https://YOUR-APP-NAME.streamlit.app"
            ```

            After saving secrets, reboot the app from the Cloud dashboard.
            """
        )
        st.stop()

    if not url or not key:
        st.error("Supabase `url` and `key` must both be set in secrets.")
        st.stop()

    return url, key


if "supabase" not in st.session_state:
    supabase_url, supabase_key = load_supabase_secrets()
    supabase: Client = create_client(supabase_url, supabase_key)
    st.session_state.supabase = supabase

# Deep links from printed QR codes: ?unit_detail=PTAC-###
_qr_unit_id = st.query_params.get("unit_detail")
if _qr_unit_id:
    st.session_state.selected_ptac_id = _qr_unit_id


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

def clear_unit_detail_selection():
    st.session_state.selected_ptac_id = None
    st.query_params.clear()

with nav_cols[1]:

    #this is the main categories (hotel operations view and contractor portal)
    selected_category = st.segmented_control(
        label = "System Mode", 
        options = list(page_map.keys()),
        default = st.session_state.current_category,
        label_visibility = "collapsed"
    )

    if selected_category and selected_category != st.session_state.current_category:
        clear_unit_detail_selection()
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
    clear_unit_detail_selection()
    st.session_state.current_page = selected_page
    st.rerun()


st.markdown("<hr style = 'margin-top: 5px; margin-bottom: 20px; border-color: #e2e8f0;'>", unsafe_allow_html = True)
target_page_obj = page_map[st.session_state.current_category][st.session_state.current_page]

pg = st.navigation([target_page_obj], position="hidden")
pg.run()
