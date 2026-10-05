# 53 — MongoDB + SQL vs NoSQL

## 1. SQL vs NoSQL — the decision framework

| | SQL (relational) | NoSQL |
|---|---|---|
| **Schema** | Strict; defined upfront | Flexible; per-document |
| **Joins** | Native, optimized | Manual; better to denormalize |
| **Transactions** | ACID, native | Limited (improved in 2020s) |
| **Scaling** | Vertical first; horizontal hard | Horizontal-native |
| **Query lang** | Standardized (SQL) | Per-DB |
| **Use case** | Most apps; default 2026 | Specific patterns (event sourcing, sharded scale, flexible schema) |

In 2026: **default is Postgres** for OLTP. NoSQL where Postgres genuinely doesn't fit.

## 2. NoSQL categories

| Category | DBs | Pattern |
|---|---|---|
| **Document** | MongoDB, CouchDB, DynamoDB, Firestore | JSON docs in collections |
| **Key-value** | Redis, DynamoDB, Memcached | Hash table |
| **Wide-column** | Cassandra, ScyllaDB, BigTable, Keyspaces | Row keys + column families |
| **Graph** | Neo4j, Neptune, ArangoDB | Nodes + edges |
| **Time-series** | InfluxDB, TimescaleDB, VictoriaMetrics | Timestamped data |
| **Vector** | Pinecone, Weaviate, Qdrant, Milvus, pgvector | Embeddings + ANN |
| **Search** | Elasticsearch, OpenSearch, Algolia | Full-text + faceting |

## 3. MongoDB at a glance

- **Document database** — stores BSON (binary JSON)
- **Schema-flexible** — documents in a collection can differ
- **Aggregation pipeline** — powerful query language
- **Sharding** native — horizontal scale by shard key
- **Replica sets** for HA
- **Atlas** — managed cloud offering (dominant 2026)
- **Vector Search** built-in (since 2023)

Versions: MongoDB 7.0 (2023), 8.0 (Oct 2024). Atlas runs 7.0+/8.0.

## 4. Basic MongoDB operations

```javascript
import { MongoClient } from 'mongodb'

const client = new MongoClient('mongodb://localhost:27017')
const db = client.db('teamable')
const users = db.collection('users')

// Create
await users.insertOne({ name: 'Alice', age: 30, roles: ['admin'] })
await users.insertMany([
  { name: 'Bob', age: 25 },
  { name: 'Carol', age: 28 },
])

// Read
const alice = await users.findOne({ name: 'Alice' })
const admins = await users.find({ roles: 'admin' }).toArray()
const adults = await users.find({ age: { $gte: 18 } })
  .sort({ age: -1 }).limit(10).toArray()

// Update
await users.updateOne({ name: 'Alice' }, { $set: { age: 31 } })
await users.updateMany({ active: false }, { $set: { archived: true } })

// Delete
await users.deleteOne({ name: 'Alice' })
await users.deleteMany({ archived: true })

// Aggregation
const pipeline = [
  { $match: { active: true } },
  { $group: { _id: '$department', count: { $sum: 1 }, avgAge: { $avg: '$age' } } },
  { $sort: { count: -1 } },
]
const stats = await users.aggregate(pipeline).toArray()
```

## 5. ACID transactions (since MongoDB 4.0, 2018)

```javascript
const session = client.startSession()
try {
  session.startTransaction()
  await db.collection('accounts').updateOne(
    { _id: from }, { $inc: { balance: -amount } }, { session }
  )
  await db.collection('accounts').updateOne(
    { _id: to }, { $inc: { balance: amount } }, { session }
  )
  await session.commitTransaction()
} catch (e) {
  await session.abortTransaction()
  throw e
} finally {
  session.endSession()
}
```

## 6. Indexes — the performance lever

