-- mart layer: merge multiple intermed results
select
    c1.id,
    c1.label,
    c2.reversed_name
from {{ ref('i_c1') }} as c1
join {{ ref('i_c2') }} as c2
    on c1.id = c2.id
