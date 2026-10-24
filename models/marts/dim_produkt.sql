select
    row_number() over (order by produkt_id)::integer  as produkt_key,
    produkt_id,
    name,
    sorte,
    kategorie,
    roestgrad,
    listenpreis_netto,
    einstandspreis
from {{ ref('stg_products') }}