```javascript
await users.createIndex({ email: 1 }, { unique: true })
await users.createIndex({ createdAt: -1 })
await users.createIndex({ name: 'text' })   // text search
await users.createIndex({ location: '2dsphere' })  // geo
await users.createIndex({ embedding: 'vector', numDimensions: 1536, similarity: 'cosine' })  // vector
```

Without indexes, queries do collection scans → slow.

`explain()` shows the query plan:
```javascript
await users.find({ email: 'alice@example.com' }).explain('executionStats')
```

## 7. Install MongoDB locally

```bash
# macOS
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
mongosh

# Docker
docker run -d -p 27017:27017 --name mongo mongo:8
mongosh
```

For production: **MongoDB Atlas** (managed cloud) — most teams skip self-hosting entirely.

## 8. Schema design — the doc-store mindset

SQL: normalize. NoSQL: **denormalize where you read**. Example:

### SQL (normalized)
```sql
CREATE TABLE posts (id, user_id, title, body);
CREATE TABLE comments (id, post_id, user_id, body);
CREATE TABLE users (id, name, email);
-- Join 3 tables to render a post page
```

### MongoDB (embedded)
```javascript
{
  _id: ObjectId('...'),
  title: 'Hello',
  body: 'World',
  author: { id: 'u1', name: 'Alice' },          // embedded user
  comments: [                                     // embedded comments
    { author: 'Bob', body: 'Nice', createdAt: ... },
    { author: 'Carol', body: 'Cool', createdAt: ... },
  ],
}
```

Render post page = 1 query. Trade-off: updating Alice's name updates many docs.

Patterns:
- **Embed** when child can't exist without parent + read together
- **Reference** when child is shared / large / changes often
- **Extended reference** — embed some fields, reference for the rest

## 9. SQL vs NoSQL — when each wins

### Postgres wins for:
- Anything with relations + joins
- Strong consistency needs
- Mature transactional workloads
- Reporting / OLAP-lite via partial indexes + materialized views
- **Default for new projects** in 2026

### MongoDB wins for:
- Flexible schema where rows really vary
- Event sourcing
- Real-time data + change streams
- Geospatial heavy
- Time-series within Atlas (TS Collections)

### DynamoDB wins for:
- Massive scale predictable access patterns
- Serverless (pay-per-request)
- Single-digit-ms latency at any scale
- AWS-native

### Redis wins for:
- Cache
- Rate limiting
- Session store
- Pub/sub
- Real-time leaderboards

### Postgres + extensions (the 2026 swiss army):
- pgvector for vector search
- TimescaleDB for time-series
- PostGIS for geo
- Citus for sharding
- JSONB for flexible schema

Postgres-with-extensions covers ~80% of what people used to need NoSQL for.

## 10. Connecting from Node (Teamable backend pattern)

```javascript
import { MongoClient } from 'mongodb'

const client = new MongoClient(process.env.MONGO_URL, {
  serverApi: { version: '1', strict: true, deprecationErrors: true },
})

let dbConnection

export async function connect() {
  if (!dbConnection) {
    await client.connect()
    dbConnection = client.db(process.env.MONGO_DB)
  }
  return dbConnection
}
```

For ORMs: **Mongoose** (Node), **Prisma** (multi-DB), **Drizzle** (TS-first, multi-DB).

## 11. Quick self-check

1. Why is Postgres often the 2026 default for OLTP?
2. What replaced Vuex / Redux-style state in MongoDB's "denormalize where you read" principle?
3. What's an Atlas Vector Search index used for?
4. When use DynamoDB over MongoDB?
5. What's the difference between embedding and referencing in MongoDB schema?

(Answers: relational + ACID + ecosystem + JSONB for flexible schema + pgvector for vector + battle-tested; embed data needed together in one document — read in one query at cost of denormalization; semantic search via embeddings — RAG, recommendations, similar items; massive predictable-access scale + serverless billing model + AWS-native + need for single-digit-ms latency; embed = child stored inside parent (read together, hard to share), reference = child stored separately and parent points to it (share easily, multiple reads).)
