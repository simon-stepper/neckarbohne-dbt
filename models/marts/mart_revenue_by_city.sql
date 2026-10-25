-- GF-Wunsch (Ticket DATA-142): Umsatz nach Kundenstadt und Monat für das Regional-Dashboard.
-- Stadt kommt aus dem Snapshot, damit wir auch Umzüge abbilden.
select
    date_trunc('month', l.order_date_local)  as month,
    s.city                                   as city,
    count(distinct l.order_id)               as orders,
    sum(l.revenue)                           as revenue
from {{ ref('int_order_lines') }} l
join {{ ref('customers_snapshot') }} s
    on s.customer_id = l.customer_source_id
group by 1, 2
