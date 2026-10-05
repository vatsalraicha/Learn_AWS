# 09 — Securing Airflow: RBAC, Auth Manager, FAB, OIDC/SAML/LDAP, audit logs, the DAG-author=admin problem

## Why this module exists

Airflow's security story is **not great by default**. This module is the honest "how regulated shops actually control Airflow" guide.

---

## 1. The structural problem: DAG code = arbitrary execution

Airflow DAGs are Python files. The scheduler imports them. Anyone with commit access to the DAG folder runs arbitrary Python in the scheduler process context. **DAG authors are effectively cluster admins.**

Mitigations (none perfect for 2.x):
- PR review every DAG change.
- CI lints for `eval`, `exec`, `subprocess.run(...)` at top level.
- Run scheduler with restricted IAM / SA permissions (so RCE in scheduler is bounded).
- Use **KubernetesExecutor** so tasks run in isolated Pods with their own SAs.
- **Airflow 3.0 Task SDK** finally isolates task execution from the scheduler — module 30.

For multi-team Airflow: each team should have **its own DAG folder + its own scheduler/worker pool** unless 3.0's Task SDK is in play.

---

## 2. Auth Manager — the 2.8+ abstraction

Auth Manager is an extension point for authentication and authorization. Default is **FAB Auth Manager** (Flask-AppBuilder). Alternative: **AWS Auth Manager** (uses IAM).

```ini
[core]
auth_manager = airflow.providers.fab.auth_manager.fab_auth_manager.FabAuthManager
```

In 3.0 the abstraction is more flexible.

---

## 3. FAB Auth Manager — the default

