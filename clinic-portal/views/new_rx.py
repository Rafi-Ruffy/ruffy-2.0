import os
import json
import re
from datetime import date
import streamlit as st
import anthropic
from mock_data import CLIENTS, PETS, PRODUCTS, CURRENT_USER


SYSTEM_PROMPT = """You are a veterinary prescription parser. Extract structured prescription information from a vet's note, voice transcript, or shorthand description.

Return ONLY valid JSON with these fields:
{
  "drug": "string or null (e.g. 'Apoquel Chewable', 'Carprofen Tablets')",
  "strength": "string or null (e.g. '16 mg', '75 mg')",
  "qty": "integer or null (count of tablets/chews per fill — leave null if phases are present)",
  "refills": "integer or null",
  "dose_amount": "number or null (amount per administration, for SINGLE-phase regimens only)",
  "dose_frequency": "string or null (one of: 'Once daily', 'Twice daily', 'Three times daily', 'Every 8 hours', 'Every 12 hours', 'Every other day', 'As needed', for SINGLE-phase only)",
  "phases": "array or null (only if the rx has multiple phases like a taper). Each phase is { 'dose_amount': number, 'frequency': string (same options as dose_frequency), 'duration_days': integer or null, 'ongoing': boolean }. The final phase typically has ongoing=true.",
  "instructions": "string or null (full label instructions)",
  "pharmacy_notes": "string or null"
}

If the rx is a single regimen (constant dose forever), populate dose_amount/dose_frequency and leave phases null.
If the rx has multiple phases (taper, step-down, induction-then-maintenance), populate the phases array and leave dose_amount/dose_frequency null.

If a field cannot be determined, set it to null."""


FREQUENCY_OPTIONS = [
    "Once daily",
    "Twice daily",
    "Three times daily",
    "Every 8 hours",
    "Every 12 hours",
    "Every other day",
    "As needed",
]

# Daily multiplier (doses per day)
FREQUENCY_MULTIPLIER = {
    "Once daily": 1.0,
    "Twice daily": 2.0,
    "Three times daily": 3.0,
    "Every 8 hours": 3.0,
    "Every 12 hours": 2.0,
    "Every other day": 0.5,
    "As needed": None,
}


def render():
    st.markdown("# New Prescription")
    st.markdown("<p style='color:#6b7280; margin-top:-12px;'>Write a new rx and send it to Ruffy pharmacy.</p>", unsafe_allow_html=True)
    st.markdown("")

    # If no client selected yet, show entry tabs
    if not st.session_state.get("newrx_selected_client"):
        tab1, tab2, tab3 = st.tabs(["Search by Client", "Search by Product", "Add a Client"])
        with tab1:
            _tab_search_by_client()
        with tab2:
            _tab_search_by_product()
        with tab3:
            _tab_add_client()
        return

    # Client is locked in — show header with Change button
    client_id = st.session_state["newrx_selected_client"]
    client = CLIENTS[client_id]
    with st.container(border=True):
        c1, c2 = st.columns([0.75, 0.25])
        with c1:
            st.markdown(f"**{client['name']}**")
            st.caption(f"{client['phone']} · {client['email']}")
            preselected = st.session_state.get("newrx_preselected_drug")
            if preselected:
                st.caption(f":green[Prescribing: {preselected}]")
        with c2:
            if st.button("← Change client", use_container_width=True, key="change_client"):
                _reset_rx_state()
                st.rerun()

    pet_id = _step_pet(client_id)
    if not pet_id:
        return

    _step_compose(pet_id)


def _reset_rx_state():
    """Clear all rx-flow state so the user can start a new rx."""
    keys_to_clear = [
        "newrx_selected_client", "newrx_selected_pet", "newrx_preselected_drug",
        "newrx_parsed", "newrx_note", "newrx_drug", "newrx_strength",
        "newrx_qty", "newrx_refills", "newrx_dose_amount", "newrx_dose_freq",
        "newrx_instr", "newrx_instr_customized", "newrx_pharma",
        "newrx_taper_mode", "newrx_phases_list", "newrx_next_phase_id",
        "newrx_m_drug", "newrx_m_strength", "newrx_m_qty", "newrx_m_refills",
        "newrx_m_dose_amount", "newrx_m_dose_freq", "newrx_m_instr",
        "newrx_m_instr_customized", "newrx_m_pharma", "newrx_m_taper_mode",
        "newrx_m_phases_list", "newrx_m_next_phase_id",
        "newrx_autoship", "newrx_autoship_freq", "newrx_autoship_start",
        "newrx_vet", "newrx_pin", "newrx_mode",
    ]
    for k in list(st.session_state.keys()):
        if k in keys_to_clear or k.startswith("newrx_phase_") or k.startswith("newrx_m_phase_"):
            del st.session_state[k]


