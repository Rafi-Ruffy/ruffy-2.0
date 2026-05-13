import streamlit as st


def render():
    st.markdown("# Invoices")
    st.markdown("<p style='color:#6b7280; margin-top:-12px;'>Your monthly payouts from Ruffy.</p>", unsafe_allow_html=True)
    st.markdown("")

    payouts = [
        {"period": "April 2026", "orders": 142, "gross": "$11,840.00", "fee": "$2,368.00", "payout": "Paid May 5"},
        {"period": "March 2026", "orders": 128, "gross": "$10,420.00", "fee": "$2,084.00", "payout": "Paid Apr 5"},
        {"period": "February 2026", "orders": 116, "gross": "$9,180.00", "fee": "$1,836.00", "payout": "Paid Mar 5"},
        {"period": "January 2026", "orders": 98, "gross": "$7,860.00", "fee": "$1,572.00", "payout": "Paid Feb 5"},
    ]

    for p in payouts:
        with st.container(border=True):
            c1, c2, c3, c4, c5 = st.columns([0.25, 0.18, 0.2, 0.2, 0.17])
            with c1:
                st.markdown(f"**{p['period']}**")
            with c2:
                st.caption("Orders")
                st.markdown(str(p["orders"]))
            with c3:
                st.caption("Gross")
                st.markdown(p["gross"])
            with c4:
                st.caption("Your share")
                st.markdown(p["fee"])
            with c5:
                st.caption("Status")
                st.markdown(f"<span style='color:#065f46;'>{p['payout']}</span>", unsafe_allow_html=True)
