from __future__ import annotations

from html import escape

import streamlit as st

from views._shared import (
    active_unit_at_location,
    btu_from_model,
    complete_doyle_repair,
    display_status,
    fetch_transfers,
    fetch_units,
    latest_doyle_dispatch_note,
    room_locations,
)

CORE_COMPONENTS = [
    "Compressor",
    "Freon Recharge",
    "Fan Motor",
    "Relay Control",
    "Capacitor",
    "Solder Repair",
]

SPARE_STORAGE = "5th Floor Storage Closet"


st.markdown(
    """
    <style>
    .doyle-page { background: #f1f5f9; margin: -1rem -1rem 0; padding: 0 0 24px; }
    .doyle-header {
        background: #0f172a; color: #fff; border-radius: 20px; padding: 24px 28px; margin-bottom: 20px;
    }
    .doyle-badge {
        display: inline-block; background: rgba(239,68,68,.2); color: #fca5a5;
        border: 1px solid rgba(239,68,68,.35); border-radius: 999px;
        padding: 4px 12px; font-size: 10px; font-weight: 900; letter-spacing: .06em;
        text-transform: uppercase;
    }
    .doyle-header h2 { margin: 10px 0 4px; font-size: 28px; font-weight: 900; }
    .doyle-header p { margin: 0; color: #94a3b8; font-size: 13px; }
    .doyle-panel {
        background: #fff; border: 1px solid #e2e8f0; border-radius: 16px;
        padding: 20px; box-shadow: 0 1px 3px rgba(15,23,42,.05); min-height: 520px;
    }
    .doyle-panel h4 { margin: 0 0 16px; font-size: 15px; font-weight: 900; color: #0f172a; }
    .doyle-queue-card {
        background: #fff; border: 1px solid #fecdd3; border-radius: 14px;
        padding: 14px 16px; margin-bottom: 10px; cursor: pointer;
    }
    .doyle-queue-card.selected { border: 2px solid #ef4444; box-shadow: 0 0 0 1px rgba(239,68,68,.15); }
    .doyle-queue-id { font-size: 16px; font-weight: 900; color: #0f172a; }
    .doyle-queue-btu { float: right; font-size: 11px; color: #64748b; font-weight: 700; }
    .doyle-queue-sn { font-size: 11px; color: #94a3b8; margin-top: 4px; }
    .doyle-queue-note {
        background: #f1f5f9; border-radius: 10px; padding: 8px 10px; margin-top: 10px;
        font-size: 11px; color: #64748b; font-style: italic; line-height: 1.4;
    }
    .doyle-unit-banner {
        background: #0f172a; color: #fff; border-radius: 14px; padding: 18px 20px;
        margin-bottom: 18px; display: flex; justify-content: space-between; align-items: flex-start; gap: 12px;
    }
    .doyle-unit-banner h3 { margin: 0 0 6px; font-size: 22px; font-weight: 900; }
    .doyle-unit-banner p { margin: 0; font-size: 12px; color: #94a3b8; }
    .doyle-status-pill {
        background: rgba(239,68,68,.25); color: #fecaca; border: 1px solid rgba(239,68,68,.4);
        border-radius: 999px; padding: 4px 10px; font-size: 10px; font-weight: 900;
        text-transform: uppercase; white-space: nowrap;
    }
    .doyle-route-box {
        background: #fff1f2; border: 1px solid #fecdd3; border-radius: 12px;
        padding: 14px 16px; margin: 8px 0 16px;
    }
    .doyle-route-box label { font-size: 11px; font-weight: 800; color: #9f1239; text-transform: uppercase; }
    .doyle-checklist {
        border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px 14px; margin-bottom: 12px;
    }
    .doyle-checklist-title {
        font-size: 11px; font-weight: 800; color: #64748b; text-transform: uppercase;
        letter-spacing: .04em; margin-bottom: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="doyle-page">', unsafe_allow_html=True)

st.markdown(
    """
    <div class="doyle-header">
      <span class="doyle-badge">Contractor Interface</span>
      <h2>Doyle Offsite Repairs Portal</h2>
      <p>Dedicated diagnostic &amp; invoices entry console for Doyle service mechanics.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

units = fetch_units()
doyle_units = [unit for unit in units if display_status(unit) == "Doyle Shop"]
transfers = fetch_transfers()

if "doyle_selected_ptac_id" not in st.session_state:
    st.session_state.doyle_selected_ptac_id = doyle_units[0]["ptac_id"] if doyle_units else None

if "doyle_form_version" not in st.session_state:
    st.session_state.doyle_form_version = 0

queue_col, work_col = st.columns([1, 2], gap="large")

selected = None

with queue_col:
    st.markdown("#### Offsite Repair Queue")
    with st.container(border=True):
        if not doyle_units:
            st.info("No dispatched jobs in repair queue.")
        else:
            for unit in doyle_units:
                is_selected = st.session_state.doyle_selected_ptac_id == unit["ptac_id"]
                card_class = "doyle-queue-card selected" if is_selected else "doyle-queue-card"
                dispatch_note = latest_doyle_dispatch_note(unit["ptac_id"], transfers)
                if len(dispatch_note) > 72:
                    dispatch_note = dispatch_note[:69] + "..."
                st.markdown(
                    f"""
                    <div class="{card_class}">
                      <span class="doyle-queue-btu">{escape(btu_from_model(unit.get('model_specs')))}</span>
                      <div class="doyle-queue-id">{escape(unit['ptac_id'])}</div>
                      <div class="doyle-queue-sn">S/N: {escape(unit.get('serial_number') or 'N/A')}</div>
                      <div class="doyle-queue-note">{escape(dispatch_note)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button(
                    f"Select {unit['ptac_id']}",
                    key=f"doyle_pick_{unit['ptac_id']}",
                    use_container_width=True,
                ):
                    st.session_state.doyle_selected_ptac_id = unit["ptac_id"]
                    st.rerun()
            selected = st.session_state.doyle_selected_ptac_id

with work_col:
    st.markdown("#### Tech Repair Entry Form")
    with st.container(border=True):
        if not selected or not doyle_units:
            st.caption("Select a dispatched PTAC unit from the queue to fill out repair logs and mark it ready.")
        else:
            unit = next(item for item in doyle_units if item["ptac_id"] == selected)
            form_key = f"doyle_form_{unit['ptac_id']}_{st.session_state.doyle_form_version}"

            st.markdown(
                f"""
                <div class="doyle-unit-banner">
                  <div>
                    <h3>{escape(unit['ptac_id'])}</h3>
                    <p>{escape(unit.get('model_specs') or '')} &bull; S/N: {escape(unit.get('serial_number') or '')} &bull; {escape(btu_from_model(unit.get('model_specs')))}</p>
                  </div>
                  <span class="doyle-status-pill">At Doyle Shop</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown('<div class="doyle-route-box">', unsafe_allow_html=True)
            route = st.radio(
                "Custody Route Post-Doyle (Send Back to Hotel)",
                ["Send to Spare Storage Closet", "Deploy Direct to Guest Room"],
                horizontal=True,
                key=f"doyle_route_{form_key}",
            )
            st.markdown("</div>", unsafe_allow_html=True)

            target_room = None
            occupying_unit = None
            if route == "Deploy Direct to Guest Room":
                target_room = st.selectbox(
                    "Target Room",
                    room_locations(),
                    index=None,
                    placeholder="Choose a guest room...",
                    key=f"doyle_room_{form_key}",
                )
                if target_room:
                    occupying_unit = active_unit_at_location(units, target_room, unit["ptac_id"])

            if route == "Deploy Direct to Guest Room" and not target_room:
                st.info("Choose a target guest room before submitting.")

            if occupying_unit:
                st.warning(
                    f"{target_room} already has active unit {occupying_unit['ptac_id']}. "
                    "If you continue, that existing unit will be moved to Maintenance Office."
                )

            with st.form(form_key):
                tech = st.text_input("Technician Signature", placeholder="e.g. Mechanic Steve")
                invoice = st.text_input("Work Order / Invoice Ref #", placeholder="e.g. DOY-9082")

                st.markdown('<div class="doyle-checklist"><div class="doyle-checklist-title">Replaced Core Components Checklist</div>', unsafe_allow_html=True)
                check_cols = st.columns(2)
                components = []
                for index, component in enumerate(CORE_COMPONENTS):
                    with check_cols[index % 2]:
                        if st.checkbox(component, key=f"doyle_comp_{component}_{form_key}"):
                            components.append(component)
                st.markdown("</div>", unsafe_allow_html=True)

                extra_parts = st.text_input(
                    "Additional Parts Used (Comma Separated)",
                    placeholder="e.g. Copper pipes, extra brackets",
                )
                total_bill = st.number_input("Total Repair Bill ($)", min_value=0.0, step=25.0, format="%.2f")
                notes = st.text_area(
                    "Diagnostics & Service Completed Notes",
                    placeholder="Describe the repair work completed at Doyle shop...",
                )

                override_occupied = False
                if occupying_unit:
                    override_occupied = st.checkbox(
                        "Confirm occupied-room override and move existing unit to Maintenance Office"
                    )

                action_cols = st.columns([1, 1])
                with action_cols[0]:
                    clear_clicked = st.form_submit_button("Clear Card", use_container_width=True)
                with action_cols[1]:
                    submitted = st.form_submit_button("Mark Fixed & Ship to Hotel", type="primary", use_container_width=True)

            if clear_clicked:
                st.session_state.doyle_form_version += 1
                st.rerun()

            if submitted:
                if not tech.strip() or not invoice.strip():
                    st.error("Technician signature and invoice reference are required.")
                elif route == "Deploy Direct to Guest Room" and not target_room:
                    st.error("Choose a target guest room before shipping back to the hotel.")
                elif occupying_unit and not override_occupied:
                    st.error("You must confirm the occupied-room override before returning to this room.")
                else:
                    target_location = target_room if target_room else SPARE_STORAGE
                    try:
                        complete_doyle_repair(
                            selected,
                            unit,
                            tech,
                            invoice,
                            total_bill,
                            components,
                            extra_parts,
                            notes,
                            target_location,
                            override_occupied=override_occupied,
                        )
                        st.session_state.doyle_selected_ptac_id = None
                        st.session_state.doyle_form_version += 1
                        st.success(f"{selected} marked fixed and returned to {target_location}.")
                        st.rerun()
                    except ValueError as error:
                        if str(error) == "occupied_room_override_required":
                            st.error("You must confirm the occupied-room override before returning to this room.")
                        else:
                            st.error(str(error))

st.markdown("</div>", unsafe_allow_html=True)
