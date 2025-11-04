{{ config(name="i_b_changed") }}
select
    id,
    upper(name) as name_upper
from {{ ref('i_a') }}
