select
    upper(trim(card_id))         as karten_id,
    nullif(lower(trim(email)), '') as email,
    issued_on                    as ausgegeben_am
from {{ source('pos', 'cards') }}
