select
    refund_id        as erstattung_id,
    order_id,
    pos              as position,
    amount           as erstattung_netto,
    refunded_at::timestamptz as erstattet_um
from {{ source('shop', 'refunds') }}
