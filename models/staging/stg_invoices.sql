select
    invoice_id,
    debitor_id,
    invoice_date,
    due_date,
    paid_date
from {{ source('erp', 'invoices') }}
