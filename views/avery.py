from __future__ import annotations

from html import escape
from urllib.parse import quote

import streamlit as st
import streamlit.components.v1 as components

from views._shared import btu_from_model, display_status, fetch_units, unit_detail_url


BATCH_OPTIONS = [
    "All Units",
    "Rooms Only",
    "Hallways Only",
    "Spares Only",
    "Maintenance Office",
    "Doyle Shop",
]


def filter_units(units, batch):
    if batch == "Rooms Only":
        return [unit for unit in units if unit.get("location_type") == "Room"]
    if batch == "Hallways Only":
        return [unit for unit in units if unit.get("location_type") == "Hallway"]
    if batch == "Spares Only":
        return [unit for unit in units if unit.get("location_type") == "Spare"]
    if batch == "Maintenance Office":
        return [unit for unit in units if unit.get("location_type") == "Maintenance Office"]
    if batch == "Doyle Shop":
        return [unit for unit in units if display_status(unit) == "Doyle Shop"]
    return units


def build_label_markup(unit):
    detail_url = unit_detail_url(unit["ptac_id"])
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=120x120&data={quote(detail_url)}"
    location = escape(unit.get("current_location_name") or "")
    ptac_id = escape(unit["ptac_id"])
    serial = escape(unit.get("serial_number") or "")
    btu = escape(btu_from_model(unit.get("model_specs")))

    return (
        '<div class="avery-label">'
        '<div class="avery-label-copy">'
        '<div class="avery-label-tag">PTAC Asset Tag</div>'
        f'<div class="avery-label-id">{ptac_id}</div>'
        f'<div class="avery-label-loc">{location}</div>'
        f'<div class="avery-label-meta">{btu} - S/N: {serial}</div>'
        "</div>"
        f'<img class="avery-label-qr" src="{qr_url}" alt="QR code for {ptac_id}">'
        "</div>"
    )


def build_sheet_markup(sheet_number, page_units):
    labels_markup = "".join(build_label_markup(unit) for unit in page_units)
    empty_slots = max(0, 10 - len(page_units))
    labels_markup += '<div class="avery-label avery-label-empty"></div>' * empty_slots
    return (
        f'<div class="avery-sheet">'
        f'<div class="avery-sheet-head">'
        f"<strong>Avery PLS-591PM-10 Thermal Sheet #{sheet_number}</strong>"
        f"<span>10 Labels on Page (2 Columns x 5 Rows)</span>"
        f"</div>"
        f'<div class="avery-grid">{labels_markup}</div>'
        f"</div>"
    )


