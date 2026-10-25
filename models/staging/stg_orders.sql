-- Bestellköpfe: Dubletten aus dem wiederholten Ladelauf entfernen, Status lesbar machen,
-- Zeitstempel in UTC und lokales Bestelldatum (Europe/Berlin) trennen.
with source as (
    select *
    from {{ source('shop', 'orders') }}
    qualify row_number() over (partition by order_id order by _loaded_at desc) = 1
)
select
    order_id,
    customer_id,
    created_at::timestamptz                                        as ordered_at,
    (created_at::timestamptz at time zone 'Europe/Berlin')::date   as order_date_local,
    channel,                                                       -- web | subscription
    status                                                         as status_code,
    case status
        when 1 then 'open'
        when 2 then 'paid'
        when 3 then 'canceled'
        when 4 then 'partially_refunded'
        when 5 then 'refunded'
    end                                                            as status,
    total_gross                                                    as total_gross_incl_vat,
    _loaded_at                                                     as loaded_at
from source
