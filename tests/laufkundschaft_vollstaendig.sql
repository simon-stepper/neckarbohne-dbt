{{ config(severity='warn') }}  -- Fortgeschritten: auf error stellen, sobald -1 eingebaut ist
-- Kein Café-Umsatz darf beim Join auf dim_kunde verloren gehen (Unknown-Member statt NULL).
select 'Café' as kanal
from {{ ref('int_order_lines') }} l
where l.kanal = 'Café'
having count(*) <> (select count(*) from {{ ref('fct_order_lines') }} f
                    join {{ ref('dim_kanal') }} k using (kanal_key) where k.kanal = 'Café')
