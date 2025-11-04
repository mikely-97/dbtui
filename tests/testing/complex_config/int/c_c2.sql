-- intermediate variant 2: transform data differently
select
    id,
    reverse(name_upper) as reversed_name
from {{ ref('c_b') }}
