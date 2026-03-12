-- =============================================================================
-- Intentionally Bad (Slow) Queries — AI DB Query Optimizer Demo
-- =============================================================================
-- These 5 queries demonstrate each detection type.
-- Run against the demo DB created by setup_demo_db.sql.
-- Each query has comments explaining exactly WHY it is slow.
-- =============================================================================


-- =============================================================================
-- QUERY 1: N+1 Pattern
-- =============================================================================
-- WHY IT'S SLOW:
--   An ORM (Django/SQLAlchemy/ActiveRecord) fetches a list of users, then fires
--   one SELECT per user to load their orders. For 847 users this becomes 848
--   separate round-trips to the database. Each round-trip costs ~3ms at minimum.
--   Total: 847 × 3ms = ~2.5 seconds just in query overhead.
--
-- HOW IT MANIFESTS:
--   The ORM generates this query 847 times with a different id each time:

SELECT * FROM users WHERE id = 1;
-- then:
SELECT * FROM users WHERE id = 2;
-- then:
SELECT * FROM users WHERE id = 3;
-- ... (repeated 844 more times in a Python/JS/Ruby loop)

-- WHAT THE LOG LOOKS LIKE (one line per query):
-- SELECT * FROM users WHERE id = 1
-- SELECT * FROM users WHERE id = 2
-- SELECT * FROM users WHERE id = 3
-- ... 847 lines total

-- REAL COST: 847 queries × 3ms avg = 2,541ms per page load
-- DETECTION: N+1 Detector normalises WHERE id = ? — groups 847 identical patterns


-- =============================================================================
-- QUERY 2: Missing Index — Sequential Scan
-- =============================================================================
-- WHY IT'S SLOW:
--   orders.user_id has no index (see setup_demo_db.sql — intentional omission).
--   PostgreSQL must read all 500,000 rows in the orders table to find the 14
--   rows belonging to user_id = 123. This is a full table scan every time.
--
-- EXPLAIN ANALYZE shows:
--   Seq Scan on orders (cost=0.00..14285.00 rows=500000 width=72)
--                       (actual time=0.043..3098.441 rows=14 loops=1)
--   Filter: (user_id = 123)
--   Rows Removed by Filter: 499986
--   Execution Time: 3098.441 ms

SELECT * FROM orders WHERE user_id = 123;

-- REAL COST: 3.1s × 1,000 calls/day × 250 days × $75/hr = $2,400/year
-- FIX: CREATE INDEX idx_orders_user_id ON orders(user_id);
-- AFTER FIX: Index Scan — 0.048ms (98% improvement)


-- =============================================================================
-- QUERY 3: Inefficient JOIN (implicit cross-join syntax)
-- =============================================================================
-- WHY IT'S SLOW:
--   The old comma-style join (FROM users u, orders o WHERE ...) is semantically
--   identical to a CROSS JOIN filtered by WHERE. With no index on user_id and
--   no index on status, PostgreSQL must:
--   1. Hash-join 100,000 users with 500,000 orders (50 billion combos before filter)
--   2. Filter by status = 'pending' — scanning the entire result
--
--   Additionally, SELECT u.*, o.* pulls all columns across the wire — far more
--   data than the caller probably needs.
--
-- EXPLAIN ANALYZE shows:
--   Hash Join  (cost=3672.00..120856.25 rows=... width=...)
--   Seq Scan on orders (actual rows=125,000)  ← no status index
--   Seq Scan on users  (actual rows=100,000)

SELECT u.*, o.*
FROM users u, orders o
WHERE u.id = o.user_id
  AND o.status = 'pending';

-- REAL COST: ~7s query, called 120 times/day = significant
-- FIX:
--   CREATE INDEX idx_orders_status ON orders(status);
--   -- Rewrite with explicit JOIN and select only needed columns:
--   SELECT u.id, u.email, o.id AS order_id, o.amount
--   FROM users u
--   JOIN orders o ON o.user_id = u.id
--   WHERE o.status = 'pending';


-- =============================================================================
-- QUERY 4: Full Table Scan with Aggregate
-- =============================================================================
-- WHY IT'S SLOW:
--   order_items has 2,000,000 rows and no index on the `price` column.
--   COUNT(*) with a WHERE clause forces a full sequential scan of all 2M rows
--   to count just those where price > 50.00 (roughly 1.5M rows pass the filter).
--
-- EXPLAIN ANALYZE shows:
--   Aggregate (actual time=892.341..892.342 rows=1 loops=1)
--   -> Seq Scan on order_items (actual time=0.028..721.193 rows=1489234 loops=1)
--      Filter: (price > 50.00)
--      Rows Removed by Filter: 510766
--   Execution Time: 892.441 ms

SELECT COUNT(*) FROM order_items WHERE price > 50.00;

-- REAL COST: 900ms × 3,400 calls/day = significant compute waste
-- FIX:
--   CREATE INDEX idx_order_items_price ON order_items(price);
--   -- Or if you only ever count, a partial index is even better:
--   CREATE INDEX idx_order_items_price_gt50 ON order_items(price) WHERE price > 50.00;


-- =============================================================================
-- QUERY 5: Redundant Subquery (can be rewritten as JOIN or EXISTS)
-- =============================================================================
-- WHY IT'S SLOW:
--   The IN (SELECT ...) subquery is evaluated for every row in users.
--   PostgreSQL may choose a Hash Semi-Join (good) or — with outdated statistics
--   or small tables — a Nested Loop (bad). Either way:
--   1. The subquery scans all 500,000 orders to find user_ids with amount > 100
--   2. The outer query then fetches all matching users
--   3. No index on orders.amount means the subquery is also a full scan
--
-- EXPLAIN ANALYZE shows (without amount index):
--   Hash Semi Join (cost=22714.00..26464.00 rows=... width=...)
--   Hash (actual rows=82,341)
--   Seq Scan on orders (cost=0.00..14285.00 rows=... actual rows=500000)
--     Filter: (amount > 100)
--   Execution Time: 3,523 ms

SELECT * FROM users
WHERE id IN (
    SELECT user_id FROM orders WHERE amount > 100
);

-- REAL COST: 3.5s per call
-- FIX (option A — use a JOIN):
--   SELECT DISTINCT u.*
--   FROM users u
--   JOIN orders o ON u.id = o.user_id
--   WHERE o.amount > 100;
--
-- FIX (option B — use EXISTS, often faster):
--   SELECT u.*
--   FROM users u
--   WHERE EXISTS (
--       SELECT 1 FROM orders o WHERE o.user_id = u.id AND o.amount > 100
--   );
--
-- FIX (option C — add missing index):
--   CREATE INDEX idx_orders_amount ON orders(amount);
