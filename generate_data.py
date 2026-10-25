#!/usr/bin/env python3
"""
Neckarbohne GmbH – synthetische Quelldaten für das dbt-Lab (Tag 2) und die Labs an Tag 3 und 4.

Spielt die Rolle des Ingestion-Tools (EL): schreibt die Rohdaten der vier Quellsysteme als CSV
nach data/ und lädt sie unverändert in die Schemas shop, pos, billing und erp von neckarbohne.duckdb.
Das ist der Bronze-Layer. Alles Weitere macht dbt.

    python generate_data.py                      # Datenstand bis 2026-10-25 (Tag 2)
    python generate_data.py --until 2026-11-29   # späterer Datenstand (Tag 4)
    python generate_data.py --customer-update    # nächste Lieferung shop.customers (Stand 2026-10-26):
                                                 # 45 Umzüge, 15 neue E-Mail-Adressen – für den Snapshot

Die Daten sind deterministisch (Seed 2026): Gleicher Stichtag, gleiche Zahlen – auf jedem Laptop.
Ein späterer Stichtag verändert die Tage davor nicht. Nur Erstattungen, Zahlungen und Abo-Status
können sich mit dem Stichtag ändern, weil sie später passieren.

Eigenheiten, die absichtlich drin sind (Staging-Arbeit!):
  - shop.orders: Statuscodes statt Namen, Bruttobeträge inkl. MwSt., Zeitstempel als Text mit Offset,
    Dubletten aus einem wiederholten Ladelauf (Bestellungen vom 2026-10-10 und 2026-10-11)
  - pos.sales: deutsches Datumsformat, Lokalzeit ohne Zone, Bruttobeträge, keine Positionsnummer,
    Kassenkarten-IDs mal klein, mal mit Leerzeichen
  - billing.*: Abo- und Zahlungsanbieter mit eigenen Kunden-IDs (cus_…), E-Mails in anderer Schreibweise, Kündigungsdatum als TT.MM.JJJJ
  - erp.*: B2B-Kunden als Debitoren mit eigenen IDs
"""
import argparse
import csv
import datetime as dt
import random
import string
import zoneinfo
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
BERLIN = zoneinfo.ZoneInfo("Europe/Berlin")
UTC = dt.timezone.utc
START = dt.date(2025, 1, 1)
HORIZON = dt.date(2026, 11, 29)
SEED = 2026

FEIERTAGE_BW = {dt.date.fromisoformat(d) for d in [
    "2025-01-01", "2025-01-06", "2025-04-18", "2025-04-21", "2025-05-01", "2025-05-29", "2025-06-09",
    "2025-06-19", "2025-10-03", "2025-11-01", "2025-12-25", "2025-12-26",
    "2026-01-01", "2026-01-06", "2026-04-03", "2026-04-06", "2026-05-01", "2026-05-14", "2026-05-25",
    "2026-06-04", "2026-10-03", "2026-11-01", "2026-12-25", "2026-12-26"]}


def money(x) -> Decimal:
    return Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def iso_local(ts: dt.datetime) -> str:
    """Lokalzeit Europe/Berlin als ISO-Text mit Offset, z. B. 2026-10-20T09:30:00+02:00"""
    return ts.replace(tzinfo=BERLIN).isoformat(timespec="seconds")


def iso_utc(ts: dt.datetime) -> str:
    return ts.replace(tzinfo=BERLIN).astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