def _tab_search_by_client():
    st.caption("Find an existing client by name to start a prescription.")
    client_options = {cid: c["name"] for cid, c in CLIENTS.items()}
    cid = st.selectbox(
        "Search clients",
        options=[""] + list(client_options.keys()),
        format_func=lambda x: client_options.get(x, "Type a client name..."),
        key="tab_client_search",
        label_visibility="collapsed",
    )
    if cid:
        client = CLIENTS[cid]
        st.caption(f"{client['phone']} · {client['email']}")
        st.markdown("")
        c1, _ = st.columns([0.3, 0.7])
        with c1:
            if st.button("Continue", type="primary", use_container_width=True, key="tab_client_continue"):
                st.session_state["newrx_selected_client"] = cid
                st.rerun()


def _tab_search_by_product():
    st.caption("Pick a product first, then choose which client to prescribe it for.")
    product_names = [p["name"] for p in PRODUCTS]
    product = st.selectbox(
        "Search products",
        options=[""] + product_names,
        format_func=lambda x: x if x else "Type a product name...",
        key="tab_product_search",
        label_visibility="collapsed",
    )
    if not product:
        return

    prod_data = next(p for p in PRODUCTS if p["name"] == product)
    st.caption(f"Strengths: {', '.join(prod_data['strengths'])} · {prod_data['price_range']} · {prod_data['stock']}")

    st.markdown("")
    st.markdown("**Which client is this for?**")
    client_options = {cid: c["name"] for cid, c in CLIENTS.items()}
    cid = st.selectbox(
        "Client",
        options=[""] + list(client_options.keys()),
        format_func=lambda x: client_options.get(x, "Type a client name..."),
        key="tab_product_client",
        label_visibility="collapsed",
    )
    if cid:
        client = CLIENTS[cid]
        st.caption(f"{client['phone']}")
        st.markdown("")
        c1, _ = st.columns([0.3, 0.7])
        with c1:
            if st.button("Continue", type="primary", use_container_width=True, key="tab_product_continue"):
                st.session_state["newrx_selected_client"] = cid
                st.session_state["newrx_preselected_drug"] = product
                # Default to manual mode since the drug is already chosen
                st.session_state["newrx_mode"] = "Build manually"
                st.session_state["newrx_m_drug"] = product
                st.rerun()


def _tab_add_client():
    st.caption("Add a new client and their first pet, then start a prescription.")

    with st.form("add_client_form", clear_on_submit=False):
        st.markdown("**Client information**")
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Full name", placeholder="e.g. Jamie Foster")
            phone = st.text_input("Phone", placeholder="(416) 555-XXXX")
        with c2:
            email = st.text_input("Email", placeholder="jamie@example.com")
            address = st.text_input("Address", placeholder="123 Yonge St, Toronto ON")

        st.markdown("")
        st.markdown("**First pet**")
        c3, c4 = st.columns(2)
        with c3:
            pet_name = st.text_input("Pet name", placeholder="e.g. Coco")
            species = st.selectbox("Species", options=["Canine", "Feline", "Other"])
        with c4:
            breed = st.text_input("Breed", placeholder="e.g. Goldendoodle")
            weight = st.number_input("Weight (lbs)", min_value=0.0, step=0.1, value=20.0)

        c5, _ = st.columns(2)
        with c5:
            age = st.text_input("Age", placeholder="e.g. 3 years")

        submitted = st.form_submit_button("Add client and start prescription", type="primary")

        if submitted:
            if not name or not pet_name:
                st.error("Client name and pet name are required.")
                return

            new_cid = f"c_new_{len([k for k in CLIENTS if k.startswith('c_new_')]) + 1}"
            new_pid = f"pet_new_{len([k for k in PETS if k.startswith('pet_new_')]) + 1}"
            CLIENTS[new_cid] = {
                "id": new_cid, "name": name, "phone": phone or "",
                "email": email or "", "address": address or "",
                "pets": [new_pid],
            }
            PETS[new_pid] = {
                "id": new_pid, "name": pet_name, "species": species,
                "breed": breed or "Mixed", "weight_lbs": float(weight),
                "age": age or "", "client_id": new_cid,
            }
            st.session_state["newrx_selected_client"] = new_cid
            st.rerun()


