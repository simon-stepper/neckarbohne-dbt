-- Datumsdimension: einmal generieren, nie von Hand pflegen.
with days as (
    select unnest(generate_series(date '{{ var("date_from") }}', date '{{ var("date_to") }}', interval 1 day))::date as calendar_date
)
select
    cast(strftime(d.calendar_date, '%Y%m%d') as integer)    as date_key,
    d.calendar_date,
    year(d.calendar_date)                                   as year,
    year(d.calendar_date) || '-Q' || quarter(d.calendar_date) as quarter,
    strftime(d.calendar_date, '%Y-%m')                      as month,
    strftime(d.calendar_date, '%G-W%V')                     as iso_week,
    ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][isodow(d.calendar_date)] as weekday,
    h.holiday_date is not null                              as is_holiday_bw,
    h.name                                                  as holiday_name,
    isodow(d.calendar_date) <= 5 and h.holiday_date is null as is_workday,
    year(d.calendar_date)                                   as fiscal_year   -- Annahme: GJ = Kalenderjahr
from days d
left join {{ ref('holidays_bw') }} h on h.holiday_date = d.calendar_date
