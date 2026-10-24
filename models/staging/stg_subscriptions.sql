select
    sub_id                                        as abo_id,
    cus_id                                        as abo_kunde_id,
    plan,
    price_monthly                                 as preis_monat_netto,
    case status when 'active' then 'aktiv' when 'paused' then 'pausiert' when 'canceled' then 'gekuendigt' end as status,
    started_on                                    as gestartet_am,
    strptime(canceled_at, '%d.%m.%Y')::date       as gekuendigt_am,
    strptime(paused_at, '%d.%m.%Y')::date         as zuletzt_pausiert_am
from {{ source('abo', 'subscriptions') }}
