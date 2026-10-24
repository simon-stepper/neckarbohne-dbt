-- Ein Kunde, bis zu vier IDs: Shop (S-…), Abo (cus_…), Kassenkarte (K-…), ERP (D-…).
-- Verknüpft wird über die normalisierte E-Mail. Wer in keinem anderen System auftaucht, bleibt eigener Kunde.
with shop as (
    select * from {{ ref('stg_customers') }}
),
abo as (
    select * from {{ ref('stg_abo_customers') }}
),
karten as (
    select * from {{ ref('stg_pos_cards') }}
),

shop_kunden as (
    select
        s.customer_id                     as kunde_id,
        s.name,
        s.stadt,
        s.plz,
        'privat'                          as segment,
        s.customer_id                     as shop_id,
        a.abo_kunde_id                    as abo_id,
        k.karten_id                       as pos_id,
        cast(null as varchar)             as erp_id,
        s.erstellt_um::date               as erstellt_am
    from shop s
    left join abo a using (email)
    left join karten k using (email)
),

-- TODO Basis: Wer fehlt noch? Ergänzt zwei CTEs nach dem Muster von shop_kunden und debitoren
--   nur_karte: Kassenkarten ohne E-Mail oder ohne passendes Shop-Konto (kunde_id = karten_id)
--   nur_abo:   Abo-Kunden ohne passendes Shop-Konto (kunde_id = abo_kunde_id)
-- und nehmt sie unten in die union all auf. Prüfen: select segment, count(*) from dim_kunde group by 1

debitoren as (
    select
        d.debitor_id                      as kunde_id,
        d.firma                           as name,
        d.stadt,
        cast(null as varchar)             as plz,
        'B2B'                             as segment,
        cast(null as varchar)             as shop_id,
        cast(null as varchar)             as abo_id,
        cast(null as varchar)             as pos_id,
        d.debitor_id                      as erp_id,
        date '2000-01-01'                 as erstellt_am
    from {{ ref('stg_debitors') }} d
)

select * from shop_kunden
union all
select * from debitoren
-- TODO: union all select * from nur_karte
-- TODO: union all select * from nur_abo
