-- intermediate layer: depends on stg.v_a
select
    id,
    upper(name) as name_upper
from {{ ref('c_a') }}
