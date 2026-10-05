# 52 — NodeJS Backend

## 1. Node.js in 2026

- **Node 22 LTS** (Oct 2024, EOL Apr 2027)
- **Node 24** (current, LTS Oct 2025)
- **Node 26 LTS** (Oct 2026 expected)
- Even-numbered = LTS; odd = current/short-lived

Key recent additions:
- Built-in `--watch` (no nodemon needed)
- Built-in `fetch()` (no node-fetch)
- Built-in test runner (`node:test`)
- WebStreams, WebCrypto
- Native TypeScript stripping (Node 22.6+) — run `.ts` files without compile

## 2. The framework landscape

| Framework | When |
|---|---|
| **Express 4/5** | Still dominant; legacy + simple APIs |
| **Fastify** | Faster than Express; schema-validated; modern |
| **Hono** | Web-standards based; runs anywhere (Bun/Deno/Workers/Node); rising fast |
| **NestJS** | Angular-inspired DI + decorators; enterprise; opinionated |
| **Koa** | Lightweight Express successor (Express team) |
| **tRPC** | Type-safe RPC (TS-only); meta-pattern not framework |
| **GraphQL Yoga / Apollo** | GraphQL servers |

Picking: **Hono** for new projects in 2026; **Fastify** for serious production APIs; **Express** for compatibility with old ecosystem; **NestJS** if you like Java-style DI.

## 3. Minimal Express server

```javascript
import express from 'express'

const app = express()
app.use(express.json())

app.get('/api/users', async (req, res) => {
  res.json({ users: ['Alice', 'Bob'] })
})

app.post('/api/users', async (req, res) => {
  const { name } = req.body
  res.status(201).json({ id: 1, name })
})

app.use((err, req, res, next) => {
  console.error(err)
  res.status(500).json({ error: 'internal' })
})

app.listen(3000, () => console.log('listening on 3000'))
```

## 4. Hono — the modern choice

```javascript
import { Hono } from 'hono'
import { logger } from 'hono/logger'

const app = new Hono()

app.use(logger())

app.get('/api/users', (c) => c.json({ users: ['Alice'] }))

app.post('/api/users', async (c) => {
  const body = await c.req.json()
  return c.json({ id: 1, ...body }, 201)
})

export default app   // works on Node, Bun, Deno, Cloudflare Workers
```

Hono is portable — same code runs on Node, Bun, Deno, Cloudflare Workers, Lambda, edge. That portability is the killer feature.

## 5. HTTP basics every backend dev needs

### Methods
- GET — retrieve (idempotent, cacheable)
- POST — create (not idempotent)
- PUT — replace entirely (idempotent)
- PATCH — partial update (not necessarily idempotent)
- DELETE — remove
- HEAD, OPTIONS, TRACE, CONNECT (rarely)

### Status codes
- 2xx — success (200 OK, 201 Created, 204 No Content)
- 3xx — redirect (301 permanent, 302 found, 304 not modified)
- 4xx — client error (400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 422 Unprocessable Entity, 429 Too Many)
- 5xx — server error (500 Internal, 502 Bad Gateway, 503 Service Unavailable, 504 Gateway Timeout)

### Headers
- `Authorization: Bearer <token>` — JWT/OAuth
- `Content-Type: application/json` — request body type
- `Accept: application/json` — response wanted
- `Cache-Control: no-cache, max-age=0`
- `X-Forwarded-For`, `X-Real-IP` — client IP through proxy
- `Strict-Transport-Security` — HSTS
- `Content-Security-Policy` — CSP

## 6. URL + IP basics

- **URL anatomy**: `https://user:pass@host.example.com:8443/path/to/page?query=value#fragment`
- **IPv4**: 4 octets (1.2.3.4); 2^32 = 4.3B addresses (exhausted)
- **IPv6**: 8 groups of 4 hex (`2001:db8::1`); 2^128 ≈ unlimited
- **Private ranges (RFC1918)**: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
- **localhost**: 127.0.0.1 / ::1
- **CIDR**: notation like `10.0.0.0/24` (256 addresses)

## 7. JSON

```javascript
const obj = { name: "Alice", roles: ["admin", "user"], active: true }
const str = JSON.stringify(obj, null, 2)
const parsed = JSON.parse(str)
```

JSON limits:
- No comments
- No trailing commas
- No undefined values (becomes `null` or omitted)
- No `Date` (becomes ISO string)
- No `BigInt`, `Map`, `Set` natively

For richer serialization: MessagePack, Protobuf, CBOR.

## 8. Data exchange between frontend and backend

Patterns:
- **REST** — resource-oriented; HTTP verbs + JSON
- **GraphQL** — query language; one endpoint
- **tRPC** — type-safe RPC for TS apps
- **WebSocket** — bidirectional, real-time
- **SSE** — server → client streaming (LLM-style)
- **gRPC** — internal services; binary; HTTP/2

For new public-facing APIs in 2026: REST + OpenAPI spec, optionally GraphQL for internal-flexibility tools.

## 9. Sample REST endpoint with validation (Zod)

```javascript
import { Hono } from 'hono'
import { zValidator } from '@hono/zod-validator'
import { z } from 'zod'

const app = new Hono()

const createUserSchema = z.object({
  name: z.string().min(1).max(100),
  email: z.string().email(),
  age: z.number().int().min(0).max(150).optional(),
})

app.post('/api/users', zValidator('json', createUserSchema), async (c) => {
  const body = c.req.valid('json')
  // body is typed!
  const user = await db.users.create(body)
  return c.json(user, 201)
})
```

Zod schemas validate at runtime + generate TS types automatically.

## 10. Connecting to MongoDB (preview for Module 53)

```javascript
import { MongoClient } from 'mongodb'

const client = new MongoClient(process.env.MONGO_URL)
await client.connect()
const db = client.db('teamable')

const users = await db.collection('users').find().toArray()
await db.collection('users').insertOne({ name: 'Alice', createdAt: new Date() })
```

## 11. Bun + Deno alternatives

- **Bun** (v1.0 Sept 2023, v1.2 in 2025) — Node-compatible runtime, 3-4x faster start, built-in test runner, bundler, package manager. Use for new projects where you control deployment.
- **Deno** (v1 in 2020, v2 Oct 2024 "Node-compatible") — Secure-by-default, TypeScript-first, built-in tools. Use for security-sensitive isolated scripts.

## 12. Quick self-check

1. What's the current Node.js LTS version?
2. What's Hono's killer feature?
3. What's the difference between PUT and PATCH?
4. What does Zod give you?
5. Why might you choose Bun over Node for a new project?

(Answers: Node 22 (until Apr 2027); portability — same code runs on Node, Bun, Deno, Workers, Lambda, edge; PUT replaces entirely (idempotent), PATCH does partial update; runtime validation + auto-generated TypeScript types from the same schema; 3-4x faster startup, built-in bundler/test/package-manager, less ops overhead.)
