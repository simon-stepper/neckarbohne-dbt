-- Datumsdimension: einmal generieren, nie von Hand pflegen.
with tage as (
    select unnest(generate_series(date '{{ var("datum_von") }}', date '{{ var("datum_bis") }}', interval 1 day))::date as datum
)
select
    cast(strftime(t.datum, '%Y%m%d') as integer)            as datum_key,
    t.datum,
    year(t.datum)                                           as jahr,
    year(t.datum) || '-Q' || quarter(t.datum)               as quartal,
    strftime(t.datum, '%Y-%m')                              as monat,
    strftime(t.datum, '%G-W%V')                             as kw_iso,
    ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'][isodow(t.datum)] as wochentag,
    f.datum is not null                                     as feiertag_bw,
    f.name                                                  as feiertag_name,
    isodow(t.datum) <= 5 and f.datum is null                as ist_werktag,
    year(t.datum)                                           as geschaeftsjahr   -- Annahme: GJ = Kalenderjahr
from tage t
left join {{ ref('feiertage_bw') }} f on f.datum = t.datum
