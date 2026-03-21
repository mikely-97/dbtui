select
    id,
    upper(name) as name_upper,
    email
from {{ ref('v_a') }}
