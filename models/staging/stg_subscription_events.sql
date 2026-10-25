select
    event_id,
    sub_id                                         as subscription_id,
    type                                           as event_type,     -- created | paused | resumed | canceled
    occurred_at,
    (occurred_at at time zone 'Europe/Berlin')::date as event_date_local
from {{ source('billing', 'subscription_events') }}
