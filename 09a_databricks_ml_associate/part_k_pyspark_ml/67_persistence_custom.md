# Chapter 67 — Pipeline Persistence, Custom Transformers, Custom Estimators

> **Goal of this chapter:** to take the Pipeline pattern from notebook toy to production artifact. We cover how `pyspark.ml` serialises fitted Pipelines to disk and reloads them, what's actually on disk in those directories, the version-compatibility caveats that bite in production, and — when built-in Transformers and Estimators don't fit your need — how to write your own custom stages that integrate cleanly with the Pipeline framework. This is the chapter that closes the gap between "I trained a model in a notebook" and "the model is part of a versioned, deployable, reloadable system."

---

## 67.1 Why this chapter exists

Models that live only in your notebook session are toys. A real ML system has these properties:

1. **You can save the trained pipeline to a known location and reload it later.** "Later" might be tomorrow's batch scoring run, next month's model audit, or three years from now when the regulator asks you to reproduce a decision.
2. **The reload is exact** — same vocabulary, same scaler statistics, same coefficients, byte-for-byte same predictions on identical inputs.
3. **The format is stable and shareable.** A pipeline saved by data-science can be loaded by data-engineering's batch job and by the serving service.
4. **When built-ins don't suffice, you can add your own custom logic and have it participate in the framework — fittable, transformable, savable, tunable.**

Properties 1-3 are about *persistence*. Property 4 is about *extending* the framework with your own Transformers and Estimators.

This chapter covers both. We'll see the on-disk layout of a saved pipeline, then write two custom stages — a `LogTransformer` (pure Transformer) and a `GroupMeanImputer` (Estimator producing a learned Transformer) — that you could use in a real Pipeline today.

---

## 67.2 Persistence: the basics

A fitted `PipelineModel` has a `.save(path)` method:

```python
model.save("/dbfs/tmp/spam_pipeline_v1")
```

This writes a *directory* — not a single file — at the given path. The directory layout looks roughly like this:

```
/dbfs/tmp/spam_pipeline_v1/
├── metadata/
│   ├── _SUCCESS
│   └── part-00000             # JSON: top-level pipeline metadata
└── stages/
    ├── 0_Tokenizer_abc123/
    │   └── metadata/
    │       └── part-00000     # JSON: tokenizer params
    ├── 1_StopWordsRemover_def456/
    │   └── metadata/
    │       └── part-00000
    ├── 2_HashingTF_ghi789/
    │   └── metadata/
    │       └── part-00000
    ├── 3_IDFModel_jkl012/
    │   ├── metadata/
    │   │   └── part-00000     # JSON: class name, params, uid
    │   └── data/
    │       └── part-00000.snappy.parquet   # the learned IDF vector
    └── 4_LogisticRegressionModel_mno345/
        ├── metadata/
        └── data/
            └── part-00000.snappy.parquet   # learned coefficients + intercept
```

A few things to read out of this:

- **One subdirectory per stage**, named with a numeric prefix that preserves stage order.
- **Each stage has a `metadata/` subdirectory** with a JSON file describing the class name, the unique ID (`uid`) Spark uses to identify the stage, and the parameter values that were set on it.
- **Stages that learned something (IDFModel, LogisticRegressionModel) also have a `data/` subdirectory** containing the learned weights, stored as Parquet for efficient I/O.
- **Stages that don't learn (Tokenizer, StopWordsRemover, HashingTF) only have metadata**, because there's nothing to persist beyond the parameter settings.

Loading is symmetrical:

```python
from pyspark.ml import PipelineModel
reloaded = PipelineModel.load("/dbfs/tmp/spam_pipeline_v1")
predictions = reloaded.transform(new_data)
```

The `PipelineModel.load` walks the stages directory in numeric order, reads each stage's metadata to figure out which class to instantiate, restores the parameters, and (for fitted stages) loads the learned weights from the Parquet files. The reconstructed `PipelineModel` is identical in behaviour to the original.

### 67.2.1 Storage backends

The `path` you give to `save` and `load` can be:

- A local filesystem path (`/tmp/my_pipeline`) — fine for development.
- DBFS (`/dbfs/...` or `dbfs:/...`) — Databricks' default.
- S3 (`s3://my-bucket/path/`).
- ADLS (`abfss://...`).
- GCS (`gs://...`).
- HDFS.

