-- Schlüsseltabelle: welche Quell-ID gehört zu welchem Kunden?
-- Damit findet jede Faktenzeile ihren Kunden, egal aus welchem System sie kommt.
select 'shop' as source_system, shop_id as source_id, customer_id from {{ ref('int_customers_unified') }} where shop_id is not null
union all
select 'billing', billing_id, customer_id from {{ ref('int_customers_unified') }} where billing_id is not null
union all
select 'pos',     pos_id,     customer_id from {{ ref('int_customers_unified') }} where pos_id is not null
union all
select 'erp',     erp_id,     customer_id from {{ ref('int_customers_unified') }} where erp_id is not null
