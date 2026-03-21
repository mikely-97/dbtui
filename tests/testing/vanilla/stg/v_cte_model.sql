with source as (
    select id, name, amount from {{ ref('stg_orders') }}
),
renamed as (
    select
        id as order_id,
        name as order_name,
        amount
    from source
)
select * from renamed
