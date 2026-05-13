import streamlit as st
from mock_data import RENEWALS, CLIENTS, PETS, DENY_REASONS


def render():
    st.markdown("# Renewals")
    st.markdown("<p style='color:#6b7280; margin-top:-12px;'>Existing prescriptions that need to continue. Auto-flagged by the system before clients run out, or logged when a client asks directly.</p>", unsafe_allow_html=True)
    st.markdown("")

    pending = [r for r in RENEWALS if not st.session_state.get(f"approved_{r['id']}") and not st.session_state.get(f"denied_{r['id']}")]
    approved = [r for r in RENEWALS if st.session_state.get(f"approved_{r['id']}")]
    denied = [r for r in RENEWALS if st.session_state.get(f"denied_{r['id']}")]

    autoship_pending = [r for r in pending if r["source"] == "autoship"]
    client_pending = [r for r in pending if r["source"] == "client"]

    tab_pending, tab_decided = st.tabs([f"Pending ({len(pending)})", f"Decided ({len(approved) + len(denied)})"])

    with tab_pending:
        if not pending:
            st.info("No pending renewals.")

        if autoship_pending:
            st.markdown(f"##### AutoShip renewals ({len(autoship_pending)})")
            st.caption("Flagged by the system. AutoShip is running and supply is approaching the end of authorization.")
            for req in autoship_pending:
                _render_request_card(req)

        if client_pending:
            st.markdown("")
            st.markdown(f"##### Client-initiated refill requests ({len(client_pending)})")
            st.caption("Clients who aren't on AutoShip and have asked for more.")
            for req in client_pending:
                _render_request_card(req)

    with tab_decided:
        if not approved and not denied:
            st.info("No decisions yet.")
        for req in approved:
            _render_decided_card(req, "approved")
        for req in denied:
            _render_decided_card(req, "denied")


def _render_request_card(req):
    client = CLIENTS[req["client_id"]]
    pet = PETS[req["pet_id"]]

    with st.container(border=True):
        top_c1, top_c2 = st.columns([0.7, 0.3])
        with top_c1:
            st.markdown(f"**{client['name']}** — {pet['name']}")
            st.caption(f"{pet['species']}, {pet['breed']} · {pet['weight_lbs']} lbs · {pet['age']}")
        with top_c2:
            badge = _source_badge(req["source"])
            st.markdown(badge, unsafe_allow_html=True)
            st.caption(req["received"])

        st.markdown(f"**{req['drug']}** {req['strength']} · Qty {req['qty']} · {req['refills_requested']} refills requested")
        st.markdown(f"<p style='background:#f9fafb; padding:8px 12px; border-radius:6px; font-size:0.85rem; color:#4b5563; margin-top:8px;'>{req['previous_rx']}</p>", unsafe_allow_html=True)

        if req.get("autoship_context"):
            st.markdown(f"<p style='background:#ecfdf5; padding:8px 12px; border-radius:6px; font-size:0.85rem; color:#065f46; margin-top:6px;'>{req['autoship_context']}</p>", unsafe_allow_html=True)

        action_c1, action_c2, _ = st.columns([0.25, 0.25, 0.5])
        with action_c1:
            if st.button("Approve", key=f"rn_approve_{req['id']}", type="primary", use_container_width=True):
                _approve_dialog(req["id"])
        with action_c2:
            if st.button("Deny", key=f"rn_deny_{req['id']}", use_container_width=True):
                _deny_dialog(req["id"])


def _render_decided_card(req, status):
    client = CLIENTS[req["client_id"]]
    pet = PETS[req["pet_id"]]
    with st.container(border=True):
        c1, c2 = st.columns([0.7, 0.3])
        with c1:
            st.markdown(f"**{client['name']}** — {pet['name']}")
            st.caption(f"{req['drug']} {req['strength']}")
        with c2:
            if status == "approved":
                st.markdown("<span style='background:#ecfdf5; color:#065f46; padding:3px 10px; border-radius:999px; font-size:0.8rem; font-weight:500;'>Approved</span>", unsafe_allow_html=True)
            else:
                reason = st.session_state.get(f"denied_{req['id']}", "—")
                st.markdown("<span style='background:#fef2f2; color:#991b1b; padding:3px 10px; border-radius:999px; font-size:0.8rem; font-weight:500;'>Denied</span>", unsafe_allow_html=True)
                st.caption(f"Reason: {reason}")


