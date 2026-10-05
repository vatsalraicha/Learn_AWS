# Chapter 56 — MapReduce: Historical Context and What Spark Improved

> **Goal of this chapter:** to teach you the MapReduce abstraction — the idea that started the modern era of distributed data processing — well enough that Spark's design choices stop looking arbitrary. Spark did not arrive in a vacuum. It was a deliberate response to MapReduce's strengths and weaknesses. Understanding the predecessor turns Spark from a list of features into a coherent answer to a specific historical question. By the end of this chapter you will know what MapReduce did right, what it did poorly, and exactly which problems Spark was designed to fix.

---

## 56.1 A small archeology of distributed processing

Distributed data processing did not begin with Spark. It did not begin with Hadoop either. People have been spreading computation across multiple machines since the 1970s — supercomputers, scientific clusters, transaction-processing systems, parallel databases. What was missing, until about 2004, was an *abstraction for ordinary developers*. To write distributed code, you had to be a specialist — you had to think about message-passing protocols, fault tolerance, node failures, and synchronisation, all of which required heroic engineering for each application.

The change came from Google. In 2004, two Google engineers, Jeffrey Dean and Sanjay Ghemawat, published a paper titled *"MapReduce: Simplified Data Processing on Large Clusters."* The paper described a programming model and a runtime that had been quietly used inside Google for several years to power things like the web index. The contribution was not so much the *math* — the patterns it captured had been known in functional programming for decades — but the *engineering*. Google had built a system where ordinary developers, with no distributed-systems background, could write programs that processed petabytes of data across thousands of machines, with automatic fault tolerance and reasonably balanced parallelism.

The paper was open-source-adjacent in spirit. Within a year, Doug Cutting and Mike Cafarella began re-implementing the ideas in Java as part of an open-source project that eventually became Apache Hadoop. By 2008–2010, Hadoop MapReduce was the de facto standard for batch data processing at internet-scale companies. The phrase "big data" entered the popular vocabulary around the same time, and Hadoop was its avatar.

This era — roughly 2008 to 2014 — is what people sometimes nostalgically call "the Hadoop era." It democratised big-data processing. It also taught the field, through painful experience, what was wrong with the MapReduce model. That experience is what Spark was built to address.

---

## 56.2 The MapReduce abstraction

MapReduce is, at its core, a two-step computation pattern. Every job, no matter how complex, is expressed as a sequence of two operations.

**Map.** Take each input record and produce zero or more `(key, value)` pairs from it. The map function is applied to every record independently, in parallel. The output of the map phase is a (huge) list of key-value pairs.

**Reduce.** All values with the same key are grouped together. For each unique key, a reduce function is applied to combine its list of values into a single output value (or sometimes a list).

That is it. Map turns one record into pairs. Reduce combines all values for each key. Everything else MapReduce can do — joining tables, aggregating, sorting, even iterative algorithms — has to be expressed via this two-step pattern, sometimes with multiple Map-Reduce stages chained together.

### 56.2.1 The canonical example: word count

The word count program is the "hello world" of MapReduce. The problem: given a huge corpus of text, count how many times each word appears.

**Map:** For each line of text, emit `(word, 1)` for each word in the line.

```
"the quick brown fox" → ("the", 1), ("quick", 1), ("brown", 1), ("fox", 1)
"the lazy dog"        → ("the", 1), ("lazy", 1), ("dog", 1)
```

**Shuffle (built into the framework):** Group all values with the same key.

```
"the"   → [1, 1]
"quick" → [1]
"brown" → [1]
"fox"   → [1]
"lazy"  → [1]
"dog"   → [1]
```

**Reduce:** For each key, sum the values.

```
"the"   → 2
"quick" → 1
"brown" → 1
"fox"   → 1
"lazy"  → 1
"dog"   → 1
```

Done. The MapReduce framework handles the parallelism (each map task processes a chunk of the input file) and the grouping (the shuffle moves all "the"s to the same reducer). The user writes only the map and reduce functions.

Let's walk through a slightly bigger numerical example. Suppose the input is a 1TB corpus spread across 10,000 files on a distributed file system (HDFS), and the cluster has 100 machines.

