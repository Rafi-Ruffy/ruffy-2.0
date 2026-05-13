"""
Mock data for the Ruffy 2.0 clinic portal prototype.
All invented. No connection to live Ruffy data.
"""

CLINIC = {
    "name": "Bayview Veterinary Hospital",
    "city": "Toronto, ON",
}

CURRENT_USER = {
    "name": "Dr. Sarah Chen",
    "role": "Veterinarian",
    "initials": "SC",
}

CLIENTS = {
    "c1": {
        "id": "c1", "name": "Olivia Hart", "phone": "(416) 555-2734",
        "email": "olivia.hart@gmail.com", "address": "44 Roncesvalles Ave, Toronto ON",
        "pets": ["pet1"],
    },
    "c2": {
        "id": "c2", "name": "Darren Cole", "phone": "(416) 555-4912",
        "email": "darren.cole@gmail.com", "address": "118 Ossington Ave, Toronto ON",
        "pets": ["pet2"],
    },
    "c3": {
        "id": "c3", "name": "Jasmine Monroe", "phone": "(416) 555-8821",
        "email": "jasmine.monroe@gmail.com", "address": "302 Queen St W, Toronto ON",
        "pets": ["pet3"],
    },
    "c4": {
        "id": "c4", "name": "Nina Walsh", "phone": "(416) 555-2237",
        "email": "nina.walsh@gmail.com", "address": "55 Yonge St, Toronto ON",
        "pets": ["pet4"],
    },
    "c5": {
        "id": "c5", "name": "Marcus Reed", "phone": "(416) 555-7627",
        "email": "marcus.reed@gmail.com", "address": "421 Spadina Ave, Toronto ON",
        "pets": ["pet5", "pet6"],
    },
    "c6": {
        "id": "c6", "name": "Jessica Ashley", "phone": "(416) 555-9001",
        "email": "jashley@gmail.com", "address": "12 Roxborough Dr, Toronto ON",
        "pets": ["pet7"],
    },
}

PETS = {
    "pet1": {"id": "pet1", "name": "Jellybean", "species": "Canine", "breed": "French Bulldog", "weight_lbs": 22.4, "age": "3 years", "client_id": "c1"},
    "pet2": {"id": "pet2", "name": "Sadie", "species": "Canine", "breed": "Labrador Retriever", "weight_lbs": 64.0, "age": "7 years", "client_id": "c2"},
    "pet3": {"id": "pet3", "name": "Nacho", "species": "Feline", "breed": "Domestic Shorthair", "weight_lbs": 11.2, "age": "5 years", "client_id": "c3"},
    "pet4": {"id": "pet4", "name": "Yumi", "species": "Feline", "breed": "Ragdoll", "weight_lbs": 9.6, "age": "2 years", "client_id": "c4"},
    "pet5": {"id": "pet5", "name": "Bear", "species": "Canine", "breed": "Bernese Mountain Dog", "weight_lbs": 92.5, "age": "8 years", "client_id": "c5"},
    "pet6": {"id": "pet6", "name": "Mabel", "species": "Feline", "breed": "Maine Coon", "weight_lbs": 14.2, "age": "6 years", "client_id": "c5"},
    "pet7": {"id": "pet7", "name": "Nala", "species": "Feline", "breed": "Bengal", "weight_lbs": 6.7, "age": "4 years", "client_id": "c6"},
}

DENY_REASONS = [
    "Incorrect product, strength, or quantity",
    "Pet due for exam or test",
    "Pet passed away or rehomed",
    "Not clinically appropriate",
    "Other",
]

