-- Schlüsseltabelle: welche Quell-ID gehört zu welchem Kunden?
-- Damit findet jede Faktenzeile ihren Kunden, egal aus welchem System sie kommt.
select 'shop' as quelle, shop_id as quelle_id, kunde_id from {{ ref('int_kunden_vereint') }} where shop_id is not null
union all
select 'abo',   abo_id, kunde_id from {{ ref('int_kunden_vereint') }} where abo_id is not null
union all
select 'kasse', pos_id, kunde_id from {{ ref('int_kunden_vereint') }} where pos_id is not null
union all
select 'erp',   erp_id, kunde_id from {{ ref('int_kunden_vereint') }} where erp_id is not null
