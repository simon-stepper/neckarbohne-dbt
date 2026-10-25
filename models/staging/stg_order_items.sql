select
    order_id,
    pos              as line_no,
    sku              as product_id,
    qty              as quantity,
    unit_price       as unit_price_net,
    discount         as discount_net
from {{ source('shop', 'order_items') }}