[Flask-AppBuilder](https://flask-appbuilder.readthedocs.io/) ships with Airflow. Provides:

- **Built-in roles**: Admin, Op, User, Viewer, Public.
- **Custom roles**: define + assign.
- **Per-DAG access control**: `dag.access_control = {"team_a": {"can_read", "can_edit"}}`.
- **Auth backends**: password (DB), LDAP, OAuth (Google/Okta/Azure AD/GitHub), Kerberos, SAML.

### 3.1 Configure OIDC (e.g., Okta)

In `webserver_config.py`:

```python
from flask_appbuilder.security.manager import AUTH_OAUTH
AUTH_TYPE = AUTH_OAUTH
AUTH_USER_REGISTRATION = True
AUTH_USER_REGISTRATION_ROLE = "Viewer"
AUTH_ROLES_MAPPING = {
    "Airflow-Admins":   ["Admin"],
    "Data-Engineers":   ["Op"],
    "ML-Engineers":     ["User"],
}
AUTH_ROLES_SYNC_AT_LOGIN = True
OAUTH_PROVIDERS = [{
    "name": "okta",
    "icon": "fa-circle-o",
    "token_key": "access_token",
    "remote_app": {
        "client_id":     "<>",
        "client_secret": "<>",
        "api_base_url":  "https://<tenant>.okta.com/oauth2/default/v1/",
        "client_kwargs": {"scope": "openid profile email groups"},
        "access_token_url": "https://<tenant>.okta.com/oauth2/default/v1/token",
        "authorize_url":    "https://<tenant>.okta.com/oauth2/default/v1/authorize",
    },
}]
```

User logs in via Okta; groups claim maps to Airflow roles.

---

## 4. Per-DAG access control

```python
@dag(
    access_control={
        "team-finance": {"can_read"},
        "team-data-eng": {"can_read", "can_edit", "can_delete"},
    },
    ...
)
def finance_etl():
    ...
```

Users in `team-finance` see this DAG (read-only); users in `team-data-eng` can pause/trigger/edit. Useful for multi-tenant.

---

## 5. The webserver_secret_key

```ini
[webserver]
secret_key = <random-32-bytes>
```

Signs session cookies. **MUST be identical across webserver replicas.** Generate via `openssl rand -hex 32`. Store in Secrets Backend; mount as env var.

---

## 6. `expose_config = False`

```ini
[webserver]
expose_config = False
```

Default in modern Airflow. Prevents UI from rendering `airflow.cfg` contents (which may include secrets, DB URLs).

---

## 7. API authentication

Airflow REST API (`/api/v1/`) auth options:

- Basic auth (DB-backed).
- JWT (2.9+).
- Kerberos.
- OAuth (via FAB session).

For machine clients: JWT or basic auth with a service-account user. Behind an API gateway / WAF.

---

## 8. Audit logging

Airflow logs UI/API actions to its `log` table:

- DAG triggered, paused, deleted.
- User login/logout.
- Variable / Connection added/changed/deleted.
- Pool changes.

Forward to SIEM:

```python
# Custom log handler that ships to Splunk/Datadog
```

Or use the OpenTelemetry log support (2.9+).

Tasks log to the configured log handler (S3, GCS, ES, etc.) — separate from audit log.

---

## 9. The scheduler's IAM/SA permissions

Scheduler does:
- Read/write metadata DB.
- Read DAG storage.
- Talk to Triggerer / workers via DB.
- Push logs to remote backend.
- Fetch secrets from Secrets Backend.

**Scheduler does NOT need access to actual data systems** (Snowflake, S3 buckets, Databricks). Those are accessed by tasks (via task IAM / SA in K8sExecutor).

Lock down scheduler IAM/SA accordingly. If scheduler is RCE'd, blast radius is `airflow/*` secrets and DAG storage, not your data warehouse.

---

## 10. Webserver hardening

- Behind LB only (no public IP).
- TLS terminated at LB; redirect HTTP→HTTPS.
- `secure: True` cookies; `SameSite=Strict`; `HttpOnly`.
- CSP headers via reverse proxy.
- mTLS if internal-only.
- OIDC auth (no DB passwords).
- Rate limit per IP.
- Health-check endpoint exempt from auth (for K8s probes).

For regulated finance: webserver behind oauth2-proxy + WAF + private network.

---

## 11. Known CVEs

- **CVE-2020-11978** — Example DAG `example_trigger_target_dag` RCE; `load_examples = False` in any non-dev env. Mandatory.
- **CVE-2022-24288** — improper neutralization of params in some operators (BashOperator).
- **Various 2023-2024 advisories** — usually patched within weeks. Subscribe to `security@airflow.apache.org`.

LTS lines: Airflow 2.6 LTS (security patches without features). Stay on a supported version; 2.10 is current at 2026-05-21.

---

## 12. The regulated-finance hardening checklist

- [ ] `load_examples = False`.
- [ ] `expose_config = False`.
- [ ] `secret_key` and `fernet_key` from Secrets Backend, distinct per env.
- [ ] OIDC auth (no password DB).
- [ ] OIDC groups → Airflow roles mapping.
- [ ] Per-DAG `access_control` for sensitive DAGs.
- [ ] Secrets Backend configured (AWS/GCP/Azure/Vault).
- [ ] Webserver behind oauth2-proxy + WAF + private network.
- [ ] mTLS for API.
- [ ] Audit log to SIEM.
- [ ] Task logs to KMS-encrypted bucket.
- [ ] Scheduler/worker IAM scoped to Secrets Backend + DAG storage only.
- [ ] KubernetesExecutor with per-task SA (IRSA / WIF / Entra Workload ID).
- [ ] PSA-restricted on the K8s namespace.
- [ ] Kyverno admission for image signing + resource limits.
- [ ] CI lints: no top-level `import` of heavyweights; no `eval`/`exec`.
- [ ] PR review for every DAG change with security-side reviewer for high-privilege DAGs.

---

## Sanity check

1. The "DAG authors == cluster admins" problem — why does it exist in Airflow 2.x?
2. What does the `secret_key` sign, and why must it be identical across webservers?
3. FAB Auth Manager + OIDC + group mapping — describe the login flow.
4. Why does `expose_config = False` matter even if you trust your team?
5. Scheduler IAM should NOT include direct access to what data systems?
6. KubernetesExecutor + per-task SA addresses the DAG-author-RCE problem how?

---

## Sources

- [Airflow Security](https://airflow.apache.org/docs/apache-airflow/stable/security/index.html)
- [Auth Manager](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/auth-manager/index.html)
- [Flask-AppBuilder OAuth](https://flask-appbuilder.readthedocs.io/en/latest/security.html#oauth-authentication)
- [Apache Airflow Security advisories](https://airflow.apache.org/docs/apache-airflow/stable/security/index.html#security-advisories)
- [NVD: CVE-2020-11978](https://nvd.nist.gov/vuln/detail/CVE-2020-11978)

→ Next: [10 — Networking Airflow](10_networking.md)
