select
    o.id,
    o.amount,
    u.name as user_name
from {{ ref('stg_orders') }} o
join {{ ref('stg_users') }} u on o.user_id = u.id