1. **Map phase.** The framework launches 10,000 map tasks (one per file, simplifying slightly). Each task reads one file from local disk (data locality, Chapter 55), tokenizes, and emits `(word, 1)` pairs to local disk. Output size per task: typically smaller than input, but still substantial.
2. **Shuffle phase.** The framework reads the map outputs and routes each `(word, 1)` pair to a reducer based on `hash(word) mod num_reducers`. Suppose there are 1,000 reducers. Every map task's output is partitioned 1,000 ways; each reducer reads its slice from every map task. Total data moved: at most as large as the map outputs.
3. **Reduce phase.** Each reducer receives all values for the words assigned to it. It sums them and writes the final output.

Aggregate counts assembled. The job runs in maybe 20 minutes on a 100-machine cluster, doing what would take days on a single machine.

### 56.2.2 Why this model is powerful

A few things make MapReduce surprisingly general.

**Independence of map tasks.** Each map task processes one chunk and emits pairs. No map task depends on another. So they can all run in parallel, in any order, on any machine. This means trivial horizontal scaling.

**Built-in fault tolerance.** If a map task fails (the machine crashed, the disk died), the framework restarts it on another machine. The intermediate output is recoverable because it was written to local disk. No special user code is needed for retries.

**Built-in parallelism.** The user doesn't pick how many map or reduce tasks to use — the framework decides based on the input size and cluster capacity.

**Simple programming model.** The user writes two pure functions. No threads, no locks, no message-passing protocols. The mental burden is small enough that a backend engineer can learn MapReduce in a week.

These properties are what made MapReduce *the* go-to abstraction for batch processing for a decade.

---

## 56.3 Expressing computations in the MapReduce idiom

The power of MapReduce comes from a surprising consequence: many problems that don't *look* like map+reduce can be rephrased to fit.

### 56.3.1 Sorting (e.g., distributed sort)

The map function emits `(record, null)`. The framework's shuffle phase sorts by key (this was a designed-in property — the shuffle uses a partitioner that, with the right configuration, produces sorted output). The reducer just outputs the records.

### 56.3.2 Grouping aggregates (e.g., total sales per region)

Map emits `(region, amount)` for each transaction. Reduce sums all amounts for each region. The output is the per-region total.

### 56.3.3 Joins (e.g., users joined with their transactions)

Map emits `(user_id, ("user_record", user_data))` from the users table and `(user_id, ("transaction_record", transaction_data))` from the transactions table. Reduce, for each `user_id`, sees a mix of user_record and transaction_record values; it joins them and emits the combined rows.

This is called a *reduce-side join* — it's straightforward but expensive because all the data crosses the network. A *map-side join* — when one table is small enough to fit in memory on every mapper — is much faster. Spark's broadcast join (Chapter 60) is the descendant of this idea.

### 56.3.4 Iterative algorithms (e.g., PageRank)

Here is where things start getting awkward. PageRank iteratively updates a vector of ranks: $r_{t+1} = M \cdot r_t$ where $M$ is the web graph's transition matrix. Each iteration is a MapReduce job. After 30 iterations, you've run 30 MapReduce jobs.

The catch: between each iteration, the entire rank vector is written to HDFS (the distributed file system) and read back. For PageRank on a billion-node graph, that's gigabytes per iteration. The disk I/O dominates the computation by a large margin. This is the fundamental weakness of MapReduce, and Spark's most important improvement (Section 56.5).

### 56.3.5 K-means clustering

K-means is another iterative algorithm. Each iteration: assign each point to its nearest centroid (map), then update each centroid as the mean of its assigned points (reduce). On a billion points and a thousand iterations, you have a thousand MapReduce jobs, each writing intermediate state to disk. The wall-clock time is dominated by disk I/O, not by the actual k-means math.

Practitioners in the late 2000s knew this was a problem. They built workarounds — chained Hadoop jobs, custom in-memory frameworks, hybrid systems — but the core abstraction itself was the bottleneck.

---

## 56.4 What MapReduce did well, and what it did poorly

It is worth being precise about the credit-and-debit ledger.

### 56.4.1 The strengths

1. **Simplicity.** Two functions to write. No distributed-systems expertise required.
2. **Linear scalability.** Adding machines doubles throughput, with very little tuning.
3. **Fault tolerance.** Built in. The framework handles retries, re-execution, replication.
4. **A real ecosystem.** Hadoop spawned an entire stack — HDFS, YARN, Hive, Pig, Mahout, HBase, Sqoop. For ten years, this was where serious big-data work happened.
5. **Open source.** The combination of Google's paper and the open-source Hadoop implementation meant any organisation could adopt it without licensing fees, accelerating adoption far beyond what a proprietary system would have achieved.

### 56.4.2 The weaknesses

