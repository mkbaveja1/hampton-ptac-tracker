from datetime import date
from html import escape
from urllib.parse import parse_qs, quote, urlparse

import streamlit as st


STATUSES = ["Active", "Needs PM", "Maintenance Office", "Doyle Shop"]
LOCATION_TYPES = ["Room", "Hallway", "Elevator Closet", "Maintenance Office", "Doyle Shop", "Spare"]
FLOORS = [2, 3, 4, 5, 6]
ROOM_SUFFIXES = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 24, 25, 26, 27, 28, 29]


# Returns the Supabase client that app.py already stored in Streamlit session state.
def get_supabase():
    return st.session_state.supabase


# Returns the public URL the app should use when generating QR-code links.
def app_base_url():
    try:
        configured_url = st.secrets["app"]["base_url"]
        if configured_url:
            return configured_url.rstrip("/")
    except Exception:
        pass

    try:
        configured_url = st.secrets["app_base_url"]
        if configured_url:
            return configured_url.rstrip("/")
    except Exception:
        pass

    try:
        host = st.context.headers.get("host")
        protocol = st.context.headers.get("x-forwarded-proto", "http")
        if host:
            return f"{protocol}://{host}".rstrip("/")
    except Exception:
        pass

    return "http://localhost:8501"


# Builds the direct URL that opens one PTAC unit's hidden detail/action screen.
def unit_detail_url(ptac_id):
    return f"{app_base_url()}?unit_detail={quote(ptac_id)}"


# Fetches all PTAC units for pages that need a complete inventory list.
def fetch_units():
    response = get_supabase().table("ptac_units").select(
        "ptac_id, serial_number, model_specs, current_location_name, location_type, status, last_pm_date, created_at"
    ).order("ptac_id").execute()
    return response.data or []


# Fetches one PTAC unit by its ptac_id for detail screens and direct lookups.
def fetch_unit(ptac_id):
    response = get_supabase().table("ptac_units").select(
        "ptac_id, serial_number, model_specs, current_location_name, location_type, status, last_pm_date, created_at"
    ).eq("ptac_id", ptac_id).single().execute()
    return response.data


# Fetches PM logs, optionally for one PTAC unit.
def fetch_pm_logs(ptac_id=None):
    query = get_supabase().table("pm_logs").select("*").order("date_performed", desc=True)
    if ptac_id:
        query = query.eq("ptac_id", ptac_id)
    return query.execute().data or []


# Fetches custody transfer logs, optionally for one PTAC unit.
def fetch_transfers(ptac_id=None):
    query = get_supabase().table("custody_transfers").select("*").order("transfer_date", desc=True)
    if ptac_id:
        query = query.eq("ptac_id", ptac_id)
    return query.execute().data or []


# Fetches onsite repair logs, optionally for one PTAC unit.
def fetch_onsite_repairs(ptac_id=None):
    query = get_supabase().table("onsite_repairs").select("*").order("repair_date", desc=True)
    if ptac_id:
        query = query.eq("ptac_id", ptac_id)
    return query.execute().data or []


# Fetches Doyle repair logs, optionally for one PTAC unit.
def fetch_doyle_repairs(ptac_id=None):
    query = get_supabase().table("doyle_repairs").select("*").order("sent_date", desc=True)
    if ptac_id:
        query = query.eq("ptac_id", ptac_id)
    return query.execute().data or []


# Kept for compatibility with older pages; reads are uncached, so nothing needs clearing.
def refresh_data():
    return None


# Converts a unit row into the status text the app should show to the user.
def is_at_maintenance_office(unit):
    if not unit:
        return False
    return (
        unit.get("status") == "Maintenance Office"
        or unit.get("location_type") == "Maintenance Office"
        or unit.get("current_location_name") == "Maintenance Office"
    )


def display_status(unit):
    if not unit:
        return "Unknown"
    if unit.get("location_type") == "Spare":
        return "Spare/Storage"
    if is_at_maintenance_office(unit):
        return "Maintenance Office"
    if unit.get("location_type") == "Doyle Shop" or unit.get("status") == "Doyle Shop":
        return "Doyle Shop"
    return unit.get("status", "Unknown")


# Converts model/spec text into the BTU label shown throughout the app.
def btu_from_model(model_specs):
    model = (model_specs or "").lower()
    if "ptac15" in model or "15" in model or "heavyduty" in model:
        return "15,000 BTU"
    if "ptac09" in model or "9" in model or "compact" in model:
        return "9,000 BTU"
    return "12,000 BTU"


# Converts model/spec text into the shorter BTU label used in dashboard tiles.
def short_btu_from_model(model_specs):
    return btu_from_model(model_specs).replace(",000", "K")


