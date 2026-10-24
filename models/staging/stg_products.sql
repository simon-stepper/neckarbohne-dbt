select
    sku                 as produkt_id,
    title               as name,
    sort                as sorte,
    category            as kategorie,
    roast               as roestgrad,
    list_price_net      as listenpreis_netto,
    unit_cost           as einstandspreis,
    vat_rate            as mwst_satz
from {{ source('shop', 'products') }}
