-- intermediate variant 1: transform data differently
select
    id,
    concat(name_upper, '_c1') as label
from {{ ref('i_b', 'extra_argument') }}
left join {{ ref() }} using a