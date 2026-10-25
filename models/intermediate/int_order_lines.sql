-- Alle Verkaufspositionen aus drei Systemen in einer Form: eine Zeile pro Position.
-- Beträge netto ohne MwSt.: revenue = Menge × Preis vor Rabatt und Retoure.
with products as (
    select * from {{ ref('stg_products') }}
),

shop as (
    select
        cast(o.order_id as varchar)                as order_id,
        i.line_no,
        o.order_date_local,
        o.channel,                                 -- web | subscription
        'shop'                                     as customer_source,
        o.customer_id                              as customer_source_id,
        i.product_id,
        i.quantity,
        i.quantity * i.unit_price_net              as gross_revenue,
        i.discount_net                             as discount_amount,
        coalesce(r.refund_net, 0)                  as refund_amount
    from {{ ref('stg_orders') }} o
    join {{ ref('stg_order_items') }} i using (order_id)
    left join {{ ref('stg_refunds') }} r on r.order_id = i.order_id and r.line_no = i.line_no
    where o.status <> 'canceled'
),

cafe as (
    select
        s.receipt_id                               as order_id,
        s.line_no,
        s.sale_date_local                          as order_date_local,
        'cafe'                                     as channel,
        'pos'                                      as customer_source,
        s.card_id                                  as customer_source_id,
        s.product_id,
        s.quantity,
        round(s.amount_gross_incl_vat / (1 + p.vat_rate), 2) as gross_revenue,
        0                                          as discount_amount,
        0                                          as refund_amount
    from {{ ref('stg_pos_sales') }} s
    join products p using (product_id)
),

b2b as (
    select
        l.invoice_id                               as order_id,
        l.line_no,
        i.invoice_date                             as order_date_local,
        'b2b'                                      as channel,
        'erp'                                      as customer_source,
        i.debitor_id                               as customer_source_id,
        l.product_id,
        l.quantity,
        l.quantity * l.unit_price_net              as gross_revenue,
        l.discount_net                             as discount_amount,
        0                                          as refund_amount
    from {{ ref('stg_invoice_lines') }} l
    join {{ ref('stg_invoices') }} i using (invoice_id)
),

all_lines as (
    select * from shop
    union all
    select * from cafe
    union all
    select * from b2b
)

select
    a.order_id || '-' || a.line_no                                 as order_line_id,
    a.order_id,
    a.line_no,
    a.order_date_local,
    a.channel,
    a.customer_source,
    a.customer_source_id,
    a.product_id,
    a.quantity,
    -- Geld immer als DECIMAL: Gleitkommazahlen hinterlassen Reste wie 89084.76000000033
    cast(a.gross_revenue as decimal(12, 2))                        as revenue,  -- kürzer, wie im Dashboard
    cast(a.discount_amount as decimal(12, 2))                      as discount_amount,
    cast(a.refund_amount as decimal(12, 2))                        as refund_amount,
    cast(a.quantity * p.unit_cost as decimal(12, 2))               as cost_amount
from all_lines a
join products p using (product_id)
