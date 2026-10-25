select
    cus_id                       as subscription_customer_id,
    lower(trim(email))           as email,
    name
from {{ source('billing', 'customers') }}
