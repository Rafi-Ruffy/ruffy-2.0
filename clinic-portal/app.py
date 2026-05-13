import streamlit as st
from mock_data import CLINIC, CURRENT_USER, RENEWALS
from views import home, clients, orders, products, invoices, renewals, new_rx

st.set_page_config(
    page_title=f"{CLINIC['name']} — Ruffy",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    h1, h2, h3 {
        font-family: 'Georgia', 'Times New Roman', serif !important;
        letter-spacing: -0.01em;
    }
    .stApp {
        background-color: #fafafa;
    }
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e5e7eb;
    }
</style>
""", unsafe_allow_html=True)

home_page = st.Page(home.render, title="Home", icon=":material/home:", default=True, url_path="home")
renewals_page = st.Page(renewals.render, title="Renewals", icon=":material/refresh:", url_path="renewals")
new_rx_page = st.Page(new_rx.render, title="New Rx", icon=":material/edit_note:", url_path="new-rx")
clients_page = st.Page(clients.render, title="Clients", icon=":material/people:", url_path="clients")
orders_page = st.Page(orders.render, title="Order history", icon=":material/inventory_2:", url_path="orders")
products_page = st.Page(products.render, title="Products", icon=":material/pill:", url_path="products")
invoices_page = st.Page(invoices.render, title="Invoices", icon=":material/receipt_long:", url_path="invoices")

with st.sidebar:
    st.markdown(f"### {CLINIC['name'].split()[0]}")
    st.caption("Ruffy partner")
    st.markdown("")

    if st.button("Start a new rx", type="primary", use_container_width=True):
        st.switch_page(new_rx_page)

    pending_count = len([r for r in RENEWALS if not st.session_state.get(f"approved_{r['id']}") and not st.session_state.get(f"denied_{r['id']}")])
    renewals_label = f"Renewals ({pending_count})" if pending_count else "Renewals"
    if st.button(renewals_label, use_container_width=True):
        st.switch_page(renewals_page)

    st.divider()

nav = st.navigation([home_page, renewals_page, new_rx_page, clients_page, orders_page, products_page, invoices_page])

with st.sidebar:
    st.divider()
    st.markdown(f"**{CURRENT_USER['name']}**")
    st.caption(CURRENT_USER["role"])

nav.run()
