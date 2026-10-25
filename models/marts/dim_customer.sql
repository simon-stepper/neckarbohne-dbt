-- Konforme Kundendimension über alle Kanäle.
--
-- TODO Basis:           eine Zeile pro Kunde aus int_customers_unified und ein eigener Surrogate Key customer_key
--                       (Tipp: row_number() over (order by customer_id) + 1000)
-- TODO Fortgeschritten: Unknown-Member -1 "Unknown / walk-in" anhängen (union all)
-- TODO Fortgeschritten: SCD 2 – Versionen aus ref('customers_snapshot') mit valid_from / valid_to.
--                       Vorher: dbt snapshot, dann python generate_data.py --customer-update, dann dbt build.
select
    -- TODO: customer_key
    customer_id,
    name,
    city,
    zip,
    segment,
    shop_id,
    billing_id,
    pos_id,
    erp_id
from {{ ref('int_customers_unified') }}