# ---------------------------------------------------------------- Stammdaten
PRODUCTS = [  # sku, title, sort, category, roast, list_price_net, unit_cost, vat_rate
    ("P-01", "Neckar Espresso 500 g", "Espresso", "beans", "dark", "16.90", "7.10", "0.07"),
    ("P-02", "Neckar Espresso 1 kg", "Espresso", "beans", "dark", "29.90", "13.20", "0.07"),
    ("P-03", "Filterkaffee Hausmischung 500 g", "Filter", "beans", "light", "12.90", "5.30", "0.07"),
    ("P-04", "Filter Äthiopien 500 g", "Filter", "beans", "light", "15.90", "7.80", "0.07"),
    ("P-05", "Entkoffeiniert 500 g", "Decaf", "beans", "medium", "14.50", "6.90", "0.07"),
    ("P-06", "Cold Brew Flasche 0,33 l", "Cold Brew", "drink", "medium", "3.90", "1.10", "0.19"),
    ("P-07", "Cappuccino (Café)", "Espresso", "drink", "dark", "3.60", "0.90", "0.19"),
    ("P-08", "Filterkaffee (Café)", "Filter", "drink", "light", "2.80", "0.50", "0.19"),
    ("P-09", "Espresso (Café)", "Espresso", "drink", "dark", "2.40", "0.40", "0.19"),
]
PROD = {p[0]: p for p in PRODUCTS}
PLANS = {  # plan, sku, monatlicher Preis netto
    "espresso_500": ("P-01", "15.90"),
    "filter_500": ("P-03", "11.90"),
    "espresso_1kg": ("P-02", "27.90"),
}
FIRST = ["Anna", "Ben", "Clara", "David", "Elif", "Felix", "Greta", "Hannes", "Ida", "Jonas", "Karla", "Luca",
         "Mia", "Noah", "Olga", "Paul", "Rosa", "Samir", "Tilda", "Umut", "Vera", "Wim", "Yara", "Zoe",
         "Lena", "Max", "Sophie", "Emil", "Leni", "Finn", "Ayşe", "Mehmet", "Jana", "Tim", "Nele", "Can"]
LAST = ["Müller", "Schmidt", "Weber", "Fischer", "Wagner", "Becker", "Schulz", "Hoffmann", "Koch", "Bauer",
        "Richter", "Klein", "Wolf", "Schröder", "Neumann", "Schwarz", "Braun", "Zimmermann", "Krüger",
        "Öztürk", "Yılmaz", "Kaya", "Hartmann", "Lange", "Werner", "Krause", "Lehmann", "Maier", "Huber"]
CITIES = [("Stuttgart", "70173", 30), ("Esslingen am Neckar", "73728", 9), ("Ludwigsburg", "71638", 8),
          ("Böblingen", "71032", 6), ("Tübingen", "72070", 6), ("Waiblingen", "71332", 5), ("Ulm", "89073", 4),
          ("Heilbronn", "74072", 4), ("Reutlingen", "72764", 4), ("Karlsruhe", "76133", 4), ("Mannheim", "68159", 3),
          ("Freiburg im Breisgau", "79098", 3), ("München", "80331", 3), ("Berlin", "10115", 3),
          ("Hamburg", "20095", 2), ("Köln", "50667", 2)]
DOMAINS = ["gmail.com", "web.de", "gmx.de", "outlook.de", "posteo.de", "t-online.de"]
CAFES = ["Café Zimt", "Kaffeehaus am Markt", "Rösterei-Bar Süd", "Bäckerei Hörnle", "Café Wilhelma",
         "Espresso Uno", "Kaffeekränzle", "Mokka & Milch", "Café Feuersee", "Bohne 42", "Hofcafé Degerloch",
         "Café Kornwestheim", "Stadtcafé Esslingen", "Café am Schloss", "Kiosk Marienplatz", "Café Schönblick",
         "Barista Lab", "Café Vaihingen", "Teehaus & Kaffee", "Kantine Neckarpark"]


def pick_city(rng):
    return rng.choices(CITIES, weights=[c[2] for c in CITIES])[0]


