from datetime import date
from html import escape
from urllib.parse import quote

import streamlit as st

from views._shared import (
    active_unit_at_location,
    btu_from_model,
    corridor_options,
    display_status,
    doyle_repair_cost,
    fetch_doyle_repairs,
    fetch_onsite_repairs,
    fetch_pm_logs,
    fetch_transfers,
    fetch_unit,
    fetch_units,
    get_supabase,
    room_options,
    target_status_for_location,
    unit_detail_url,
    update_unit_location,
)


# Gets the currently selected PTAC ID from the URL or Streamlit session state.
def get_selected_ptac_id():
    query_id = st.query_params.get("unit_detail")
    if query_id:
        return query_id
    return st.session_state.get("selected_ptac_id")


# Maps display status text to the CSS class used by the unit detail status badge.
def status_badge_class(status):
    if status == "Active":
        return "detail-status-active"
    if status == "Needs PM":
        return "detail-status-pm"
    if status == "Maintenance Office":
        return "detail-status-maint"
    if status == "Doyle Shop":
        return "detail-status-doyle"
    return "detail-status-spare"


# Returns the allowed custody destination categories for a unit's current state.
def allowed_transfer_paths(unit):
    status = display_status(unit)
    location_type = unit.get("location_type")

    if status in ["Active", "Needs PM"] and location_type in ["Room", "Hallway", "Elevator Closet"]:
        return ["Maintenance Office", "Doyle Shop"]
    if status == "Doyle Shop":
        return ["Spare Storage", "Guest Room", "Maintenance Office"]
    if status == "Maintenance Office":
        return ["Guest Room", "Corridor/Hallway", "Elevator Closet", "Spare Storage", "Doyle Shop"]
    if status == "Spare/Storage":
        return ["Guest Room", "Corridor/Hallway", "Elevator Closet", "Maintenance Office", "Doyle Shop"]
    return ["Maintenance Office", "Doyle Shop"]


# Converts a route category plus dropdown choice into a concrete destination location.
def resolve_target_location(route, room_choice=None, corridor_choice=None):
    if route == "Guest Room":
        return room_choice
    if route == "Corridor/Hallway":
        return corridor_choice
    if route == "Elevator Closet":
        return "Elevator Closet"
    if route == "Spare Storage":
        return "5th Floor Storage Closet"
    return route


# Combines unit installation, transfer, PM, onsite repair, and Doyle repair records into one timeline.
def fetch_history(unit):
    ptac_id = unit["ptac_id"]
    events = []

    if unit.get("created_at"):
        events.append(
            {
                "date": unit["created_at"],
                "title": "Installation",
                "location": unit.get("current_location_name", "Initial Location"),
                "notes": f"Initial {btu_from_model(unit.get('model_specs'))} unit deployment.",
            }
        )

    transfers = fetch_transfers(ptac_id)
    for transfer in transfers:
        events.append(
            {
                "date": transfer.get("transfer_date"),
                "title": "Custody Transfer",
                "location": transfer.get("to_location"),
                "notes": transfer.get("notes") or f"Moved from {transfer.get('from_location')} to {transfer.get('to_location')}.",
            }
        )

    pm_logs = fetch_pm_logs(ptac_id)
    for log in pm_logs:
        checks = []
        if log.get("filters_washed_replaced"):
            checks.append("filters")
        if log.get("coils_vacuumed_inspected"):
            checks.append("coils")
        if log.get("wiring_thermostat_calibrated"):
            checks.append("wiring")
        if log.get("blower_fan_centered_oiled"):
            checks.append("blower fan")
        events.append(
            {
                "date": log.get("date_performed"),
                "title": "Preventative Maintenance",
                "location": unit.get("current_location_name"),
                "notes": f"Completed checks: {', '.join(checks) or 'general inspection'}. {log.get('diagnostic_notes') or ''}".strip(),
            }
        )

    onsite_repairs = fetch_onsite_repairs(ptac_id)
    for repair in onsite_repairs:
        events.append(
            {
                "date": repair.get("repair_date"),
                "title": "Onsite Repair",
                "location": "Maintenance Office",
                "notes": f"Parts: {repair.get('parts_replaced')}. Cost: ${repair.get('repair_cost')}. {repair.get('diagnostic_notes') or ''}".strip(),
            }
        )

    doyle_repairs = fetch_doyle_repairs(ptac_id)
    for repair in doyle_repairs:
        events.append(
            {
                "date": repair.get("return_date") or repair.get("sent_date"),
                "title": "Doyle Repair",
                "location": "Doyle Shop",
                "notes": f"Diagnosis: {repair.get('doyle_diagnosis') or 'Pending'}. Cost: ${doyle_repair_cost(repair):,.2f}.",
            }
        )

    events.sort(key=lambda event: str(event.get("date") or ""), reverse=True)
    return events


