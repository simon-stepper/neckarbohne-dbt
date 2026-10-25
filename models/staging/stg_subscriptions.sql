select
    sub_id                                        as subscription_id,
    cus_id                                        as subscription_customer_id,
    plan,
    price_monthly                                 as monthly_price_net,
    status,                                       -- active | paused | canceled
    started_on,
    strptime(canceled_at, '%d.%m.%Y')::date       as canceled_on,
    strptime(paused_at, '%d.%m.%Y')::date         as last_paused_on
from {{ source('billing', 'subscriptions') }}
