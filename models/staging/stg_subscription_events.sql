select
    event_id                                       as ereignis_id,
    sub_id                                         as abo_id,
    case type when 'created' then 'gestartet' when 'paused' then 'pausiert'
              when 'resumed' then 'fortgesetzt' when 'canceled' then 'gekuendigt' end as ereignis,
    occurred_at                                    as passiert_um,
    (occurred_at at time zone 'Europe/Berlin')::date as datum_lokal
from {{ source('abo', 'subscription_events') }}
