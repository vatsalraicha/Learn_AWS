# 08 — Connections, Variables, and Secrets Backends

## Why this module exists

Connections + Variables are the primitives Airflow uses for runtime config and credentials. Where they live (metadata DB vs Secrets Backend) is a security decision.

---

## 1. Connection

A Connection is a typed record: conn_id, type, host, port, schema, login, password, extras (JSON).

```bash
airflow connections add snowflake_prod \
  --conn-type snowflake \
  --conn-host myorg.snowflakecomputing.com \
  --conn-login svc_airflow \
  --conn-password '<from-vault>' \
  --conn-schema ANALYTICS \
  --conn-extra '{"warehouse":"ETL_WH","database":"PROD","role":"airflow_etl"}'
```

Stored in `connection` table; password column encrypted with **Fernet key**.

For an operator: `SnowflakeOperator(conn_id="snowflake_prod", sql="...")`.

The Hook for a given type looks up the conn, extracts auth, builds the client.

---

## 2. Variable

Key-value strings in `variable` table (encrypted with Fernet).

```python
threshold = Variable.get("quality_threshold", default_var="0.95")
team = Variable.get("team_routing", deserialize_json=True)  # parses JSON
```

Use for: env-specific paths, feature flags, thresholds.

**Don't put secrets in Variables.** Use Connections (audited better) or Secrets Backend.

---

## 3. Fernet key

`fernet_key` in `airflow.cfg` (or env `AIRFLOW__CORE__FERNET_KEY`) encrypts:
- Connection passwords
- Variables (their values)

If you lose the Fernet key: encrypted values are unrecoverable. **Treat it like a master key.** Rotate via `airflow rotate-fernet-key` with the new key appended to the config (old key still readable during transition).

---

## 4. Secrets Backend — the production answer

A Secrets Backend pulls secrets from an external system at runtime. **Replaces the metadata DB** for secret storage.

### 4.1 Order of precedence

When `conn_id` is looked up:

1. Environment variables (`AIRFLOW_CONN_X=`).
2. **Secrets Backend** (if configured).
3. Metadata DB (the legacy default).

Variables similarly via `AIRFLOW_VAR_X=`.

### 4.2 Configuration

```ini
[secrets]
backend = airflow.providers.amazon.aws.secrets.secrets_manager.SecretsManagerBackend
backend_kwargs = {"connections_prefix": "airflow/connections", "variables_prefix": "airflow/variables", "profile_name": null}
```

Now `conn_id=snowflake_prod` → look up `airflow/connections/snowflake_prod` in AWS Secrets Manager. JSON like:

```json
{
  "conn_type": "snowflake",
  "host": "myorg.snowflakecomputing.com",
  "login": "svc_airflow",
  "password": "<secret>",
  "schema": "ANALYTICS",
  "extra": "{\"warehouse\":\"ETL_WH\",\"database\":\"PROD\"}"
}
```

### 4.3 Built-in backends

| Backend | Provider |
|---|---|
| `SecretsManagerBackend` | AWS Secrets Manager |
| `SystemsManagerParameterStoreBackend` | AWS SSM Parameter Store |
| `CloudSecretManagerBackend` | GCP Secret Manager |
| `AzureKeyVaultBackend` | Azure Key Vault |
| `VaultBackend` | HashiCorp Vault |
| `LocalFilesystemBackend` | Plain files (dev only) |

Each from the provider package (`apache-airflow-providers-amazon`, etc.).

---

## 5. AWS Secrets Manager backend — wiring

```ini
[secrets]
backend = airflow.providers.amazon.aws.secrets.secrets_manager.SecretsManagerBackend
backend_kwargs = {
  "connections_prefix": "airflow/connections",
  "variables_prefix":   "airflow/variables",
  "config_prefix":      "airflow/config"
}
```

Airflow scheduler/worker IAM role needs `secretsmanager:GetSecretValue` on `airflow/*`. On MWAA: the execution role (module 16).

Pattern: put secret in Secrets Manager once; reference by conn_id everywhere; rotate via Secrets Manager rotation Lambda.

---

## 6. GCP Secret Manager backend

```ini
backend = airflow.providers.google.cloud.secrets.secret_manager.CloudSecretManagerBackend
backend_kwargs = {
  "connections_prefix": "airflow-connections",
  "variables_prefix":   "airflow-variables",
  "project_id":         "my-airflow-proj"
}
```

