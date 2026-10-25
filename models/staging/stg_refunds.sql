select
    refund_id,
    order_id,
    pos              as line_no,
    amount           as refund_net,
    refunded_at::timestamptz as refunded_at
from {{ source('shop', 'refunds') }}