Anything Spark can read with its filesystem layer is fair game. In Databricks production, the canonical choice is to save to a managed Unity Catalog volume or to register the pipeline as an MLflow model (covered in Part L), which gives you versioning and access control on top of the raw file dump.

### 67.2.2 overwrite vs append

If the target path already exists, `.save(path)` errors. To overwrite:

```python
model.write().overwrite().save(path)
```

For append semantics — adding a new version alongside the old one — you would version the path yourself (`/path/v1/`, `/path/v2/`). MLflow's model registry handles this for you (Part L); without MLflow, the discipline is yours.

### 67.2.3 Saving unfitted Pipelines

A `Pipeline` (the Estimator, before `.fit`) is also savable:

```python
pipeline.save("/path/to/pipeline_unfit")
# ... later ...
from pyspark.ml import Pipeline
reloaded_unfit = Pipeline.load("/path/to/pipeline_unfit")
model = reloaded_unfit.fit(train_df)
```

This is useful when you want to share a *pipeline design* — the stages, their parameter settings — without sharing the trained weights. It's also how you separate "we agreed on the architecture" from "we ran the training." Less common in day-to-day work, but a clean pattern when pipeline design and training happen in different jobs or by different teams.

---

## 67.3 Version compatibility caveats

This is the section that bites people in production. Pyspark.ml does *not* guarantee that a pipeline saved with one Spark version loads in another.

The risks:

1. **Major version upgrades (e.g., 3.x → 4.0)** sometimes change serialization formats. A pipeline saved with 3.5 may fail to load in 4.0.
2. **Custom stages are even more fragile** — if you wrote a custom Transformer in your codebase and the codebase moved, the class might not be importable when the loader tries to instantiate it.
3. **Underlying numeric libraries** (BLAS, LAPACK) can differ across runtimes, producing tiny floating-point differences in predictions. Usually negligible for downstream use; matters when reproducibility is regulatory.

The mitigations:

- **Pin your Databricks runtime version** in production. Don't auto-upgrade.
- **Test load on every Spark version you intend to support** before upgrading.
- **For regulated environments**, save not just the pipeline but the *runtime image* you trained on — Databricks Model Serving lets you snapshot this.
- **Use MLflow** (Part L) for end-to-end provenance — it captures the conda environment, package versions, and the pipeline together.

A production sanity check: every CI job that trains a pipeline should also immediately load it back and run a small prediction comparison. If load-after-save fails, you find out at CI time, not at serving time three weeks later.

---

## 67.4 Why you might need a custom stage

`pyspark.ml.feature` has a lot of Transformers. It also has gaps:

- You want to impute missing values *with the group mean* (the mean within each category of another column), not just the global mean. Pyspark's `Imputer` doesn't do this.
- You want to apply $\log(x + 1)$ to a column. Pyspark has `Log` SQL function but no Transformer wrapping it cleanly.
- You want to apply a winsorisation (cap values at the 1st and 99th percentiles). Pyspark has nothing for this.
- You want a `StringIndexer` that maps unseen categories to a specific "OTHER" bucket rather than the next-largest integer (the default `handleInvalid="keep"`).
- You want to apply a complex domain-specific transformation that involves multiple input columns.

You have three options:

1. **`SQLTransformer`** — a Transformer that applies a Spark SQL statement to the input DataFrame. Quick and dirty; great for one-liners.
2. **Pandas UDFs** — if the transformation is naturally row-wise or grouped, a Pandas UDF can express it efficiently.
3. **A custom Transformer or Estimator class** — when the operation has parameters, needs to learn from data, or you want it to integrate as a first-class Pipeline stage (savable, tunable, etc.).

The first two are escape hatches; the third is the principled solution and what we'll focus on.

---

## 67.5 A custom Transformer: `LogTransformer`

We want a stage that takes a numeric column and adds a new column with $\log(x + 1)$ applied. No learning needed — purely a function of the input.

