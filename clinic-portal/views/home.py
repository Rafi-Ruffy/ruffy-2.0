import streamlit as st
from mock_data import RENEWALS, CLIENTS, PETS, ORDERS, CURRENT_USER, DENY_REASONS


def render():
    st.markdown(f"# Today")
    st.markdown(f"<p style='color:#6b7280; margin-top:-12px;'>Welcome back, {CURRENT_USER['name'].split()[-1]}.</p>", unsafe_allow_html=True)
    st.markdown("")

    _render_kpis()

    st.markdown("")
    _render_quickstart()

    st.markdown("")
    _render_renewal_queue()

    st.markdown("")
    _render_recent_orders()


def _render_kpis():
    pending = [r for r in RENEWALS if not st.session_state.get(f"approved_{r['id']}") and not st.session_state.get(f"denied_{r['id']}")]
    autoship_pending = len([r for r in pending if r["source"] == "autoship"])
    client_pending = len([r for r in pending if r["source"] == "client"])
    in_flight = len([o for o in ORDERS if o["status"] in ("Awaiting payment", "Processing", "Shipped")])
    delivered_recent = len([o for o in ORDERS if o["status"] == "Delivered"])

    c1, c2, c3, c4 = st.columns(4)
    _kpi_tile(c1, "AutoShip renewals", autoship_pending, "needs your sign-off")
    _kpi_tile(c2, "Client refill requests", client_pending, "waiting on you")
    _kpi_tile(c3, "Orders in flight", in_flight, "shipping or paying")
    _kpi_tile(c4, "Delivered this month", delivered_recent, "complete")


def _kpi_tile(col, label, value, hint):
    with col:
        with st.container(border=True):
            st.markdown(f"<p style='color:#6b7280; font-size:0.85rem; margin:0;'>{label}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size:2.2rem; font-weight:600; margin:4px 0; font-family:Georgia,serif;'>{value}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='color:#9ca3af; font-size:0.8rem; margin:0;'>{hint}</p>", unsafe_allow_html=True)


def _render_quickstart():
    st.markdown("### Start a new prescription")

    with st.container(border=True):
        client_options = {cid: f"{c['name']}" for cid, c in CLIENTS.items()}
        choice = st.selectbox(
            "Search for a client or pet",
            options=[""] + list(client_options.keys()),
            format_func=lambda x: client_options.get(x, "Type a client or pet name..."),
            label_visibility="collapsed",
            key="quickstart_client",
        )

        if choice:
            client = CLIENTS[choice]
            pets = [PETS[pid] for pid in client["pets"]]
            pet_names = ", ".join(p["name"] for p in pets)
            st.caption(f"{client['name']} · {pet_names}")
            c1, _ = st.columns([0.25, 0.75])
            with c1:
                st.button("Start prescription", type="primary", use_container_width=True, key="quickstart_btn")


def _render_renewal_queue():
    pending = [r for r in RENEWALS if not st.session_state.get(f"approved_{r['id']}") and not st.session_state.get(f"denied_{r['id']}")]

    if not pending:
        return

    st.markdown(f"### Renewals awaiting your approval ({len(pending)})")
    st.markdown("<p style='color:#6b7280; margin-top:-8px; font-size:0.9rem;'>System-flagged AutoShips and client refill requests.</p>", unsafe_allow_html=True)

    for req in pending:
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
                if st.button("Approve", key=f"home_approve_{req['id']}", type="primary", use_container_width=True):
                    _approve_dialog(req["id"])
            with action_c2:
                if st.button("Deny", key=f"home_deny_{req['id']}", use_container_width=True):
                    _deny_dialog(req["id"])


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
        st.number_input("Refills", value=req["refills_requested"], min_value=0, max_value=12, key=f"home_refills_{req_id}")
    with c2:
        st.date_input("Expiry date (optional)", value=None, key=f"home_expiry_{req_id}")

    st.text_area("Pharmacy notes (optional)", height=80, key=f"home_pharma_{req_id}")
    st.text_area("Instructions", value="Give as previously directed.", height=80, key=f"home_instr_{req_id}")

    st.markdown("")
    cancel_c, approve_c = st.columns([0.3, 0.7])
    with cancel_c:
        if st.button("Cancel", use_container_width=True, key=f"home_cancel_a_{req_id}"):
            st.rerun()
    with approve_c:
        if st.button("Approve and send to Ruffy", type="primary", use_container_width=True, key=f"home_confirm_a_{req_id}"):
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
    reason = st.selectbox("Deny reason", options=DENY_REASONS, key=f"home_dreason_{req_id}")
    st.text_area("Note (optional)", height=80, key=f"home_dnote_{req_id}")

    st.markdown("")
    cancel_c, deny_c = st.columns([0.3, 0.7])
    with cancel_c:
        if st.button("Cancel", use_container_width=True, key=f"home_cancel_d_{req_id}"):
            st.rerun()
    with deny_c:
        if st.button("Send denial", type="primary", use_container_width=True, key=f"home_confirm_d_{req_id}"):
            st.session_state[f"denied_{req_id}"] = reason
            st.rerun()


def _row(label, value):
    c1, c2 = st.columns([0.25, 0.75])
    with c1:
        st.markdown(f"<p style='color:#6b7280; margin:0;'>{label}</p>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<p style='margin:0; font-weight:500;'>{value}</p>", unsafe_allow_html=True)


def _render_recent_orders():
    st.markdown("### Recent orders")

    for order in ORDERS[:4]:
        client = CLIENTS[order["client_id"]]
        pet = PETS[order["pet_id"]]
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([0.3, 0.3, 0.2, 0.2])
            with c1:
                st.markdown(f"**{client['name']}**")
                st.caption(f"{pet['name']} · {pet['species']}")
            with c2:
                st.caption("Prescription")
                st.markdown(f"{order['drug']}")
            with c3:
                st.caption("Status")
                st.markdown(_status_pill(order["status"]), unsafe_allow_html=True)
            with c4:
                st.caption("Order")
                st.markdown(f"`{order['id']}`")


def _status_pill(status: str) -> str:
    palette = {
        "Awaiting payment": ("#fff7ed", "#9a3412"),
        "Shipped": ("#ecfdf5", "#065f46"),
        "Delivered": ("#f3f4f6", "#374151"),
        "Processing": ("#eff6ff", "#1e40af"),
    }
    bg, fg = palette.get(status, ("#f3f4f6", "#374151"))
    return f"<span style='background:{bg}; color:{fg}; padding:3px 10px; border-radius:999px; font-size:0.8rem; font-weight:500;'>{status}</span>"
