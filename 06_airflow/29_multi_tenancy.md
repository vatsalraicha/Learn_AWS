# 29 — Multi-tenancy patterns: namespaced executors, one-Airflow-per-team vs shared

## Why this module exists

Org-shape determines architecture. This module covers the three Airflow multi-tenancy patterns + the controls each requires.

---

## 1. Pattern A: One Airflow per team

Each team has a dedicated MWAA env / Composer env / Astro deployment / Helm install.

**Pros**:
- Hard isolation (separate cluster, separate metadata DB).
- Per-team budget / cost allocation easy.
- Per-team upgrade cadence.
- DAG author = cluster admin is bounded to the team.

**Cons**:
- N envs to operate.
- N idle baselines.
- N upgrade paths to track.

When right: regulated finance with strong separation requirements; teams with very different needs (one team on 2.7, one on 3.0).

---

## 2. Pattern B: One shared Airflow

Single env serves all teams. Use:

- **Namespaces** in K8sExecutor (one ns per team).
- **Pools** to limit per-team concurrency.
- **Per-DAG `access_control`** (FAB roles).
- **Per-task IRSA/WIF/Entra SA** (different cloud identity per team).
- **NetworkPolicy** per team namespace.
- **Tag-based cost allocation** (`team`, `cost-center`).

**Pros**: single env, single ops burden, cheaper.

**Cons**:
- DAG-author-as-cluster-admin problem widens (any DAG can take down scheduler).
- Upgrade is org-wide.
- Pool contention.

When right: many teams with low isolation needs; org with strong code-review culture.

---

## 3. Pattern C: Hybrid

Sensitive / regulated DAGs on dedicated env; remainder on shared.

For Capital One: finance team or trading-systems team gets dedicated; data eng + ML teams share.

---

## 4. The K8sExecutor + per-task SA pattern

The strongest in-cluster tenancy:

```python
@dag(...)
def team_alpha_dag():
    @task(executor_config={
        "pod_override": V1Pod(spec=V1PodSpec(
            service_account_name="team-alpha-tasks",     # IRSA → team-alpha role
            namespace="airflow-team-alpha",
        )),
    })
    def secure_task(): ...
```

Each team's DAGs run pods with team-specific SAs in team-specific namespaces with team-specific IAM. The scheduler is shared but task execution is isolated.

This is the modern multi-tenant model.

---

## 5. RBAC + access_control

```python
@dag(
    access_control={
        "team-alpha-developers": {"can_read", "can_edit", "can_delete"},
        "team-alpha-viewers":    {"can_read"},
    },
    ...
)
def alpha_dag(): ...
```

Combined with OIDC group → FAB role mapping (module 09), users see only DAGs they're entitled to.

---

## 6. Pool + queue isolation

```yaml
pools:
  - name: team-alpha-snowflake
    slots: 5
  - name: team-bravo-snowflake
    slots: 10

queues:
  - team-alpha
  - team-bravo
```

Tasks declare `pool=team-alpha-snowflake` + `queue=team-alpha`. K8sExecutor can run team-alpha tasks on dedicated worker nodes (via node selector).

---

## 7. The shared-Airflow security checklist

For shared:
- [ ] K8sExecutor (not Celery).
- [ ] Per-team namespace.
- [ ] Per-team K8s SA + cloud IAM binding.
- [ ] NetworkPolicy default-deny per namespace.
- [ ] Per-team DAG folder in shared bucket / git repo.
- [ ] Per-team OIDC group → FAB role mapping.
- [ ] Per-team `access_control` on DAGs.
- [ ] Pool per team's resource budget.
- [ ] PR review by team-aware reviewer.
- [ ] CI lints for forbidden patterns per team.
- [ ] Cost allocation tags enforced via Kyverno.
- [ ] Audit log per-team segments.

---

## 8. Capital One context

Capital One likely runs **hybrid**:

- Critical regulated DAGs (compliance reporting, model risk) → dedicated MWAA env.
- General data eng → shared MWAA / Astro / EKS-Helm Airflow.

The architectural principle: **isolate by blast radius, not by org chart.**

---

## 9. Multi-tenancy and Airflow 3.0

Airflow 3.0's Task SDK + multi-cluster scheduler are designed for multi-tenancy:

- Tasks run with scoped permissions.
- Multiple teams' DAGs can share a scheduler without sharing execution context.
- Easier upgrades (DAGs less tied to specific Airflow version).

This is the architectural direction. For new shared Airflow in 2026+: design for 3.0 even if you start on 2.10.

---

## Sanity check

1. One Airflow per team vs one shared — three trade-offs.
2. K8sExecutor + per-task SA — what does this give multi-tenancy?
3. `access_control` on DAGs — how does this interact with FAB OIDC groups?
4. Hybrid pattern — when do you put a DAG on the dedicated env?
5. Airflow 3.0 multi-tenancy direction — what's the Task SDK's contribution?

---

## Sources

- [Airflow security](https://airflow.apache.org/docs/apache-airflow/stable/security/index.html)
- [Per-DAG access control](https://airflow.apache.org/docs/apache-airflow/stable/security/access-control.html)
- [Airflow 3.0 design docs](https://airflow.apache.org/blog/airflow-3-0/)

→ Next: [30 — **Airflow 3.0 deep**](30_airflow_3.md)