1. **Disk-based shuffle.** Every MapReduce stage's output is written to disk, read back from disk by the next stage. For multi-stage and iterative workloads, the disk I/O dominates. A typical Hadoop job might spend 90% of its time on I/O and 10% on actual computation.
2. **Inflexible primitives.** Everything must be Map and Reduce. Expressing operations that don't fit this pattern — multi-way joins, windowed aggregations, nested data — requires awkward gymnastics. The Hadoop ecosystem responded with higher-level languages (Pig, Hive) that compiled to MapReduce, but the underlying limitation remained.
3. **No abstraction over the JVM.** Hadoop MapReduce is fundamentally a Java framework. Python support exists (Hadoop Streaming) but is awkward, slow, and not ergonomic.
4. **No native iterative support.** As we saw above, iterative algorithms are a worst-case for MapReduce because each iteration writes to disk. ML training and graph algorithms suffer especially.
5. **No interactive querying.** A MapReduce job runs as a batch. You submit it; you wait minutes or hours; you get results. There's no way to interactively explore data the way a SQL session or a Python REPL allows. Hive partially addressed this by compiling SQL to MapReduce, but the latency was still in tens of seconds at best.
6. **Operational complexity.** Hadoop clusters were notorious for requiring large operations teams to keep healthy. The configuration knobs were many and inscrutable.

The weaknesses didn't kill MapReduce — it was the best option available for years, and millions of jobs ran on it productively. But they did create *pressure* for something better. By 2010 or so, that pressure had crystallised into specific demands: keep the simplicity, keep the fault tolerance, but make iterative algorithms fast, support more abstractions than just map and reduce, and make it interactive.

---

## 56.5 Enter Spark

In 2009, a Berkeley grad student named Matei Zaharia started working on what became Apache Spark. The motivating problem, in Zaharia's own description, was the iterative-machine-learning pain point: MapReduce's disk-bound shuffle made ML training impractically slow on large datasets. He wanted a system that kept MapReduce's fault tolerance and scalability but performed iteration in memory.

The result was the **RDD** — Resilient Distributed Dataset — Spark's foundational abstraction (Chapter 58 covers it in depth). An RDD is an immutable, distributed collection of objects, partitioned across the cluster. The key word is *immutable*. Operations on RDDs produce *new* RDDs; the originals are unchanged. And — critically — Spark tracks the *lineage* of every RDD: the sequence of operations that produced it from the original input data.

This lineage tracking is what gave Spark its name's "Resilient" property and its iterative-workload speed.

### 56.5.1 The key innovations

**1. In-memory computation.** When you process data in Spark, intermediate results stay in RAM by default. Only when you explicitly persist them to disk, or when memory pressure forces a spill, do they touch the disk. For iterative algorithms, this is the single biggest win — the inter-iteration disk write/read is eliminated.

**2. Lineage-based fault tolerance.** Spark doesn't need to checkpoint every intermediate result to recover from failure. If a partition is lost, Spark looks at the lineage — the chain of operations that produced it — and recomputes the partition from the still-extant inputs. This is more memory-efficient than MapReduce's "write everything to disk" approach, while still being fault-tolerant.

**3. Richer primitives.** Beyond `map` and `reduce`, RDDs support `filter`, `flatMap`, `union`, `intersection`, `distinct`, `groupByKey`, `reduceByKey`, `join`, `cogroup`, `sample`, `cartesian`, and many more. Each is implemented to be efficient in the distributed setting. The user doesn't have to shoehorn their algorithm into Map+Reduce.

**4. Lazy evaluation.** Operations on RDDs don't execute immediately. They build up a *plan* — a directed acyclic graph (DAG) of transformations. Only when you call an *action* (like `count`, `collect`, `saveAsTextFile`) does Spark actually run the plan. This is crucial because it lets Spark *optimise* the plan before executing — combining filters, pushing predicates down, choosing the best join strategy. Hadoop MapReduce, with its eager Map and Reduce, had no such opportunity.

**5. The interactive shell and notebook story.** Because Spark could run quickly enough on cached data, it could support interactive querying. A data scientist could load a 100GB dataset into memory once, then run dozens of ad-hoc queries against it in seconds each, instead of submitting MapReduce jobs that each took minutes. This was a huge ergonomic improvement that opened distributed data work to a much wider audience.

**6. Multiple language APIs.** Spark was Scala-first, but Python (PySpark), Java, and R bindings were first-class citizens from early on. This matched the actual data-science community much better than Hadoop's Java-only world.