```python
from pyspark.ml import Transformer
from pyspark.ml.param.shared import HasInputCol, HasOutputCol
from pyspark.ml.param import Param, Params, TypeConverters
from pyspark.ml.util import DefaultParamsReadable, DefaultParamsWritable
from pyspark.sql import functions as F


class LogTransformer(Transformer, HasInputCol, HasOutputCol,
                     DefaultParamsReadable, DefaultParamsWritable):
    """Apply log(x + offset) elementwise to a numeric column."""
    
    offset = Param(
        Params._dummy(),
        "offset",
        "The constant added before taking the log (default 1.0).",
        typeConverter=TypeConverters.toFloat,
    )
    
    def __init__(self, inputCol=None, outputCol=None, offset=1.0):
        super().__init__()
        self._setDefault(offset=1.0)
        self._set(inputCol=inputCol, outputCol=outputCol, offset=offset)
    
    def setOffset(self, value):
        return self._set(offset=value)
    
    def getOffset(self):
        return self.getOrDefault(self.offset)
    
    def _transform(self, dataset):
        in_col = self.getInputCol()
        out_col = self.getOutputCol()
        off = self.getOffset()
        return dataset.withColumn(out_col, F.log(F.col(in_col) + F.lit(off)))
```

Let's walk through what's going on, because every line earns its place.

### 67.5.1 The class hierarchy