def _source_badge(source: str) -> str:
    if source == "autoship":
        return "<span style='background:#ecfdf5; color:#065f46; padding:3px 10px; border-radius:999px; font-size:0.75rem; font-weight:500;'>AutoShip renewal</span>"
    return "<span style='background:#eff6ff; color:#1e40af; padding:3px 10px; border-radius:999px; font-size:0.75rem; font-weight:500;'>Client request</span>"


@st.dialog("Approve Renewal", width="large")
def _approve_dialog(req_id: str):
    req = next(r for r in RENEWALS if r["id"] == req_id)
    client = CLIENTS[req["client_id"]]
    pet = PETS[req["pet_id"]]

    _row("Item", f"{req['drug']} {req['strength']} · Qty {req['qty']}")
    _row("Client", client["name"])
    _row("Patient", f"{pet['name']} — {pet['breed']} ({pet['species']})")
    _row("Weight", f"{pet['weight_lbs']} lbs")
    _row("Age", pet["age"])
    _row("Previous rx", req["previous_rx"])
    if req.get("autoship_context"):
        _row("AutoShip", req["autoship_context"])

    st.markdown("")
    c1, c2 = st.columns(2)
    with c1:
        st.number_input("Refills", value=req["refills_requested"], min_value=0, max_value=12, key=f"rn_refills_{req_id}")
    with c2:
        st.date_input("Expiry date (optional)", value=None, key=f"rn_expiry_{req_id}")

    st.text_area("Pharmacy notes (optional)", height=80, key=f"rn_pharma_{req_id}")
    st.text_area("Instructions", value="Give as previously directed.", height=80, key=f"rn_instr_{req_id}")

    st.markdown("")
    cancel_c, approve_c = st.columns([0.3, 0.7])
    with cancel_c:
        if st.button("Cancel", use_container_width=True, key=f"rn_cancel_a_{req_id}"):
            st.rerun()
    with approve_c:
        if st.button("Approve and send to Ruffy", type="primary", use_container_width=True, key=f"rn_confirm_a_{req_id}"):
            st.session_state[f"approved_{req_id}"] = True
            st.rerun()


@st.dialog("Deny Renewal")
def _deny_dialog(req_id: str):
    req = next(r for r in RENEWALS if r["id"] == req_id)
    client = CLIENTS[req["client_id"]]
    pet = PETS[req["pet_id"]]

    _row("Item", f"{req['drug']} {req['strength']}")
    _row("Client", client["name"])
    _row("Patient", pet["name"])

    st.markdown("")
    reason = st.selectbox("Deny reason", options=DENY_REASONS, key=f"rn_dreason_{req_id}")
    st.text_area("Note (optional)", placeholder="Add context for the CE or client...", height=80, key=f"rn_dnote_{req_id}")

    st.markdown("")
    cancel_c, deny_c = st.columns([0.3, 0.7])
    with cancel_c:
        if st.button("Cancel", use_container_width=True, key=f"rn_cancel_d_{req_id}"):
            st.rerun()
    with deny_c:
        if st.button("Send denial", type="primary", use_container_width=True, key=f"rn_confirm_d_{req_id}"):
            st.session_state[f"denied_{req_id}"] = reason
            st.rerun()


def _row(label, value):
    c1, c2 = st.columns([0.25, 0.75])
    with c1:
        st.markdown(f"<p style='color:#6b7280; margin:0;'>{label}</p>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<p style='margin:0; font-weight:500;'>{value}</p>", unsafe_allow_html=True)