### 56.5.2 The numerical impact

For iterative workloads — the original motivating use case — Spark was *10–100× faster* than equivalent MapReduce jobs. This was not a marginal improvement; it was a step change that made workloads tractable that hadn't been before.

For one-shot batch workloads — the bread and butter of MapReduce — Spark was typically 2–10× faster, mostly because of the smarter optimisation and the avoidance of unnecessary intermediate writes.

Within five years of Spark's release (2014–2018), it had displaced Hadoop MapReduce as the default for new big-data projects. The shift was decisive enough that by 2020, "Hadoop" mostly meant "HDFS and YARN, with Spark on top." Map-and-reduce as a programming model survived — Spark still has `map` and `reduce` operations — but as one pattern among many, not the only one.

---

## 56.6 The MapReduce model still matters

It would be a mistake to read this chapter as "MapReduce is dead, ignore it." Two things matter for Spark practitioners.

First, Spark's `groupByKey`, `reduceByKey`, and aggregate operations are *direct descendants* of MapReduce's reduce phase. When you call `df.groupBy("region").agg(F.sum("amount"))`, what happens under the hood is essentially the same thing the MapReduce reduce phase does. Spark's shuffle is the same conceptual operation as MapReduce's shuffle. Understanding *why* shuffles happen — because all values for the same key must end up on the same machine before they can be reduced — is the central performance concept in Spark, and it comes straight from MapReduce.

Second, the MapReduce model is the *minimum* useful abstraction. Spark adds many things on top, but you can always fall back to map and reduce when nothing else fits. RDDs (Chapter 58) expose the map/reduce primitives directly. Even DataFrame operations decompose, under the hood, into map and reduce stages connected by shuffles.

The lesson is: MapReduce was a brilliant abstraction that hit its limits when applied to iterative and interactive workloads. Spark fixed those limits by keeping the conceptual core (parallel transformations across a partitioned dataset, with a shuffle to group by key) and adding lazy evaluation, in-memory state, richer primitives, and optimisation. Knowing the predecessor turns Spark's design from a set of features into a coherent system.

---

## 56.7 Worked example: word count in Spark vs. MapReduce

Let's see the difference directly. Same problem (word count over a corpus), two implementations.

### 56.7.1 Hadoop MapReduce (conceptual, Java)

```java
public class WordCount {
    public static class Map extends Mapper<LongWritable, Text, Text, IntWritable> {
        private final static IntWritable one = new IntWritable(1);
        private Text word = new Text();

        public void map(LongWritable key, Text value, Context context) {
            for (String token : value.toString().split("\\s+")) {
                word.set(token);
                context.write(word, one);
            }
        }
    }

    public static class Reduce extends Reducer<Text, IntWritable, Text, IntWritable> {
        public void reduce(Text key, Iterable<IntWritable> values, Context context) {
            int sum = 0;
            for (IntWritable val : values) sum += val.get();
            context.write(key, new IntWritable(sum));
        }
    }

    public static void main(String[] args) throws Exception {
        // ~30 more lines of boilerplate to configure the job, input/output paths,
        // serialization formats, etc.
    }
}
```

50+ lines, mostly boilerplate. The actual logic — emit (word, 1), sum — is buried.

### 56.7.2 Spark (RDD API)

```python
text = sc.textFile("hdfs://corpus/*")
counts = (text
    .flatMap(lambda line: line.split())
    .map(lambda word: (word, 1))
    .reduceByKey(lambda a, b: a + b))
counts.saveAsTextFile("hdfs://output/")
```

Five lines. The shape is exactly the same — flatMap is the map step (tokenize), map produces (word, 1), reduceByKey is the reduce step (sum). The Spark code reads almost like a description of the algorithm.

### 56.7.3 Spark (DataFrame API — what modern Spark users actually write)

```python
from pyspark.sql import functions as F
df = spark.read.text("hdfs://corpus/*")
counts = (df.select(F.explode(F.split("value", "\\s+")).alias("word"))
    .groupBy("word").count())
counts.write.parquet("output/")
```

Five lines again, but now leveraging Spark SQL — the Catalyst optimizer (Chapter 59) sees what we're doing and can apply optimisations like vectorisation. This is the form you would actually use in production today.

All three programs compute the same answer. The Hadoop version takes 30 minutes on a 100-node cluster. The Spark versions take 2 minutes on the same cluster — most of the speedup from avoiding intermediate disk writes.

---

