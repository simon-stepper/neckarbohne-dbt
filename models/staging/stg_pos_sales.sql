-- Café-Kasse: deutsches Datumsformat, Lokalzeit ohne Zone, keine Positionsnummer.
with source as (
    select
        *,
        strptime(ts, '%d.%m.%Y %H:%M') as sold_at_local
    from {{ source('pos', 'sales') }}
)
select
    receipt_id,
    row_number() over (partition by receipt_id order by sku, qty)  as line_no,
    sold_at_local,
    timezone('Europe/Berlin', sold_at_local)                   as sold_at,
    sold_at_local::date                                        as sale_date_local,
    sku                                                        as product_id,
    qty                                                        as quantity,
    amount_gross                                               as amount_gross_incl_vat,
    nullif(upper(trim(card_id)), '')                           as card_id,
    register
from source
