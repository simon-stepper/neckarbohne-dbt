select
    debitor_id,
    company              as firma,
    city                 as stadt,
    payment_terms_days   as zahlungsziel_tage
from {{ source('erp', 'debitors') }}
