-- Shop-Kunden: Namen vereinheitlichen, E-Mail normalisieren
select
    customer_id,
    lower(trim(email))                       as email,
    first_name || ' ' || last_name           as name,
    city,
    zip,
    created_at::timestamptz                  as created_at,
    updated_at::timestamptz                  as updated_at
from {{ source('shop', 'customers') }}
