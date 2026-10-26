# Neckarbohne GmbH · dbt + DuckDB

Starter-Projekt für das Lab an Tag 2 (Star Schema mit dbt). Dieselben Daten nutzen wir an Tag 3 (Iceberg) und Tag 4 (Text-to-SQL).

Neckarbohne ist eine fiktive Kaffeerösterei in Stuttgart: Webshop, Kaffee-Abos, B2B-Cafés und ein eigenes Café. Die Daten sind synthetisch – keine echten Personen.

## Setup

Ihr braucht Git und entweder [uv](https://docs.astral.sh/uv/) oder Python 3.14 (3.10 bis 3.13 gehen auch). Die DuckDB-CLI ist optional (`duckdb -ui`).

### Lokal mit uv (empfohlen)

[uv](https://docs.astral.sh/uv/) installiert bei Bedarf auch das passende Python (3.14, siehe `.python-version`).

```bash
uv sync                              # .venv anlegen, Pakete aus uv.lock installieren
uv run python generate_data.py       # lädt die Rohdaten nach neckarbohne.duckdb
uv run dbt debug                     # Verbindung prüfen
uv run dbt build                     # alles bauen und testen
```

Wer nicht jedes Mal `uv run` tippen will: `source .venv/bin/activate` (Windows: `.venv\Scripts\activate`), danach direkt `dbt build`.

### Lokal mit pip (Python 3.14, ältere ab 3.10 gehen auch)

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python generate_data.py              # lädt die Rohdaten nach neckarbohne.duckdb
dbt debug                            # Verbindung prüfen
dbt build                            # alles bauen und testen
```

### Plan B: GitHub Codespaces

Repository öffnen → **Code** → **Codespaces** → **Create codespace**. Python, dbt, die DuckDB-CLI und die Rohdaten werden beim Start eingerichtet. Danach im Terminal: `dbt build`.

### In die Daten schauen

```bash
duckdb -ui neckarbohne.duckdb        # Notebook im Browser (Port 4213)
dbt show --inline "select * from {{ ref('fct_order_lines') }}" --limit 10
```

DuckDB erlaubt nur einen Schreiber: Die UI schließen, bevor ihr `dbt build` oder `generate_data.py` startet.

## Woher die Daten kommen

`generate_data.py` spielt das Ingestion-Tool: Es lädt die Rohdaten der vier Quellsysteme unverändert in eigene Schemas. Das ist Bronze.

| Schema | Quellsystem | Tabellen |
|---|---|---|
| `shop` | Onlineshop (Webshop und Abo-Lieferungen) | customers, products, orders, order_items, refunds, reviews |
| `pos` | Kasse im Café | sales, cards |
| `billing` | Abo- und Zahlungsanbieter | customers, subscriptions, subscription_events |
| `erp` | Buchhaltung, B2B-Kunden | debitors, invoices, invoice_lines |

Die Quellen haben Eigenheiten, die ihr aus der Vorlesung kennt: Statuscodes statt Namen, Bruttobeträge inkl. MwSt., Text-Zeitstempel, ein doppelter Ladelauf, drei verschiedene IDs für dieselbe Person. Die Beschreibungen stehen in `models/staging/_sources.yml`.

## Projektstruktur

```
models/
  staging/        Silver · 1:1 pro Quelle: umbenennen, Typen, Dubletten        ✔ fertig
  intermediate/   Silver · zusammenführen
    int_order_lines.sql        alle Verkaufspositionen aus Shop, Kasse, ERP     ✔ fertig
    int_customers_unified.sql  ein Kunde, bis zu vier IDs                       ✎ teilweise
    int_customer_keys.sql      Quell-ID → customer_id                           ✔ fertig
  marts/          Gold · das Star Schema
    dim_date, dim_product, dim_channel                                          ✔ fertig
    dim_customer.sql                                                            ✎ eure Aufgabe
    fct_order_lines.sql                                                         ✎ eure Aufgabe
snapshots/        customers_snapshot: SCD 2 für Shop-Kunden                     ✔ fertig
analyses/         die Fragen der Geschäftsführung                               ✎ eure Aufgabe
```

## Namen im Modell

Tabellen und Spalten sind englisch, die Beschreibungen deutsch. Die wichtigsten Begriffe:

| Spalte | heißt in der Vorlesung |
|---|---|
| `gross_revenue` | Umsatz brutto: Menge × Preis netto, vor Rabatt und Retoure (ohne MwSt.) |
| `discount_amount`, `refund_amount` | Rabatt, Retoure (netto) |
| `cost_amount` | Einstandskosten |
| Nettoumsatz | `gross_revenue - discount_amount - refund_amount` |
| `channel` | Kanal: `web`, `subscription` (Abo), `cafe`, `b2b` |
| `coffee_type` | Sorte: Espresso, Filter, Decaf, Cold Brew |
| `customer_key` = -1 | Unknown Member: Laufkundschaft im Café |

## Aufgaben

### Basis

1. `int_customers_unified`: Kassenkarten und Abo-Kunden ohne Shop-Konto ergänzen. Was ist eigentlich ein „Kunde“?
2. `dim_customer`: Surrogate Key vergeben.
3. `fct_order_lines`: `channel_key` und `customer_key` ergänzen. Grain: eine Zeile pro Position.
4. `dbt build`, bis die Tests grün sind. Rote Tests am Anfang sind Absicht.
5. Fragen der GF in `analyses/` beantworten: Umsatz nach Kanal, Marge pro Sorte.

### Fortgeschritten

6. Unknown-Member: Café-Verkäufe ohne Kassenkarte bekommen `customer_key = -1`. Danach die beiden Tests mit `severity: warn` auf Fehler stellen.
7. SCD 2 sichtbar machen:
   ```bash
   dbt snapshot                            # erster Stand
   python generate_data.py --customer-update  # nächste Lieferung: 45 Umzüge, 15 neue E-Mails
   dbt snapshot                            # zweiter Stand
   ```
   Dann `dim_customer` aus `customers_snapshot` mit `valid_from` / `valid_to` bauen und in `fct_order_lines` die Version joinen, die am Bestelltag galt.

### Bonus

8. `fct_subscription_month` mit MRR: eine Zeile pro Abo und Monat, Status am Monatsende.
9. GF: Abo-Kündigungen pro Monat. Pausierte Abos zählen nicht.
10. Warum ist MRR semi-additiv? Zeigt es mit einer Query.

## Nützliche Befehle

| Befehl | Was er tut |
|---|---|
| `dbt build` | Seeds, Snapshots, Modelle und Tests in der richtigen Reihenfolge |
| `dbt build --select dim_customer+` | ein Modell und alles, was davon abhängt |
| `dbt show --select fct_order_lines` | die ersten Zeilen eines Modells |
| `dbt compile --select revenue_by_channel` | Analyse kompilieren, SQL steht dann in `target/compiled/` |
| `dbt docs generate && dbt docs serve` | Doku und Lineage-Graph im Browser |

## Wenn etwas nicht geht

- **`Could not set lock on file`**: Die DuckDB-UI oder ein anderes Programm hat die Datei offen. Schließen und neu starten.
- **`Binder Error: … not found`**: Spaltenname prüfen; Staging benennt einiges um (`stg_orders.order_date_local` und `ordered_at`, nicht `created_at`). Tabellen und Spalten sind englisch, die Beschreibungen in den YAML-Dateien deutsch.
- **Firmenlaptop ohne Python**: Codespaces nutzen (siehe oben).