def _step_pet(client_id: str) -> str:
    client = CLIENTS[client_id]
    pet_ids = client["pets"]

    selected_pet = st.session_state.get("newrx_selected_pet")
    if selected_pet and selected_pet not in pet_ids:
        st.session_state["newrx_selected_pet"] = None
        selected_pet = None

    st.markdown("")
    st.markdown("### Patient")
    st.caption(f"{client['name']} has {len(pet_ids)} pet{'s' if len(pet_ids) != 1 else ''}. Select one to prescribe for.")

    n_cols = min(len(pet_ids), 3)
    cols = st.columns(n_cols)
    for i, pid in enumerate(pet_ids):
        pet = PETS[pid]
        is_selected = selected_pet == pid
        with cols[i % n_cols]:
            with st.container(border=True):
                st.markdown(f"**{pet['name']}**")
                st.caption(f"{pet['species']}, {pet['breed']}")
                st.caption(f"{pet['weight_lbs']} lbs · {pet['age']}")
                label = "Selected" if is_selected else "Select"
                if st.button(label, key=f"select_pet_{pid}", use_container_width=True, type=("primary" if is_selected else "secondary"), disabled=is_selected):
                    st.session_state["newrx_selected_pet"] = pid
                    st.session_state["newrx_parsed"] = None
                    st.rerun()

    return selected_pet if selected_pet in pet_ids else ""


def _step_compose(pet_id: str):
    pet = PETS[pet_id]

    st.markdown("")
    st.markdown(f"### Prescription for {pet['name']}")

    mode = st.segmented_control(
        "How would you like to build this?",
        options=["Describe in your own words", "Build manually"],
        default="Describe in your own words",
        key="newrx_mode",
    )

    rx_ready = False

    if mode == "Describe in your own words":
        rx_ready = _describe_section(pet)
    else:
        rx_ready = _manual_section(pet)

    if not rx_ready:
        return

    _autoship_section()
    _approval_section()
    _send_section()


