-- Shop-Kunden: Namen vereinheitlichen, E-Mail normalisieren
select
    customer_id,
    lower(trim(email))                       as email,
    first_name || ' ' || last_name           as name,
    city                                     as stadt,
    zip                                      as plz,
    created_at::timestamptz                  as erstellt_um,
    updated_at::timestamptz                  as aktualisiert_um
from {{ source('shop', 'customers') }}
