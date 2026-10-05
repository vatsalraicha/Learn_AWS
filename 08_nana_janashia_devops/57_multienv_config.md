# 57 — Multi-environment Configuration + Secrets

## 1. The 12-factor app principle (Heroku, 2011)

The relevant factors for config:
- **Factor III: Config** — strict separation of config from code. Config in env vars, not files in repo.
- **Factor X: Dev/prod parity** — keep dev, staging, prod as similar as possible.

## 2. Three categories of config

| Category | Examples | Where it lives |
|---|---|---|
| **Non-secret, env-specific** | `LOG_LEVEL=debug`, `DATABASE_URL=...` | Env vars, configmaps |
| **Secret, env-specific** | DB password, API keys | Secrets Manager / Vault |
| **Constants / app config** | feature flags, app version | Config file in repo OR feature-flag service |

## 3. The `.env` file pattern

Local development:
```bash
# .env.local — gitignored
DATABASE_URL=postgresql://localhost/myapp_dev
API_KEY=dev-fake-key
LOG_LEVEL=debug
```

```javascript
// load with dotenv
import 'dotenv/config'
console.log(process.env.DATABASE_URL)
```

```python
# load with python-dotenv
from dotenv import load_dotenv
load_dotenv()
os.environ.get("DATABASE_URL")
```

**Never commit `.env` to Git.** Use `.env.example` with placeholder values to document what's needed:
```
# .env.example — committed
DATABASE_URL=
API_KEY=
LOG_LEVEL=info
```

## 4. Multi-env file pattern (Vite / Next.js)

```
.env                  # all envs (committed if non-secret)
.env.local            # local override (gitignored)
.env.development      # dev only
.env.production       # prod only
.env.production.local # prod local override (gitignored)
```

Precedence (highest wins): `.env.<mode>.local > .env.local > .env.<mode> > .env`.

## 5. Production: env vars from the runtime

| Platform | How env vars get into the app |
|---|---|
| **systemd** | `EnvironmentFile=/etc/app/env` (file mode 600) |
| **Docker Compose** | `environment:` block or `env_file:` in compose.yaml |
| **K8s** | `env:` block in container spec, often from ConfigMap/Secret |
| **AWS Lambda** | Function environment variables |
| **Fly.io / Railway / Render** | Web UI or CLI |
| **GitHub Actions** | `env:` block + `secrets.X` |
| **Jenkins** | Credentials + `withCredentials` |
| **GitLab CI** | CI/CD Variables |

## 6. Secrets backends (recap from Module 35)

In 2026:
1. **AWS Secrets Manager / Azure Key Vault / GCP Secret Manager** — cloud-native
2. **HashiCorp Vault / OpenBao** — multi-cloud
3. **External Secrets Operator** — sync them into K8s
4. **Doppler / Infisical / 1Password Secrets Automation** — developer-friendly SaaS
5. **SOPS** — encrypt-in-repo (when ESO not available)

Anti-patterns:
- `.env` committed to Git ❌
- Secrets in Jenkins job config ❌
- Long-lived API keys ❌
- Same DB password across dev/staging/prod ❌

## 7. Securing MongoDB access (Nana's bootcamp example)

```javascript
// app.js
import { MongoClient } from 'mongodb'

const uri = process.env.MONGO_URL  // mongodb://user:pass@host:port/db
const client = new MongoClient(uri, {
  tls: true,
  tlsCAFile: '/etc/ssl/mongo-ca.pem',
})
```

- Dev: local MongoDB or Atlas free tier with weak creds
- Prod: Atlas + IP allowlist + DB user with **least-privilege role** (`readWrite` on app DB only, not `dbAdmin` or `clusterAdmin`)
- Connection string in Secrets Manager; injected as env var

## 8. Environment-aware code

```javascript
// config.js
const config = {
  database: {
    url: process.env.DATABASE_URL,
    poolSize: parseInt(process.env.DB_POOL_SIZE ?? '10'),
  },
  logging: {
    level: process.env.LOG_LEVEL ?? 'info',
    json: process.env.NODE_ENV === 'production',
  },
  features: {
    newDashboard: process.env.FEATURE_NEW_DASHBOARD === 'true',
  },
}

// validate at startup
if (!config.database.url) {
  throw new Error('DATABASE_URL is required')
}

export default config
```

Validate config at startup; fail fast, not at request time.

## 9. Feature flags (config you want to flip without redeploy)

Tools:
- **LaunchDarkly** — commercial, enterprise default
- **Statsig** — commercial, A/B + flags
- **GrowthBook** — OSS
- **Unleash** — OSS, self-host
- **PostHog** — OSS, includes flags + analytics
- **OpenFeature** — vendor-neutral spec

```javascript
import { ldClient } from './ld'

if (await ldClient.boolVariation('new-checkout', user)) {
  // show new checkout
} else {
  // old checkout
}
```

Flags decouple deploy from release. Critical for trunk-based development at scale.

## 10. Configuration in Kubernetes

```yaml
apiVersion: v1
kind: ConfigMap
metadata: { name: app-config, namespace: my-app }
data:
  LOG_LEVEL: info
  DB_POOL_SIZE: "20"
  API_BASE_URL: https://api.example.com
---
apiVersion: v1
kind: Secret
metadata: { name: app-secrets, namespace: my-app }
type: Opaque
stringData:
  DATABASE_URL: postgresql://...
---
apiVersion: apps/v1
kind: Deployment
metadata: { name: app, namespace: my-app }
spec:
  template:
    spec:
      containers:
      - name: app
        envFrom:
          - configMapRef: { name: app-config }
          - secretRef: { name: app-secrets }
```

Secret should come from ESO → cloud Secret Manager, not be committed directly.

## 11. Completing the Sprint (Nana's Jira link)

Wrap-up:
- Mark stories Done when feature shipped + observed in prod
- Run sprint retro
- Update env-config docs if anything changed
- Audit secrets: anything leaked? anything not rotated in 90+ days?

## 12. Quick self-check

1. Why are env vars preferred over config files in repo?
2. Why never commit `.env`?
3. What's the precedence order for Vite's `.env*` files?
4. What's a feature flag and why does it decouple deploy from release?
5. Where should K8s Secrets actually come from in production?

(Answers: 12-factor — config varies between envs but code doesn't — env vars give clean separation + no risk of accidental commit; secrets leak if pushed; `.env.<mode>.local > .env.local > .env.<mode> > .env`; runtime config that can be flipped without code change — feature visible only when flag on so you can deploy code without releasing the feature to users; from cloud Secret Manager via External Secrets Operator — never base64'd into Git.)
