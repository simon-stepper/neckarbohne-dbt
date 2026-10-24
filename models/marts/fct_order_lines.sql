-- Grain: eine Zeile pro Bestellposition – Webshop, Abo, Café und B2B.
-- Beträge in Euro, netto ohne MwSt.: Nettoumsatz = umsatz_brutto - rabatt_betrag - retoure_betrag
--
-- TODO Basis: kanal_key und kunde_key ergänzen.
--   kanal_key: über dim_kanal (l.kanal)
--   kunde_key: int_kunden_schluessel ordnet jede Quell-ID (Shop, Kassenkarte, Debitor) einem kunde_id zu,
--              dim_kunde liefert dazu den kunde_key
-- TODO Fortgeschritten: Café-Verkäufe ohne Kassenkarte bekommen -1 statt NULL
-- TODO Fortgeschritten (SCD 2): die Version joinen, die am Bestelltag galt
select
    l.order_line_id,
    l.order_id,                                       -- degenerierte Dimension
    l.position                                        as line_no,
    d.datum_key,
    p.produkt_key,
    -- TODO: kanal_key
    -- TODO: kunde_key
    l.menge,
    l.umsatz_brutto,
    l.rabatt_betrag,
    l.retoure_betrag,
    l.einstandskosten
from {{ ref('int_order_lines') }} l
join {{ ref('dim_datum') }} d on d.datum = l.bestelldatum_lokal
join {{ ref('dim_produkt') }} p on p.produkt_id = l.produkt_id