# Builds every guest-room location option used in transfer dropdowns.
def room_options():
    rooms = []
    for floor in FLOORS:
        for suffix in ROOM_SUFFIXES:
            room_num = f"{floor}{suffix:02d}"
            if suffix == 11:
                rooms.append(f"Suite {room_num}-A")
                rooms.append(f"Suite {room_num}-B")
            else:
                rooms.append(f"Room {room_num}")
    return rooms


# Backwards-compatible alias for pages that already call room_locations().
def room_locations():
    return room_options()


# Builds the broader location dropdown list used by action forms.
def location_options():
    return room_options() + corridor_options() + [
        "Elevator Closet",
        "Maintenance Office",
        "Doyle Shop",
        "5th Floor Storage Closet",
    ]


# Builds every hallway/corridor location option used in transfer dropdowns.
def corridor_options():
    return [f"Floor {floor} Hallway" for floor in FLOORS]


# Infers the Supabase location_type value from a human-readable location name.
def infer_location_type(location):
    if location == "Maintenance Office":
        return "Maintenance Office"
    if location == "Doyle Shop":
        return "Doyle Shop"
    if "Storage" in location or "Spare" in location:
        return "Spare"
    if "Hallway" in location or "Corridor" in location:
        return "Hallway"
    if "Elevator" in location:
        return "Elevator Closet"
    return "Room"


# Infers the Supabase status value that should be stored for a destination location.
def target_status_for_location(location):
    if location == "Maintenance Office":
        return "Maintenance Office"
    if location == "Doyle Shop":
        return "Doyle Shop"
    return "Active"


# Finds another active unit already assigned to a target location, if one exists.
def active_unit_at_location(units, target_location, current_ptac_id):
    for unit in units:
        if unit.get("ptac_id") == current_ptac_id:
            continue
        if unit.get("current_location_name") == target_location and unit.get("status") == "Active":
            return unit
    return None


# Generates the next PTAC ID by looking at existing PTAC-### values.
def next_ptac_id(units):
    numbers = []
    for unit in units:
        raw_id = unit.get("ptac_id", "")
        number_part = raw_id.replace("PTAC-", "")
        if number_part.isdigit():
            numbers.append(int(number_part))
    next_number = max(numbers, default=0) + 1
    return f"PTAC-{next_number:03d}"


# Returns the inline CSS used by the dashboard room tiles for a given status.
def dashboard_status_style(status):
    styles = {
        "Active": "background:#f0fdf4;border:1px solid #bbf7d0;color:#166534;",
        "Needs PM": "background:#fffbeb;border:1px solid #fde68a;color:#92400e;animation:pmPulse 2s infinite ease-in-out;",
        "Maintenance Office": "background:#f5f3ff;border:1px solid #ddd6fe;color:#5b21b6;",
        "Doyle Shop": "background:#fff1f2;border:1px solid #fecdd3;color:#9f1239;",
        "Spare/Storage": "background:#eff6ff;border:1px solid #bfdbfe;color:#1e40af;",
        "Unknown": "background:#f8fafc;border:1px dashed #cbd5e1;color:#64748b;",
    }
    return styles.get(status, styles["Unknown"])