GCP Secret Manager secret names like `airflow-connections-snowflake_prod`. Workload Identity / service account permission for the secret.

---

## 7. Azure Key Vault backend

```ini
backend = airflow.providers.microsoft.azure.secrets.key_vault.AzureKeyVaultBackend
backend_kwargs = {
  "vault_url":           "https://my-kv.vault.azure.net/",
  "connections_prefix":  "airflow-connections",
  "variables_prefix":    "airflow-variables",
  "sep":                 "-"
}
```

KV secret names like `airflow-connections-snowflake-prod` (note: KV doesn't allow `/`; use `-` separator).

Managed Identity / workload identity for KV access.

---

## 8. Vault backend

```ini
backend = airflow.providers.hashicorp.secrets.vault.VaultBackend
backend_kwargs = {
  "url":                 "https://vault.corp.example:8200",
  "auth_type":           "kubernetes",
  "kubernetes_role":     "airflow",
  "connections_path":    "airflow/connections",
  "variables_path":      "airflow/variables",
  "mount_point":         "secret"
}
```

Vault K8s auth: the pod's projected SA token authenticates to Vault; Vault returns secrets. Supports dynamic secrets (Vault generates a new DB password per request).

---

## 9. Dynamic secrets — the Vault advantage

```hcl
# Vault config
path "database/creds/airflow-snowflake" {
  capabilities = ["read"]
}
```

Vault generates a fresh Snowflake password for each read; password expires after lease. Airflow scheduler/worker reads at task start, uses for the connection lifetime.

For regulated finance: dynamic secrets eliminate static creds. The bar.

---

## 10. Connection lookup precedence (worth memorizing)

```
For conn_id="snowflake_prod":

1. env var: AIRFLOW_CONN_SNOWFLAKE_PROD=snowflake://user:pass@host/db?warehouse=X
   → if set, this WINS

2. Secrets Backend lookup at connections_prefix + "snowflake_prod"
   → returns Connection if found

3. Metadata DB SELECT * FROM connection WHERE conn_id='snowflake_prod'
   → final fallback
```

In MWAA / Composer / Astronomer: env-var setup happens via their UI; production secrets always in backend.

---

## 11. Anti-patterns

| Anti-pattern | Why bad | Fix |
|---|---|---|
| Hardcoded creds in DAG | Image leak, git leak | Connection + Secrets Backend |
| Plaintext password in Connection | Encrypted at rest, but visible to anyone with DB access | Secrets Backend |
| Putting tokens in Variables | Audited less than Connections | Connections or Secrets Backend |
| Same conn_id across envs | Dev creds == prod creds | Env-specific conn_ids |
| Long-lived static creds in Snowflake | Insider risk + rotation pain | Dynamic creds via Vault |

---

## 12. Provider Lookup Pattern

You can extend lookup with patterns:

```ini
backend_kwargs = {
  "connections_lookup_pattern": "^airflow_.*",
  "variables_lookup_pattern":   "^secret_.*"
}
```

Only call Secrets Backend for matching IDs; non-matching fall through to metadata DB. Cuts unnecessary API calls.

---

## Sanity check

1. The Fernet key encrypts what, and what's lost if the key is lost?
2. Lookup order for a `conn_id` — list the three sources in precedence.
3. Why is Vault's "dynamic secrets" pattern superior to a rotated static secret?
4. Azure Key Vault has a quirk that requires a config-level workaround. What is it?
5. What permission does the AWS Secrets Manager backend need from the Airflow IAM role?
6. Why is putting secrets in Variables an anti-pattern even though Variables are encrypted-at-rest?

---

## Sources

- [Secrets Backend overview](https://airflow.apache.org/docs/apache-airflow/stable/security/secrets/secrets-backend/index.html)
- [AWS Secrets Manager Backend](https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/secrets-backends/aws-secrets-manager.html)
- [GCP Secret Manager Backend](https://airflow.apache.org/docs/apache-airflow-providers-google/stable/secrets-backends/google-cloud-secret-manager-backend.html)
- [Azure Key Vault Backend](https://airflow.apache.org/docs/apache-airflow-providers-microsoft-azure/stable/secrets-backends/azure-key-vault.html)
- [Vault Backend](https://airflow.apache.org/docs/apache-airflow-providers-hashicorp/stable/secrets-backends/hashicorp-vault.html)
- [Connections concept](https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/connections.html)

→ Next: [09 — **Securing Airflow**](09_securing_airflow.md)
