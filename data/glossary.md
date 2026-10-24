# Business glossary and join paths (Olist e-commerce)

## Tables
- olist_orders_dataset: one row per order (order_id, customer_id, order_status, order_purchase_timestamp, order_approved_at, order_delivered_carrier_date, order_delivered_customer_date, order_estimated_delivery_date)
- olist_order_items_dataset: line items (order_id, order_item_id, product_id, seller_id, price, freight_value)
- olist_order_payments_dataset: payments per order (order_id, payment_type, payment_installments, payment_value)
- olist_order_reviews_dataset: reviews (order_id, review_score 1-5)
- olist_customers_dataset: customers (customer_id, customer_unique_id, customer_city, customer_state)
- olist_sellers_dataset: sellers (seller_id, seller_city, seller_state)
- olist_products_dataset: products (product_id, product_category_name in Portuguese)
- product_category_name_translation: product_category_name -> product_category_name_english

## Join paths
- olist_orders_dataset.order_id = olist_order_items_dataset.order_id
- olist_orders_dataset.order_id = olist_order_payments_dataset.order_id
- olist_orders_dataset.order_id = olist_order_reviews_dataset.order_id
- olist_orders_dataset.customer_id = olist_customers_dataset.customer_id
- olist_order_items_dataset.product_id = olist_products_dataset.product_id
- olist_order_items_dataset.seller_id = olist_sellers_dataset.seller_id
- olist_products_dataset.product_category_name = product_category_name_translation.product_category_name

## Metric definitions
- Revenue = SUM(olist_order_items_dataset.price) for orders with order_status = 'delivered' (freight excluded).
- Delivered order = order_status = 'delivered'.
- Order month = strftime('%Y-%m', order_purchase_timestamp).
- Delivery delay (days) = julianday(order_delivered_customer_date) - julianday(order_estimated_delivery_date); positive means late.
- Late order = delivered order whose delivery delay > 0.
- Average order value = total revenue / number of distinct delivered orders.
- Customer = olist_customers_dataset.customer_unique_id (customer_id is per order).
- Use product_category_name_english (via the translation table) when showing categories.
- Dates in the data span roughly 2016-09 to 2018-10; 2017 is the only full calendar year.
