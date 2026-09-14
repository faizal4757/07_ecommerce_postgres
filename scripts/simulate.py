import os
import random
from datetime import datetime, timedelta, timezone

import psycopg
from dotenv import load_dotenv

load_dotenv()


def connect():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "olist"),
        user=os.getenv("POSTGRES_USER", "olist_user"),
        password=os.getenv("POSTGRES_PASSWORD", "olist_pass"),
    )


def fetch_random(cur, query, params=None):
    cur.execute(query, params or ())
    row = cur.fetchone()
    return row


def rand_bool(rate):
    return random.random() < rate


def main():
    daily_orders = int(os.getenv("SIMULATOR_DAILY_ORDERS", "100"))
    duplicate_rate = float(os.getenv("SIMULATOR_DUPLICATE_RATE", "0.02"))
    late_update_rate = float(os.getenv("SIMULATOR_LATE_UPDATE_RATE", "0.02"))
    missing_value_rate = float(os.getenv("SIMULATOR_MISSING_VALUE_RATE", "0.02"))
    delayed_payment_rate = float(os.getenv("SIMULATOR_DELAYED_PAYMENT_RATE", "0.02"))

    now = datetime.now(timezone.utc)

    with connect() as conn:
        with conn.cursor() as cur:

            if fetch_random(
                cur,
                "SELECT customer_id FROM olist.customers LIMIT 1",
            ) is None:
                raise RuntimeError(
                    "Seed data is missing. Run python scripts/seed.py first."
                )

            created_orders = 0
            created_payments = 0
            updated_orders = 0
            review_rows = 0

            for _ in range(daily_orders):

                # ---------------------------------------------------------
                # Select a random customer
                # ---------------------------------------------------------
                customer_row = fetch_random(
                    cur,
                    """
                    SELECT customer_id
                    FROM olist.customers
                    ORDER BY RANDOM()
                    LIMIT 1
                    """,
                )

                # ---------------------------------------------------------
                # Select a valid product + seller combination from
                # historical Olist transactions.
                #
                # This prevents the simulator from inventing arbitrary
                # product/seller relationships.
                # ---------------------------------------------------------
                product_seller_row = fetch_random(
                    cur,
                    """
                    SELECT
                        product_id,
                        seller_id,
                        AVG(price) AS average_price
                    FROM olist.order_items
                    WHERE product_id IS NOT NULL
                      AND seller_id IS NOT NULL
                      AND price IS NOT NULL
                    GROUP BY product_id, seller_id
                    ORDER BY RANDOM()
                    LIMIT 1
                    """,
                )

                if not customer_row or not product_seller_row:
                    raise RuntimeError(
                        "Unable to select required reference data."
                    )

                customer_id = customer_row[0]
                product_id = product_seller_row[0]
                seller_id = product_seller_row[1]
                average_price = float(product_seller_row[2])

                # ---------------------------------------------------------
                # Generate a realistic price around the historical price
                # for this exact product/seller relationship.
                # ---------------------------------------------------------
                price = round(
                    average_price * random.uniform(0.85, 1.15),
                    2,
                )

                # Keep the generated price sensible.
                price = max(price, 1.00)

                # ---------------------------------------------------------
                # Generate freight based loosely on item value.
                # ---------------------------------------------------------
                freight_value = round(
                    max(
                        5.00,
                        price * random.uniform(0.05, 0.15),
                    ),
                    2,
                )

                payment_value = round(
                    price + freight_value,
                    2,
                )

                # ---------------------------------------------------------
                # Generate order
                # ---------------------------------------------------------
                order_id = (
                    f"sim_{now.strftime('%Y%m%d%H%M%S')}_"
                    f"{random.randint(1000, 999999)}"
                )

                purchase_ts = now - timedelta(
                    days=random.randint(0, 2),
                    hours=random.randint(0, 12),
                )

                cur.execute(
                    """
                    INSERT INTO olist.orders (
                        order_id,
                        customer_id,
                        order_status,
                        order_purchase_timestamp,
                        order_approved_at,
                        order_delivered_carrier_date,
                        order_delivered_customer_date,
                        order_estimated_delivery_date,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s,
                        NOW(), NOW()
                    )
                    ON CONFLICT (order_id) DO NOTHING
                    """,
                    (
                        order_id,
                        customer_id,
                        "created",
                        purchase_ts,
                        None,
                        None,
                        None,
                        purchase_ts + timedelta(days=7),
                    ),
                )

                if cur.rowcount:
                    created_orders += 1

                # ---------------------------------------------------------
                # Create order item using the valid product/seller pair
                # ---------------------------------------------------------
                cur.execute(
                    """
                    INSERT INTO olist.order_items (
                        order_id,
                        order_item_id,
                        product_id,
                        seller_id,
                        shipping_limit_date,
                        price,
                        freight_value,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        %s, 1, %s, %s, %s, %s, %s,
                        NOW(), NOW()
                    )
                    ON CONFLICT (order_id, order_item_id) DO NOTHING
                    """,
                    (
                        order_id,
                        product_id,
                        seller_id,
                        purchase_ts + timedelta(days=1),
                        price,
                        freight_value,
                    ),
                )

                # ---------------------------------------------------------
                # Create payment
                # ---------------------------------------------------------
                payment_ts = purchase_ts + timedelta(
                    hours=random.randint(1, 12)
                )

                if rand_bool(delayed_payment_rate):
                    payment_ts += timedelta(days=1)

                cur.execute(
                    """
                    INSERT INTO olist.order_payments (
                        order_id,
                        payment_sequential,
                        payment_type,
                        payment_installments,
                        payment_value,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        %s, 1, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (order_id, payment_sequential) DO NOTHING
                    """,
                    (
                        order_id,
                        random.choice(
                            [
                                "credit_card",
                                "boleto",
                                "voucher",
                                "debit_card",
                            ]
                        ),
                        random.choice([1, 1, 1, 2, 3]),
                        payment_value,
                        payment_ts,
                        now,
                    ),
                )

                if cur.rowcount:
                    created_payments += 1

                # ---------------------------------------------------------
                # Additional payment event
                # ---------------------------------------------------------
                if rand_bool(duplicate_rate):
                    cur.execute(
                        """
                        INSERT INTO olist.order_payments (
                            order_id,
                            payment_sequential,
                            payment_type,
                            payment_installments,
                            payment_value,
                            created_at,
                            updated_at
                        )
                        VALUES (
                            %s, 2, %s, %s, %s, NOW(), NOW()
                        )
                        ON CONFLICT (order_id, payment_sequential) DO NOTHING
                        """,
                        (
                            order_id,
                            "credit_card",
                            1,
                            payment_value,
                        ),
                    )

                # ---------------------------------------------------------
                # Simulate a late order update
                # ---------------------------------------------------------
                if rand_bool(late_update_rate):
                    cur.execute(
                        """
                        UPDATE olist.orders
                        SET
                            order_status = 'processing',
                            order_approved_at = %s,
                            updated_at = NOW()
                        WHERE order_id = %s
                        """,
                        (
                            purchase_ts + timedelta(hours=2),
                            order_id,
                        ),
                    )

                    updated_orders += 1

                # ---------------------------------------------------------
                # Simulate missing optional value
                # ---------------------------------------------------------
                if rand_bool(missing_value_rate):
                    cur.execute(
                        """
                        UPDATE olist.orders
                        SET
                            order_approved_at = NULL,
                            updated_at = NOW()
                        WHERE order_id = %s
                        """,
                        (order_id,),
                    )

                # ---------------------------------------------------------
                # Simulate a review
                # ---------------------------------------------------------
                if rand_bool(0.20):
                    review_id = (
                        f"sim_review_"
                        f"{now.strftime('%Y%m%d%H%M%S')}_"
                        f"{random.randint(1000, 999999)}"
                    )

                    review_ts = now - timedelta(days=1)

                    cur.execute(
                        """
                        INSERT INTO olist.order_reviews (
                            review_id,
                            order_id,
                            review_score,
                            review_comment_title,
                            review_comment_message,
                            review_creation_date,
                            review_answer_timestamp,
                            created_at,
                            updated_at
                        )
                        VALUES (
                            %s, %s, %s, %s, %s, %s, %s,
                            NOW(), NOW()
                        )
                        ON CONFLICT (order_id, review_id) DO NOTHING
                        """,
                        (
                            review_id,
                            order_id,
                            random.randint(1, 5),
                            "simulated review",
                            "daily simulation review",
                            review_ts,
                            review_ts,
                        ),
                    )

                    if cur.rowcount:
                        review_rows += 1

            conn.commit()

            print(
                {
                    "orders_created": created_orders,
                    "payments_created": created_payments,
                    "orders_updated": updated_orders,
                    "reviews_created": review_rows,
                }
            )


if __name__ == "__main__":
    main()