-- Grain: eine Zeile pro Bestellposition – Webshop, Abo, Café und B2B.
-- Beträge in Euro, netto ohne MwSt.: Nettoumsatz = gross_revenue - discount_amount - refund_amount
--
-- TODO Basis: channel_key und customer_key ergänzen.
--   channel_key:  über dim_channel (l.channel)
--   customer_key: int_customer_keys ordnet jede Quell-ID (Shop, Kassenkarte, Debitor) einer customer_id zu,
--                 dim_customer liefert dazu den customer_key
-- TODO Fortgeschritten: Café-Verkäufe ohne Kassenkarte bekommen -1 statt NULL
-- TODO Fortgeschritten (SCD 2): die Version joinen, die am Bestelltag galt
select
    l.order_line_id,
    l.order_id,                                       -- degenerierte Dimension
    l.line_no,
    d.date_key,
    p.product_key,
    -- TODO: channel_key
    -- TODO: customer_key
    l.quantity,
    l.gross_revenue,
    l.discount_amount,
    l.refund_amount,
    l.cost_amount
from {{ ref('int_order_lines') }} l
join {{ ref('dim_date') }} d on d.calendar_date = l.order_date_local
join {{ ref('dim_product') }} p on p.product_id = l.product_id
