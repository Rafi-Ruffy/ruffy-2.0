import streamlit as st
from mock_data import PRODUCTS


def render():
    st.markdown("# Products")
    st.markdown("<p style='color:#6b7280; margin-top:-12px;'>Ruffy catalog with your retail pricing.</p>", unsafe_allow_html=True)
    st.markdown("")

    search = st.text_input("Search products", placeholder="Search by product name…", label_visibility="collapsed")

    for product in PRODUCTS:
        if search and search.lower() not in product["name"].lower():
            continue

        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([0.4, 0.25, 0.2, 0.15])
            with c1:
                st.markdown(f"**{product['name']}**")
                st.caption(", ".join(product["strengths"]))
            with c2:
                st.caption("Retail price")
                st.markdown(product["price_range"])
            with c3:
                st.caption("Stock")
                if product["stock"] == "In stock":
                    st.markdown("<span style='color:#065f46;'>In stock</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='color:#9a3412;'>{product['stock']}</span>", unsafe_allow_html=True)
            with c4:
                st.button("Prescribe", key=f"rx_{product['name']}", use_container_width=True)
