import csv
import os
from datetime import datetime
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = Path(os.getenv("OLIST_DATA_PATH", str(BASE_DIR.parent / "07_ecommerce_platform_build" / "data" / "raw"))).resolve()

CSV_FILES = {
    "customers": "olist_customers_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}


def connect():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "olist"),
        user=os.getenv("POSTGRES_USER", "olist_user"),
        password=os.getenv("POSTGRES_PASSWORD", "olist_pass"),
    )


def to_int(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def to_float(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_ts(value):
    if value is None or str(value).strip() == "":
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            return datetime.strptime(str(value), fmt)
        except ValueError:
            continue
    return None


def row_to_mapping(row):
    cleaned = {}
    for key, value in row.items():
        if value is None:
            cleaned[key] = None
        elif isinstance(value, str):
            cleaned[key] = value.strip()
        else:
            cleaned[key] = value
    return cleaned


def load_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return [row_to_mapping(r) for r in reader]


def upsert_customers(cur):
    rows = []
    for row in load_csv(DATA_PATH / CSV_FILES["customers"]):
        rows.append(
            (
                row.get("customer_id"),
                row.get("customer_unique_id"),
                to_int(row.get("customer_zip_code_prefix")),
                row.get("customer_city"),
                row.get("customer_state"),
            )
        )
    cur.executemany(
        """
        INSERT INTO olist.customers (customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
        ON CONFLICT (customer_id) DO UPDATE SET
            customer_unique_id = EXCLUDED.customer_unique_id,
            customer_zip_code_prefix = EXCLUDED.customer_zip_code_prefix,
            customer_city = EXCLUDED.customer_city,
            customer_state = EXCLUDED.customer_state,
            updated_at = NOW()
        """,
        rows,
    )
    return len(rows)


def upsert_orders(cur):
    rows = []
    for row in load_csv(DATA_PATH / CSV_FILES["orders"]):
        rows.append(
            (
                row.get("order_id"),
                row.get("customer_id"),
                row.get("order_status"),
                parse_ts(row.get("order_purchase_timestamp")),
                parse_ts(row.get("order_approved_at")),
                parse_ts(row.get("order_delivered_carrier_date")),
                parse_ts(row.get("order_delivered_customer_date")),
                parse_ts(row.get("order_estimated_delivery_date")),
            )
        )
    cur.executemany(
        """
        INSERT INTO olist.orders (order_id, customer_id, order_status, order_purchase_timestamp, order_approved_at, order_delivered_carrier_date, order_delivered_customer_date, order_estimated_delivery_date, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        ON CONFLICT (order_id) DO UPDATE SET
            customer_id = EXCLUDED.customer_id,
            order_status = EXCLUDED.order_status,
            order_purchase_timestamp = EXCLUDED.order_purchase_timestamp,
            order_approved_at = EXCLUDED.order_approved_at,
            order_delivered_carrier_date = EXCLUDED.order_delivered_carrier_date,
            order_delivered_customer_date = EXCLUDED.order_delivered_customer_date,
            order_estimated_delivery_date = EXCLUDED.order_estimated_delivery_date,
            updated_at = NOW()
        """,
        rows,
    )
    return len(rows)


def upsert_products(cur):
    rows = []
    for row in load_csv(DATA_PATH / CSV_FILES["products"]):
        rows.append(
            (
                row.get("product_id"),
                row.get("product_category_name"),
                to_int(row.get("product_name_lenght")),
                to_int(row.get("product_description_lenght")),
                to_int(row.get("product_photos_qty")),
                to_int(row.get("product_weight_g")),
                to_int(row.get("product_length_cm")),
                to_int(row.get("product_height_cm")),
                to_int(row.get("product_width_cm")),
            )
        )
    cur.executemany(
        """
        INSERT INTO olist.products (product_id, product_category_name, product_name_lenght, product_description_lenght, product_photos_qty, product_weight_g, product_length_cm, product_height_cm, product_width_cm, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        ON CONFLICT (product_id) DO UPDATE SET
            product_category_name = EXCLUDED.product_category_name,
            product_name_lenght = EXCLUDED.product_name_lenght,
            product_description_lenght = EXCLUDED.product_description_lenght,
            product_photos_qty = EXCLUDED.product_photos_qty,
            product_weight_g = EXCLUDED.product_weight_g,
            product_length_cm = EXCLUDED.product_length_cm,
            product_height_cm = EXCLUDED.product_height_cm,
            product_width_cm = EXCLUDED.product_width_cm,
            updated_at = NOW()
        """,
        rows,
    )
    return len(rows)


def upsert_sellers(cur):
    rows = []
    for row in load_csv(DATA_PATH / CSV_FILES["sellers"]):
        rows.append(
            (
                row.get("seller_id"),
                to_int(row.get("seller_zip_code_prefix")),
                row.get("seller_city"),
                row.get("seller_state"),
            )
        )
    cur.executemany(
        """
        INSERT INTO olist.sellers (seller_id, seller_zip_code_prefix, seller_city, seller_state, created_at, updated_at)
        VALUES (%s, %s, %s, %s, NOW(), NOW())
        ON CONFLICT (seller_id) DO UPDATE SET
            seller_zip_code_prefix = EXCLUDED.seller_zip_code_prefix,
            seller_city = EXCLUDED.seller_city,
            seller_state = EXCLUDED.seller_state,
            updated_at = NOW()
        """,
        rows,
    )
    return len(rows)


def upsert_order_items(cur):
    rows = []
    for row in load_csv(DATA_PATH / CSV_FILES["order_items"]):
        rows.append(
            (
                row.get("order_id"),
                to_int(row.get("order_item_id")),
                row.get("product_id"),
                row.get("seller_id"),
                parse_ts(row.get("shipping_limit_date")),
                to_float(row.get("price")),
                to_float(row.get("freight_value")),
            )
        )
    cur.executemany(
        """
        INSERT INTO olist.order_items (order_id, order_item_id, product_id, seller_id, shipping_limit_date, price, freight_value, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        ON CONFLICT (order_id, order_item_id) DO UPDATE SET
            product_id = EXCLUDED.product_id,
            seller_id = EXCLUDED.seller_id,
            shipping_limit_date = EXCLUDED.shipping_limit_date,
            price = EXCLUDED.price,
            freight_value = EXCLUDED.freight_value,
            updated_at = NOW()
        """,
        rows,
    )
    return len(rows)


def upsert_order_payments(cur):
    rows = []
    for row in load_csv(DATA_PATH / CSV_FILES["order_payments"]):
        rows.append(
            (
                row.get("order_id"),
                to_int(row.get("payment_sequential")),
                row.get("payment_type"),
                to_int(row.get("payment_installments")),
                to_float(row.get("payment_value")),
            )
        )
    cur.executemany(
        """
        INSERT INTO olist.order_payments (order_id, payment_sequential, payment_type, payment_installments, payment_value, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
        ON CONFLICT (order_id, payment_sequential) DO UPDATE SET
            payment_type = EXCLUDED.payment_type,
            payment_installments = EXCLUDED.payment_installments,
            payment_value = EXCLUDED.payment_value,
            updated_at = NOW()
        """,
        rows,
    )
    return len(rows)


def upsert_order_reviews(cur):
    rows = []
    for row in load_csv(DATA_PATH / CSV_FILES["order_reviews"]):
        rows.append(
            (
                row.get("review_id"),
                row.get("order_id"),
                to_int(row.get("review_score")),
                row.get("review_comment_title"),
                row.get("review_comment_message"),
                parse_ts(row.get("review_creation_date")),
                parse_ts(row.get("review_answer_timestamp")),
            )
        )
    cur.executemany(
        """
        INSERT INTO olist.order_reviews (review_id, order_id, review_score, review_comment_title, review_comment_message, review_creation_date, review_answer_timestamp, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        ON CONFLICT (order_id, review_id) DO UPDATE SET
            review_score = EXCLUDED.review_score,
            review_comment_title = EXCLUDED.review_comment_title,
            review_comment_message = EXCLUDED.review_comment_message,
            review_creation_date = EXCLUDED.review_creation_date,
            review_answer_timestamp = EXCLUDED.review_answer_timestamp,
            updated_at = NOW()
        """,
        rows,
    )
    return len(rows)


def upsert_geolocation(cur):
    rows = []
    for row in load_csv(DATA_PATH / CSV_FILES["geolocation"]):
        rows.append(
            (
                to_int(row.get("geolocation_zip_code_prefix")),
                to_float(row.get("geolocation_lat")),
                to_float(row.get("geolocation_lng")),
                row.get("geolocation_city"),
                row.get("geolocation_state"),
            )
        )

    cur.executemany(
        """
        INSERT INTO olist.geolocation (
            geolocation_zip_code_prefix,
            geolocation_lat,
            geolocation_lng,
            geolocation_city,
            geolocation_state,
            created_at,
            updated_at
        )
        VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
        """,
        rows,
    )

    return len(rows)

def upsert_category_translation(cur):
    rows = []

    for row in load_csv(DATA_PATH / CSV_FILES["category_translation"]):
        category_name = row.get("product_category_name")

        if not category_name:
            continue

        rows.append(
            (
                category_name,
                row.get("product_category_name_english"),
            )
        )

    cur.executemany(
        """
        INSERT INTO olist.category_translation (
            product_category_name,
            product_category_name_english,
            created_at,
            updated_at
        )
        VALUES (%s, %s, NOW(), NOW())
        ON CONFLICT (product_category_name) DO UPDATE SET
            product_category_name_english = EXCLUDED.product_category_name_english,
            updated_at = NOW()
        """,
        rows,
    )

    return len(rows)

def main():
    missing = [name for name, file_name in CSV_FILES.items() if not (DATA_PATH / file_name).exists()]
    if missing:
        raise FileNotFoundError(f"Missing Olist files: {missing}")

    with connect() as conn:
        with conn.cursor() as cur:
            totals = {
                "customers": upsert_customers(cur),
                "orders": upsert_orders(cur),
                "products": upsert_products(cur),
                "sellers": upsert_sellers(cur),
                "order_items": upsert_order_items(cur),
                "order_payments": upsert_order_payments(cur),
                "order_reviews": upsert_order_reviews(cur),
                "geolocation": upsert_geolocation(cur),
                "category_translation": upsert_category_translation(cur),
            }
            conn.commit()
            print(totals)


if __name__ == "__main__":
    main()
