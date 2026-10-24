select
    invoice_id      as rechnung_id,
    debitor_id,
    invoice_date    as rechnungsdatum,
    due_date        as faellig_am,
    paid_date       as bezahlt_am
from {{ source('erp', 'invoices') }}