def build_preview_html(sheets_markup, auto_print=False):
    print_script = "<script>window.print();</script>" if auto_print else ""
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: transparent;
  }}
  .avery-sheet {{
    background: #fff;
    border: 1px solid #cbd5e1;
    border-radius: 14px;
    padding: 18px 16px 20px;
    margin: 0 auto 18px;
    max-width: 8.5in;
  }}
  .avery-sheet-head {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
    padding-bottom: 10px;
    border-bottom: 1px solid #e2e8f0;
    font-size: 11px;
    color: #64748b;
    font-weight: 700;
  }}
  .avery-sheet-head strong {{
    color: #0f172a;
    font-size: 12px;
  }}
  .avery-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }}
  .avery-label {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    min-height: 1.9in;
    border: 1px solid #cbd5e1;
    border-radius: 12px;
    padding: 12px 14px;
    background: #fff;
  }}
  .avery-label-empty {{
    visibility: hidden;
    border-color: transparent;
  }}
  .avery-label-copy {{
    flex: 1;
    min-width: 0;
  }}
  .avery-label-tag {{
    font-size: 8px;
    font-weight: 800;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #94a3b8;
    margin-bottom: 6px;
  }}
  .avery-label-id {{
    font-size: 24px;
    font-weight: 900;
    color: #0f172a;
    line-height: 1;
    margin-bottom: 6px;
  }}
  .avery-label-loc {{
    font-size: 11px;
    font-weight: 700;
    color: #334155;
    margin-bottom: 3px;
  }}
  .avery-label-meta {{
    font-size: 10px;
    font-weight: 600;
    color: #64748b;
  }}
  .avery-label-qr {{
    width: 78px;
    height: 78px;
    flex-shrink: 0;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 4px;
    background: #fff;
  }}
  @media print {{
    body {{ background: #fff; }}
    .avery-sheet {{
      border: none;
      border-radius: 0;
      padding: 0.5in 0.15in;
      page-break-after: always;
      max-width: none;
      margin: 0;
    }}
  }}
</style>
</head>
<body>
  {sheets_markup}
  {print_script}
</body>
</html>"""


st.markdown(
    """
    <style>
    .avery-page-title {
        font-size: 28px;
        font-weight: 950;
        color: #0f172a;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .avery-page-subtitle {
        font-size: 13px;
        color: #64748b;
        font-weight: 600;
        margin: 6px 0 0;
        line-height: 1.5;
    }
    .avery-selection-card {
        background: #fff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 16px 18px;
        margin: 20px 0 14px;
        box-shadow: 0 1px 3px rgba(15,23,42,.05);
    }
    .avery-info-banner {
        background: #fffbeb;
        border: 1px solid #fde68a;
        border-radius: 14px;
        padding: 14px 16px;
        margin-bottom: 18px;
        font-size: 12px;
        color: #92400e;
        line-height: 1.5;
    }
    .avery-preview-shell {
        background: #eef2ff;
        border: 1px solid #c7d2fe;
        border-radius: 18px;
        padding: 18px;
    }
    .avery-preview-title {
        text-align: center;
        font-size: 11px;
        font-weight: 900;
        letter-spacing: 0.14em;
        color: #64748b;
        margin: 0 0 14px;
    }
    .avery-batch-label {
        font-size: 11px;
        font-weight: 900;
        color: #64748b;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    div[data-testid="stHorizontalBlock"] .stButton > button[kind="primary"] {
        background: #0f172a;
        border: 1px solid #0f172a;
        color: #fff;
        font-weight: 800;
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

units = fetch_units()

title_col, print_col = st.columns([4, 1])
with title_col:
    st.markdown(
        """
        <h2 class="avery-page-title">Avery Thermal Sheet Printer</h2>
        <p class="avery-page-subtitle">
          Formally laid out for Avery Manufacturer Part Number <strong>PLS-591PM-10</strong>
          (2 Columns x 5 Rows, 4" x 2" standard sticker labels).
        </p>
        """,
        unsafe_allow_html=True,
    )
with print_col:
    print_clicked = st.button("Print Label Sheet", type="primary", use_container_width=True)

st.markdown('<div class="avery-selection-card">', unsafe_allow_html=True)

filter_cols = st.columns([2, 1, 1])
with filter_cols[0]:
    st.markdown('<div class="avery-batch-label">Selection Batch</div>', unsafe_allow_html=True)
    batch = st.selectbox(
        "Selection Batch",
        BATCH_OPTIONS,
        label_visibility="collapsed",
    )

filtered = filter_units(units, batch)
filtered_ids = [unit["ptac_id"] for unit in filtered]

if "avery_selected_ids" not in st.session_state:
    st.session_state.avery_selected_ids = filtered_ids[: min(10, len(filtered_ids))]

if "avery_selection_version" not in st.session_state:
    st.session_state.avery_selection_version = 0

if st.session_state.get("avery_batch") != batch:
    st.session_state.avery_batch = batch
    st.session_state.avery_selected_ids = filtered_ids[: min(10, len(filtered_ids))]
    st.session_state.avery_selection_version += 1


def clear_avery_checkbox_widgets():
    for key in list(st.session_state.keys()):
        if str(key).startswith("avery_chk_"):
            del st.session_state[key]


with filter_cols[1]:
    st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)
    if st.button("Select All Shown", use_container_width=True, disabled=not filtered_ids):
        st.session_state.avery_selected_ids = list(filtered_ids)
        st.session_state.avery_selection_version += 1
        clear_avery_checkbox_widgets()
        st.rerun()
with filter_cols[2]:
    st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)
    if st.button("Clear All Selection", use_container_width=True):
        st.session_state.avery_selected_ids = []
        st.session_state.avery_selection_version += 1
        clear_avery_checkbox_widgets()
        st.rerun()

if filtered:
    checkbox_cols = st.columns(3)
    selected_ids = set(st.session_state.avery_selected_ids)
    selection_version = st.session_state.avery_selection_version
    for index, unit in enumerate(filtered):
        with checkbox_cols[index % 3]:
            checked = st.checkbox(
                f"{unit['ptac_id']} — {unit.get('current_location_name') or 'Unassigned'}",
                value=unit["ptac_id"] in selected_ids,
                key=f"avery_chk_{batch}_{selection_version}_{unit['ptac_id']}",
            )
            if checked:
                selected_ids.add(unit["ptac_id"])
            else:
                selected_ids.discard(unit["ptac_id"])
    st.session_state.avery_selected_ids = sorted(selected_ids)
else:
    st.caption("No units match this batch filter.")

st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    """
    <div class="avery-info-banner">
      <strong>Avery PLS-591PM-10 Specifications:</strong>
      10 Labels per Sheet (4.0" x 2.0"). Perfect sizing for PTAC chassis.
      Under check selection, labels will utilize standard paper configurations on print output.
    </div>
    """,
    unsafe_allow_html=True,
)

printable = [unit for unit in filtered if unit["ptac_id"] in st.session_state.avery_selected_ids]

st.markdown(
    """
    <div class="avery-preview-shell">
      <p class="avery-preview-title">AVERY PLS-591PM-10 PREVIEW LAYOUT</p>
    """,
    unsafe_allow_html=True,
)

if not printable:
    st.info("Choose at least one unit above to preview labels.")
else:
    sheets = []
    for sheet_index, page_start in enumerate(range(0, len(printable), 10), start=1):
        page_units = printable[page_start : page_start + 10]
        sheets.append(build_sheet_markup(sheet_index, page_units))

    preview_height = min(1800, 900 * len(sheets))
    preview_html = build_preview_html("".join(sheets), auto_print=print_clicked)
    components.html(preview_html, height=preview_height, scrolling=True)

st.markdown("</div>", unsafe_allow_html=True)
