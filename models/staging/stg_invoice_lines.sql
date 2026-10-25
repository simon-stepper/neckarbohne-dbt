select
    invoice_id,
    line_no,
    sku             as product_id,
    qty             as quantity,
    unit_price_net,
    discount_net
from {{ source('erp', 'invoice_lines') }}
