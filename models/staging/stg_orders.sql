-- Bestellköpfe: Dubletten aus dem wiederholten Ladelauf entfernen, Status lesbar machen,
-- Zeitstempel in UTC und lokales Bestelldatum (Europe/Berlin) trennen.
with quelle as (
    select *
    from {{ source('shop', 'orders') }}
    qualify row_number() over (partition by order_id order by _loaded_at desc) = 1
)
select
    order_id,
    customer_id,
    created_at::timestamptz                                        as bestellt_um,
    (created_at::timestamptz at time zone 'Europe/Berlin')::date   as bestelldatum_lokal,
    case channel when 'web' then 'Webshop' when 'subscription' then 'Abo' end as kanal,
    status                                                         as status_code,
    case status
        when 1 then 'offen'
        when 2 then 'bezahlt'
        when 3 then 'storniert'
        when 4 then 'teilweise erstattet'
        when 5 then 'erstattet'
    end                                                            as status,
    total_gross                                                    as gesamt_brutto_inkl_mwst,
    _loaded_at                                                     as geladen_um
from quelle
