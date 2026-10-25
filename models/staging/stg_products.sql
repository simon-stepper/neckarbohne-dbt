select
    sku                 as product_id,
    title               as name,
    sort                as coffee_type,
    category,
    roast,
    list_price_net,
    unit_cost,
    vat_rate
from {{ source('shop', 'products') }}
