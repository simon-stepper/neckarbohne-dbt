select
    debitor_id,
    company,
    city,
    payment_terms_days
from {{ source('erp', 'debitors') }}