def build(rng: random.Random):
    days = [START + dt.timedelta(d) for d in range((HORIZON - START).days + 1)]

    # --- Shop-Kunden
    customers, seen_mail = [], set()
    for i in range(1, 1701):
        f, l = rng.choice(FIRST), rng.choice(LAST)
        city, zipc, _ = pick_city(rng)
        created = dt.datetime(2024, 6, 1) + dt.timedelta(minutes=rng.randint(0, int((HORIZON - dt.date(2024, 6, 1)).days * 1440)))
        local = f"{f}.{l}".lower().replace("ü", "ue").replace("ö", "oe").replace("ä", "ae").replace("ş", "s").replace("ı", "i")
        email = f"{local}{rng.randint(1, 99) if rng.random() < 0.6 else ''}@{rng.choice(DOMAINS)}"
        while email in seen_mail:
            email = f"{local}{rng.randint(100, 999)}@{rng.choice(DOMAINS)}"
        seen_mail.add(email)
        if rng.random() < 0.15:  # Shop speichert, was eingegeben wurde
            email = email[0].upper() + email[1:]
        customers.append(dict(customer_id=f"S-{1000 + i}", email=email, first_name=f, last_name=l,
                              city=city, zip=zipc, created=created, updated=created))
    by_id = {c["customer_id"]: c for c in customers}

    # --- Abos (alle Abo-Kunden haben ein Shop-Konto; das Abo-System hat eigene IDs)
    abo_customers, subs, events = [], [], []
    abo_pool = rng.sample(customers, 330)
    for n, c in enumerate(abo_pool, start=1):
        cus = "cus_" + "".join(rng.choices(string.ascii_letters + string.digits, k=6))
        mail = c["email"].lower()
        r = rng.random()
        mail = mail.upper() if r < 0.08 else (" " + mail if r < 0.16 else mail)
        abo_customers.append(dict(cus_id=cus, email=mail, name=f"{c['first_name']} {c['last_name']}"))
        start = max(c["created"].date() + dt.timedelta(days=rng.randint(0, 60)), START)
        if start > HORIZON - dt.timedelta(days=10):
            start = START + dt.timedelta(days=rng.randint(0, 600))
        plan = rng.choices(list(PLANS), weights=[50, 30, 20])[0]
        sub = dict(sub_id=f"sub_{n:04d}", cus_id=cus, shop_customer=c["customer_id"], plan=plan,
                   price=money(PLANS[plan][1]), anchor=min(start.day, 28), start=start)
        t0 = dt.datetime.combine(start, dt.time(rng.randint(8, 21), rng.randint(0, 59)))
        ev = [("created", t0)]
        state, pause_left = "active", 0
        m = dt.date(start.year, start.month, 1)
        while True:
            m = (m.replace(day=28) + dt.timedelta(days=4)).replace(day=1)  # nächster Monat
            if m > HORIZON:
                break
            when = dt.datetime.combine(m.replace(day=rng.randint(1, 28)), dt.time(rng.randint(7, 22), rng.randint(0, 59)))
            if when.date() > HORIZON:
                break
            if state == "active":
                r = rng.random()
                if r < 0.045:
                    ev.append(("canceled", when))
                    break
                if r < 0.10:
                    ev.append(("paused", when))
                    state, pause_left = "paused", rng.randint(1, 3)
            elif state == "paused":
                pause_left -= 1
                if pause_left <= 0:
                    if rng.random() < 0.25:
                        ev.append(("canceled", when))
                        break
                    ev.append(("resumed", when))
                    state = "active"
        sub["events"] = ev
        subs.append(sub)
        for typ, when in ev:
            events.append((sub["sub_id"], typ, when))

    def sub_state(sub, on: dt.date):
        st, last_pause, canceled = None, None, None
        for typ, when in sub["events"]:
            if when.date() > on:
                break
            st = {"created": "active", "resumed": "active", "paused": "paused", "canceled": "canceled"}[typ]
            if typ == "paused":
                last_pause = when.date()
            if typ == "canceled":
                canceled = when.date()
        return st, last_pause, canceled

    # --- Kassenkarten im Café
    cards = []
    card_owners = rng.sample(customers, 260)
    for n in range(1, 431):
        if n <= 260:
            c = card_owners[n - 1]
            mail = c["email"].lower()
        elif n <= 400:
            f, l = rng.choice(FIRST), rng.choice(LAST)
            mail = f"{f.lower()}.{l.lower()}.cafe{n}@{rng.choice(DOMAINS)}".replace("ü", "ue").replace("ö", "oe").replace("ı", "i").replace("ş", "s")
        else:
            mail = None
        issued = START + dt.timedelta(days=rng.randint(0, (HORIZON - START).days - 5))
        cards.append(dict(card_id=f"K-{n}", email=mail, issued=issued))

    # --- B2B-Debitoren
    debitors = []
    for n, name in enumerate(CAFES, start=1):
        city, zipc, _ = rng.choices(CITIES[:10], weights=[c[2] for c in CITIES[:10]])[0]
        debitors.append(dict(debitor_id=f"D-{20000 + n}", company=f"{name} GmbH" if n % 3 else name, city=city,
                             terms=30 if name == "Café Zimt" else rng.choice([14, 14, 30]),
                             discount=Decimal("0.03") if n % 5 == 0 else Decimal("0"),
                             weekday=rng.randint(0, 3), every=rng.choice([1, 1, 2]),
                             since=START + dt.timedelta(days=rng.randint(0, 400))))

    # --- Bewegungsdaten, Tag für Tag
    web_orders, items, refunds, pos_lines, invoices, inv_lines = [], [], [], [], [], []
    order_seq, bon_seq, inv_seq = 100000, 0, {2025: 0, 2026: 0}
    active_customers = sorted(customers, key=lambda c: c["created"])
    for d in days:
        trend = 1 + 0.35 * (d - START).days / 700
        season = 1.35 if d.month == 12 else (0.85 if d.month in (7, 8) else 1.0)
        weekday = [1.0, 0.95, 0.95, 1.0, 1.1, 0.9, 1.25][d.weekday()]
        n_web = max(5, int(rng.gauss(24, 4) * trend * season * weekday))
        eligible = [c for c in active_customers if c["created"].date() <= d]
        day_orders = []
        for _ in range(n_web):
            c = eligible[min(int(rng.paretovariate(1.2)) - 1, len(eligible) - 1)] if rng.random() < 0.45 else rng.choice(eligible)
            ts = dt.datetime.combine(d, dt.time(rng.randint(6, 23), rng.randint(0, 59), rng.randint(0, 59)))
            skus = rng.sample(["P-01", "P-02", "P-03", "P-04", "P-05", "P-06"], rng.choices([1, 2, 3], weights=[55, 32, 13])[0])
            voucher = rng.random() < 0.12
            lines = []
            for sku in skus:
                qty = rng.choices([1, 2, 3], weights=[70, 22, 8])[0] if sku != "P-06" else rng.choice([4, 6, 12])
                price = money(PROD[sku][5])
                disc = money(qty * price * Decimal("0.10")) if voucher else Decimal("0.00")
                lines.append([sku, qty, price, disc])
            day_orders.append(dict(ts=ts, customer=c["customer_id"], channel="web", lines=lines))
        for sub in subs:  # monatliche Abo-Lieferung am Ankertag
            if d.day == sub["anchor"] and d > sub["start"]:
                st, _, _ = sub_state(sub, d)
                if st == "active":
                    ts = dt.datetime.combine(d, dt.time(4, rng.randint(0, 59), rng.randint(0, 59)))
                    day_orders.append(dict(ts=ts, customer=sub["shop_customer"], channel="subscription",
                                           lines=[[PLANS[sub["plan"]][0], 1, sub["price"], Decimal("0.00")]]))
        day_orders.sort(key=lambda o: o["ts"])
        for o in day_orders:
            order_seq += 1
            o["order_id"] = order_seq
            o["cancelled"] = o["channel"] == "web" and rng.random() < 0.015
            o["refunds"] = []
            for pos, (sku, qty, price, disc) in enumerate(o["lines"], start=1):
                items.append((order_seq, pos, sku, qty, price, disc))
            if not o["cancelled"] and o["channel"] == "web" and rng.random() < 0.035:
                pos = rng.randint(1, len(o["lines"]))
                sku, qty, price, disc = o["lines"][pos - 1]
                when = o["ts"] + dt.timedelta(days=rng.randint(3, 21), hours=rng.randint(0, 8))
                o["refunds"].append((pos, money(qty * price - disc), when))
                refunds.append((order_seq, pos, money(qty * price - disc), when))
            web_orders.append(o)

        # Café: Mo–Sa, nicht an Feiertagen
        if d.weekday() < 6 and d not in FEIERTAGE_BW:
            n_bons = int(rng.gauss(95 if d.weekday() < 5 else 125, 12) * (1.1 if d.month in (11, 12) else 1.0))
            valid_cards = [c for c in cards if c["issued"] <= d]
            for ts in sorted(dt.datetime.combine(d, dt.time(7, 30)) + dt.timedelta(minutes=rng.randint(0, 660))
                             for _ in range(n_bons)):
                bon_seq += 1
                card = rng.choice(valid_cards)["card_id"] if valid_cards and rng.random() < 0.22 else None
                if card and rng.random() < 0.1:
                    card = rng.choice([card.lower(), f" {card}", f"{card} "])
                skus = rng.sample(["P-07", "P-08", "P-09", "P-06"], rng.choices([1, 2, 3], weights=[62, 30, 8])[0])
                if rng.random() < 0.06:
                    skus.append(rng.choice(["P-01", "P-03"]))
                for sku in skus:
                    qty = rng.choices([1, 2], weights=[85, 15])[0]
                    net = money(qty * money(PROD[sku][5]))
                    gross = money(net * (1 + Decimal(PROD[sku][7])))
                    pos_lines.append((f"C-{bon_seq:06d}", ts, sku, qty, gross, card, "K1" if rng.random() < 0.7 else "K2"))

        # B2B: Rechnungen am Liefertag
        for deb in debitors:
            if d >= deb["since"] and d.weekday() == deb["weekday"] and ((d - START).days // 7) % deb["every"] == 0:
                inv_seq[d.year] += 1
                inv_id = f"R-{d.year}-{inv_seq[d.year]:05d}"
                due = d + dt.timedelta(days=deb["terms"])
                r = rng.random()
                paid = (due + dt.timedelta(days=rng.randint(-10, 3)) if r < 0.82 else
                        due + dt.timedelta(days=rng.randint(8, 45)) if r < 0.97 else None)
                invoices.append(dict(invoice_id=inv_id, debitor_id=deb["debitor_id"], date=d, due=due, paid=paid))
                for ln, sku in enumerate(rng.sample(["P-01", "P-02", "P-03", "P-04"], rng.randint(1, 3)), start=1):
                    qty = rng.randint(4, 24)
                    price = money(Decimal(PROD[sku][5]) * Decimal("0.80"))
                    disc = money(qty * price * deb["discount"])
                    inv_lines.append((inv_id, ln, sku, qty, price, disc))

    reviews = [(8801, "P-01", 5, "Bester Espresso in Stuttgart.", dt.datetime(2026, 9, 2, 19, 4)),
               (8802, "P-03", 2, "Lieferung kam zwei Tage zu spät.", dt.datetime(2026, 9, 8, 7, 51)),
               (8803, "P-04", 3, "Filter Äthiopien ok, aber teuer.", dt.datetime(2026, 9, 21, 12, 30)),
               (8804, "P-05", 4, "Endlich ein Entkoffeinierter, der nach Kaffee schmeckt.", dt.datetime(2026, 10, 1, 20, 12)),
               (8805, "P-02", 1, "Packung war aufgerissen.", dt.datetime(2026, 10, 14, 9, 45)),
               (8806, "P-06", 5, "Cold Brew im Abo wäre super.", dt.datetime(2026, 10, 19, 16, 3))]

    return dict(customers=customers, by_id=by_id, abo_customers=abo_customers, subs=subs, events=events,
                sub_state=sub_state, cards=cards, debitors=debitors, web_orders=web_orders, items=items,
                refunds=refunds, pos_lines=pos_lines, invoices=invoices, inv_lines=inv_lines, reviews=reviews)


UPDATE_DAY = dt.date(2026, 10, 26)  # Montag nach Tag 2: Umzüge und neue E-Mails werden im Shop gepflegt


def apply_customer_update(customers):
    """Änderungen an shop.customers vom 2026-10-26: Umzüge und neue E-Mail-Adressen."""
    rng = random.Random(SEED + 1)
    when = dt.datetime.combine(UPDATE_DAY, dt.time(6, 0))
    existing = [c for c in customers if c["created"].date() < UPDATE_DAY]
    for c in rng.sample(existing, 45):
        city, zipc, _ = pick_city(rng)
        while city == c["city"]:
            city, zipc, _ = pick_city(rng)
        c.update(city=city, zip=zipc, updated=when + dt.timedelta(minutes=rng.randint(0, 50)))
    for c in rng.sample(existing, 15):
        user, _, dom = c["email"].lower().partition("@")
        c.update(email=f"{user}.neu@{rng.choice(DOMAINS)}", updated=when + dt.timedelta(minutes=rng.randint(0, 50)))


# ---------------------------------------------------------------- schreiben & laden
TABLES = {
    "shop.customers": "customer_id VARCHAR, email VARCHAR, first_name VARCHAR, last_name VARCHAR, city VARCHAR, zip VARCHAR, created_at VARCHAR, updated_at VARCHAR",
    "shop.products": "sku VARCHAR, title VARCHAR, sort VARCHAR, category VARCHAR, roast VARCHAR, list_price_net DECIMAL(10,2), unit_cost DECIMAL(10,2), vat_rate DECIMAL(4,2)",
    "shop.orders": "order_id BIGINT, customer_id VARCHAR, created_at VARCHAR, channel VARCHAR, status INTEGER, total_gross DECIMAL(12,2), _loaded_at TIMESTAMP",
    "shop.order_items": "order_id BIGINT, pos INTEGER, sku VARCHAR, qty INTEGER, unit_price DECIMAL(10,2), discount DECIMAL(10,2)",
    "shop.refunds": "refund_id BIGINT, order_id BIGINT, pos INTEGER, amount DECIMAL(10,2), refunded_at VARCHAR",
    "shop.reviews": "review_id BIGINT, sku VARCHAR, stars INTEGER, text VARCHAR, created_at VARCHAR",
    "pos.sales": "receipt_id VARCHAR, ts VARCHAR, sku VARCHAR, qty INTEGER, amount_gross DECIMAL(10,2), card_id VARCHAR, register VARCHAR",
    "pos.cards": "card_id VARCHAR, email VARCHAR, issued_on DATE",
    "billing.customers": "cus_id VARCHAR, email VARCHAR, name VARCHAR",
    "billing.subscriptions": "sub_id VARCHAR, cus_id VARCHAR, plan VARCHAR, price_monthly DECIMAL(10,2), status VARCHAR, started_on DATE, canceled_at VARCHAR, paused_at VARCHAR",
    "billing.subscription_events": "event_id BIGINT, sub_id VARCHAR, type VARCHAR, occurred_at TIMESTAMPTZ",
    "erp.debitors": "debitor_id VARCHAR, company VARCHAR, city VARCHAR, payment_terms_days INTEGER",
    "erp.invoices": "invoice_id VARCHAR, debitor_id VARCHAR, invoice_date DATE, due_date DATE, paid_date DATE",
    "erp.invoice_lines": "invoice_id VARCHAR, line_no INTEGER, sku VARCHAR, qty INTEGER, unit_price_net DECIMAL(10,2), discount_net DECIMAL(10,2)",
}


def rows_for(data, cutoff: dt.date):
    subs_state = data["sub_state"]
    out = {}
    out["shop.customers"] = [(c["customer_id"], c["email"], c["first_name"], c["last_name"], c["city"], c["zip"],
                              iso_local(c["created"]), iso_local(c["updated"]))
                             for c in data["customers"] if c["created"].date() <= cutoff]
    out["shop.products"] = [(p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7]) for p in PRODUCTS]
    orders, keep = [], set()
    for o in data["web_orders"]:
        if o["ts"].date() > cutoff:
            continue
        keep.add(o["order_id"])
        refunded = [r for r in o["refunds"] if r[2].date() <= cutoff]
        # 1 offen · 2 bezahlt · 3 storniert · 4 teilweise erstattet · 5 erstattet
        status = 3 if o["cancelled"] else (4 if refunded and len(o["lines"]) > 1 else 5 if refunded else 2)
        gross = sum(money((q * p - dsc) * (1 + Decimal(PROD[s][7]))) for s, q, p, dsc in o["lines"])
        loaded = dt.datetime.combine(o["ts"].date() + dt.timedelta(days=1), dt.time(5, 0))
        orders.append((o["order_id"], o["customer"], iso_local(o["ts"]), o["channel"], status, money(gross), loaded))
        if o["ts"].date() in (dt.date(2026, 10, 10), dt.date(2026, 10, 11)):  # Rerun nach Abbruch: doppelt geladen
            orders.append((o["order_id"], o["customer"], iso_local(o["ts"]), o["channel"], status, money(gross),
                           loaded + dt.timedelta(hours=2, minutes=15)))
    out["shop.orders"] = orders
    out["shop.order_items"] = [i for i in data["items"] if i[0] in keep]
    out["shop.refunds"] = [(n, r[0], r[1], r[2], iso_local(r[3])) for n, r in
                           enumerate(sorted(data["refunds"], key=lambda r: r[3]), start=1)
                           if r[0] in keep and r[3].date() <= cutoff]
    out["shop.reviews"] = [(r[0], r[1], r[2], r[3], iso_local(r[4])) for r in data["reviews"] if r[4].date() <= cutoff]
    out["pos.sales"] = [(b, ts.strftime("%d.%m.%Y %H:%M"), s, q, g, c, reg) for b, ts, s, q, g, c, reg in data["pos_lines"]
                        if ts.date() <= cutoff]
    out["pos.cards"] = [(c["card_id"], c["email"], c["issued"]) for c in data["cards"] if c["issued"] <= cutoff]
    subs = [s for s in data["subs"] if s["start"] <= cutoff]
    cus_keep = {s["cus_id"] for s in subs}
    out["billing.customers"] = [(a["cus_id"], a["email"], a["name"]) for a in data["abo_customers"] if a["cus_id"] in cus_keep]
    srows = []
    for s in subs:
        st, last_pause, canceled = subs_state(s, cutoff)
        srows.append((s["sub_id"], s["cus_id"], s["plan"], s["price"], st, s["start"],
                      canceled.strftime("%d.%m.%Y") if canceled else None,
                      last_pause.strftime("%d.%m.%Y") if last_pause else None))
    out["billing.subscriptions"] = srows
    evs = sorted((e for e in data["events"] if e[2].date() <= cutoff), key=lambda e: e[2])
    out["billing.subscription_events"] = [(n, e[0], e[1], iso_utc(e[2])) for n, e in enumerate(evs, start=1)]
    out["erp.debitors"] = [(d["debitor_id"], d["company"], d["city"], d["terms"]) for d in data["debitors"]]
    inv_keep = {i["invoice_id"] for i in data["invoices"] if i["date"] <= cutoff}
    out["erp.invoices"] = [(i["invoice_id"], i["debitor_id"], i["date"], i["due"],
                            i["paid"] if i["paid"] and i["paid"] <= cutoff else None)
                           for i in data["invoices"] if i["invoice_id"] in inv_keep]
    out["erp.invoice_lines"] = [l for l in data["inv_lines"] if l[0] in inv_keep]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--until", "--bis", dest="until", default="2026-10-25", help="Stichtag der Daten (YYYY-MM-DD), höchstens 2026-11-29")
    ap.add_argument("--customer-update", "--kundenupdate", dest="customer_update", action="store_true", help="nur shop.customers neu laden, Stand 2026-10-26 (Umzüge)")
    ap.add_argument("--db", default=str(HERE / "neckarbohne.duckdb"))
    ap.add_argument("--csv", default=str(HERE / "data"), help="Ordner für die CSV-Dateien")
    args = ap.parse_args()
    cutoff = dt.date.fromisoformat(args.until)
    assert START < cutoff <= HORIZON, f"Stichtag muss zwischen {START} und {HORIZON} liegen"

    data = build(random.Random(SEED))
    if args.customer_update or cutoff >= UPDATE_DAY:
        apply_customer_update(data["customers"])
    tables = rows_for(data, cutoff)
    if args.customer_update:  # nur die neue Lieferung der Kundentabelle, Stand 2026-10-26
        tables = {"shop.customers": rows_for(data, max(cutoff, UPDATE_DAY))["shop.customers"]}

    csv_dir = Path(args.csv)
    con = duckdb.connect(args.db)
    for name, rows in tables.items():
        schema, table = name.split(".")
        path = csv_dir / schema / f"{table}.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        cols = [c.split()[0] for c in TABLES[name].split(", ")]
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(cols)
            for r in rows:
                w.writerow(["" if v is None else v.isoformat(sep=" ") if isinstance(v, dt.datetime) else v for v in r])
        types = ", ".join(f"'{c.split()[0]}': '{' '.join(c.split()[1:])}'" for c in TABLES[name].split(", "))
        con.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        con.execute(f"""CREATE OR REPLACE TABLE {schema}.{table} AS
                        SELECT * FROM read_csv('{path.as_posix()}', header=true, columns={{{types}}},
                                               nullstr='', quote='"', escape='"')""")
        print(f"{name:26s} {len(rows):>7,d} Zeilen")
    con.close()
    print(f"Stichtag {cutoff} · geladen nach {args.db}" + (" · Kundenupdate" if args.customer_update else ""))


if __name__ == "__main__":
    main()
