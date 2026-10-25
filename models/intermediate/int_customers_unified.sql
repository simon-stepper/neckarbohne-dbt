-- Ein Kunde, bis zu vier IDs: Shop (S-…), Abo-Anbieter (cus_…), Kassenkarte (K-…), ERP (D-…).
-- Verknüpft wird über die normalisierte E-Mail. Wer in keinem anderen System auftaucht, bleibt eigener Kunde.
with shop as (
    select * from {{ ref('stg_customers') }}
),
billing as (
    select * from {{ ref('stg_subscription_customers') }}
),
cards as (
    select * from {{ ref('stg_pos_cards') }}
),

shop_customers as (
    select
        s.customer_id                     as customer_id,
        s.name,
        s.city,
        s.zip,
        'consumer'                        as segment,
        s.customer_id                     as shop_id,
        b.subscription_customer_id        as billing_id,
        c.card_id                         as pos_id,
        cast(null as varchar)             as erp_id,
        s.created_at::date                as created_on
    from shop s
    left join billing b using (email)
    left join cards c using (email)
),

-- TODO Basis: Wer fehlt noch? Ergänzt zwei CTEs nach dem Muster von shop_customers und debitors
--   card_only:    Kassenkarten ohne E-Mail oder ohne passendes Shop-Konto (customer_id = card_id)
--   billing_only: Abo-Kunden ohne passendes Shop-Konto (customer_id = subscription_customer_id)
-- und nehmt sie unten in die union all auf. Prüfen: select segment, count(*) from dim_customer group by 1

debitors as (
    select
        d.debitor_id                      as customer_id,
        d.company                         as name,
        d.city,
        cast(null as varchar)             as zip,
        'b2b'                             as segment,
        cast(null as varchar)             as shop_id,
        cast(null as varchar)             as billing_id,
        cast(null as varchar)             as pos_id,
        d.debitor_id                      as erp_id,
        date '2000-01-01'                 as created_on
    from {{ ref('stg_debitors') }} d
)

select * from shop_customers
union all
select * from debitors
-- TODO: union all select * from card_only
-- TODO: union all select * from billing_only
