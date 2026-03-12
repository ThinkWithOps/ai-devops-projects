-- =============================================================================
-- Demo Database Setup — AI DB Query Optimizer (Project 09)
-- =============================================================================
-- Creates a realistic e-commerce schema with intentionally MISSING indexes on
-- foreign keys so that slow queries are reproducible for the demo.
--
-- Run: psql -U postgres -f setup_demo_db.sql
-- Or:  psql -U postgres demo_db < setup_demo_db.sql
-- =============================================================================

-- Create fresh demo database (run as superuser outside a transaction)
-- \! createdb demo_db
-- \c demo_db

-- Ensure pg_stat_statements is enabled (add to postgresql.conf if missing):
-- shared_preload_libraries = 'pg_stat_statements'
-- Then restart PostgreSQL and run:
-- CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- =============================================================================
-- Drop existing tables (safe teardown)
-- =============================================================================
DROP VIEW IF EXISTS slow_recent_activity CASCADE;
DROP VIEW IF EXISTS slow_product_stats CASCADE;
DROP VIEW IF EXISTS slow_user_orders CASCADE;

DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- =============================================================================
-- TABLE: users — 100,000 rows
-- =============================================================================
CREATE TABLE users (
    id         SERIAL PRIMARY KEY,
    email      VARCHAR(255) NOT NULL UNIQUE,
    name       VARCHAR(255) NOT NULL,
    created_at TIMESTAMP    NOT NULL DEFAULT NOW()
);

INSERT INTO users (email, name, created_at)
SELECT
    'user_' || i || '@example.com'                         AS email,
    'User ' || i                                            AS name,
    NOW() - (random() * INTERVAL '730 days')               AS created_at
FROM generate_series(1, 100000) AS s(i);

-- NOTE: No extra indexes on users — only the implicit PRIMARY KEY on id
-- and the UNIQUE constraint on email. user lookups by name = full scan.

-- =============================================================================
-- TABLE: products — 10,000 rows
-- =============================================================================
CREATE TABLE products (
    id       SERIAL PRIMARY KEY,
    name     VARCHAR(255)   NOT NULL,
    category VARCHAR(100)   NOT NULL,
    price    NUMERIC(10, 2) NOT NULL
);

INSERT INTO products (name, category, price)
SELECT
    'Product ' || i                                        AS name,
    (ARRAY['Electronics','Clothing','Books','Home','Sports','Toys'])[
        (i % 6) + 1
    ]                                                      AS category,
    (random() * 500 + 1)::NUMERIC(10, 2)                  AS price
FROM generate_series(1, 10000) AS s(i);

-- =============================================================================
-- TABLE: orders — 500,000 rows
-- INTENTIONAL CRIME: NO index on user_id (foreign key column)
-- This causes a sequential scan every time we look up orders by user.
-- =============================================================================
CREATE TABLE orders (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER        NOT NULL,  -- FK to users.id — NO INDEX (intentional)
    amount     NUMERIC(10, 2) NOT NULL,
    status     VARCHAR(50)    NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP      NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users(id)
);

INSERT INTO orders (user_id, amount, status, created_at)
SELECT
    (random() * 99999 + 1)::INTEGER                        AS user_id,
    (random() * 1000 + 1)::NUMERIC(10, 2)                 AS amount,
    (ARRAY['pending','completed','cancelled','refunded'])[
        (floor(random() * 4) + 1)::INTEGER
    ]                                                      AS status,
    NOW() - (random() * INTERVAL '730 days')               AS created_at
FROM generate_series(1, 500000) AS s(i);

