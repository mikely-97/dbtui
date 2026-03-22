{% snapshot snap_orders %}
  {{
    config(
      target_schema='snapshots',
      unique_key='id',
      strategy='timestamp',
      updated_at='updated_at'
    )
  }}

  SELECT
    id,
    customer_id,
    amount,
    updated_at
  FROM {{ source('raw', 'orders') }}
{% endsnapshot %}
