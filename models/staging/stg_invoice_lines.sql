select
    invoice_id      as rechnung_id,
    line_no         as position,
    sku             as produkt_id,
    qty             as menge,
    unit_price_net  as einzelpreis_netto,
    discount_net    as rabatt_netto
from {{ source('erp', 'invoice_lines') }}
