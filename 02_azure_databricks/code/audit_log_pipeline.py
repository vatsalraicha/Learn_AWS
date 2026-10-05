# audit_log_pipeline.py
# Lakeflow Declarative Pipeline that snapshots system.access.audit into a long-retention
# compliance Delta table. Closes the gap between Databricks's ~1yr native retention and
# HIPAA's 6yr requirement (45 CFR §164.316(b)(2)(i)).
#
# Pairs with Module 17 (Admin Playbook) and Module 21 (HIPAA).
#
# Deploy via:
#   databricks bundle deploy --target prod
#
# Schedule: continuous or hourly (via Lakeflow trigger).

# %% [markdown]
# # Audit log pipeline — HIPAA 6-year retention
#
# Two layers (Module 17):
# 1. **Compliance Delta sink** — full record, 6+ year retention (THIS PIPELINE)
# 2. **SIEM forwarding** — Azure Monitor diagnostic settings → Event Hub → Splunk/Sentinel
#    with optional tokenization for PHI in request_params (configured separately)

# %% Pipeline definition
from pyspark import pipelines as dp  # Lakeflow Spark Declarative Pipelines (DBR 17.3+)
from pyspark.sql import functions as F


@dp.table(
    name="audit_events",
    comment="Audit events from system.access.audit, tagged for HIPAA 6-year retention.",
    table_properties={
        "phi_class": "high",                      # request_params CAN contain PHI
        "data_classification": "phi",
        "retention_years": "6",
        "delta.enableDeletionVectors": "false",   # immutable
        "delta.enableChangeDataFeed": "false",    # we don't need CDF on this
    },
    cluster_by=["event_date", "service_name"],    # Liquid Clustering for query speed
)
def audit_events():
    """
    Stream system.access.audit into the compliance Delta table.

    Source: system.access.audit (account-level system table).
    Destination: _compliance.audit.audit_events (governed catalog).

    The destination table inherits CMK from the workspace storage and is bound
    to the tier-0 governance workspace (workspace-catalog binding in Module 9).
    """
    return (
        dp.read_stream("system.access.audit")
        .withColumn("ingestion_ts", F.current_timestamp())
        .withColumn("event_date", F.to_date("event_time"))
    )


# %% [markdown]
# ## Why each setting matters
#
# - `phi_class=high` — `request_params` can contain literal SQL values that include MRNs,
#   member IDs, etc. Audit logs ARE PHI. ABAC policies must protect this table.
# - `retention_years=6` — informational tag; actual retention enforced via Azure Storage
#   immutability policy on the underlying ADLS container + Delta retention.
# - `delta.enableDeletionVectors=false` — compliance evidence should be append-only.
#   No DV; no UPDATE/DELETE capability.
# - `cluster_by` — `event_date` + `service_name` are the dominant query patterns
#   (date-range audit queries; service-specific compliance reviews).


# %% [markdown]
# ## Companion: must-have-five SIEM alert queries (run separately in DBSQL or via SIEM)

# %% Alerting queries — each is a saved query / scheduled alert in DBSQL or SIEM
ALERT_QUERIES = {
    "phi_grants": """
        SELECT event_time, user_identity.email AS who, action_name, request_params
        FROM system.access.audit
        WHERE service_name = 'unityCatalog'
          AND action_name LIKE '%Grant%'
          AND request_params:securable_full_name LIKE 'prod_phi_%'
          AND user_identity.email NOT IN (SELECT email FROM _admin.metastore_admins.current)
          AND event_time >= current_timestamp() - INTERVAL 1 HOUR
    """,
    "failed_login_burst": """
        SELECT user_identity.email AS who, COUNT(*) AS fails, MIN(event_time) AS first_fail
        FROM system.access.audit
        WHERE service_name = 'accounts'
          AND action_name LIKE '%Login%'
          AND response.status_code >= 400
          AND event_time >= current_timestamp() - INTERVAL 5 MINUTES
        GROUP BY 1
        HAVING COUNT(*) > 10
    """,
    "unrestricted_cluster_create": """
        SELECT event_time, user_identity.email AS who, request_params:cluster_name AS cluster
        FROM system.access.audit
        WHERE service_name = 'clusters'
          AND action_name = 'create'
          AND request_params:policy_id IS NULL  -- no cluster policy = unrestricted
          AND event_time >= current_timestamp() - INTERVAL 1 HOUR
    """,
    "download_query_result": """
        SELECT event_time, user_identity.email AS who, request_params:query_id AS qid
        FROM system.access.audit
        WHERE service_name = 'sqlanalytics'
          AND action_name = 'downloadQueryResult'
          AND user_identity.email NOT IN (SELECT email FROM _admin.allowlists.exporters)
          AND event_time >= current_timestamp() - INTERVAL 1 HOUR
    """,
    "admin_group_changes": """
        SELECT event_time, user_identity.email AS who, action_name, request_params
        FROM system.access.audit
        WHERE service_name = 'accounts'
          AND action_name LIKE '%Group%'
          AND request_params:group_name IN (
              'oncall-platform-admins',
              'metastore-admins',
              'account-admins'
          )
          AND event_time >= current_timestamp() - INTERVAL 1 HOUR
    """,
}


# %% [markdown]
# ## Production deployment notes
#
# 1. **The destination catalog (`_compliance`)** must be:
#    - Bound to the tier-0 governance workspace via workspace-catalog binding (Module 9)
#    - Tagged `phi_class=high` and `data_classification=phi`
#    - Have ABAC policies that restrict reads to a 2-3 person compliance team
#
# 2. **Azure Storage immutability** must be configured on the underlying ADLS container:
#    - Time-based retention policy = 6 years
#    - Locked policy (cannot be reduced post-creation)
#    - Container-level (catalog managed location)
#
# 3. **Schedule the Lakeflow pipeline** as continuous OR hourly trigger:
#    - Continuous: lower lag, higher cost
#    - Hourly trigger: ~1 hour gap; cheaper. For HIPAA audit, hourly is sufficient.
#
# 4. **Monitor the pipeline itself**:
#    - Alert if the pipeline fails or hasn't run in >2 hours
#    - The audit log of the audit pipeline is itself audit-relevant (recursion is normal)
#
# 5. **Test recovery quarterly**:
#    - Verify the immutability policy is locked
#    - Confirm restoration from `_compliance.audit.audit_events` works
#    - Document the test in your IRP (Incident Response Plan)
