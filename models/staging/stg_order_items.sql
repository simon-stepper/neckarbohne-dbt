select
    order_id,
    pos              as position,
    sku              as produkt_id,
    qty              as menge,
    unit_price       as einzelpreis_netto,
    discount         as rabatt_netto
from {{ source('shop', 'order_items') }}
