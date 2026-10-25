select
    upper(trim(card_id))         as card_id,
    nullif(lower(trim(email)), '') as email,
    issued_on
from {{ source('pos', 'cards') }}
