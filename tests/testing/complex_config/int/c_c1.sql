-- intermediate variant 1: transform data differently
select
    id,
    concat(name_upper, '_c1') as label
from {{ ref('c_b') }}
