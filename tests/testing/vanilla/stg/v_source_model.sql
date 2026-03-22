select id, name from {{ source('raw_data', 'users') }}