def _describe_section(pet) -> bool:
    with st.container(border=True):
        st.markdown("**Describe the prescription**")
        st.caption("Type, paste a clinical note, or dictate. We'll structure it for you below.")
        note = st.text_area(
            "Description",
            placeholder=f"e.g. {pet['name']} doing well on apoquel, continue 16mg once daily, 30 tabs, 3 refills",
            height=140,
            label_visibility="collapsed",
            key="newrx_note",
        )
        c1, _ = st.columns([0.3, 0.7])
        with c1:
            if st.button("Extract & structure", type="primary", use_container_width=True, disabled=not note.strip(), key="newrx_extract"):
                with st.spinner("Reading..."):
                    st.session_state["newrx_parsed"] = _parse(note)

    parsed = st.session_state.get("newrx_parsed")
    if not parsed:
        return False

    st.markdown("")
    with st.container(border=True):
        st.markdown("**Structured rx — review and edit**")

        # Map parsed drug to catalog
        product_names = [p["name"] for p in PRODUCTS]
        matched_drug = _match_drug(parsed.get("drug"), product_names)
        drug_idx = product_names.index(matched_drug) + 1 if matched_drug else 0

        if parsed.get("drug") and not matched_drug:
            st.caption(f":orange[⚠ Couldn't match '{parsed.get('drug')}' to the catalog — pick the closest match below.]")

        drug = st.selectbox("Drug", options=[""] + product_names, index=drug_idx, key="newrx_drug")

        if not drug:
            return False

        product = next(p for p in PRODUCTS if p["name"] == drug)

        # Map parsed strength to product's available strengths
        matched_strength = _match_strength(parsed.get("strength"), product["strengths"])
        strength_idx = product["strengths"].index(matched_strength) if matched_strength else 0

        c1, c2 = st.columns(2)
        with c1:
            st.selectbox("Strength", options=product["strengths"], index=strength_idx, key="newrx_strength")
            st.text_input("Retail price range", value=product["price_range"], disabled=True, key="newrx_price")
        with c2:
            qty = st.number_input("Quantity per fill", min_value=1, value=int(parsed.get("qty") or 30), key="newrx_qty")
            refills = st.number_input("Refills", min_value=0, max_value=12, value=int(parsed.get("refills") or 3), key="newrx_refills")

        # Detect taper mode from parsed phases
        parsed_phases = parsed.get("phases")
        if parsed_phases and "newrx_taper_mode" not in st.session_state:
            st.session_state["newrx_taper_mode"] = True
            # Seed phases from parse
            st.session_state["newrx_phases_list"] = [
                {
                    "id": f"p{i+1}",
                    "dose_amount": float(p.get("dose_amount") or 1.0),
                    "frequency": p.get("frequency") if p.get("frequency") in FREQUENCY_OPTIONS else "Once daily",
                    "duration_days": int(p.get("duration_days") or 0),
                    "ongoing": bool(p.get("ongoing", i == len(parsed_phases) - 1)),
                }
                for i, p in enumerate(parsed_phases)
            ]
            st.session_state["newrx_next_phase_id"] = len(parsed_phases) + 1

        # Seed single-phase values from parse (only once)
        if "newrx_dose_amount" not in st.session_state:
            st.session_state["newrx_dose_amount"] = float(parsed.get("dose_amount") or 1.0)
        if "newrx_dose_freq" not in st.session_state:
            st.session_state["newrx_dose_freq"] = parsed.get("dose_frequency") if parsed.get("dose_frequency") in FREQUENCY_OPTIONS else "Once daily"
        if "newrx_instr" not in st.session_state:
            st.session_state["newrx_instr"] = parsed.get("instructions") or _generate_dose_text(st.session_state["newrx_dose_amount"], st.session_state["newrx_dose_freq"])

        taper_mode = st.checkbox("Multi-phase / tapered prescription", key="newrx_taper_mode")

        if taper_mode:
            phases = _render_phases_ui("newrx")
            summary = _compute_taper_summary(phases)
            total_authorized = int(summary["first_fill"]) + int(refills) * int(summary["maintenance_per_cycle"])
            st.caption(
                f"**First fill:** {summary['first_fill']} units · **Maintenance per cycle:** {summary['maintenance_per_cycle']} units · "
                f"**Total authorized:** {total_authorized} units (first fill + {refills} refills × maintenance qty)"
            )
            # Auto-generate label instructions from phases — only if vet hasn't customized
            if summary["label_instructions"] and not st.session_state.get("newrx_instr_customized", False):
                st.session_state["newrx_instr"] = summary["label_instructions"]
        else:
            # Dose fields (with bidirectional sync)
            d1, d2 = st.columns(2)
            with d1:
                dose_amount = st.number_input(
                    "Dose amount (per administration)",
                    min_value=0.0, step=0.5,
                    key="newrx_dose_amount",
                    on_change=_on_dose_freq_change, args=("newrx",),
                )
            with d2:
                freq = st.selectbox(
                    "Frequency", options=FREQUENCY_OPTIONS,
                    key="newrx_dose_freq",
                    on_change=_on_dose_freq_change, args=("newrx",),
                )

            total = int(qty) * (int(refills) + 1)
            daily = FREQUENCY_MULTIPLIER.get(freq)
            if daily and dose_amount:
                daily_units = daily * dose_amount
                days_of_supply = int(total / daily_units) if daily_units else None
                st.caption(f"**Total prescribed:** {total} units across {refills + 1} fill{'s' if refills + 1 != 1 else ''} · **Days of supply:** {days_of_supply} days at {daily_units:g} units/day")
            else:
                st.caption(f"**Total prescribed:** {total} units across {refills + 1} fill{'s' if refills + 1 != 1 else ''}")

        instr_help = "Auto-generated from phases — edit freely to add 'with food', 'do not crush', etc." if taper_mode else None
        st.text_area(
            "Instructions (printed on label)",
            height=80,
            key="newrx_instr",
            on_change=_on_instructions_change, args=("newrx",),
            help=instr_help,
        )

        # Show regenerate option if vet has customized in taper mode
        if taper_mode and st.session_state.get("newrx_instr_customized", False):
            cap_c1, cap_c2 = st.columns([0.7, 0.3])
            with cap_c1:
                st.caption(":orange[Custom instructions — auto-sync from phases is paused.]")
            with cap_c2:
                if st.button("↻ Regenerate from phases", key="newrx_regen_instr", use_container_width=True):
                    st.session_state["newrx_instr_customized"] = False
                    st.session_state["newrx_instr"] = _compute_taper_summary(st.session_state["newrx_phases_list"])["label_instructions"]
                    st.rerun()

        st.text_area("Pharmacy notes (optional)", value=parsed.get("pharmacy_notes") or "", height=80, key="newrx_pharma")

    return True


def _phase_label(dose, freq, duration, ongoing) -> str:
    if dose == 0.5:
        amount = "1/2 tablet"
    elif dose == 1.0:
        amount = "1 tablet"
    elif dose == int(dose):
        amount = f"{int(dose)} tablets"
    else:
        amount = f"{dose:g} tablets"
    base = f"Give {amount} by mouth {freq.lower()}"
    return base + " ongoing" if ongoing else base + f" for {duration} days"


