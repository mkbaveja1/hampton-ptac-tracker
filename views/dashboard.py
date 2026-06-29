import streamlit as st
from urllib.parse import quote

from views._shared import (
    FLOORS,
    ROOM_SUFFIXES,
    dashboard_status_style,
    display_status,
    fetch_units,
    is_at_maintenance_office,
    short_btu_from_model,
)
from views.unit_detail import get_selected_ptac_id, render_unit_detail

# Pulls the live PTAC inventory from Supabase through the shared data helper.
all_units = fetch_units()

if get_selected_ptac_id():
    render_unit_detail()
    st.stop()

#KPI counts
total_count = len(all_units)

active_total = 0
for u in all_units:
    if u.get("status") == "Active" and u.get("location_type") != "Spare":
        active_total += 1

pm_overdue_total = 0
for u in all_units:
    if u.get("status") == "Needs PM":
        pm_overdue_total += 1

maint_office_total = 0
for u in all_units:
    if is_at_maintenance_office(u):
        maint_office_total += 1

doyle_total = 0
for u in all_units:
    if u.get("status") == "Doyle Shop":
        doyle_total += 1


st.markdown(
    """
    <style>
    .stApp {
        background: #f8fafc;
    }

    @keyframes pmPulse {
        0%, 100% {
            background-color: #fffbeb;
            border-color: #fde68a;
            color: #92400e;
        }
        50% {
            background-color: #fef3c7;
            border-color: #f59e0b;
            color: #78350f;
        }
    }

    .kpi-card {
        background: #ffffff;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
        border: 1px solid #e2e8f0;
        min-height: 130px;
    }

    .kpi-label {
        font-size: 11px;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: .04em;
        display: block;
    }

    .kpi-value {
        font-size: 36px;
        font-weight: 900;
        margin: 6px 0 0 0;
        line-height: 1;
        display: block;
    }

    .kpi-sub {
        font-size: 10px;
        color: #94a3b8;
        font-weight: 600;
        margin-top: 6px;
        display: block;
    }

    .dashboard-hero {
        background: #0f172a;
        color: white;
        border-radius: 24px;
        padding: 24px;
        margin: 22px 0 16px 0;
        box-shadow: 0 16px 28px rgba(15, 23, 42, .14);
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 20px;
        overflow: hidden;
    }

    .dashboard-hero h3 {
        margin: 0;
        font-size: 24px;
        font-weight: 900;
        color: white;
    }

    .dashboard-hero p {
        margin: 8px 0 0 0;
        font-size: 13px;
        color: #cbd5e1;
        font-weight: 500;
        max-width: 700px;
        line-height: 1.5;
    }

    .scanner-pill {
        background: #2563eb;
        color: white;
        padding: 13px 18px;
        border-radius: 14px;
        font-size: 12px;
        font-weight: 900;
        white-space: nowrap;
        box-shadow: 0 10px 20px rgba(37, 99, 235, .24);
    }

    .legend-panel {
        background: #ffffff;
        padding: 14px 20px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
        align-items: center;
        justify-content: center;
        margin-bottom: 20px;
        font-size: 11px;
        font-weight: 800;
        box-shadow: 0 1px 3px rgba(15, 23, 42, .04);
    }

    .legend-title {
        color: #94a3b8;
        text-transform: uppercase;
        font-size: 9px;
        letter-spacing: .08em;
        font-weight: 900;
    }

    .legend-dot {
        display: inline-block;
        width: 14px;
        height: 14px;
        border-radius: 4px;
        margin-right: 6px;
        vertical-align: -2px;
    }

    .floor-card {
        background: #ffffff;
        border-radius: 18px;
        border: 1px solid #e2e8f0;
        padding: 18px 20px;
        margin-bottom: 14px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    }

    .floor-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 1px solid #f1f5f9;
        padding-bottom: 10px;
        margin-bottom: 12px;
    }

    .floor-header h3 {
        margin: 0;
        color: #0f172a;
        font-size: 20px;
        font-weight: 950;
        letter-spacing: -0.01em;
    }

    .floor-header span {
        color: #94a3b8;
        font-size: 10px;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: .06em;
    }

    .floor-row {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(60px, 1fr));
        gap: 8px;
        align-items: stretch;
    }

    .room-cell {
        border-radius: 12px;
        min-height: 68px;
        text-align: center;
        font-weight: 900;
        padding: 8px 5px;
        font-size: 11px;
        line-height: 1.1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        transition: transform .15s ease, box-shadow .15s ease;
        cursor: pointer;
        text-decoration: none;
    }

    a.room-cell-link {
        text-decoration: none !important;
        color: inherit !important;
        display: block;
    }

    .room-cell:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 16px rgba(15, 23, 42, .08);
    }

    .room-cell small {
        display: block;
        margin-bottom: 5px;
        font-size: 9px;
        font-weight: 800;
        color: #94a3b8;
        max-width: 100%;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .cell-main-label {
        display: block;
        color: #0f172a;
        font-size: 15px;
        font-weight: 950;
        line-height: 1.05;
        margin-bottom: 6px;
    }

    .cell-btu {
        display: block;
        color: #6aa08d;
        font-size: 10px;
        font-weight: 950;
        letter-spacing: .14em;
    }

    .support-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(82px, 1fr));
        gap: 8px;
    }

    @media (max-width: 700px) {
        .dashboard-hero {
            display: block;
        }
        .scanner-pill {
            display: inline-block;
            margin-top: 16px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


#KPI card row
kpi_cols = st.columns(5)

cards = [
    ("#0f172a",  "Total Inventory",    total_count,        "125 Rooms • 5 Floors"),
    ("#10b981",  "Active & Running",   active_total,       "Healthy climate zones"),
    ("#f59e0b",  "PM Clean Overdue",   pm_overdue_total,   "Filter/coil check alert"),
    ("#8b5cf6",  "At Maint. Office",   maint_office_total, "Onsite testing & diagnostics"),
    ("#ef4444",  "At Doyle Shop",      doyle_total,        "Contractor offsite queue"),
]
for col, (color, label, val, sub) in zip(kpi_cols, cards):
    with col:
        st.markdown(
            f"""
            <div class='kpi-card'>
              <span class='kpi-label' style='color:{color};'>{label}</span>
              <span class='kpi-value' style='color:{color};'>{val}</span>
              <span class='kpi-sub'>{sub}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


# Draw the main dark navy banner layout wrapper for the interactive floor grid map
st.markdown(
    """
    <div class='dashboard-hero'>
      <div>
        <h3>Control Room Visual Grid</h3>
        <p>
          Click any color-coded room, hallway, or elevator block below to view diagnostics history,
          execute custody transfers, or review technician parts invoices.
        </p>
      </div>
      <div class='scanner-pill'>▦ Launch QR Scanner</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# Legend
st.markdown(
    """
    <div class='legend-panel'>
      <span class='legend-title'>Operational Board Legend:</span>
      <span><span class='legend-dot' style='background:#f0fdf4;border:1px solid #bbf7d0;'></span><span style='color:#166534;'>Active</span></span>
      <span><span class='legend-dot' style='background:#fffbeb;border:1px solid #fde68a;animation:pmPulse 2s infinite ease-in-out;'></span><span style='color:#92400e;'>Needs PM Clean</span></span>
      <span><span class='legend-dot' style='background:#f5f3ff;border:1px solid #ddd6fe;'></span><span style='color:#5b21b6;'>Onsite Maint. Office</span></span>
      <span><span class='legend-dot' style='background:#fff1f2;border:1px solid #fecdd3;'></span><span style='color:#9f1239;'>Offsite Doyle Repair</span></span>
      <span><span class='legend-dot' style='background:#eff6ff;border:1px solid #bfdbfe;'></span><span style='color:#1e40af;'>Storage Spare Closet</span></span>
    </div>
    """,
    unsafe_allow_html=True,
)


# Lookup to map room # directly to status
loc_unit = {u.get("current_location_name"): u for u in all_units}

# Returns the short BTU text shown in each dashboard tile.
def btu_label(unit):
    if not unit:
        return ""
    location_type = unit.get("location_type")
    if location_type == "Hallway":
        return "15K BTU"
    if location_type == "Elevator Closet":
        return "9K BTU"
    return short_btu_from_model(unit.get("model_specs"))


# Builds the HTML for one dashboard tile and wraps real units in a detail-page link.
def make_cell(label, unit, display_label=None):
    status = display_status(unit)
    ptac_id = unit.get("ptac_id", "No unit") if unit else "No unit"
    main_label = display_label or label
    btu = btu_label(unit)
    cell_html = (
        f"<div class='room-cell' style='{dashboard_status_style(status)}' title='{label} - {status} - {ptac_id}'>"
        f"<small>{ptac_id}</small>"
        f"<span class='cell-main-label'>{main_label}</span>"
        f"<span class='cell-btu'>{btu}</span>"
        f"</div>"
    )
    if not unit:
        return cell_html
    return f"<a class='room-cell-link' href='?unit_detail={quote(ptac_id)}' target='_self'>{cell_html}</a>"


# Making floor grid
for floor in FLOORS:
    grid_html = f"""
    <div class='floor-card'>
        <div class='floor-header'>
            <h3>Floor {floor}</h3>
            <span>Dynamic Control Matrix</span>
        </div>
        <div class='floor-row'>
    """

    for room in ROOM_SUFFIXES:
        rnum = f"{floor}{room:02d}"
        if room == 11:
            #two units
            loc_a = f"Suite {rnum}-A"
            loc_b = f"Suite {rnum}-B"
            grid_html += make_cell(f"{rnum}A", loc_unit.get(loc_a))
            grid_html += make_cell(f"{rnum}B", loc_unit.get(loc_b))
        else:
            loc = f"Room {rnum}"
            grid_html += make_cell(rnum, loc_unit.get(loc))
    
    grid_html += """
        </div>
    </div>
    """
    st.markdown(grid_html, unsafe_allow_html=True)

# Sorts hallway units by floor number so corridors render Floor 2 through Floor 6.
def hallway_sort_key(unit):
    location = unit.get("current_location_name", "")
    for floor in FLOORS:
        if f"Floor {floor}" in location:
            return floor
    return 99

hallway_units = [
    u for u in all_units
    if u.get("location_type") == "Hallway"
    or "Hallway" in u.get("current_location_name", "")
    or "Corridor" in u.get("current_location_name", "")
]
hallway_units = sorted(hallway_units, key=hallway_sort_key)

support_groups = [
    ("Corridors/Hallways", hallway_units),
    ("Elevator Closet", [u for u in all_units if u.get("location_type") == "Elevator Closet"]),
    ("Maintenance Office Onsite", [u for u in all_units if is_at_maintenance_office(u)]),
    ("Doyle Repair Shop", [u for u in all_units if u.get("status") == "Doyle Shop"]),
    ("Spare Storage Closet", [u for u in all_units if u.get("location_type") == "Spare"]),
]

for title, units in support_groups:
    support_cells = ""
    for unit in units:
        location = unit.get("current_location_name", "")
        if title == "Corridors/Hallways":
            display_name = location.replace(" Hallway", "").replace(" Corridor", "")
        elif title == "Elevator Closet":
            display_name = "Elev."
        else:
            display_name = location or unit.get("ptac_id", "PTAC")
        support_cells += make_cell(unit.get("ptac_id", "PTAC"), unit, display_name)
    if not support_cells:
        support_cells = "<span style='font-size:12px;color:#94a3b8;font-weight:700;'>No units in this queue.</span>"

    st.markdown(
        f"""
        <div class='floor-card'>
            <div class='floor-header'>
                <h3>{title} ({len(units)} Units)</h3>
                <span>Support Assets</span>
            </div>
            <div class='support-grid'>{support_cells}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
