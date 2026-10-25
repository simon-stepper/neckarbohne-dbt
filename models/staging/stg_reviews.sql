select
    review_id,
    sku              as product_id,
    stars,
    text,
    created_at::timestamptz as created_at
from {{ source('shop', 'reviews') }}