def _compute_taper_summary(phases: list, maintenance_cycle_days: int = 30) -> dict:
    """Given a list of phase dicts, compute first-fill, maintenance qty, and label instructions."""
    first_fill = 0
    maintenance_per_cycle = 0
    parts = []
    for i, phase in enumerate(phases):
        dose = phase.get("dose_amount", 0) or 0
        freq = phase.get("frequency", "")
        duration = phase.get("duration_days", 0) or 0
        ongoing = phase.get("ongoing", False)
        daily_mult = FREQUENCY_MULTIPLIER.get(freq) or 0
        if ongoing:
            cycle_qty = int(daily_mult * dose * maintenance_cycle_days)
            maintenance_per_cycle = cycle_qty
            first_fill += cycle_qty
            label = _phase_label(dose, freq, None, ongoing=True)
        else:
            phase_qty = int(daily_mult * dose * duration)
            first_fill += phase_qty
            label = _phase_label(dose, freq, duration, ongoing=False)
        # Strip leading "Give " from subsequent phases so the joined label reads naturally
        if i > 0 and label.startswith("Give "):
            label = label[5:]
        parts.append(label)
    return {
        "first_fill": first_fill,
        "maintenance_per_cycle": maintenance_per_cycle,
        "label_instructions": ", then ".join(parts),
    }


def _render_phases_ui(prefix: str):
    """Render dynamic multi-phase UI for tapered prescriptions."""
    phases_key = f"{prefix}_phases_list"
    next_id_key = f"{prefix}_next_phase_id"

    if phases_key not in st.session_state:
        st.session_state[phases_key] = [
            {"id": "p1", "dose_amount": 1.0, "frequency": "Twice daily", "duration_days": 14, "ongoing": False},
            {"id": "p2", "dose_amount": 1.0, "frequency": "Once daily", "duration_days": 0, "ongoing": True},
        ]
        st.session_state[next_id_key] = 3

    phases = st.session_state[phases_key]

    for i, phase in enumerate(phases):
        pid = phase["id"]
        with st.container(border=True):
            header_c1, header_c2 = st.columns([0.8, 0.2])
            with header_c1:
                phase_label = f"**Phase {i+1}**" + (" — maintenance, ongoing" if phase["ongoing"] else "")
                st.markdown(phase_label)
            with header_c2:
                if len(phases) > 1:
                    if st.button("Remove", key=f"{prefix}_remove_{pid}", use_container_width=True):
                        was_ongoing = phase["ongoing"]
                        phases.pop(i)
                        # If we removed the ongoing phase, make new last phase ongoing
                        if was_ongoing and phases:
                            phases[-1]["ongoing"] = True
                            phases[-1]["duration_days"] = 0
                        st.rerun()

            dose_key = f"{prefix}_phase_{pid}_dose"
            freq_key = f"{prefix}_phase_{pid}_freq"
            duration_key = f"{prefix}_phase_{pid}_duration"

            if dose_key not in st.session_state:
                st.session_state[dose_key] = phase["dose_amount"]
            if freq_key not in st.session_state:
                st.session_state[freq_key] = phase["frequency"]
            if duration_key not in st.session_state and not phase["ongoing"]:
                st.session_state[duration_key] = phase["duration_days"] or 7

            c1, c2, c3 = st.columns(3)
            with c1:
                st.number_input("Dose amount", min_value=0.0, step=0.5, key=dose_key)
            with c2:
                st.selectbox("Frequency", options=FREQUENCY_OPTIONS, key=freq_key)
            with c3:
                if phase["ongoing"]:
                    st.markdown("")
                    st.caption("Ongoing (autoship continues until refills used)")
                else:
                    st.number_input("Duration (days)", min_value=1, key=duration_key)

            # Sync widget values back to phase dict
            phase["dose_amount"] = st.session_state[dose_key]
            phase["frequency"] = st.session_state[freq_key]
            if not phase["ongoing"] and duration_key in st.session_state:
                phase["duration_days"] = st.session_state[duration_key]

    if st.button("+ Add phase", key=f"{prefix}_add_phase_btn"):
        # Demote current ongoing phase to finite, then append new ongoing
        for p in phases:
            if p["ongoing"]:
                p["ongoing"] = False
                p["duration_days"] = p.get("duration_days") or 7
        new_id = f"p{st.session_state[next_id_key]}"
        st.session_state[next_id_key] += 1
        phases.append({"id": new_id, "dose_amount": 1.0, "frequency": "Once daily", "duration_days": 0, "ongoing": True})
        st.rerun()

    return phases


