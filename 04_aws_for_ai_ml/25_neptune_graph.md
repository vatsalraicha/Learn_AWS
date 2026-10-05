# Module 25 — Neptune — Graph Database

> **What this is:** Amazon Neptune — property graph + RDF, Gremlin/SPARQL/openCypher languages, Neptune Serverless, Neptune Analytics, Neptune ML, and the GraphRAG pattern.

---

## 1. The dual nature

Neptune supports **two graph models simultaneously**:

- **Property graph** — nodes + edges with properties. Queried with **Gremlin** (Apache TinkerPop) or **openCypher** (Neo4j's language).
- **RDF (Resource Description Framework)** — subject-predicate-object triples. Queried with **SPARQL**.

Most non-academic use cases pick **property graph + openCypher** (modern, familiar to engineers from Neo4j).

## 2. Capacity tiers

- **Neptune Provisioned** — instance-based, like Aurora.
- **Neptune Serverless** (GA late 2022) — Neptune Capacity Units (NCU); 1 NCU ≈ 2 GB RAM. Autoscale.

## 3. Neptune Analytics (the 2024 story)

**Neptune Analytics** (GA Nov 2023, expanded 2024) is a separate service for **analytical graph workloads**.

- **In-memory graph database** for one-off analytical workloads.
- Built-in algorithms: PageRank, connected components, shortest path, community detection.
- **Native vector search** built in — combines graph traversal with vector similarity.
- Used for ad-hoc graph analytics where Neptune Database (the transactional store) is overkill.

## 4. Neptune ML

GNN (Graph Neural Network) training and inference, integrated with SageMaker.

- Trains on **Deep Graph Library (DGL)** under the hood.
- Inductive node classification, link prediction, edge classification.
- Capital One use case: **fraud detection** — entities and relationships as graph, GNN learns suspicious-relationship patterns.

## 5. GraphRAG

The intersection of LLMs and graph databases: use graph traversal as part of retrieval for RAG.

- Vector search retrieves candidates by semantic similarity.
- Graph traversal expands context (e.g., from a customer node, hop to recent transactions, related accounts).
- LLM generates with both vector + graph context.

**Bedrock Knowledge Bases** added Neptune Analytics as a supported vector backend in 2024.

## 6. Bulk loading

S3 → Neptune via the **bulk loader** (CSV with `~id`, `~from`, `~to`, `~label` columns). Much faster than per-record inserts for initial population.

## 7. Cluster topology

- Primary (writer) + up to 15 replicas.
- 6-way replicated storage (Aurora-style).
- Multi-AZ failover.

## 8. Capital One lens — fraud and graph

Capital One's tech blog publishes work on:

- **Graph ML for fraud** — entity-relationship graphs detect identity-fraud rings, money laundering patterns.
- **University partnerships** on global graph transformers and dynamic customer embeddings.

Likely architecture pattern:
1. Stream transactions to Neptune (writer).
2. Run periodic Neptune ML GNN training.
3. Score new transactions via real-time SageMaker inference using GNN-derived features.

**Talking point:** *"For fraud-graph workloads, I'd put the transactional graph in Neptune Database with Neptune ML for periodic GNN retraining, and use Neptune Analytics for ad-hoc investigations that benefit from in-memory speed."*

## 9. Pitfalls

- **Choosing the wrong language** — Gremlin's API is imperative; openCypher is declarative. Most teams pick openCypher.
- **Large traversals** — graph queries that visit millions of nodes time out; design queries with hop limits.
- **Neptune ML training time** — non-trivial; GNNs are slow vs tabular ML.
- **Bulk loader CSV format** — strict; one mistake aborts the load.

## 10. Sanity check

1. What are the three query languages, and which one most teams pick?
2. Neptune Database vs Neptune Analytics — when do you pick each?
3. What is Neptune ML, and what's the underlying library?
4. What does GraphRAG add over plain vector RAG?
5. How might Capital One use Neptune for fraud detection?

## 11. Cross-references

- **Module 27** — vector capabilities decision framework (Neptune Analytics as one of the vector options)
- **Module 42** — Bedrock Knowledge Bases (Neptune Analytics backend)
- **Topic 01 Module 22** — GraphRAG deep dive
- **Module 53** — Capital One MLOps spine (fraud-graph patterns)

## Primary sources

- [`Neptune_Best_Practices.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Neptune_Best_Practices.html)
- [`Neptune_Analytics.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Neptune_Analytics.html)
- [`Neptune_ML.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Neptune_ML.html)
- Research report: [`06c_analytical_vector_graph.md`](../../research_inputs/04_aws_for_ai_ml/06c_analytical_vector_graph.md)
