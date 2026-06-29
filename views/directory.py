import streamlit as st

from views._shared import btu_from_model, display_status, fetch_units, next_ptac_id
from views.unit_detail import get_selected_ptac_id, render_unit_detail


supabase = st.session_state.supabase


# Pull the inventory fields needed for the directory table.
# No new table is needed for this page: these columns already live in ptac_units.
all_units = fetch_units()

if get_selected_ptac_id():
    render_unit_detail()
    st.stop()


st.markdown(
    """
    <style>
    .stApp {
        background: #f8fafc;
    }

    .directory-title-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 18px;
        margin: 26px 0 22px 0;
    }

    .directory-title-row h2 {
        color: #0f172a;
        font-size: 28px;
        font-weight: 950;
        letter-spacing: -0.02em;
        margin: 0;
    }

    .directory-title-row p {
        color: #64748b;
        font-size: 13px;
        font-weight: 600;
        margin: 4px 0 0 0;
    }

    .filter-shell {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        padding: 16px;
        margin-bottom: 26px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, .05);
    }

    .directory-table {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(15, 23, 42, .04);
    }

    .directory-header {
        background: #f8fafc;
        border-bottom: 1px solid #e2e8f0;
        padding: 17px 20px;
        color: #64748b;
        font-size: 12px;
        font-weight: 950;
        text-transform: uppercase;
        letter-spacing: .08em;
    }

    .directory-row {
        padding: 18px 20px;
        min-height: 76px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: flex-start;
    }

    hr {
        margin: 0;
        border: none;
        border-top: 1px solid #e2e8f0;
    }

    .action-button-offset {
        height: 15px;
    }

    .id-pill {
        display: inline-block;
        background: #f1f5f9;
        border: 1px solid #e2e8f0;
        color: #0f172a;
        border-radius: 7px;
        padding: 5px 10px;
        font-size: 12px;
        font-weight: 950;
    }

    .primary-text {
        color: #0f172a;
        font-size: 15px;
        font-weight: 950;
        line-height: 1.2;
    }

    .secondary-text {
        color: #94a3b8;
        font-size: 11px;
        font-weight: 850;
        line-height: 1.2;
        margin-top: 4px;
        text-transform: uppercase;
    }

    .status-pill {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: fit-content;
        border-radius: 999px;
        padding: 4px 11px;
        font-size: 11px;
        font-weight: 900;
        line-height: 1;
        white-space: nowrap;
    }

    .status-active {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        color: #15803d;
    }

    .status-pm {
        background: #fffbeb;
        border: 1px solid #fde68a;
        color: #92400e;
    }

    .status-maint {
        background: #f5f3ff;
        border: 1px solid #ddd6fe;
        color: #5b21b6;
    }

    .status-doyle {
        background: #fff1f2;
        border: 1px solid #fecdd3;
        color: #9f1239;
    }

    .status-spare {
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        color: #1d4ed8;
    }

    .empty-state {
        padding: 40px;
        color: #94a3b8;
        font-size: 13px;
        font-weight: 800;
        text-align: center;
    }

    .action-panel {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        padding: 18px 20px;
        margin-top: 22px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, .04);
    }

    div[data-testid="stButton"] > button {
        border-radius: 11px;
        font-weight: 900;
        white-space: nowrap;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# Maps display status text to the CSS class used by directory status pills.
def status_class(status):
    if status == "Active":
        return "status-active"
    if status == "Needs PM":
        return "status-pm"
    if status == "Maintenance Office":
        return "status-maint"
    if status == "Doyle Shop":
        return "status-doyle"
    if status == "Spare/Storage":
        return "status-spare"
    return "status-spare"


# Checks whether a unit should remain visible for the selected location filter.
def matches_location_filter(unit, selected_filter):
    location_type = unit.get("location_type")
    status = unit.get("status")

    if selected_filter == "All Locations":
        return True
    if selected_filter == "Guest Rooms":
        return location_type == "Room"
    if selected_filter == "Hallways":
        return location_type == "Hallway"
    if selected_filter == "Elevator Closet":
        return location_type == "Elevator Closet"
    if selected_filter == "Storage / Spares":
        return location_type == "Spare"
    if selected_filter == "Maintenance Office":
        return status == "Maintenance Office" or location_type == "Maintenance Office"
    if selected_filter == "Doyle Shop":
        return status == "Doyle Shop" or location_type == "Doyle Shop"
    return True


# Checks whether a unit should remain visible for the selected status filter.
def matches_status_filter(unit, selected_filter):
    if selected_filter == "All Statuses":
        return True
    return display_status(unit) == selected_filter


# Builds one lowercase searchable string from the fields the directory search bar should scan.
def search_text(unit):
    values = [
        unit.get("ptac_id", ""),
        unit.get("serial_number", ""),
        unit.get("model_specs", ""),
        unit.get("current_location_name", ""),
        unit.get("location_type", ""),
        display_status(unit),
    ]
    return " ".join(values).lower()


if "show_add_spare_form" not in st.session_state:
    st.session_state.show_add_spare_form = False

title_cols = st.columns([3, 1])
with title_cols[0]:
    st.markdown(
        """
        <div class='directory-title-row'>
          <div>
            <h2>Equipment Inventory Directory</h2>
            <p>Full tabular view of rooms, hallway corridors, elevator equipment, and spares closet.</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with title_cols[1]:
    st.write("")
    st.write("")
    if st.button("+ Register New Spare Unit", type="primary", use_container_width=True):
        st.session_state.show_add_spare_form = not st.session_state.show_add_spare_form


if st.session_state.show_add_spare_form:
    with st.form("add_spare_form", border=True):
        st.markdown("#### Register New Spare Unit")
        st.caption("This inserts a new row into the existing `ptac_units` table. It does not require a separate spares table.")
        new_id = next_ptac_id(all_units)
        st.code(f"Next ID: {new_id}", language="text")

        spare_cols = st.columns(3)
        model_specs = spare_cols[0].selectbox(
            "Model Specifications",
            [
                "Amana PTAC12-Standard",
                "Amana PTAC15-Standard",
                "Amana PTAC15-HeavyDuty",
                "Amana PTAC09-Compact",
            ],
        )
        serial_number = spare_cols[1].text_input("Serial Number", placeholder="AMN-12345678")
        storage_location = spare_cols[2].text_input("Storage Location", value="5th Floor Storage Closet")

        submitted = st.form_submit_button("Ingest Stock Spare", type="primary")

        if submitted:
            if not serial_number.strip():
                st.error("Serial number is required.")
            else:
                supabase.table("ptac_units").insert(
                    {
                        "ptac_id": new_id,
                        "serial_number": serial_number.strip(),
                        "model_specs": model_specs,
                        "current_location_name": storage_location.strip() or "5th Floor Storage Closet",
                        "location_type": "Spare",
                        # Supabase enum does not include Spare/Storage, so spare is tracked by location_type.
                        "status": "Active",
                    }
                ).execute()
                st.success(f"{new_id} was added as a spare unit.")
                st.rerun()


st.markdown("<div class='filter-shell'>", unsafe_allow_html=True)
filter_cols = st.columns([3.4, 1.1, 1.1])
search_query = filter_cols[0].text_input(
    "Search directory",
    placeholder="Type to search ID, Serial, Location or Model...",
    label_visibility="collapsed",
)
location_filter = filter_cols[1].selectbox(
    "Location Filter",
    [
        "All Locations",
        "Guest Rooms",
        "Hallways",
        "Elevator Closet",
        "Storage / Spares",
        "Maintenance Office",
        "Doyle Shop",
    ],
    label_visibility="collapsed",
)
status_filter = filter_cols[2].selectbox(
    "Status Filter",
    ["All Statuses", "Active", "Needs PM", "Maintenance Office", "Doyle Shop", "Spare/Storage"],
    label_visibility="collapsed",
)
st.markdown("</div>", unsafe_allow_html=True)


filtered_units = []
query = search_query.strip().lower()
for unit in all_units:
    if query and query not in search_text(unit):
        continue
    if not matches_location_filter(unit, location_filter):
        continue
    if not matches_status_filter(unit, status_filter):
        continue
    filtered_units.append(unit)


st.markdown("<div class='directory-table'>", unsafe_allow_html=True)
header_cols = st.columns([1.0, 2.3, 1.9, 1.8, 1.4, 1.1])
headers = ["ID", "SPECS & SERIAL", "LOCATION", "OPERATIONAL STATUS", "LAST PM CHECK", "ACTIONS"]
for col, header in zip(header_cols, headers):
    col.markdown(f"<div class='directory-header'>{header}</div>", unsafe_allow_html=True)

if not filtered_units:
    st.markdown("<div class='empty-state'>No PTAC units matched those search criteria.</div>", unsafe_allow_html=True)

for unit in filtered_units:
    status = display_status(unit)
    row_cols = st.columns([1.0, 2.3, 1.9, 1.8, 1.4, 1.1])

    row_cols[0].markdown(
        f"""
        <div class='directory-row'>
          <span class='id-pill'>{unit.get("ptac_id", "")}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    row_cols[1].markdown(
        f"""
        <div class='directory-row'>
          <div class='primary-text'>{unit.get("model_specs", "")}</div>
          <div class='secondary-text'>{btu_from_model(unit.get("model_specs"))} · S/N: {unit.get("serial_number", "")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    row_cols[2].markdown(
        f"""
        <div class='directory-row'>
          <div class='primary-text'>{unit.get("current_location_name", "")}</div>
          <div class='secondary-text'>{unit.get("location_type", "")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    row_cols[3].markdown(
        f"""
        <div class='directory-row'>
          <span class='status-pill {status_class(status)}'>{status}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    row_cols[4].markdown(
        f"""
        <div class='directory-row'>
          <div class='primary-text' style='font-size:13px;color:#64748b;'>{unit.get("last_pm_date") or "Not logged"}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with row_cols[5]:
        st.markdown("<div class='action-button-offset'></div>", unsafe_allow_html=True)
        if st.button("View / Action", key=f"view_{unit.get('ptac_id')}"):
            st.session_state.selected_ptac_id = unit.get("ptac_id")
            st.rerun()
    st.divider()

st.markdown("</div>", unsafe_allow_html=True)