def _parse_dose_text(text: str) -> dict:
    """Extract dose_amount and dose_frequency from free-text instructions."""
    if not text:
        return {}
    lower = text.lower()
    result = {}

    # Dose amount — match numbers followed by common dose units
    if "1/2" in lower or "half" in lower or "0.5" in lower:
        result["dose_amount"] = 0.5
    else:
        m = re.search(r"(\d+(?:\.\d+)?)\s*(tab|tablet|chew|cap|capsule|pill|drop|puff|spray|ml|mg|unit)", lower)
        if m:
            result["dose_amount"] = float(m.group(1))

    # Frequency — most specific patterns first
    if (
        "twice" in lower or " bid" in lower or "q12h" in lower or "every 12" in lower
        or "morning and night" in lower or "morning and evening" in lower
        or "am and pm" in lower or "a.m. and p.m." in lower
    ):
        result["dose_frequency"] = "Twice daily"
    elif "three times" in lower or " tid" in lower or "q8h" in lower or "every 8 hour" in lower:
        result["dose_frequency"] = "Three times daily"
    elif "every other day" in lower or "qod" in lower or "every 2 days" in lower:
        result["dose_frequency"] = "Every other day"
    elif "as needed" in lower or " prn" in lower:
        result["dose_frequency"] = "As needed"
    elif (
        "once daily" in lower or "once a day" in lower or " sid" in lower or " qd" in lower
        or "daily" in lower
        or "at night" in lower or "at bedtime" in lower or "before bed" in lower
        or "in the morning" in lower or "every morning" in lower or "every evening" in lower
        or "every night" in lower
    ):
        result["dose_frequency"] = "Once daily"

    return result


def _generate_dose_text(dose_amount, freq) -> str:
    """Generate label-friendly instructions from dose and frequency."""
    if not dose_amount or not freq or freq == "As needed":
        return ""
    if dose_amount == 0.5:
        amount = "1/2 tablet"
    elif dose_amount == 1.0:
        amount = "1 tablet"
    elif dose_amount == int(dose_amount):
        amount = f"{int(dose_amount)} tablets"
    else:
        amount = f"{dose_amount:g} tablets"
    return f"Give {amount} by mouth {freq.lower()}"


def _on_instructions_change(prefix: str):
    """When the vet edits instructions, parse dose + frequency from it AND mark as customized."""
    text = st.session_state.get(f"{prefix}_instr", "")
    # Mark as customized so taper auto-generation doesn't overwrite
    st.session_state[f"{prefix}_instr_customized"] = True
    parsed = _parse_dose_text(text)
    if parsed.get("dose_amount") is not None:
        st.session_state[f"{prefix}_dose_amount"] = parsed["dose_amount"]
    if parsed.get("dose_frequency"):
        st.session_state[f"{prefix}_dose_freq"] = parsed["dose_frequency"]


def _on_dose_freq_change(prefix: str):
    """When the vet changes dose or frequency, regenerate instructions —
    but only if the current instructions look auto-generated (don't overwrite custom notes)."""
    dose = st.session_state.get(f"{prefix}_dose_amount")
    freq = st.session_state.get(f"{prefix}_dose_freq")
    generated = _generate_dose_text(dose, freq)
    if not generated:
        return
    current = st.session_state.get(f"{prefix}_instr", "").strip()
    # Only overwrite if empty or starts with a known auto-generated pattern
    if not current or current.startswith("Give "):
        st.session_state[f"{prefix}_instr"] = generated


def _match_drug(parsed_drug: str, catalog_names: list) -> str:
    """Fuzzy match a parsed drug name to a catalog product."""
    if not parsed_drug:
        return None
    parsed_lower = parsed_drug.lower().strip()
    # Exact match first
    for name in catalog_names:
        if name.lower() == parsed_lower:
            return name
    # Substring match: catalog name contains parsed name, or vice versa
    for name in catalog_names:
        if parsed_lower in name.lower() or name.lower() in parsed_lower:
            return name
    # Word-level match
    parsed_words = set(parsed_lower.split())
    for name in catalog_names:
        if parsed_words & set(name.lower().split()):
            return name
    return None


def _match_strength(parsed_strength: str, available: list) -> str:
    """Match parsed strength against available strengths."""
    if not parsed_strength:
        return None
    parsed_lower = parsed_strength.lower().strip().replace(" ", "")
    for s in available:
        if s.lower().replace(" ", "") == parsed_lower:
            return s
    for s in available:
        if parsed_lower in s.lower().replace(" ", "") or s.lower().replace(" ", "") in parsed_lower:
            return s
    return None


