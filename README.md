# Neckarbohne GmbH · dbt + DuckDB

Starter-Projekt für das Lab an Tag 2 (Star Schema mit dbt). Dieselben Daten nutzen wir an Tag 3 (Iceberg) und Tag 4 (Text-to-SQL).

Neckarbohne ist eine fiktive Kaffeerösterei in Stuttgart: Webshop, Kaffee-Abos, B2B-Cafés und ein eigenes Café. Die Daten sind synthetisch – keine echten Personen.

## Setup

### Projekt holen

Eine der drei Varianten, der Inhalt ist identisch:

- **Fork** (empfohlen, wenn ihr einen GitHub-Account habt): oben rechts **Fork**, dann euren Fork klonen. So könnt ihr eure Lösung pushen und Codespaces nutzen.
- **Klonen:** `git clone https://github.com/simon-stepper/neckarbohne-dbt.git`
- **Ohne Git:** ZIP aus Moodle oder hier über **Code → Download ZIP**.

### Lokal (Python 3.10–3.13)

```bash
cd neckarbohne-dbt
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
| `abo` | Abo- und Zahlungsanbieter | customers, subscriptions, subscription_events |
| `erp` | Buchhaltung, B2B-Kunden | debitors, invoices, invoice_lines |

Die Quellen haben Eigenheiten, die ihr aus der Vorlesung kennt: Statuscodes statt Namen, Bruttobeträge inkl. MwSt., Text-Zeitstempel, ein doppelter Ladelauf, drei verschiedene IDs für dieselbe Person. Die Beschreibungen stehen in `models/staging/_sources.yml`.

## Projektstruktur

```
models/
  staging/        Silver · 1:1 pro Quelle: umbenennen, Typen, Dubletten        ✔ fertig
  intermediate/   Silver · zusammenführen
    int_order_lines.sql        alle Verkaufspositionen aus Shop, Kasse, ERP     ✔ fertig
    int_kunden_vereint.sql     ein Kunde, bis zu vier IDs                       ✎ teilweise
    int_kunden_schluessel.sql  Quell-ID → kunde_id                              ✔ fertig
  marts/          Gold · das Star Schema
    dim_datum, dim_produkt, dim_kanal                                           ✔ fertig
    dim_kunde.sql                                                               ✎ eure Aufgabe
    fct_order_lines.sql                                                         ✎ eure Aufgabe
snapshots/        customers_snapshot: SCD 2 für Shop-Kunden                     ✔ fertig
analyses/         die Fragen der Geschäftsführung                               ✎ eure Aufgabe
```

## Aufgaben

### Basis

1. `int_kunden_vereint`: Kassenkarten und Abo-Kunden ohne Shop-Konto ergänzen. Was ist eigentlich ein „Kunde“?
2. `dim_kunde`: Surrogate Key vergeben.
3. `fct_order_lines`: `kanal_key` und `kunde_key` ergänzen. Grain: eine Zeile pro Position.
4. `dbt build`, bis die Tests grün sind. Rote Tests am Anfang sind Absicht.
5. Fragen der GF in `analyses/` beantworten: Umsatz nach Kanal, Marge pro Sorte.

### Fortgeschritten

6. Unknown-Member: Café-Verkäufe ohne Kassenkarte bekommen `kunde_key = -1`. Danach die beiden Tests mit `severity: warn` auf Fehler stellen.
7. SCD 2 sichtbar machen:
   ```bash
   dbt snapshot                            # erster Stand
   python generate_data.py --kundenupdate  # nächste Lieferung: 45 Umzüge, 15 neue E-Mails
   dbt snapshot                            # zweiter Stand
   ```
   Dann `dim_kunde` aus `customers_snapshot` mit `valid_from` / `valid_to` bauen und in `fct_order_lines` die Version joinen, die am Bestelltag galt.

### Bonus

8. `fct_abo_monat` mit MRR: eine Zeile pro Abo und Monat, Status am Monatsende.
9. GF: Abo-Kündigungen pro Monat. Pausierte Abos zählen nicht.
10. Warum ist MRR semi-additiv? Zeigt es mit einer Query.

## Nützliche Befehle

| Befehl | Was er tut |
|---|---|
| `dbt build` | Seeds, Snapshots, Modelle und Tests in der richtigen Reihenfolge |
| `dbt build --select dim_kunde+` | ein Modell und alles, was davon abhängt |
| `dbt show --select fct_order_lines` | die ersten Zeilen eines Modells |
| `dbt compile --select gf_umsatz_nach_kanal` | Analyse kompilieren, SQL steht dann in `target/compiled/` |
| `dbt docs generate && dbt docs serve` | Doku und Lineage-Graph im Browser |

## Wenn etwas nicht geht

- **`Could not set lock on file`**: Die DuckDB-UI oder ein anderes Programm hat die Datei offen. Schließen und neu starten.
- **`Binder Error: … not found`**: Spaltenname prüfen; Staging benennt fast alles auf Deutsch um (`stg_orders.bestelldatum_lokal`, nicht `created_at`).
- **Firmenlaptop ohne Python**: Codespaces nutzen (siehe oben).
