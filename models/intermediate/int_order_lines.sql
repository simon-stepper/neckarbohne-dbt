-- Alle Verkaufspositionen aus drei Systemen in einer Form: eine Zeile pro Position.
-- Beträge netto ohne MwSt.: umsatz_brutto = Menge × Preis vor Rabatt und Retoure.
with produkte as (
    select * from {{ ref('stg_products') }}
),

shop as (
    select
        cast(o.order_id as varchar)                as order_id,
        i.position,
        o.bestelldatum_lokal,
        o.kanal,
        'shop'                                     as kunde_quelle,
        o.customer_id                              as kunde_quelle_id,
        i.produkt_id,
        i.menge,
        i.menge * i.einzelpreis_netto              as umsatz_brutto,
        i.rabatt_netto                             as rabatt_betrag,
        coalesce(r.erstattung_netto, 0)            as retoure_betrag
    from {{ ref('stg_orders') }} o
    join {{ ref('stg_order_items') }} i using (order_id)
    left join {{ ref('stg_refunds') }} r on r.order_id = i.order_id and r.position = i.position
    where o.status <> 'storniert'
),

cafe as (
    select
        s.bon_id                                   as order_id,
        s.position,
        s.verkaufsdatum_lokal                      as bestelldatum_lokal,
        'Café'                                     as kanal,
        'kasse'                                    as kunde_quelle,
        s.karten_id                                as kunde_quelle_id,
        s.produkt_id,
        s.menge,
        round(s.betrag_brutto_inkl_mwst / (1 + p.mwst_satz), 2) as umsatz_brutto,
        0                                          as rabatt_betrag,
        0                                          as retoure_betrag
    from {{ ref('stg_pos_sales') }} s
    join produkte p using (produkt_id)
),

b2b as (
    select
        l.rechnung_id                              as order_id,
        l.position,
        r.rechnungsdatum                           as bestelldatum_lokal,
        'B2B'                                      as kanal,
        'erp'                                      as kunde_quelle,
        r.debitor_id                               as kunde_quelle_id,
        l.produkt_id,
        l.menge,
        l.menge * l.einzelpreis_netto              as umsatz_brutto,
        l.rabatt_netto                             as rabatt_betrag,
        0                                          as retoure_betrag
    from {{ ref('stg_invoice_lines') }} l
    join {{ ref('stg_invoices') }} r using (rechnung_id)
),

alle as (
    select * from shop
    union all
    select * from cafe
    union all
    select * from b2b
)

select
    a.order_id || '-' || a.position                                as order_line_id,
    a.order_id,
    a.position,
    a.bestelldatum_lokal,
    a.kanal,
    a.kunde_quelle,
    a.kunde_quelle_id,
    a.produkt_id,
    a.menge,
    -- Geld immer als DECIMAL: Gleitkommazahlen hinterlassen Reste wie 89084.76000000033
    cast(a.umsatz_brutto as decimal(12, 2))                        as umsatz_brutto,
    cast(a.rabatt_betrag as decimal(12, 2))                        as rabatt_betrag,
    cast(a.retoure_betrag as decimal(12, 2))                       as retoure_betrag,
    cast(a.menge * p.einstandspreis as decimal(12, 2))             as einstandskosten
from alle a
join produkte p using (produkt_id)
