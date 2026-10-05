# vector_search_demo.py
# Build a Mosaic AI Vector Search Delta Sync index with hybrid (BM25+ANN) and run queries.
# Pairs with Module 13 (Vector Search & RAG).
#
# Requires: Databricks workspace with Vector Search enabled; embedding model accessible
# via FMAPI (BGE-large used here).

# %% Setup
from databricks.vector_search.client import VectorSearchClient
from pyspark.sql import functions as F

vsc = VectorSearchClient()

CATALOG = "clinical"
SCHEMA  = "silver"
ENDPOINT_NAME = "prod_clinical_vs"
INDEX_NAME    = f"{CATALOG}.indexes.notes_v1"
SOURCE_TABLE  = f"{CATALOG}.{SCHEMA}.note_chunks_with_embeddings"


# %% Step 1 — Source Silver table with embeddings
def create_source_table_with_embeddings():
    spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {SOURCE_TABLE} (
      chunk_id        STRING NOT NULL,
      member_id       STRING,
      encounter_id    STRING,
      source_doc      STRING,
      text            STRING,
      embedding       ARRAY<FLOAT>,
      ingestion_ts    TIMESTAMP,
      PRIMARY KEY (chunk_id)
    )
    USING DELTA
    CLUSTER BY (member_id)
    TBLPROPERTIES (
      'delta.enableChangeDataFeed' = 'true'  -- required for Delta Sync index
    )
    """)


def backfill_embeddings():
    """One-time: compute embeddings for the existing chunks via ai_query."""
    spark.sql(f"""
    INSERT INTO {SOURCE_TABLE}
    SELECT
      chunk_id, member_id, encounter_id, source_doc, text,
      ai_query('databricks-bge-large-en', text) AS embedding,
      current_timestamp() AS ingestion_ts
    FROM {CATALOG}.{SCHEMA}.note_chunks
    WHERE chunk_id NOT IN (SELECT chunk_id FROM {SOURCE_TABLE})
    """)


# %% Step 2 — Create the Delta Sync index
def create_delta_sync_index():
    """
    Delta Sync index automatically follows the source table via CDF.
    pipeline_type:
      - TRIGGERED: nightly sync. Cheaper. Recommended for stable corpora.
      - CONTINUOUS: tail CDF; ~minutes lag. More expensive. For active-add corpora.
    """
    vsc.create_delta_sync_index(
        endpoint_name      = ENDPOINT_NAME,
        source_table_name  = SOURCE_TABLE,
        index_name         = INDEX_NAME,
        pipeline_type      = "TRIGGERED",
        primary_key        = "chunk_id",
        embedding_dimension= 1024,                # BGE-large
        embedding_vector_column = "embedding",
        columns_to_sync    = [
            "chunk_id", "text", "member_id", "encounter_id", "source_doc"
        ],
    )


# %% Step 3 — Hybrid query (BM25 + ANN with RRF)
def query_clinical_notes(question: str, member_id: str | None = None, num_results: int = 10):
    """
    Hybrid search combines keyword (BM25) and semantic (dense ANN).
    Essential for healthcare retrieval where notes mix prose with codes (ICD-10, CPT, SNOMED).
    """
    filters = {}
    if member_id:
        filters = {"member_id": [member_id]}

    results = (
        vsc.get_index(ENDPOINT_NAME, INDEX_NAME)
        .similarity_search(
            query_text  = question,
            columns     = ["chunk_id", "text", "member_id", "encounter_id", "source_doc"],
            num_results = num_results,
            query_type  = "HYBRID",   # BM25 + ANN with RRF
            filters     = filters,
        )
    )
    return results


# %% Step 4 — Trigger a sync (for TRIGGERED indexes)
def sync_index():
    vsc.get_index(ENDPOINT_NAME, INDEX_NAME).sync()


# %% Demo run
if __name__ == "__main__":
    create_source_table_with_embeddings()
    backfill_embeddings()
    create_delta_sync_index()

    # Sample query — find chunks about chest pain for a specific member
    results = query_clinical_notes(
        question="shortness of breath chest pain emergency",
        member_id="MBR-DEID-12345",
        num_results=5,
    )
    print(results)


# %% Production discipline notes
"""
1. **Index rebuild** for embedding model upgrades (e.g., BGE-large → BGE-large-v2):
   - Build a NEW index (notes_v2) in parallel
   - Backfill: re-embed via ai_query into a new column
   - Switch agent's index reference; deprecate old index
   - DON'T try to swap embedding models on the same index — vector spaces incompatible

2. **Scale limits** (May 2026):
   - Standard endpoint: ~320M vectors cap; tens-of-ms latency
   - Storage-optimized: ~1B vectors at 768-dim; ~250ms latency; 7× cheaper per vector
   - QPS plateau ~30 QPS per endpoint at large scale

3. **HIPAA discipline**:
   - Index lives in UC managed encrypted storage (managed-services CMK applies)
   - Members must have explicit grants on source table for the agent (running as their identity)
     to retrieve their data
   - Filter by member_id at retrieval time for per-member RAG

4. **Cost monitoring**:
   - Pricing per "vector search unit" (~2M vectors of 768-dim per unit)
   - Monitor via system.billing.usage under VECTOR_SEARCH SKU
   - For >50M chunks, use storage-optimized; tag with cost_center for chargeback
"""
