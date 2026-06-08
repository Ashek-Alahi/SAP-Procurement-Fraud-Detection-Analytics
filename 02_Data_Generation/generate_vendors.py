"""Generate SAP-like vendor master data for a Japanese hospitality company.

Output: 03_Data/vendors.csv
SAP context: LFA1/LFB1 vendor master data created through XK01/BP.
"""

from __future__ import annotations

from datetime import date

from inject_fraud_patterns import DATA_DIR, PAYMENT_TERMS, VENDOR_CATEGORIES, iso, random_date, rng, write_csv

FIELDNAMES = [
    "vendor_id",
    "vendor_name",
    "bank_account_number",
    "registration_date",
    "payment_terms",
    "vendor_category",
    "contact_person",
    "is_active",
    "is_ghost_vendor",
    "similar_to_vendor",
]

LEGITIMATE_VENDORS = [
    ("Sakura Seafood Co.", "FOOD"),
    ("Hokkaido Dairy Supply", "FOOD"),
    ("Kansai Linen Service", "LINN"),
    ("Nippon Facility Maintenance", "MAIN"),
    ("Tokyo Guest Services", "SERV"),
    ("Kyoto Organic Farms", "FOOD"),
    ("Osaka Beverage Trading", "FOOD"),
    ("Fuji Laundry Partners", "LINN"),
    ("Nagoya HVAC Engineering", "MAIN"),
    ("Yokohama Security Services", "SERV"),
    ("Setouchi Fish Market", "FOOD"),
    ("Aomori Apple Growers", "FOOD"),
    ("Kobe Premium Linens", "LINN"),
    ("Shizuoka Electrical Works", "MAIN"),
    ("Nara Cultural Events", "SERV"),
    ("Okinawa Tropical Produce", "FOOD"),
    ("Miyagi Dry Goods", "FOOD"),
    ("Chiba Housekeeping Supply", "LINN"),
    ("Sapporo Kitchen Equipment", "MAIN"),
    ("Hiroshima IT Support", "SERV"),
    ("Kumamoto Wagyu Foods", "FOOD"),
    ("Ehime Citrus Cooperative", "FOOD"),
    ("Sendai Linen Works", "LINN"),
    ("Fukuoka Plumbing Systems", "MAIN"),
    ("Hakone Spa Consultants", "SERV"),
    ("Tsukiji Premium Foods", "FOOD"),
    ("Nagano Mountain Vegetables", "FOOD"),
    ("Biwa Resort Textiles", "LINN"),
    ("Karuizawa Maintenance Crew", "MAIN"),
    ("Shonan Event Staffing", "SERV"),
    ("Toyama Seafood Logistics", "FOOD"),
    ("Ibaraki Rice Mills", "FOOD"),
    ("Mie Towel Service", "LINN"),
    ("Ginza Elevator Maintenance", "MAIN"),
    ("Roppongi Translation Services", "SERV"),
    ("Akita Sake Distributors", "FOOD"),
    ("Yamanashi Wine Merchants", "FOOD"),
    ("Izumo Linen Rental", "LINN"),
    ("Kagoshima Boiler Service", "MAIN"),
    ("Daikanyama Design Studio", "SERV"),
    ("Narita Import Foods", "FOOD"),
    ("Uji Tea Suppliers", "FOOD"),
    ("Toba Room Amenities", "LINN"),
    ("Asakusa Carpentry Works", "MAIN"),
    ("Kamakura Concierge Agency", "SERV"),
]

GHOST_VENDOR_MAP = [
    ("Sakura Seafoods Co.", "VEND001"),
    ("Hokkaido Dairy Supplies", "VEND002"),
    ("Kansai Linen Servise", "VEND003"),
    ("Nippon Facility Maint.", "VEND004"),
    ("Tokyo Guest Service KK", "VEND005"),
]

CONTACT_GIVEN = ["Haruto", "Yui", "Ren", "Sakura", "Minato", "Aoi", "Riku", "Mei", "Sota", "Hina"]
CONTACT_FAMILY = ["Tanaka", "Sato", "Suzuki", "Takahashi", "Watanabe", "Ito", "Yamamoto", "Nakamura"]


def make_bank_account(index: int, duplicate_from: str | None = None) -> str:
    if duplicate_from:
        return duplicate_from
    return f"JP{1000 + index:04d}-{2000000 + index * 7919:07d}"


def generate_vendors() -> list[dict[str, object]]:
    randomizer = rng(10)
    rows: list[dict[str, object]] = []
    start = date(2023, 1, 1)
    end = date(2025, 10, 31)

    for index, (name, category) in enumerate(LEGITIMATE_VENDORS, start=1):
        rows.append(
            {
                "vendor_id": f"VEND{index:03d}",
                "vendor_name": name,
                "bank_account_number": make_bank_account(index),
                "registration_date": iso(random_date(randomizer, start, end)),
                "payment_terms": randomizer.choice(PAYMENT_TERMS),
                "vendor_category": category,
                "contact_person": f"{randomizer.choice(CONTACT_GIVEN)} {randomizer.choice(CONTACT_FAMILY)}",
                "is_active": "False" if index in {18, 34} else "True",
                "is_ghost_vendor": "False",
                "similar_to_vendor": "",
            }
        )

    for offset, (ghost_name, linked_vendor) in enumerate(GHOST_VENDOR_MAP, start=46):
        linked = rows[int(linked_vendor[-3:]) - 1]
        duplicate_bank = linked["bank_account_number"] if offset in {46, 48} else None
        rows.append(
            {
                "vendor_id": f"VEND{offset:03d}",
                "vendor_name": ghost_name,
                "bank_account_number": make_bank_account(offset, duplicate_bank),
                "registration_date": iso(random_date(randomizer, date(2025, 10, 1), date(2025, 12, 15))),
                "payment_terms": linked["payment_terms"],
                "vendor_category": linked["vendor_category"],
                "contact_person": f"{randomizer.choice(CONTACT_GIVEN)} {randomizer.choice(CONTACT_FAMILY)}",
                "is_active": "True",
                "is_ghost_vendor": "True",
                "similar_to_vendor": linked_vendor,
            }
        )

    return rows


if __name__ == "__main__":
    vendors = generate_vendors()
    write_csv(DATA_DIR / "vendors.csv", vendors, FIELDNAMES)
    print(f"Generated {len(vendors)} vendors at {DATA_DIR / 'vendors.csv'}")