## 56.8 A short note on Hadoop's continued relevance

Hadoop didn't die when Spark rose. What changed is its role.

- **HDFS** (the Hadoop Distributed File System) is still widely used as the storage layer in on-prem big-data deployments, though cloud object stores (S3, ADLS, GCS) have taken over in cloud-native environments. Modern Databricks uses cloud object stores almost exclusively.
- **YARN** (Yet Another Resource Negotiator) is one of the cluster managers Spark can run on. In cloud deployments, Kubernetes or proprietary managers (Databricks Resource Manager) are more common.
- **Hadoop MapReduce** — the actual MapReduce execution engine — is now mostly legacy. New work doesn't use it. Existing pipelines often still do, because rewriting is expensive.

For the Databricks ML Associate exam, you don't need to know Hadoop's internals. You need to know that MapReduce was the predecessor, that Spark improved on it primarily by adding in-memory computation and richer primitives, and that the basic map/group/reduce concept survives in Spark's DataFrame operations.

---

## 56.9 Summary

1. MapReduce, introduced by Google in 2004 and popularised by Hadoop, was the first widely-adopted abstraction for ordinary developers to write distributed batch jobs. Its core idea: every computation is a sequence of Map (transform records to key-value pairs) and Reduce (combine all values for each key) operations.
2. The framework handles parallelism, shuffle, and fault tolerance automatically — the developer writes only the two functions.
3. MapReduce's main weakness was disk-based shuffle: between every Map and Reduce stage, intermediate data is written to and read from disk. For iterative algorithms (ML, graph), this dominated runtime.
4. Other weaknesses: inflexible primitives, no native iterative support, no interactive querying, awkward Python support, heavy operational complexity.
5. Spark, introduced in 2009-2010 at UC Berkeley, kept MapReduce's strengths (parallelism, fault tolerance, simple programming model) and fixed the weaknesses: in-memory computation, lineage-based fault tolerance, richer primitives, lazy evaluation enabling whole-program optimisation, interactive querying, first-class Python support.
6. Spark is typically 10–100× faster than Hadoop MapReduce on iterative workloads and 2–10× faster on batch workloads. It displaced Hadoop MapReduce as the default for new big-data projects between 2014 and 2018.
7. The MapReduce conceptual model still underlies Spark — `groupByKey`, `reduceByKey`, and DataFrame `groupBy(...).agg(...)` are direct descendants. Shuffles in Spark are the same conceptual operation as shuffles in MapReduce.

---

## 56.10 What this builds on / where this returns

**Builds on:** Chapter 55's shared-nothing architecture and the cost of network communication. MapReduce *is* the canonical shared-nothing batch abstraction; everything in this chapter assumes that mental model.

**Returns:**
- Chapter 57 makes the Spark execution model concrete: driver, executors, cluster manager. The "framework that handles parallelism and shuffle" we waved at in this chapter becomes a specific set of processes.
- Chapter 58 introduces RDDs formally — Spark's direct successor to MapReduce's key-value pair list.
- Chapter 60 dissects the shuffle operation in detail — the place where Spark and MapReduce share the most DNA and where Spark performance is most often won or lost.
- Chapter 59 explains Catalyst, which is the *optimisation* layer that lazy evaluation makes possible — something MapReduce structurally could not have.

---

## 56.11 Exercises

1. **Map-reduce by hand.** You have a list of customer purchase records, each with `(customer_id, amount)`. Write the map function and the reduce function (in pseudocode) for computing the total spend per customer.

2. **MapReduce-style join.** You have a Users table and a Transactions table, both keyed on `user_id`. Sketch how a MapReduce reduce-side join would work. What does map emit? What does reduce do?

3. **Iterative algorithm pain.** Suppose you want to compute the average of a column over 100GB of data — easy, one MapReduce job. Now suppose you want to compute the *running* average after each consecutive 1GB chunk (so 100 averages total). How would this look in Hadoop MapReduce? How does Spark do it better?

4. **The lineage idea.** Spark's "resilient" means a lost partition can be *recomputed* from its lineage. Explain why this works for `rdd1.map(...).filter(...).map(...)` but doesn't work in a useful way if the original input data is also lost.

5. **Choose your tool.** For each of the following, decide whether MapReduce alone (Hadoop) would have been adequate in 2010, or whether you'd want Spark's improvements. Justify briefly:
   1. A one-time ETL job that joins two tables and aggregates.
   2. Training a logistic regression with 100 iterations.
   3. Computing the daily page-view count from web logs.
   4. Running PageRank for 30 iterations on a 10-billion-node graph.
   5. An interactive exploration session where a data scientist runs 50 queries against a 100GB dataset.

