import streamlit as st
from mock_data import ORDERS, CLIENTS, PETS


def render():
    st.markdown("# Order history")
    st.markdown("<p style='color:#6b7280; margin-top:-12px;'>Every prescription you've sent to Ruffy pharmacy.</p>", unsafe_allow_html=True)
    st.markdown("")

    filter_choice = st.segmented_control(
        "Filter",
        options=["All", "Awaiting payment", "Shipped", "Delivered"],
        default="All",
        label_visibility="collapsed",
    )

    filtered = ORDERS if filter_choice == "All" else [o for o in ORDERS if o["status"] == filter_choice]

    for order in filtered:
        client = CLIENTS[order["client_id"]]
        pet = PETS[order["pet_id"]]
        with st.container(border=True):
            c1, c2, c3, c4, c5 = st.columns([0.25, 0.25, 0.18, 0.14, 0.18])
            with c1:
                st.markdown(f"**{client['name']}**")
                st.caption(f"{pet['name']} · {pet['species']}")
            with c2:
                st.caption("Prescription")
                st.markdown(f"{order['drug']}")
                st.caption(f"{order['strength']} · Qty {order['qty']}")
            with c3:
                st.caption("Date placed")
                st.markdown(order["date"])
            with c4:
                st.caption("Total")
                st.markdown(order["total"])
            with c5:
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
