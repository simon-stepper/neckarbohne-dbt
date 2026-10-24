-- Konforme Kundendimension über alle Kanäle.
--
-- TODO Basis:           eine Zeile pro Kunde aus int_kunden_vereint und ein eigener Surrogate Key kunde_key
--                       (Tipp: row_number() over (order by kunde_id) + 1000)
-- TODO Fortgeschritten: Unknown-Member -1 "Unbekannt / Laufkundschaft" anhängen (union all)
-- TODO Fortgeschritten: SCD 2 – Versionen aus ref('customers_snapshot') mit valid_from / valid_to.
--                       Vorher: dbt snapshot, dann python generate_data.py --kundenupdate, dann dbt build.
select
    -- TODO: kunde_key
    kunde_id,
    name,
    stadt,
    plz,
    segment,
    shop_id,
    abo_id,
    pos_id,
    erp_id
from {{ ref('int_kunden_vereint') }}