`Transformer` is the base class — gives us `.transform`. `HasInputCol` and `HasOutputCol` are mixins that provide standard `inputCol` and `outputCol` parameters (you don't have to redeclare them). `DefaultParamsReadable` and `DefaultParamsWritable` are mixins that give you the standard save/load behaviour for free — saving the parameter values to JSON, instantiating on load.

This is the **standard recipe** for a parameter-only custom Transformer (no learned data). If your Transformer needs to persist *data* (not just parameters), you'd use different mixins (`MLReadable`, `MLWritable`) and implement read/write methods yourself.

### 67.5.2 The `Param` declaration

```python
offset = Param(
    Params._dummy(),
    "offset",
    "Description.",
    typeConverter=TypeConverters.toFloat,
)
```

`Param` is pyspark.ml's typed parameter class. The first argument should be the class instance, but at class definition time `self` doesn't exist yet, so `Params._dummy()` is a sentinel that pyspark replaces during normal use. `typeConverter` ensures the parameter value gets coerced to the right type when set.

Why use `Param` rather than just a Python attribute? Because the Pipeline framework introspects Params:

- CrossValidator's grid can target a Param: `ParamGridBuilder().addGrid(my_transformer.offset, [0.5, 1.0, 2.0])`.
- `save`/`load` uses Params for serialisation.
- `.explainParams()` lists them for documentation.

Anything you want to be a tunable, persistable, framework-aware knob must be a Param.

### 67.5.3 The `__init__`

The constructor does three things: calls super, sets defaults, sets the user-supplied values. The pattern `self._setDefault(...)` then `self._set(...)` is the canonical way to allow defaults to be overridden by explicit user arguments. This dual-step exists because Spark distinguishes between "this is the default that ships with the class" and "this is the value the user explicitly set".

### 67.5.4 The setter/getter methods

```python
def setOffset(self, value):
    return self._set(offset=value)

def getOffset(self):
    return self.getOrDefault(self.offset)
```

These provide the standard pyspark API (`getX`, `setX`) for the parameter. `getOrDefault` returns the explicit value if set, otherwise the default. Convention; not strictly required to make the class work, but conventional and expected.

### 67.5.5 The `_transform` method

```python
def _transform(self, dataset):
    in_col = self.getInputCol()
    out_col = self.getOutputCol()
    off = self.getOffset()
    return dataset.withColumn(out_col, F.log(F.col(in_col) + F.lit(off)))
```

This is where the actual work happens. The framework calls `_transform` (note the underscore) when the user calls `.transform`. Return a new DataFrame with the transformation applied.

Crucially: this must be a *pure Spark DataFrame operation*. Don't pull the data to the driver, don't do a Python loop. Use Spark SQL functions (`pyspark.sql.functions.*`). If you absolutely need row-by-row Python, use a Pandas UDF or a regular UDF — but consider that route an anti-pattern unless there's no SQL-native equivalent.

### 67.5.6 Using the class

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("custom").getOrCreate()
df = spark.createDataFrame([(1.0,), (10.0,), (100.0,)], ["value"])

log_t = LogTransformer(inputCol="value", outputCol="log_value", offset=1.0)
out = log_t.transform(df)
out.show()
# +-----+------------------+
# |value|         log_value|
# +-----+------------------+
# |  1.0|0.6931471805599453|
# | 10.0|2.3978952727983707|
# |100.0| 4.61512051684126  |
# +-----+------------------+
```

And the framework integration just works:

```python
from pyspark.ml import Pipeline
from pyspark.ml.feature import VectorAssembler

pipeline = Pipeline(stages=[
    LogTransformer(inputCol="value", outputCol="log_value", offset=1.0),
    VectorAssembler(inputCols=["log_value"], outputCol="features"),
    # ... an estimator
])
pipeline_model = pipeline.fit(df)
pipeline_model.save("/tmp/pipeline_with_custom")
# reload and use
reloaded = PipelineModel.load("/tmp/pipeline_with_custom")
```

Because we used the `DefaultParamsReadable`/`DefaultParamsWritable` mixins, save and load work without our writing any extra code.

---

## 67.6 A custom Estimator: `GroupMeanImputer`

Now a harder case. We want a stage that imputes missing values in a column with the mean *within each group* of another column. For example, impute missing `income` with the mean income *within the same age bracket*.

This needs to learn from data (the per-group means), so it's an Estimator. The `.fit` will compute the per-group means and return a Transformer (a `GroupMeanImputerModel`) that carries them.

```python
from pyspark.ml import Estimator, Transformer
from pyspark.ml.param.shared import HasInputCol, HasOutputCol
from pyspark.ml.param import Param, Params, TypeConverters
from pyspark.ml.util import DefaultParamsReadable, DefaultParamsWritable
from pyspark.sql import functions as F


class GroupMeanImputer(Estimator, HasInputCol, HasOutputCol,
                       DefaultParamsReadable, DefaultParamsWritable):
    """Impute missing values in inputCol with the mean within each groupCol value."""
    
    groupCol = Param(
        Params._dummy(),
        "groupCol",
        "Column to group by when computing means.",
        typeConverter=TypeConverters.toString,
    )
    
    def __init__(self, inputCol=None, outputCol=None, groupCol=None):
        super().__init__()
        self._set(inputCol=inputCol, outputCol=outputCol, groupCol=groupCol)
    
    def setGroupCol(self, value):
        return self._set(groupCol=value)
    
    def getGroupCol(self):
        return self.getOrDefault(self.groupCol)
    
    def _fit(self, dataset):
        in_col = self.getInputCol()
        group_col = self.getGroupCol()
        # Compute per-group means
        means_df = (dataset
                    .filter(F.col(in_col).isNotNull())
                    .groupBy(group_col)
                    .agg(F.mean(F.col(in_col)).alias("__group_mean__")))
        # Also compute global mean as a fallback for unseen groups
        global_mean = (dataset
                       .filter(F.col(in_col).isNotNull())
                       .agg(F.mean(F.col(in_col)).alias("__global_mean__"))
                       .collect()[0]["__global_mean__"])
        # Materialise the per-group means as a dict on the driver
        means = {row[group_col]: row["__group_mean__"] for row in means_df.collect()}
        # Construct and return the fitted Transformer
        return GroupMeanImputerModel(
            inputCol=in_col,
            outputCol=self.getOutputCol(),
            groupCol=group_col,
            means=means,
            globalMean=global_mean,
        )


class GroupMeanImputerModel(Transformer, HasInputCol, HasOutputCol,
                            DefaultParamsReadable, DefaultParamsWritable):
    """Transformer returned by GroupMeanImputer.fit; carries learned per-group means."""
    
    groupCol = Param(Params._dummy(), "groupCol", "", typeConverter=TypeConverters.toString)
    
    def __init__(self, inputCol=None, outputCol=None, groupCol=None,
                 means=None, globalMean=None):
        super().__init__()
        self._set(inputCol=inputCol, outputCol=outputCol, groupCol=groupCol)
        self._means = means or {}
        self._global_mean = globalMean
    
    def _transform(self, dataset):
        in_col = self.getInputCol()
        out_col = self.getOutputCol()
        group_col = self.getOrDefault(self.groupCol)
        # Build a CASE WHEN expression for the lookup
        # Use spark.createDataFrame to broadcast means
        means_data = [(k, v) for k, v in self._means.items()]
        means_df = dataset.sql_ctx.createDataFrame(
            means_data, [group_col, "__group_mean__"]
        )
        # Left join the means
        joined = dataset.join(F.broadcast(means_df), on=group_col, how="left")
        # Fill: if input is null, use group mean; if group mean is null too, use global mean
        filled = joined.withColumn(
            out_col,
            F.coalesce(
                F.col(in_col),
                F.col("__group_mean__"),
                F.lit(self._global_mean),
            ),
        )
        return filled.drop("__group_mean__")
```

A lot to unpack.

### 67.6.1 The two-class structure

A custom Estimator is *two* classes: the Estimator itself (with `.fit`) and its Model (with `.transform`). This mirrors the built-in pattern (`StringIndexer` / `StringIndexerModel`, `LogisticRegression` / `LogisticRegressionModel`).

### 67.6.2 The `_fit` method

`_fit` computes the per-group means as a Python dict (small enough to live on the driver), computes a global mean as fallback, and constructs and returns a `GroupMeanImputerModel`. The Model holds the learned data.

### 67.6.3 The Model's `_transform`

`_transform` joins the dataset against a small DataFrame of `(group, mean)` pairs (broadcasted because it's small), then uses `coalesce(input, group_mean, global_mean)` to fill missing values with the appropriate fallback.

There's a subtlety here. We *could* implement this as a giant `CASE WHEN` expression — `when(group == "A", mean_A).when(group == "B", mean_B)...` — but for high-cardinality groups, the expression gets unwieldy and the query plan inflates. The join-with-broadcasted-small-DataFrame approach scales better.

### 67.6.4 Limitations of this implementation

This implementation is illustrative, not production-grade. Things it doesn't do:

- **Doesn't properly persist the `_means` dict.** With just `DefaultParamsReadable/Writable`, only the *Params* (inputCol, outputCol, groupCol) are saved — not the dict that lives in `self._means`. To persist data, we'd implement `MLReadable.read()` and `MLWritable.write()` ourselves, with custom Parquet I/O for the means. The full machinery is a few dozen extra lines.
- **Driver memory for `.collect()` on the means.** If you have millions of distinct groups, materialising them on the driver might OOM. A scalable version would keep the means in a small DataFrame and join, never collecting.
- **No `handleInvalid` parameter.** Unseen groups at serve time silently fall back to global mean; a configurable parameter would be more flexible.

For real production use of custom logic this complex, MLflow's `python_function` flavour (Part L) sometimes provides a cleaner path than a full custom Pyspark Estimator. But knowing the pattern matters: it's how you extend pyspark.ml when the framework abstractions are right but the built-in stages aren't.

---

## 67.7 Persisting custom stages: the bigger picture

When you save a Pipeline containing a custom Transformer:

1. The pipeline's metadata file records the *class path* of your custom Transformer — something like `myproject.transformers.LogTransformer`.
2. The custom Transformer's own metadata file records its Param values.
3. If the Transformer has any learned data (i.e., it's a Model), that data is persisted as Parquet.

When you load the pipeline:

1. Spark reads the class path string.
2. Spark tries to import it.
3. If the import succeeds, Spark instantiates the class and restores its Params.
4. If you had a custom Model with learned data, Spark also restores that.

The fragile point is step 2. If your custom class isn't importable in the loading environment, the load fails. The implications:

- **Your custom stages must live in a package that the loading environment installs.** A class defined inline in a notebook cell will save fine but won't reload in a different notebook unless the cell that defines the class runs first.
- **Refactoring class paths breaks reload.** If you move `LogTransformer` from `myproject.transformers` to `myproject.feature.log`, old pipelines won't load. The fix is to either keep the old path as a stub or use MLflow to package the code alongside the model.
- **In Databricks specifically**, the recommended pattern is to put custom stages in a workspace library (a `.whl` or `.egg` file) that all relevant clusters install, OR to use MLflow's `python_function` flavour to bundle the code with the model.

This is one of those "everything works in dev, blows up in prod" classes of problem. The mitigation is discipline: custom stages live in a versioned package, period.

---

## 67.8 When to write custom code vs reach for an alternative

Some heuristics for when to write a custom stage versus an alternative:

**Reach for `SQLTransformer` if**:
- The transformation is a single SQL expression.
- You don't need to tune it under CV.
- It's specific enough that a class would be overkill.

```python
from pyspark.ml.feature import SQLTransformer
sql_t = SQLTransformer(
    statement="SELECT *, LOG(price + 1) AS log_price FROM __THIS__"
)
```

**Reach for a Pandas UDF if**:
- The transformation is row-wise or windowed and complex enough that Spark SQL can't express it well.
- The performance of a Python loop in a UDF is acceptable.

**Reach for a custom Transformer/Estimator if**:
- You want the transformation to be a first-class Pipeline stage (tunable via Param grids, savable as part of a pipeline, etc.).
- The logic is complex enough that wrapping it as a class produces clearer code than inlining it.
- You want to share it across multiple pipelines or projects.

**Reach for MLflow's `python_function` flavour if**:
- The model is a black-box scikit-learn or PyTorch object that doesn't fit `pyspark.ml`'s shape at all.
- You want maximum flexibility at the cost of giving up `pyspark.ml`'s framework integration.

Most teams have a small library of custom Transformers that they reuse across projects. Writing them is a one-time investment that pays back over years.

---

## 67.9 An end-to-end persistence demo

Putting Chapters 62-67 together, here's the lifecycle of a pipeline from training to load:

```python
from pyspark.sql import SparkSession
from pyspark.ml import Pipeline, PipelineModel
from pyspark.ml.feature import StringIndexer, OneHotEncoder, VectorAssembler, StandardScaler
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
from pyspark.ml.evaluation import BinaryClassificationEvaluator

spark = SparkSession.builder.appName("ch67-demo").getOrCreate()

# === Step 1: prepare data ===
train = spark.createDataFrame([
    ("M",  35, 75000.0, 1),
    ("F",  29, 62000.0, 0),
    ("M",  41, 85000.0, 1),
    ("F",  52, 110000.0, 1),
    ("M",  23, 45000.0, 0),
    ("F",  47, 95000.0, 1),
    ("M",  31, 70000.0, 0),
    ("F",  38, 90000.0, 1),
], ["gender", "age", "income", "label"])

# === Step 2: build the pipeline ===
gender_idx = StringIndexer(inputCol="gender", outputCol="gender_idx", handleInvalid="keep")
gender_ohe = OneHotEncoder(inputCols=["gender_idx"], outputCols=["gender_ohe"])
log_inc    = LogTransformer(inputCol="income", outputCol="log_income", offset=1.0)
assembler  = VectorAssembler(inputCols=["age", "log_income", "gender_ohe"], outputCol="features_raw")
scaler     = StandardScaler(inputCol="features_raw", outputCol="features",
                            withMean=True, withStd=True)
lr         = LogisticRegression(featuresCol="features", labelCol="label", maxIter=20)

pipeline = Pipeline(stages=[gender_idx, gender_ohe, log_inc, assembler, scaler, lr])

# === Step 3: tune via CV ===
grid = ParamGridBuilder().addGrid(lr.regParam, [0.0, 0.01, 0.1]).build()
evaluator = BinaryClassificationEvaluator(labelCol="label", metricName="areaUnderROC")
cv = CrossValidator(estimator=pipeline, estimatorParamMaps=grid,
                    evaluator=evaluator, numFolds=3)
cv_model = cv.fit(train)
best_pipeline_model = cv_model.bestModel    # this is a PipelineModel

# === Step 4: save ===
best_pipeline_model.write().overwrite().save("/tmp/ch67_best_pipeline")

# === Step 5: simulate a new SparkSession (in a real system, this is a new job) ===
reloaded = PipelineModel.load("/tmp/ch67_best_pipeline")

# === Step 6: predict ===
test = spark.createDataFrame([
    ("M", 40, 80000.0),
    ("F", 25, 50000.0),
], ["gender", "age", "income"])

predictions = reloaded.transform(test)
predictions.select("gender", "age", "income", "prediction", "probability").show()
```

Walk through what happened:

- We trained a 6-stage pipeline containing one *custom* Transformer (`LogTransformer`) and five built-in stages.
- We tuned `regParam` via CV, training $3 \times 3 + 1 = 10$ models.
- We saved the best pipeline (the +1 refit, with the chosen `regParam`).
- We loaded it back. The custom `LogTransformer` was reinstantiated from its class path; the StringIndexerModel, OneHotEncoderModel, StandardScalerModel, and LogisticRegressionModel were all reloaded with their learned weights.
- We predicted on new data. The prediction path uses the same transformations as training — the same StringIndexer dictionary, the same log offset, the same scaler stats, the same LR coefficients.

This is the production shape. Every other Part L topic (MLflow tracking, Model Registry, Databricks Model Serving) is a layer of governance and operational tooling *on top of* what this snippet does. The plumbing here is the foundation.

---

## 67.10 What this chapter taught you, in one sentence

**`PipelineModel.save(path)` writes the entire fitted pipeline — every parameter and every learned weight — to a versioned directory of metadata JSON and data Parquet files, reloadable in a new SparkSession via `PipelineModel.load`; when built-in stages don't suffice, you subclass `Transformer` or `Estimator`, declare your knobs as `Param` objects, implement `_transform` or `_fit`, and inherit `DefaultParamsReadable/Writable` for free serialisation — but custom-stage classes must remain importable in any environment that loads pipelines containing them, which makes packaging discipline a production requirement.**

---

## 67.11 What this builds on / where this returns

**Builds on:**

- Chapter 62 — the Pipeline pattern and the Transformer/Estimator interfaces.
- Chapter 63 — built-in Transformers, the things we'd otherwise have to write ourselves.
- Chapter 64 — built-in Estimators, ditto.
- Chapter 65 — CrossValidator, which produces a `bestModel` worth saving.

**Returns:**

- Chapter 72 — MLflow's tracking captures pipeline metadata alongside metrics; the artifact is a saved pipeline at heart.
- Chapter 73 — MLflow's Model Registry sits on top of the persistence we built here, adding aliases, lifecycle stages, and access control.
- Part L generally — production serving paths consume the saved-pipeline artifact this chapter produces.

This chapter is the closing arch of Part K. The next chapters (Part L) take the artifacts we now know how to produce and put governance, deployment, and operational tooling around them.

---

## 67.12 Exercises

1. **The disk layout.** You save a 4-stage pipeline (Tokenizer, StopWordsRemover, IDFModel, LogisticRegressionModel). Roughly what subdirectories appear under the save path?

2. **Which stages have data.** Of those 4 stages, which have `data/` subdirectories and which only have `metadata/`? Justify in each case.

3. **Save-load reproducibility.** You train a Pipeline on a fresh SparkSession, save it, reload it in a different SparkSession, and run `.transform` on identical data. Should the predictions be exactly the same? Why or why not?

4. **The class-path trap.** You define `LogTransformer` in cell 5 of a notebook, use it in a pipeline, save the pipeline, restart the notebook kernel, and try to load the pipeline without re-running cell 5. What happens?

5. **`SQLTransformer` vs custom Transformer.** Your team needs a "subtract column A from column B and store in column C" stage that will appear in three pipelines. Pick the better tool and justify in two sentences.

6. **Why `Param` not Python attributes.** Name two concrete framework features that depend on custom knobs being declared as `Param` objects rather than plain Python attributes.

7. **The `_transform` vs `transform` convention.** Why does the user call `.transform` but the implementation override `_transform`? What does the framework do in between?

8. **Estimator returning Transformer.** In `GroupMeanImputer._fit`, why does it return a *different* class (`GroupMeanImputerModel`) rather than `self`? What would go wrong if we returned `self`?

9. **`DefaultParamsReadable` limits.** Why isn't `DefaultParamsReadable` enough for `GroupMeanImputerModel` to be properly saveable in production? What's missing?

10. **Version pinning.** A regulator asks you to reproduce a model prediction made 3 years ago. What aspects of the training environment do you need to have pinned to do this? Name at least 4.

11. **Picking your tool.** For each scenario, pick the right approach (custom Transformer, custom Estimator, SQLTransformer, Pandas UDF, MLflow python_function):
    - (a) One-line "split a string column on commas, take the first element, store in a new column."
    - (b) Learn a per-customer median spend, then impute missing values in a transaction-amount column with the customer's median.
    - (c) Wrap a pre-trained sklearn `LightGBM` model for use in a Spark pipeline.
    - (d) Apply a domain-specific rounding rule: round price to nearest $0.99 if it's above $10, else nearest $0.49.

12. **CV with a custom stage's parameter.** Can you put a custom Transformer's `Param` into a `ParamGridBuilder().addGrid(...)` and have CrossValidator tune it? Justify.

<details>
<summary>Answers</summary>

1. Top-level `metadata/` for the pipeline; under `stages/`, four subdirectories like `0_Tokenizer_*`, `1_StopWordsRemover_*`, `2_IDFModel_*`, `3_LogisticRegressionModel_*`. Each stage subdirectory has at minimum a `metadata/` directory; the fitted Model stages also have `data/` directories.

2. Only stages 2 (IDFModel) and 3 (LogisticRegressionModel) have `data/` — they carry learned weights (the IDF vector, the LR coefficients). Tokenizer and StopWordsRemover are parameterless Transformers; nothing to persist beyond the JSON metadata.

3. The predictions should be exact (bit-for-bit identical) modulo floating-point differences from numeric library version drift. Both runs use the same learned weights and the same transformation logic. The exceptions: shuffles with non-deterministic key ordering, or random-state operations like UDFs that internally generate randomness. For pure inference on a saved pipeline, reproducibility should be exact.

4. The load fails. The pipeline's metadata records the class path of `LogTransformer`, and the loader tries to import it. With the class not defined in the current session, the import fails and `PipelineModel.load` raises.

5. `SQLTransformer` for a single SQL expression used in 3 pipelines is fine and faster to maintain than a custom class. But if the team expects to add tunable parameters later (offset, scaling factor, configurable column names) or wants the operation to be a tunable CV target, a custom Transformer pays back the marginal effort.

6. (a) `ParamGridBuilder.addGrid` targets Param objects — Cartesian-product grids over your knob require it. (b) `PipelineModel.save`/`load` serialises Params automatically via `DefaultParamsReadable/Writable`. Bonus: `.explainParams()`, `.copy(extra)`, and other framework features all rely on the Param machinery.

7. The framework's `transform` method calls your `_transform` after doing parameter validation, copy-on-write handling, and column-name resolution. The underscore is the standard "implementation hook" pattern; users see the clean `.transform`, you implement the work in `_transform`.

8. Returning `self` would mean the Estimator's class also has a `.transform` method, which is the contract of a Transformer not an Estimator. Architecturally, the two roles are separate. Mechanically, you also can't easily attach learned data to `self` while keeping `self` semantically an "Estimator." Building a separate Model class keeps the framework's role distinction clean and matches the pattern of every built-in `(X, XModel)` pair.

9. `DefaultParamsReadable/Writable` only persists `Param`s. The learned `_means` dict and `_global_mean` scalar live as plain Python attributes on the Model instance, so they're not saved. To persist them, you'd implement `write()` and `read()` methods that serialise/deserialise these to Parquet alongside the metadata.

10. (a) The Spark/Databricks runtime version; (b) the pyspark and pyspark.ml package versions; (c) any custom code packages used (your custom Transformers' source); (d) the training data snapshot (or a hash of it). Optionally: the JVM version, the OS, BLAS versions. MLflow + Delta Lake snapshots together capture most of this automatically.

11. (a) `SQLTransformer`. (b) Custom Estimator (with learned per-customer medians). (c) MLflow `python_function`. (d) Custom Transformer (no learning needed) OR `SQLTransformer` with a CASE WHEN — either is reasonable.

12. Yes. As long as the knob is declared as a `Param` (not a plain Python attribute), `ParamGridBuilder().addGrid(my_transformer.my_param, [...])` works. CrossValidator will refit the entire pipeline for each grid value, including your custom Transformer with the appropriate parameter set. This is one of the main payoffs of using the Param API.

</details>
