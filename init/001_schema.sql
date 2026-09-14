CREATE SCHEMA IF NOT EXISTS olist;

CREATE TABLE IF NOT EXISTS olist.customers (
    customer_id VARCHAR(64) PRIMARY KEY,
    customer_unique_id VARCHAR(64),
    customer_zip_code_prefix INTEGER,
    customer_city VARCHAR(100),
    customer_state VARCHAR(2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS olist.orders (
    order_id VARCHAR(64) PRIMARY KEY,
    customer_id VARCHAR(64) REFERENCES olist.customers(customer_id) ON DELETE SET NULL,
    order_status VARCHAR(30) NOT NULL,
    order_purchase_timestamp TIMESTAMPTZ,
    order_approved_at TIMESTAMPTZ,
    order_delivered_carrier_date TIMESTAMPTZ,
    order_delivered_customer_date TIMESTAMPTZ,
    order_estimated_delivery_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS olist.products (
    product_id VARCHAR(64) PRIMARY KEY,
    product_category_name VARCHAR(100),
    product_name_lenght INTEGER,
    product_description_lenght INTEGER,
    product_photos_qty INTEGER,
    product_weight_g INTEGER,
    product_length_cm INTEGER,
    product_height_cm INTEGER,
    product_width_cm INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS olist.sellers (
    seller_id VARCHAR(64) PRIMARY KEY,
    seller_zip_code_prefix INTEGER,
    seller_city VARCHAR(100),
    seller_state VARCHAR(2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS olist.order_items (
    order_id VARCHAR(64) NOT NULL REFERENCES olist.orders(order_id),
    order_item_id INTEGER NOT NULL,
    product_id VARCHAR(64) REFERENCES olist.products(product_id) ON DELETE SET NULL,
    seller_id VARCHAR(64) REFERENCES olist.sellers(seller_id) ON DELETE SET NULL,
    shipping_limit_date TIMESTAMPTZ,
    price NUMERIC(12,2),
    freight_value NUMERIC(12,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (order_id, order_item_id)
);

CREATE TABLE IF NOT EXISTS olist.order_payments (
    order_id VARCHAR(64) NOT NULL REFERENCES olist.orders(order_id),
    payment_sequential INTEGER NOT NULL,
    payment_type VARCHAR(40),
    payment_installments INTEGER,
    payment_value NUMERIC(12,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (order_id, payment_sequential)
);

CREATE TABLE IF NOT EXISTS olist.order_reviews (
    review_id VARCHAR(64) NOT NULL,
    order_id VARCHAR(64) NOT NULL REFERENCES olist.orders(order_id),
    review_score INTEGER,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TIMESTAMPTZ,
    review_answer_timestamp TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (order_id, review_id)
);

CREATE TABLE IF NOT EXISTS olist.geolocation (
    geolocation_id BIGSERIAL PRIMARY KEY,
    geolocation_zip_code_prefix INTEGER,
    geolocation_lat DOUBLE PRECISION,
    geolocation_lng DOUBLE PRECISION,
    geolocation_city VARCHAR(100),
    geolocation_state VARCHAR(2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS olist.category_translation (
    product_category_name VARCHAR(100) NOT NULL,
    product_category_name_english VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (product_category_name)
);

CREATE TABLE IF NOT EXISTS olist.seed_state (
    seed_key VARCHAR(100) PRIMARY KEY,
    last_seeded_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
