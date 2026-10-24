-- Café-Kasse: deutsches Datumsformat, Lokalzeit ohne Zone, keine Positionsnummer.
with quelle as (
    select
        *,
        strptime(ts, '%d.%m.%Y %H:%M') as verkauft_um_lokal
    from {{ source('pos', 'sales') }}
)
select
    bon_id,
    row_number() over (partition by bon_id order by sku, qty)  as position,
    verkauft_um_lokal,
    timezone('Europe/Berlin', verkauft_um_lokal)                as verkauft_um,
    verkauft_um_lokal::date                                    as verkaufsdatum_lokal,
    sku                                                        as produkt_id,
    qty                                                        as menge,
    amount_gross                                               as betrag_brutto_inkl_mwst,
    nullif(upper(trim(card_id)), '')                           as karten_id,
    register                                                   as kasse
from quelle
