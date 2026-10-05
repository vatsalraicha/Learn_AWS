-- chargeback.sql — System tables queries for cost attribution + chargeback
-- Pairs with Module 16 (Cost & FinOps).
-- Run in DBSQL or notebook. Materialize daily into _admin.billing.* for dashboards.

-- ============================================================================
-- 1. 30-day chargeback by business unit / cost center / SKU
-- ============================================================================
WITH usage_30d AS (
  SELECT
    custom_tags['business_unit']        AS bu,
    custom_tags['cost_center']          AS cc,
    custom_tags['environment']          AS env,
    custom_tags['data_classification']  AS data_class,
    sku_name,
    cloud,
    date_trunc('month', usage_date)     AS usage_month,
    SUM(usage_quantity)                 AS dbu
  FROM system.billing.usage
  WHERE usage_date >= current_date - INTERVAL 30 DAYS
  GROUP BY 1, 2, 3, 4, 5, 6, 7
)
SELECT
  u.usage_month,
  u.bu,
  u.cc,
  u.env,
  u.data_class,
  u.sku_name,
  u.dbu,
  ROUND(u.dbu * p.pricing.default, 2) AS list_cost
FROM usage_30d u
LEFT JOIN system.billing.list_prices p
  ON u.sku_name = p.sku_name
  AND u.cloud = p.cloud
WHERE p.price_start_time <= u.usage_month
  AND (p.price_end_time IS NULL OR p.price_end_time > u.usage_month)
ORDER BY list_cost DESC;


-- ============================================================================
-- 2. Top 20 cost concentrators (jobs, warehouses, model serving endpoints)
-- ============================================================================
SELECT
  resource_id,
  resource_type,
  custom_tags['business_unit']       AS bu,
  custom_tags['cost_center']         AS cc,
  custom_tags['workload']            AS workload,
  SUM(usage_quantity * list_price)   AS list_cost_30d,
  SUM(usage_quantity)                AS dbu_30d
FROM (
  SELECT
    u.*,
    p.pricing.default AS list_price,
    COALESCE(u.usage_metadata.cluster_id, u.usage_metadata.warehouse_id, u.usage_metadata.endpoint_name) AS resource_id,
    CASE
      WHEN u.usage_metadata.cluster_id      IS NOT NULL THEN 'cluster'
      WHEN u.usage_metadata.warehouse_id    IS NOT NULL THEN 'warehouse'
      WHEN u.usage_metadata.endpoint_name   IS NOT NULL THEN 'serving_endpoint'
      ELSE 'other'
    END AS resource_type
  FROM system.billing.usage u
  LEFT JOIN system.billing.list_prices p
    ON u.sku_name = p.sku_name AND u.cloud = p.cloud
  WHERE u.usage_date >= current_date - INTERVAL 30 DAYS
)
GROUP BY 1, 2, 3, 4, 5
ORDER BY list_cost_30d DESC
LIMIT 20;


-- ============================================================================
-- 3. Idle cluster check — clusters with no recent activity
-- ============================================================================
WITH recent_activity AS (
  SELECT
    custom_tags['cluster_id'] AS cluster_id,
    MAX(usage_date)           AS last_active
  FROM system.billing.usage
  WHERE custom_tags['cluster_id'] IS NOT NULL
  GROUP BY 1
)
SELECT
  c.cluster_id,
  c.cluster_name,
  c.creator,
  c.cluster_source,
  c.auto_termination_minutes,
  r.last_active,
  current_date - r.last_active AS days_idle
FROM system.compute.clusters c
LEFT JOIN recent_activity r ON c.cluster_id = r.cluster_id
WHERE c.delete_time IS NULL                 -- still exists
  AND (r.last_active IS NULL OR r.last_active < current_date - INTERVAL 7 DAYS)
ORDER BY days_idle DESC NULLS FIRST;


-- ============================================================================
-- 4. Cost trend — 7-day vs prior-7-day comparison
-- ============================================================================
WITH daily AS (
  SELECT
    usage_date,
    SUM(usage_quantity * COALESCE(list_price, 0)) AS daily_cost
  FROM system.billing.usage u
  LEFT JOIN system.billing.list_prices p
    ON u.sku_name = p.sku_name AND u.cloud = p.cloud
    AND p.price_start_time <= u.usage_date
    AND (p.price_end_time IS NULL OR p.price_end_time > u.usage_date)
  WHERE usage_date >= current_date - INTERVAL 14 DAYS
  GROUP BY 1
)
SELECT
  CASE WHEN usage_date >= current_date - INTERVAL 7 DAYS THEN 'last_7d' ELSE 'prior_7d' END AS period,
  ROUND(SUM(daily_cost), 2)                                                                AS total_cost,
  ROUND(AVG(daily_cost), 2)                                                                AS avg_daily_cost
FROM daily
GROUP BY 1;


-- ============================================================================
-- 5. Anomaly detection — yesterday's spend vs 14-day average
-- ============================================================================
WITH daily AS (
  SELECT
    usage_date,
    SUM(usage_quantity * COALESCE(list_price, 0)) AS daily_cost
  FROM system.billing.usage u
  LEFT JOIN system.billing.list_prices p
    ON u.sku_name = p.sku_name AND u.cloud = p.cloud
  WHERE usage_date >= current_date - INTERVAL 14 DAYS
  GROUP BY 1
),
stats AS (
  SELECT
    AVG(daily_cost)    AS mean_cost,
    STDDEV(daily_cost) AS std_cost
  FROM daily
  WHERE usage_date < current_date - INTERVAL 1 DAY  -- baseline excludes yesterday
)
SELECT
  d.usage_date,
  d.daily_cost,
  s.mean_cost,
  s.std_cost,
  ROUND((d.daily_cost - s.mean_cost) / NULLIF(s.std_cost, 0), 2) AS z_score,
  CASE
    WHEN d.daily_cost > s.mean_cost + 2 * s.std_cost THEN 'ANOMALY_HIGH'
    WHEN d.daily_cost < s.mean_cost - 2 * s.std_cost THEN 'ANOMALY_LOW'
    ELSE 'NORMAL'
  END AS status
FROM daily d
CROSS JOIN stats s
WHERE d.usage_date = current_date - INTERVAL 1 DAY;


-- ============================================================================
-- 6. Photon cost-effectiveness probe (find Photon-on jobs with low speedup)
-- ============================================================================
-- (Requires custom MLflow tags or job tag like 'photon=on/off' for clean cohort)
SELECT
  custom_tags['job_id']           AS job_id,
  custom_tags['photon']           AS photon,
  AVG(usage_quantity)             AS avg_dbu_per_run,
  COUNT(*)                        AS run_count
FROM system.billing.usage
WHERE custom_tags['job_id'] IS NOT NULL
  AND custom_tags['photon'] IS NOT NULL
  AND usage_date >= current_date - INTERVAL 30 DAYS
GROUP BY 1, 2
ORDER BY job_id, photon;