ORDERS = [
    {
        "id": "OJ40Z", "date": "May 12, 2026", "client_id": "c1", "pet_id": "pet1",
        "drug": "Apoquel Chewable", "strength": "16 mg", "qty": 30,
        "status": "Awaiting payment", "total": "$89.79",
    },
    {
        "id": "WC43E", "date": "May 11, 2026", "client_id": "c2", "pet_id": "pet2",
        "drug": "NexGard Chewables", "strength": "Large (24–60 lbs)", "qty": 3,
        "status": "Shipped", "total": "$74.50",
    },
    {
        "id": "I21V5", "date": "May 11, 2026", "client_id": "c3", "pet_id": "pet3",
        "drug": "Mirtazapine Tablets", "strength": "15 mg", "qty": 30,
        "status": "Delivered", "total": "$42.10",
    },
    {
        "id": "VIPLD", "date": "May 10, 2026", "client_id": "c4", "pet_id": "pet4",
        "drug": "Hill's Prescription Diet c/d", "strength": "8.5 lb bag", "qty": 1,
        "status": "Shipped", "total": "$56.99",
    },
    {
        "id": "K78XQ", "date": "May 9, 2026", "client_id": "c5", "pet_id": "pet5",
        "drug": "Carprofen Tablets", "strength": "75 mg", "qty": 60,
        "status": "Delivered", "total": "$48.25",
    },
    {
        "id": "B41WM", "date": "May 8, 2026", "client_id": "c6", "pet_id": "pet7",
        "drug": "Apoquel Chewable", "strength": "16 mg", "qty": 30,
        "status": "Delivered", "total": "$89.79",
    },
]

RENEWALS = [
    {
        "id": "rn1",
        "source": "autoship",  # system-initiated
        "received": "Today, 6:00 AM (system)",
        "client_id": "c1", "pet_id": "pet1",
        "drug": "Apoquel Chewable", "strength": "16 mg", "qty": 30, "refills_requested": 3,
        "previous_rx": "Original rx written Jan 12, 2026 · 4 fills dispensed · 28 days of runway before next ship",
        "autoship_context": "Active monthly AutoShip since Jan 20. 4 of 4 cycles shipped on time. No payment issues.",
    },
    {
        "id": "rn2",
        "source": "autoship",
        "received": "Yesterday, 6:00 AM (system)",
        "client_id": "c5", "pet_id": "pet5",
        "drug": "Carprofen Tablets", "strength": "75 mg", "qty": 60, "refills_requested": 3,
        "previous_rx": "Original rx written Nov 8, 2025 · 5 fills dispensed · 12 days of runway before next ship",
        "autoship_context": "Bi-monthly AutoShip since Nov 12. 5 of 5 cycles shipped on time.",
    },
    {
        "id": "rn3",
        "source": "client",  # client-initiated
        "received": "Today, 9:14 AM",
        "client_id": "c6", "pet_id": "pet7",
        "drug": "Apoquel Chewable", "strength": "16 mg", "qty": 30, "refills_requested": 3,
        "previous_rx": "Original rx written Jan 15, 2026 · 4 fills dispensed · no refills remaining",
        "autoship_context": None,
    },
]

PRODUCTS = [
    {"name": "Apoquel Chewable", "strengths": ["3.6 mg", "5.4 mg", "16 mg"], "price_range": "$89.79 – $299.09", "stock": "In stock"},
    {"name": "Apoquel Tablets", "strengths": ["3.6 mg", "5.4 mg", "16 mg"], "price_range": "$47.49 – $316.29", "stock": "Limited stock"},
    {"name": "NexGard Chewables", "strengths": ["Small", "Medium", "Large", "X-Large"], "price_range": "$58.00 – $84.00", "stock": "In stock"},
    {"name": "Carprofen Tablets", "strengths": ["25 mg", "75 mg", "100 mg"], "price_range": "$22.50 – $48.25", "stock": "In stock"},
    {"name": "Cerenia Tablets", "strengths": ["16 mg", "24 mg", "60 mg"], "price_range": "$38.99 – $112.50", "stock": "In stock"},
    {"name": "Mirtazapine Tablets", "strengths": ["7.5 mg", "15 mg", "30 mg"], "price_range": "$32.10 – $58.40", "stock": "In stock"},
    {"name": "Hill's Prescription Diet c/d", "strengths": ["4 lb", "8.5 lb", "17.6 lb"], "price_range": "$34.99 – $98.50", "stock": "In stock"},
    {"name": "Royal Canin Veterinary Diet Hydrolyzed Protein", "strengths": ["7.7 lb", "17.6 lb"], "price_range": "$78.50 – $156.00", "stock": "In stock"},
]