# Builds the full history card HTML in one block so Streamlit does not split the container.
def build_history_markup(events):
    if not events:
        body = "<p style='color:#94a3b8;font-size:13px;font-weight:600;margin:0;'>No history found for this unit yet.</p>"
    else:
        parts = []
        for event in events:
            title = escape(event.get("title") or "")
            date_str = escape(str(event.get("date") or "")[:10])
            location = escape(event.get("location") or "Unknown")
            notes = escape(event.get("notes") or "")
            parts.append(
                "<div class='history-item'>"
                "<span class='history-dot'></span>"
                f"<span class='history-title'>{title}</span>"
                f"<span class='history-date'>{date_str}</span>"
                f"<div class='history-loc'>Location: {location}</div>"
                f"<div class='history-notes'>\"{notes}\"</div>"
                "</div>"
            )
        body = "".join(parts)

    return (
        "<div class='history-card'>"
        "<div class='history-head'>"
        "<h3>Location History &amp; Maintenance Feed</h3>"
        "<span>Newest First</span>"
        "</div>"
        f"{body}"
        "</div>"
    )


# Injects the CSS that gives the hidden unit detail screen its card/timeline layout.
def inject_detail_styles():
    st.markdown(
        """
        <style>
        .unit-topline {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 18px;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 20px;
            margin-bottom: 26px;
        }
        .unit-title-wrap { display:flex; align-items:center; gap:14px; }
        .unit-title-wrap h2 { margin:0; color:#0f172a; font-size:28px; font-weight:950; letter-spacing:-.02em; }
        .unit-subtitle { color:#64748b; font-size:13px; font-weight:700; margin-top:3px; }
        .detail-status {
            display:inline-flex; align-items:center; justify-content:center; border-radius:999px;
            padding:4px 10px; font-size:11px; font-weight:900; vertical-align:middle;
        }
        .detail-status-active { background:#f0fdf4; color:#15803d; border:1px solid #bbf7d0; }
        .detail-status-pm { background:#fffbeb; color:#92400e; border:1px solid #fde68a; }
        .detail-status-maint { background:#f5f3ff; color:#5b21b6; border:1px solid #ddd6fe; }
        .detail-status-doyle { background:#fff1f2; color:#9f1239; border:1px solid #fecdd3; }
        .detail-status-spare { background:#eff6ff; color:#1d4ed8; border:1px solid #bfdbfe; }
        .detail-card {
            background:#fff; border:1px solid #e2e8f0; border-radius:22px; padding:24px 28px;
            box-shadow:0 1px 3px rgba(15,23,42,.04); min-height:360px;
        }
        .detail-card-title {
            color:#64748b; font-size:12px; font-weight:950; letter-spacing:.08em;
            text-transform:uppercase; border-bottom:1px solid #f1f5f9; padding-bottom:10px; margin-bottom:18px;
        }
        .qr-wrap { text-align:center; }
        .qr-img { width:165px; height:165px; border:1px solid #e2e8f0; border-radius:14px; padding:10px; background:white; }
        .qr-help { color:#94a3b8; font-size:12px; font-weight:700; margin:18px auto 22px; max-width:320px; line-height:1.45; }
        .assigned-location { border-top:1px solid #f1f5f9; padding-top:16px; text-align:center; }
        .assigned-location span { color:#94a3b8; font-size:11px; font-weight:950; text-transform:uppercase; }
        .assigned-location h3 { color:#0f172a; font-size:22px; font-weight:950; margin:4px 0; }
        .action-tile {
            border:2px solid #f1f5f9; border-radius:16px; padding:20px; min-height:132px;
            background:#fff; text-align:left;
        }
        .action-icon {
            width:38px; height:38px; border-radius:12px; display:flex; align-items:center;
            justify-content:center; font-weight:900; margin-bottom:14px;
        }
        .action-tile h4 { color:#0f172a; font-size:15px; font-weight:950; margin:0 0 7px; }
        .action-tile p { color:#94a3b8; font-size:12px; font-weight:750; margin:0; line-height:1.35; }
        .history-card { background:#fff; border:1px solid #e2e8f0; border-radius:22px; padding:24px 28px; margin-top:26px; }
        .history-head { display:flex; justify-content:space-between; border-bottom:1px solid #f1f5f9; padding-bottom:14px; margin-bottom:18px; }
        .history-head h3 { margin:0; color:#0f172a; font-size:18px; font-weight:950; }
        .history-head span { color:#94a3b8; font-size:12px; font-weight:900; }
        .history-item { border-left:2px solid #e2e8f0; margin-left:8px; padding:0 0 18px 22px; position:relative; }
        .history-dot { position:absolute; left:-7px; top:4px; width:12px; height:12px; border-radius:999px; background:#94a3b8; }
        .history-title { color:#0f172a; font-weight:950; font-size:13px; }
        .history-date { float:right; color:#94a3b8; font-size:12px; font-weight:850; }
        .history-loc { color:#94a3b8; font-size:10px; font-weight:950; text-transform:uppercase; margin-top:4px; }
        .history-notes { background:#f8fafc; border-radius:12px; padding:12px; color:#475569; font-size:12px; font-weight:650; margin-top:9px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# Renders the custody transfer form and executes a transfer when submitted.
def render_transfer_form(unit):
    all_units = fetch_units()
    route_options = allowed_transfer_paths(unit)

    route = st.selectbox(
        "Authorized Target Destination",
        route_options,
        index=None,
        placeholder="Choose a destination...",
        key=f"transfer_route_{unit['ptac_id']}",
    )

    room_choice = None
    corridor_choice = None
    if route == "Guest Room":
        room_choice = st.selectbox(
            "Hotel Drop Zone Selection",
            room_options(),
            index=None,
            placeholder="Choose a guest room...",
            key=f"transfer_room_{unit['ptac_id']}",
        )
    if route == "Corridor/Hallway":
        corridor_choice = st.selectbox(
            "Corridor Selection",
            corridor_options(),
            index=None,
            placeholder="Choose a hallway...",
            key=f"transfer_corridor_{unit['ptac_id']}",
        )

    target_location = resolve_target_location(route, room_choice, corridor_choice)
    occupying_unit = active_unit_at_location(all_units, target_location, unit["ptac_id"]) if target_location else None

    if route and not target_location:
        st.info("Choose the specific destination before executing the transfer.")

    if occupying_unit:
        st.warning(
            f"{target_location} already has active unit {occupying_unit['ptac_id']}. "
            "If you continue, that existing unit will be moved to Maintenance Office and logged."
        )

    with st.form("custody_transfer_form", border=True):
        override_occupied = False
        technician = ""
        notes = ""

        if target_location:
            if occupying_unit:
                override_occupied = st.checkbox("Confirm occupied-room override and move existing unit to Maintenance Office")

            technician = st.text_input("Technician Name", placeholder="Enter technician name")
            default_notes = f"Transfer {unit['ptac_id']} from {unit.get('current_location_name') or 'Unknown'} to {target_location}."
            if occupying_unit:
                default_notes += f" Occupied-location override: {occupying_unit['ptac_id']} will be moved to Maintenance Office."
            notes = st.text_area("Transfer Notes", value=default_notes)

        submitted = st.form_submit_button(
            "Execute Custody Transfer",
            type="primary",
            disabled=not target_location,
        )

    if submitted:
        if occupying_unit and not override_occupied:
            st.error("You must confirm the occupied-room override before transferring into this location.")
            return
        if not target_location:
            st.error("Choose a valid target destination.")
            return
        if not technician.strip():
            st.error("Technician name is required.")
            return

        final_notes = notes.strip() or f"Transfer {unit['ptac_id']} to {target_location}."
        if occupying_unit:
            override_note = f"Occupied-location override: {occupying_unit['ptac_id']} was moved to Maintenance Office."
            if override_note not in final_notes:
                final_notes = f"{final_notes} {override_note}"

        if occupying_unit:
            update_unit_location(
                occupying_unit["ptac_id"],
                "Maintenance Office",
                "Maintenance Office",
                technician.strip(),
                f"Displaced by {unit['ptac_id']} deployment to {target_location}.",
            )

        update_unit_location(
            unit["ptac_id"],
            target_status_for_location(target_location),
            target_location,
            technician.strip(),
            final_notes,
        )
        st.success(f"{unit['ptac_id']} moved to {target_location}.")
        st.rerun()


# Renders the routine PM checklist and writes a completed PM log when submitted.
def render_pm_form(unit):
    with st.form("pm_form", border=True):
        st.markdown("#### Preventative Maintenance")
        st.caption("PM work is logged from the Maintenance Office. Submitting this will move the unit there first if needed.")
        technician = st.text_input("Technician Name", placeholder="Enter technician name", key="pm_tech")
        c1, c2 = st.columns(2)
        filters = c1.checkbox("Filters washed / replaced")
        coils = c1.checkbox("Coils vacuumed & inspected")
        wiring = c2.checkbox("Wiring & thermostat calibrated")
        blower = c2.checkbox("Blower fan centered & oiled")
        notes = st.text_area("Diagnostic Notes", placeholder="e.g. Filters cleaned. Air output temperature verified optimal.")
        submitted = st.form_submit_button("Register PM Log", type="primary")

    if submitted:
        if not technician.strip():
            st.error("Technician name is required.")
            return
        if not all([filters, coils, wiring, blower]):
            st.error("All four PM checklist items must be checked before logging PM completion.")
            return

        if unit.get("current_location_name") != "Maintenance Office":
            update_unit_location(
                unit["ptac_id"],
                "Maintenance Office",
                "Maintenance Office",
                technician.strip(),
                "Moved to Maintenance Office for routine PM service.",
            )

        get_supabase().table("pm_logs").insert(
            {
                "ptac_id": unit["ptac_id"],
                "technician_name": technician.strip(),
                "filters_washed_replaced": filters,
                "coils_vacuumed_inspected": coils,
                "wiring_thermostat_calibrated": wiring,
                "blower_fan_centered_oiled": blower,
                "diagnostic_notes": notes,
            }
        ).execute()
        get_supabase().table("ptac_units").update(
            {"last_pm_date": str(date.today())}
        ).eq("ptac_id", unit["ptac_id"]).execute()
        st.success("Preventative maintenance logged. Unit remains at Maintenance Office until deployed back.")
        st.rerun()


# Renders the onsite repair cost form and writes an onsite repair log when submitted.
def render_repair_form(unit):
    with st.form("onsite_repair_form", border=True):
        st.markdown("#### Document Repair Costs")
        st.caption("Onsite repairs are performed from the Maintenance Office. Submitting this will move the unit there first if needed.")
        technician = st.text_input("Technician Name", placeholder="Enter technician name", key="repair_tech")
        parts = st.text_input("Replaced Parts", placeholder="Capacitor, fan relay, blower wheel")
        cost = st.number_input("Total Repair Cost ($)", min_value=0.0, step=10.0)
        notes = st.text_area("Diagnostic / Repair Notes")
        submitted = st.form_submit_button("Log Onsite Repair", type="primary")

    if submitted:
        if not technician.strip():
            st.error("Technician name is required.")
            return
        if not notes.strip():
            st.error("Diagnostic or repair notes are required.")
            return

        if unit.get("current_location_name") != "Maintenance Office":
            update_unit_location(
                unit["ptac_id"],
                "Maintenance Office",
                "Maintenance Office",
                technician.strip(),
                "Moved to Maintenance Office for onsite repair.",
            )

        get_supabase().table("onsite_repairs").insert(
            {
                "ptac_id": unit["ptac_id"],
                "technician_name": technician.strip(),
                "parts_replaced": parts.strip() or "None",
                "repair_cost": cost,
                "diagnostic_notes": notes,
            }
        ).execute()
        st.success("Onsite repair logged.")
        st.rerun()


# Renders the specification edit form and updates model/serial fields when submitted.
def render_edit_form(unit):
    with st.form("edit_specs_form", border=True):
        st.markdown("#### Edit Specifications")
        model_specs = st.text_input("Model / Specifications", value=unit.get("model_specs") or "")
        serial_number = st.text_input("Serial Number", value=unit.get("serial_number") or "")
        submitted = st.form_submit_button("Save Specification Edits", type="primary")

    if submitted:
        if not model_specs.strip() or not serial_number.strip():
            st.error("Model specifications and serial number are required.")
            return
        get_supabase().table("ptac_units").update(
            {"model_specs": model_specs.strip(), "serial_number": serial_number.strip()}
        ).eq("ptac_id", unit["ptac_id"]).execute()
        st.success("Specifications updated.")
        st.rerun()


# Renders the delete confirmation form and deletes the unit record when confirmed.
def render_delete_form(unit):
    with st.form("delete_record_form", border=True):
        st.markdown("#### Delete Record")
        st.warning("This permanently deletes the PTAC unit record. Use only for accidental test records or true removal.")
        confirm = st.checkbox(f"I understand and want to delete {unit['ptac_id']}")
        submitted = st.form_submit_button("Delete Record", type="primary")

    if submitted:
        if not confirm:
            st.error("Confirm deletion before continuing.")
            return
        get_supabase().table("ptac_units").delete().eq("ptac_id", unit["ptac_id"]).execute()
        st.session_state.selected_ptac_id = None
        st.query_params.clear()
        st.session_state.current_page = "Dashboard Grid"
        st.success("Record deleted.")
        st.rerun()


# Opens the custody transfer form as a modal dialog over the current detail page.
@st.dialog("Transfer PTAC Custody")
def transfer_dialog(unit):
    render_transfer_form(unit)


# Opens the PM checklist form as a modal dialog over the current detail page.
@st.dialog("Preventative Maintenance")
def pm_dialog(unit):
    render_pm_form(unit)


# Opens the onsite repair form as a modal dialog over the current detail page.
@st.dialog("Document Repair Costs")
def repair_dialog(unit):
    render_repair_form(unit)


# Opens the specification edit form as a modal dialog over the current detail page.
@st.dialog("Edit Specifications")
def edit_dialog(unit):
    render_edit_form(unit)


# Opens the delete confirmation form as a modal dialog over the current detail page.
@st.dialog("Delete Record")
def delete_dialog(unit):
    render_delete_form(unit)


# Renders the full hidden unit detail screen used by dashboard clicks and directory View/Action.
def render_unit_detail(ptac_id=None):
    inject_detail_styles()
    ptac_id = ptac_id or get_selected_ptac_id()
    if not ptac_id:
        st.error("No PTAC unit selected.")
        return

    unit = fetch_unit(ptac_id)
    if not unit:
        st.error(f"No PTAC unit found for {ptac_id}.")
        return

    status = display_status(unit)
    detail_url = unit_detail_url(unit["ptac_id"])
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=220x220&data={quote(detail_url, safe='')}"

    left_head, right_head = st.columns([3, 2])
    with left_head:
        if st.button("← Back to Board"):
            st.session_state.selected_ptac_id = None
            st.query_params.clear()
            st.session_state.current_category = "🏨 Hotel Operations View"
            st.session_state.current_page = "Dashboard Grid"
            st.rerun()
        st.markdown(
            f"""
            <div class='unit-title-wrap'>
              <div>
                <h2>{unit['ptac_id']} <span class='detail-status {status_badge_class(status)}'>{status}</span></h2>
                <div class='unit-subtitle'>{unit.get('model_specs')} · S/N: {unit.get('serial_number')} · {btu_from_model(unit.get('model_specs'))}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right_head:
        edit_col, delete_col = st.columns(2)
        if edit_col.button("Edit Specifications", use_container_width=True):
            edit_dialog(unit)
        if delete_col.button("Delete Record", use_container_width=True):
            delete_dialog(unit)

    st.markdown("<hr style='margin:18px 0 26px;border:none;border-top:1px solid #e2e8f0;'>", unsafe_allow_html=True)

    left, right = st.columns([1.05, 2.15])
    with left:
        st.markdown(
            f"""
            <div class='detail-card qr-wrap'>
              <div class='detail-card-title' style='text-align:left;'>Physical QR Identification</div>
              <img class='qr-img' src='{qr_url}' alt='QR code for {unit['ptac_id']}'>
              <div class='qr-help'>Scanning this tag opens the live action screen for {unit['ptac_id']}.</div>
              <div class='assigned-location'>
                <span>Current Assigned Location</span>
                <h3>{unit.get('current_location_name')}</h3>
                <span>Type: {unit.get('location_type')}</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(f"QR scan link: {detail_url}")
        if detail_url.startswith("http://localhost"):
            st.warning(
                "This QR link points to localhost and will not work on a phone. "
                "Open the app on Streamlit Cloud and reprint labels, or set `[app].base_url` in secrets."
            )

    with right:
        with st.container(border=True):
            st.markdown("<div class='detail-card-title'>Register New Custody/Maintenance Actions</div>", unsafe_allow_html=True)
            action_cols = st.columns(2)
            with action_cols[0]:
                st.markdown(
                    """
                    <div class='action-tile'>
                      <div class='action-icon' style='background:#dbeafe;color:#2563eb;'>→</div>
                      <h4>Custody Transfer Route</h4>
                      <p>Relocate asset following strict hotel lifecycle paths.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("Open Custody Transfer", use_container_width=True):
                    transfer_dialog(unit)
            with action_cols[1]:
                st.markdown(
                    """
                    <div class='action-tile'>
                      <div class='action-icon' style='background:#fef3c7;color:#92400e;'>✓</div>
                      <h4>Register Routine PM</h4>
                      <p>Clear "Needs PM" alert. Log clean filters and coil washes.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("Open PM Checklist", use_container_width=True):
                    pm_dialog(unit)

            repair_cols = st.columns(2)
            with repair_cols[0]:
                st.markdown(
                    """
                    <div class='action-tile'>
                      <div class='action-icon' style='background:#ffe4e6;color:#be123c;'>$</div>
                      <h4>Log Onsite Repair</h4>
                      <p>Document custom labor costs, spare motor, or compressor fixes.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("Open Repair Log", use_container_width=True):
                    repair_dialog(unit)

    events = fetch_history(unit)
    st.markdown(build_history_markup(events), unsafe_allow_html=True)