def _manual_section(pet) -> bool:
    with st.container(border=True):
        st.markdown("**Build the prescription**")

        product_names = [p["name"] for p in PRODUCTS]
        drug = st.selectbox("Drug", options=[""] + product_names, key="newrx_m_drug")

        if not drug:
            return False

        product = next(p for p in PRODUCTS if p["name"] == drug)

        c1, c2 = st.columns(2)
        with c1:
            st.selectbox("Strength", options=product["strengths"], key="newrx_m_strength")
        with c2:
            st.text_input("Retail price range", value=product["price_range"], disabled=True, key="newrx_m_price")

        c3, c4 = st.columns(2)
        with c3:
            qty = st.number_input("Quantity per fill", min_value=1, value=30, key="newrx_m_qty")
        with c4:
            refills = st.number_input("Refills", min_value=0, max_value=12, value=3, key="newrx_m_refills")

        # Seed defaults on first render
        if "newrx_m_dose_amount" not in st.session_state:
            st.session_state["newrx_m_dose_amount"] = 1.0
        if "newrx_m_dose_freq" not in st.session_state:
            st.session_state["newrx_m_dose_freq"] = "Once daily"
        if "newrx_m_instr" not in st.session_state:
            st.session_state["newrx_m_instr"] = _generate_dose_text(1.0, "Once daily")

        taper_mode = st.checkbox("Multi-phase / tapered prescription", key="newrx_m_taper_mode")

        if taper_mode:
            phases = _render_phases_ui("newrx_m")
            summary = _compute_taper_summary(phases)
            total_authorized = int(summary["first_fill"]) + int(refills) * int(summary["maintenance_per_cycle"])
            st.caption(
                f"**First fill:** {summary['first_fill']} units · **Maintenance per cycle:** {summary['maintenance_per_cycle']} units · "
                f"**Total authorized:** {total_authorized} units (first fill + {refills} refills × maintenance qty)"
            )
            if summary["label_instructions"] and not st.session_state.get("newrx_m_instr_customized", False):
                st.session_state["newrx_m_instr"] = summary["label_instructions"]
        else:
            # Dose fields (with bidirectional sync)
            d1, d2 = st.columns(2)
            with d1:
                dose_amount = st.number_input(
                    "Dose amount (per administration)",
                    min_value=0.0, step=0.5,
                    key="newrx_m_dose_amount",
                    on_change=_on_dose_freq_change, args=("newrx_m",),
                )
            with d2:
                freq = st.selectbox(
                    "Frequency", options=FREQUENCY_OPTIONS,
                    key="newrx_m_dose_freq",
                    on_change=_on_dose_freq_change, args=("newrx_m",),
                )

            total = int(qty) * (int(refills) + 1)
            daily = FREQUENCY_MULTIPLIER.get(freq)
            if daily and dose_amount:
                daily_units = daily * dose_amount
                days_of_supply = int(total / daily_units) if daily_units else None
                st.caption(f"**Total prescribed:** {total} units across {refills + 1} fill{'s' if refills + 1 != 1 else ''} · **Days of supply:** {days_of_supply} days at {daily_units:g} units/day")
            else:
                st.caption(f"**Total prescribed:** {total} units across {refills + 1} fill{'s' if refills + 1 != 1 else ''}")

        instr_help_m = "Auto-generated from phases — edit freely to add 'with food', 'do not crush', etc." if taper_mode else None
        st.text_area(
            "Instructions (printed on label)",
            height=80,
            key="newrx_m_instr",
            on_change=_on_instructions_change, args=("newrx_m",),
            help=instr_help_m,
        )

        if taper_mode and st.session_state.get("newrx_m_instr_customized", False):
            cap_c1, cap_c2 = st.columns([0.7, 0.3])
            with cap_c1:
                st.caption(":orange[Custom instructions — auto-sync from phases is paused.]")
            with cap_c2:
                if st.button("↻ Regenerate from phases", key="newrx_m_regen_instr", use_container_width=True):
                    st.session_state["newrx_m_instr_customized"] = False
                    st.session_state["newrx_m_instr"] = _compute_taper_summary(st.session_state["newrx_m_phases_list"])["label_instructions"]
                    st.rerun()

        st.text_area("Pharmacy notes (optional)", placeholder="Notes for the pharmacist...", height=80, key="newrx_m_pharma")

    return True


def _autoship_section():
    st.markdown("")
    with st.container(border=True):
        st.markdown("**AutoShip**")
        st.caption("Set up automatic recurring shipments. The client can also adjust this from their checkout.")

        autoship = st.checkbox("Set this up as an AutoShip", key="newrx_autoship")

        if autoship:
            c1, c2 = st.columns(2)
            with c1:
                st.selectbox(
                    "Frequency",
                    options=["Weekly", "Every 2 weeks", "Every 3 weeks", "Monthly", "Every 2 months", "Every 3 months"],
                    index=3,
                    key="newrx_autoship_freq",
                )
            with c2:
                st.date_input("First ship date", value=date.today(), key="newrx_autoship_start")