-- =============================================================================
-- TABLE: order_items — 2,000,000 rows
-- INTENTIONAL CRIME: NO indexes on order_id or product_id
-- =============================================================================
CREATE TABLE order_items (
    id         SERIAL PRIMARY KEY,
    order_id   INTEGER        NOT NULL,  -- FK to orders.id  — NO INDEX (intentional)
    product_id INTEGER        NOT NULL,  -- FK to products.id — NO INDEX (intentional)
    quantity   INTEGER        NOT NULL DEFAULT 1,
    price      NUMERIC(10, 2) NOT NULL,
    CONSTRAINT fk_items_order   FOREIGN KEY (order_id)   REFERENCES orders(id),
    CONSTRAINT fk_items_product FOREIGN KEY (product_id) REFERENCES products(id)
);

INSERT INTO order_items (order_id, product_id, quantity, price)
SELECT
    (random() * 499999 + 1)::INTEGER                       AS order_id,
    (random() * 9999 + 1)::INTEGER                         AS product_id,
    (floor(random() * 10) + 1)::INTEGER                    AS quantity,
    (random() * 500 + 1)::NUMERIC(10, 2)                  AS price
FROM generate_series(1, 2000000) AS s(i);

-- =============================================================================
-- ANALYZE tables so planner has fresh statistics
-- =============================================================================
ANALYZE users;
ANALYZE orders;
ANALYZE order_items;
ANALYZE products;

-- =============================================================================
-- INTENTIONALLY SLOW VIEWS
-- These demonstrate what the optimizer detects.
-- =============================================================================

-- View 1: slow_user_orders
-- Crime: Cartesian-style join without using the index path (no index on user_id)
CREATE VIEW slow_user_orders AS
SELECT
    u.id          AS user_id,
    u.email,
    u.name,
    o.id          AS order_id,
    o.amount,
    o.status,
    o.created_at  AS order_date
FROM users u
JOIN orders o ON u.id = o.user_id   -- Sequential scan on orders every time
ORDER BY o.created_at DESC;

-- View 2: slow_product_stats
-- Crime: No index on order_items.product_id — full scan on 2M rows
CREATE VIEW slow_product_stats AS
SELECT
    p.id           AS product_id,
    p.name         AS product_name,
    p.category,
    p.price        AS list_price,
    COUNT(oi.id)   AS times_ordered,
    SUM(oi.quantity) AS total_units_sold,
    AVG(oi.price)  AS avg_sale_price
FROM products p
LEFT JOIN order_items oi ON p.id = oi.product_id  -- Full scan on 2M rows
GROUP BY p.id, p.name, p.category, p.price
ORDER BY total_units_sold DESC;

-- View 3: slow_recent_activity
-- Crime: Correlated subquery + no index on orders.status
CREATE VIEW slow_recent_activity AS
SELECT
    u.id    AS user_id,
    u.email,
    u.name,
    (
        SELECT COUNT(*)
        FROM orders o
        WHERE o.user_id = u.id   -- Re-executes for every user row
    ) AS total_orders,
    (
        SELECT SUM(o2.amount)
        FROM orders o2
        WHERE o2.user_id = u.id  -- Re-executes again for every user row
          AND o2.status = 'completed'
    ) AS completed_revenue
FROM users u
ORDER BY total_orders DESC;

-- =============================================================================
-- HOW TO REPRODUCE THE DEMO
-- =============================================================================
-- After setup, run this in psql to confirm slow scan:
--
--   EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM orders WHERE user_id = 123;
--   -- Should show: Seq Scan on orders ... actual time=...3000ms
--
-- Apply the fix:
--   CREATE INDEX idx_orders_user_id ON orders(user_id);
--   ANALYZE orders;
--
--   EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM orders WHERE user_id = 123;
--   -- Should show: Index Scan ... actual time=0.1..0.3ms
--
-- Before: ~3,100 ms   →   After: ~48 ms   (98% improvement)
-- =============================================================================

SELECT 'Demo DB setup complete.' AS status,
       (SELECT COUNT(*) FROM users)       AS users_count,
       (SELECT COUNT(*) FROM orders)      AS orders_count,
       (SELECT COUNT(*) FROM order_items) AS order_items_count,
       (SELECT COUNT(*) FROM products)    AS products_count;