# Renders a KPI card with consistent dashboard styling.
def kpi_card(label, value, sublabel, color):
    st.markdown(
        f"""
        <div style='background:#fff;padding:20px;border-radius:16px;
                    box-shadow:0 1px 3px rgba(15,23,42,.05);border:1px solid #e2e8f0;'>
          <span style='font-size:11px;color:{color};font-weight:900;text-transform:uppercase;letter-spacing:.04em;'>{escape(label)}</span>
          <h2 style='font-size:36px;font-weight:900;color:{color};margin:4px 0 0;line-height:1;'>{value}</h2>
          <span style='font-size:10px;color:#94a3b8;font-weight:600;'>{escape(sublabel)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Moves a unit to a new location, writes the custody transfer, and updates the live ptac_units row.
def update_unit_location(ptac_id, status, location, technician, notes):
    units = fetch_units()
    unit = next((item for item in units if item.get("ptac_id") == ptac_id), None)
    if not unit:
        raise ValueError(f"No PTAC unit found for {ptac_id}")

    get_supabase().table("custody_transfers").insert(
        {
            "ptac_id": ptac_id,
            "from_location": unit.get("current_location_name") or "Unknown",
            "to_location": location,
            "technician_name": technician,
            "notes": notes,
        }
    ).execute()

    get_supabase().table("ptac_units").update(
        {
            "status": status,
            "current_location_name": location,
            "location_type": infer_location_type(location),
        }
    ).eq("ptac_id", ptac_id).execute()
    refresh_data()


# Writes a PM log and updates the unit's last PM date.
def register_pm_log(ptac_id, technician, notes, tasks):
    get_supabase().table("pm_logs").insert(
        {
            "ptac_id": ptac_id,
            "technician_name": technician,
            "diagnostic_notes": notes,
            "filters_washed_replaced": tasks.get("filters", False),
            "coils_vacuumed_inspected": tasks.get("coils", False),
            "wiring_thermostat_calibrated": tasks.get("wiring", False),
            "blower_fan_centered_oiled": tasks.get("blower", False),
        }
    ).execute()
    # Keep the unit at Maintenance Office after PM; deploy back to a room via custody transfer.
    get_supabase().table("ptac_units").update({"last_pm_date": str(date.today())}).eq("ptac_id", ptac_id).execute()
    refresh_data()


# Writes an onsite repair log for a unit.
def register_onsite_repair(ptac_id, technician, parts, cost, notes):
    get_supabase().table("onsite_repairs").insert(
        {
            "ptac_id": ptac_id,
            "technician_name": technician,
            "parts_replaced": parts or "None",
            "repair_cost": cost,
            "diagnostic_notes": notes,
        }
    ).execute()
    refresh_data()


# Normalizes scanner input into a PTAC ID from plain text or a unit-detail URL.
def parse_scan_lookup(raw):
    text = (raw or "").strip()
    if not text:
        return None

    if "unit_detail=" in text:
        query = urlparse(text).query if "://" in text else text.lstrip("?")
        if not query and "?" in text:
            query = text.split("?", 1)[1]
        values = parse_qs(query).get("unit_detail")
        if values:
            return values[0].strip().upper()

    return text.upper()


# Returns the billable total for a Doyle repair row from total_cost or labor + parts.
def doyle_repair_cost(repair_row):
    if repair_row.get("total_cost") is not None:
        return float(repair_row.get("total_cost") or 0)
    return float(repair_row.get("labor_cost") or 0) + float(repair_row.get("parts_cost") or 0)


# Returns the most recent custody-transfer note for a unit sent to Doyle Shop.
def latest_doyle_dispatch_note(ptac_id, transfers=None):
    if transfers is None:
        transfers = fetch_transfers(ptac_id)

    for transfer in transfers:
        if transfer.get("ptac_id") != ptac_id:
            continue
        to_location = transfer.get("to_location") or ""
        if "Doyle" in to_location:
            note = (transfer.get("notes") or "").strip()
            if note:
                return note
            return "Offsite dispatch to Doyle Repair Shop."

    return "Offsite dispatch to Doyle Repair Shop."


# Completes a Doyle repair, optionally displacing an occupied room, and returns the unit to the hotel.
def complete_doyle_repair(
    ptac_id,
    unit,
    technician,
    invoice,
    total_bill,
    components,
    extra_parts,
    notes,
    target_location,
    override_occupied=False,
):
    all_units = fetch_units()
    occupying_unit = None
    if target_location and infer_location_type(target_location) == "Room":
        occupying_unit = active_unit_at_location(all_units, target_location, ptac_id)

    if occupying_unit and not override_occupied:
        raise ValueError("occupied_room_override_required")

    all_parts = list(components) + [part.strip() for part in extra_parts.split(",") if part.strip()]
    target_type = infer_location_type(target_location)
    target_status = target_status_for_location(target_location)

    transfer_notes = f"Doyle return invoice {invoice}. Parts: {', '.join(all_parts) or 'None'}. {notes}".strip()
    if occupying_unit:
        override_note = f"Occupied-location override: {occupying_unit['ptac_id']} was moved to Maintenance Office."
        transfer_notes = f"{transfer_notes} {override_note}"
        update_unit_location(
            occupying_unit["ptac_id"],
            "Maintenance Office",
            "Maintenance Office",
            technician.strip(),
            f"Displaced by {ptac_id} Doyle return deployment to {target_location}.",
        )

    get_supabase().table("doyle_repairs").insert(
        {
            "ptac_id": ptac_id,
            "sent_date": str(date.today()),
            "return_date": str(date.today()),
            "doyle_diagnosis": f"Invoice {invoice}. {notes}".strip(),
            "labor_cost": 0,
            "parts_cost": total_bill,
            "is_completed": True,
        }
    ).execute()

    get_supabase().table("custody_transfers").insert(
        {
            "ptac_id": ptac_id,
            "from_location": unit.get("current_location_name") or "Doyle Shop",
            "to_location": target_location,
            "technician_name": technician.strip(),
            "notes": transfer_notes,
        }
    ).execute()

    get_supabase().table("ptac_units").update(
        {
            "status": target_status,
            "location_type": target_type,
            "current_location_name": target_location,
        }
    ).eq("ptac_id", ptac_id).execute()
    refresh_data()