def _approval_section():
    st.markdown("")
    with st.container(border=True):
        st.markdown("**Approval**")
        st.caption("Enter your name and PIN to pre-approve and skip the queue. Otherwise it goes to the approval queue.")
        c1, c2 = st.columns(2)
        with c1:
            st.selectbox("Prescribing vet", options=["", CURRENT_USER["name"]], key="newrx_vet")
        with c2:
            st.text_input("PIN", type="password", placeholder="4-digit PIN", key="newrx_pin")


def _send_section():
    st.markdown("")
    c1, c2, _ = st.columns([0.3, 0.3, 0.4])
    with c1:
        if st.button("Send to Ruffy", type="primary", use_container_width=True, key="newrx_send"):
            vet = st.session_state.get("newrx_vet")
            pin = st.session_state.get("newrx_pin")
            if vet and pin:
                st.success("Pre-approved and sent to Ruffy pharmacy.")
            else:
                st.info("Sent to the approval queue. A vet will need to approve before it ships.")
    with c2:
        st.button("Save as draft", use_container_width=True, key="newrx_draft")


def _parse(note: str) -> dict:
    # Try Streamlit Cloud secrets first, fall back to env var
    api_key = ""
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        pass
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return _mock_parse(note)
    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": note}],
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except Exception:
        return _mock_parse(note)


def _mock_parse(note: str) -> dict:
    lower = note.lower()
    drug = None
    if "apoquel" in lower:
        drug = "Apoquel Chewable"
    elif "carprofen" in lower:
        drug = "Carprofen Tablets"
    elif "cerenia" in lower:
        drug = "Cerenia Tablets"
    elif "nexgard" in lower:
        drug = "NexGard Chewables"
    elif "mirtazapine" in lower:
        drug = "Mirtazapine Tablets"

    frequency = None
    if "twice daily" in lower or "twice a day" in lower or "bid" in lower:
        frequency = "Twice daily"
    elif "three times" in lower or "tid" in lower:
        frequency = "Three times daily"
    elif "every other day" in lower or "qod" in lower:
        frequency = "Every other day"
    elif "as needed" in lower or "prn" in lower:
        frequency = "As needed"
    elif "once daily" in lower or "once a day" in lower or "sid" in lower or "qd" in lower or "daily" in lower:
        frequency = "Once daily"

    # Multi-phase detection: presence of "then", "taper", "for X days" suggests phases
    phases = None
    if "then" in lower and ("days" in lower or "ongoing" in lower or "daily" in lower):
        phases = _mock_extract_phases(lower)

    return {
        "drug": drug,
        "strength": "16 mg" if "16" in lower else ("75 mg" if "75" in lower else None),
        "qty": 30 if "30" in lower else None,
        "refills": 3 if "3 refill" in lower or "3 more" in lower else None,
        "dose_amount": None if phases else (1.0 if "1 tab" in lower or "one tab" in lower else (0.5 if "1/2" in lower or "half" in lower else None)),
        "dose_frequency": None if phases else frequency,
        "phases": phases,
        "instructions": None if phases else ("Give 1 tablet by mouth once daily" if "apoquel" in lower else None),
        "pharmacy_notes": None,
    }


def _mock_extract_phases(text_lower: str) -> list:
    """Very rough mock taper parser. Splits on 'then' and tries to extract per-phase info."""
    segments = re.split(r"\bthen\b", text_lower)
    if len(segments) < 2:
        return None

    phases = []
    for i, seg in enumerate(segments):
        # Dose amount
        if "1/2" in seg or "half" in seg:
            dose = 0.5
        else:
            m = re.search(r"(\d+(?:\.\d+)?)\s*(tab|tablet|chew|cap|capsule|pill|drop|ml)", seg)
            dose = float(m.group(1)) if m else 1.0

        # Frequency
        if "twice" in seg or "bid" in seg or "every 12" in seg or "q12h" in seg:
            freq = "Twice daily"
        elif "three times" in seg or "tid" in seg or "every 8" in seg or "q8h" in seg:
            freq = "Three times daily"
        elif "every other day" in seg or "qod" in seg:
            freq = "Every other day"
        else:
            freq = "Once daily"

        # Duration
        m = re.search(r"for\s+(\d+)\s+day", seg)
        duration = int(m.group(1)) if m else None

        ongoing = ("ongoing" in seg) or (i == len(segments) - 1 and not duration)

        phases.append({
            "dose_amount": dose,
            "frequency": freq,
            "duration_days": duration,
            "ongoing": ongoing,
        })

    return phases
