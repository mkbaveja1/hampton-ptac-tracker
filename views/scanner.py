from __future__ import annotations

import streamlit as st

from views._shared import fetch_unit, fetch_units, parse_scan_lookup
from views.unit_detail import get_selected_ptac_id, render_unit_detail


if get_selected_ptac_id():
    render_unit_detail()
    st.stop()


st.markdown("### Smart QR Tag Scanner")
st.caption(
    "Look up a PTAC by ID or scan a label URL. Matching units open the shared unit detail screen for custody, PM, and repair actions."
)

units = fetch_units()
unit_ids = {unit["ptac_id"] for unit in units}

lookup_raw = st.text_input(
    "Manual Unit Lookup Code or Scanned URL",
    placeholder="PTAC-012 or https://your-app-url?unit_detail=PTAC-012",
    key="scanner_lookup_input",
)

parsed_id = parse_scan_lookup(lookup_raw) if lookup_raw else None

if lookup_raw and parsed_id and parsed_id not in unit_ids:
    st.error(f"No active profile matching `{parsed_id}`.")

if parsed_id and parsed_id in unit_ids:
    unit = fetch_unit(parsed_id)
    if unit:
        st.session_state.selected_ptac_id = parsed_id
        st.rerun()

if not lookup_raw:
    fallback_id = st.selectbox("Or select a unit", sorted(unit_ids) if unit_ids else [])
    if st.button("Open Unit Detail", type="primary", disabled=not fallback_id):
        st.session_state.selected_ptac_id = fallback_id
        st.rerun()
