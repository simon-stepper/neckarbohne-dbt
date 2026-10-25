{{ config(severity='warn') }}  -- Fortgeschritten: auf error stellen, sobald -1 eingebaut ist
-- Kein Café-Umsatz darf beim Join auf dim_customer verloren gehen (Unknown-Member statt NULL).
select 'cafe' as channel
from {{ ref('int_order_lines') }} l
where l.channel = 'cafe'
having count(*) <> (select count(*) from {{ ref('fct_order_lines') }} f
                    join {{ ref('dim_channel') }} ch using (channel_key) where ch.channel = 'cafe')
