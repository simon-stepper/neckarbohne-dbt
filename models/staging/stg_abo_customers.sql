select
    cus_id                       as abo_kunde_id,
    lower(trim(email))           as email,
    name
from {{ source('abo', 'customers') }}
