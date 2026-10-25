select
    row_number() over (order by product_id)::integer  as product_key,
    product_id,
    name,
    coffee_type,
    category,
    roast,
    list_price_net,
    unit_cost
from {{ ref('stg_products') }}
