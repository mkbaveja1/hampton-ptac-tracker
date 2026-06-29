from __future__ import annotations
from datetime import date, timedelta
import pandas as pd
import streamlit as st

from views._shared import (
    display_status,
    doyle_repair_cost,
    fetch_doyle_repairs,
    fetch_onsite_repairs,
    fetch_pm_logs,
    fetch_units,
    kpi_card,
)

from views.unit_detail import (
    get_selected_ptac_id,
    render_unit_detail
)

if get_selected_ptac_id():
    render_unit_detail()
    st.stop()

st.markdown("### Spending & PM Audits")
st.caption("Management view for repair spend, PM coverage, and active contractor queue.")

units = fetch_units()
onsite = fetch_onsite_repairs()
doyle = fetch_doyle_repairs()
pm_logs = fetch_pm_logs()

date_filter = st.selectbox("Repair Spend Window", ["All Time", "Last 30 Days", "Last 90 Days"], index=0)

cutoff = None
if date_filter == "Last 30 Days":
    cutoff = date.today() - timedelta(days = 30)
elif date_filter == "Last 90 Days":
    cutoff = date.today() - timedelta(days = 90)

def parse_row_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def in_window(row, date_field):
    if cutoff is None:
        return True
    row_date = parse_row_date(row.get(date_field))
    return row_date is not None and row_date >= cutoff


filtered_onsite = [row for row in onsite if in_window(row, "repair_date")]
filtered_doyle = [row for row in doyle if in_window(row, "sent_date")]

onsite_total = sum(float(row.get("repair_cost") or 0) for row in filtered_onsite)
doyle_total = sum(doyle_repair_cost(row) for row in filtered_doyle)
repair_count = len(filtered_onsite) + len([row for row in filtered_doyle if doyle_repair_cost(row) > 0])
avg = (onsite_total + doyle_total) / repair_count if repair_count else 0
pm_due = sum(1 for unit in units if display_status(unit) == "Needs PM")
compliance = round(((len(units) - pm_due) / len(units)) * 100) if units else 0
doyle_active = sum(1 for unit in units if display_status(unit) == "Doyle Shop")

cols = st.columns(4)
with cols[0]:
    kpi_card("Accumulated Repairs Spend", f"${onsite_total + doyle_total:,.2f}", date_filter.lower(), "#0f172a")
with cols[1]:
    kpi_card("Avg Repair Cost", f"${avg:,.0f}", "Per logged intervention", "#2563eb")
with cols[2]:
    kpi_card("PM Compliance", f"{compliance}%", f"{pm_due} units require PM", "#f59e0b")
with cols[3]:
    kpi_card("Active Doyle Units", str(doyle_active), "Currently at Doyle Shop", "#dc2626")

left, right = st.columns(2)

with left:
    st.container(border=True).markdown("#### Highest Repair Expenses")
    repair_rows = []
    for row in filtered_onsite:
        repair_rows.append(
            {
                "PTAC": row.get("ptac_id"),
                "Source": "Onsite",
                "Cost": float(row.get("repair_cost") or 0),
                "Date": row.get("repair_date"),
            }
        )
    for row in filtered_doyle:
        repair_rows.append(
            {
                "PTAC": row.get("ptac_id"),
                "Source": "Doyle",
                "Cost": doyle_repair_cost(row),
                "Date": row.get("sent_date"),
            }
        )

    if not repair_rows:
        st.info("No repair costs logged yet.")
    else:
        repairs_df = pd.DataFrame(repair_rows)
        grouped = repairs_df.groupby("PTAC", as_index=False)["Cost"].sum().sort_values("Cost", ascending=False).head(10)
        for _, row in grouped.iterrows():
            ptac_id = row["PTAC"]
            cost = row["Cost"]
            if st.button(f"{ptac_id} — ${cost:,.2f}", key=f"analytics_ptac_{ptac_id}", use_container_width=True):
                st.session_state.selected_ptac_id = ptac_id
                st.rerun()
        st.bar_chart(grouped.set_index("PTAC"))

with right:
    st.container(border=True).markdown("#### Active Doyle Contractor Shipments")
    doyle_units = [unit for unit in units if display_status(unit) == "Doyle Shop"]
    if not doyle_units:
        st.info("No units currently at Doyle Shop.")
    else:
        for unit in doyle_units:
            ptac_id = unit["ptac_id"]
            if st.button(f"View {ptac_id}", key=f"analytics_doyle_{ptac_id}"):
                st.session_state.selected_ptac_id = ptac_id
                st.rerun()
            st.markdown(
                f"""
                <div style='background:#fff1f2;border:1px solid #fecdd3;border-radius:14px;padding:14px;margin-bottom:10px;'>
                  <strong>{ptac_id}</strong>
                  <span style='float:right;color:#9f1239;font-size:11px;font-weight:800;'>At Doyle Shop</span>
                  <div style='font-size:12px;color:#64748b;margin-top:6px;'>{unit.get('model_specs')} · S/N {unit.get('serial_number')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.markdown("#### Recent PM Logs")
if not pm_logs:
    st.info("No PM logs found yet.")
else:
    recent_pm = pm_logs[:20]
    for log in recent_pm:
        ptac_id = log.get("ptac_id")
        performed = log.get("date_performed") or "Unknown date"
        tech = log.get("technician_name") or "Unknown tech"
        if st.button(f"{ptac_id} — {performed} ({tech})", key=f"analytics_pm_{ptac_id}_{performed}"):
            st.session_state.selected_ptac_id = ptac_id
            st.rerun()
