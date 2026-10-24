select
    review_id        as bewertung_id,
    sku              as produkt_id,
    stars            as sterne,
    text,
    created_at::timestamptz as erstellt_um
from {{ source('shop', 'reviews') }}