6. **Disk I/O math.** Suppose a MapReduce job writes 200GB of intermediate data to local disk and reads it back. Disk write bandwidth is 500 MB/s. How long does the write phase take? The read phase? What's the total disk-I/O wall-clock time? How does this affect overall job runtime?

7. **Lazy evaluation benefit.** Suppose your Spark code is `df.filter(x > 100).select("a").filter(a < 500).count()`. Why is laziness helpful here? What would happen in an eager system? Hint: think about what the optimiser can do.

8. **Word count cost comparison.** Same word-count problem, same corpus (1TB), same cluster (100 machines). Hadoop MapReduce takes 30 minutes; Spark takes 2 minutes. Without changing the algorithm, where did the 28 minutes go?

9. **Why not just use MapReduce with more RAM?** A naive response to MapReduce's disk-shuffle problem is "buy more RAM and tell Hadoop to use it." Why didn't this work — what's structurally different about Spark's in-memory model?

10. **The PageRank example.** Without re-reading, sketch in your own words why PageRank is a worst-case workload for MapReduce. What does Spark do differently that solves it?

<details>
<summary>Answers</summary>

1. Map: `(customer_id, amount) → emit(customer_id, amount)`. Reduce: `(customer_id, [amounts]) → emit(customer_id, sum(amounts))`. Identical structure to word count.

2. Map for Users emits `(user_id, ("U", user_record))`. Map for Transactions emits `(user_id, ("T", txn_record))`. Reduce sees, for each `user_id`, a list of records mixing U and T entries. It separates them, then emits the cross product (one user_record joined with each transaction). Reduce-side joins move all data through the shuffle — expensive but general.

3. In MapReduce: 100 sequential jobs, each writing intermediate state to HDFS and reading it back next iteration. ~100× the disk I/O of a single pass. Spark: cache the input data in memory, then run 100 incremental aggregations against the cached RDD. Disk touched once (to read the original data) instead of 200 times.

4. The lineage is "starting from input X, do these operations." If X is gone, the lineage can't replay. So Spark only achieves fault tolerance against *executor* failures, not against catastrophic input-data loss. The input data must be durably stored (HDFS, S3, etc.). Beyond a certain lineage depth, Spark also supports checkpointing — write an intermediate to disk so the lineage can restart from there.

5. (i) Either works; one-shot ETL is MapReduce's sweet spot. (ii) Spark — 100 iterations of writes to HDFS would make Hadoop painfully slow. (iii) MapReduce works fine — one-pass aggregation. (iv) Spark — 30 iterations is exactly the iterative-disk-I/O pain point. (v) Spark, hands down — MapReduce can't support interactive exploration at sub-minute latencies.

6. Write 200GB at 500 MB/s = 400 seconds. Read 200GB = 400 seconds. Total: ~800 seconds = ~13 minutes just on local disk I/O for one shuffle. For an iterative job that does this 30 times, that's 400 minutes of pure disk I/O. This is the "MapReduce is disk-bound" problem in numbers.

7. With laziness, the optimiser can see the whole chain before executing. It can: (a) combine the two filters into one predicate (`100 < x < 500`); (b) push the filters down to be applied during the read; (c) drop unused columns. In an eager system, each operation is executed standalone, producing an intermediate that's then re-filtered — wasted work.

8. Mostly disk I/O on the intermediate shuffle, plus serialisation overhead, plus the lack of pipelining between map and reduce (Hadoop's reduce can only start after all map is done; Spark can sometimes pipeline). The Spark version keeps the partial counts in memory and ships them directly to the reducer.

9. Hadoop's data format and execution model are *built around* writing to disk between stages. There's no in-memory path for the shuffle output to skip the disk; you'd need to redesign the execution engine. That redesign is what Spark *is*. You can't bolt it onto Hadoop without rewriting almost everything.

10. PageRank iterates: `rank = M * rank`, repeated until convergence (~30 iterations on web-scale graphs). Each iteration is a join (M with rank) and a reduce (sum contributions). In MapReduce, every iteration writes the new rank vector to HDFS and reads it back — gigabytes of disk I/O per iteration, dominating the math. In Spark, the matrix M and the rank vector live in memory after the first read; each iteration is pure compute, with no inter-iteration disk I/O. Result: 30–100× speedup.

</details>
