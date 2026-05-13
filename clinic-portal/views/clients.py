import streamlit as st
from mock_data import CLIENTS, PETS, ORDERS


def render():
    if "selected_client" not in st.session_state:
        st.session_state.selected_client = None

    if st.session_state.selected_client:
        _render_client_detail(st.session_state.selected_client)
    else:
        _render_client_list()


def _render_client_list():
    st.markdown("# Clients")
    st.markdown("<p style='color:#6b7280; margin-top:-12px;'>All clients and their pets.</p>", unsafe_allow_html=True)
    st.markdown("")

    search = st.text_input("Search clients or pets", placeholder="Search by name…", label_visibility="collapsed")

    for cid, client in CLIENTS.items():
        pets = [PETS[pid] for pid in client["pets"]]
        pet_names = ", ".join(p["name"] for p in pets)

        if search and search.lower() not in client["name"].lower() and not any(search.lower() in p["name"].lower() for p in pets):
            continue

        with st.container(border=True):
            c1, c2, c3 = st.columns([0.45, 0.35, 0.2])
            with c1:
                st.markdown(f"**{client['name']}**")
                st.caption(client["phone"])
            with c2:
                st.caption("Pets")
                st.markdown(pet_names)
            with c3:
                if st.button("View", key=f"view_{cid}", use_container_width=True):
                    st.session_state.selected_client = cid
                    st.rerun()


def _render_client_detail(cid: str):
    client = CLIENTS[cid]

    if st.button("← Back to clients"):
        st.session_state.selected_client = None
        st.rerun()

    st.markdown(f"# {client['name']}")
    st.caption(f"{client['phone']} · {client['email']} · {client['address']}")
    st.markdown("")

    st.markdown("### Pets")
    for pid in client["pets"]:
        pet = PETS[pid]
        with st.container(border=True):
            c1, c2, c3 = st.columns([0.4, 0.4, 0.2])
            with c1:
                st.markdown(f"**{pet['name']}**")
                st.caption(f"{pet['species']} · {pet['breed']}")
            with c2:
                st.caption("Weight")
                st.markdown(f"{pet['weight_lbs']} lbs")
            with c3:
                st.button("Start rx", key=f"newrx_{pid}", use_container_width=True)

    st.markdown("")
    st.markdown("### Order history")
    client_orders = [o for o in ORDERS if o["client_id"] == cid]
    if not client_orders:
        st.caption("No orders yet.")
        return

    for order in client_orders:
        pet = PETS[order["pet_id"]]
        with st.container(border=True):
            c1, c2, c3 = st.columns([0.35, 0.35, 0.3])
            with c1:
                st.markdown(f"**{order['drug']}** {order['strength']}")
                st.caption(f"For {pet['name']} · Qty {order['qty']}")
            with c2:
                st.caption("Date placed")
                st.markdown(order["date"])
            with c3:
                st.caption("Status")
                st.markdown(_status_pill(order["status"]), unsafe_allow_html=True)


def _status_pill(status: str) -> str:
    palette = {
        "Awaiting payment": ("#fff7ed", "#9a3412"),
        "Shipped": ("#ecfdf5", "#065f46"),
        "Delivered": ("#f3f4f6", "#374151"),
        "Processing": ("#eff6ff", "#1e40af"),
    }
    bg, fg = palette.get(status, ("#f3f4f6", "#374151"))
    return f"<span style='background:{bg}; color:{fg}; padding:3px 10px; border-radius:999px; font-size:0.8rem; font-weight:500;'>{status}</span>"
