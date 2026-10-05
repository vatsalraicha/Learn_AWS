# Databricks Certified Machine Learning Associate — Mastery Track

> A textbook for engineers preparing to sit the Databricks Certified Machine Learning Associate exam — written to teach the underlying concepts from first principles, not to drill exam objectives. The Databricks APIs are the syntactic surface; the depth lives in the math, the intuition, and the engineering tradeoffs underneath. If you finish this book, no question on this material should surprise you, and you will be genuinely better at doing the job.
>
> **Audience:** strong Python assumed; PySpark and Spark taught from zero. Machine learning taught from zero.

---

## Contents

| Part | Theme | Chapters |
|------|-------|---------:|
| **A** | [Why ML exists](#part-a--why-ml-exists) — framing the problem | 4 |
| **B** | [Probability & statistics primer](#part-b--probability--statistics-primer) | 6 |
| **C** | [Linear algebra & calculus essentials](#part-c--linear-algebra--calculus-essentials) | 5 |
| **D** | [The fundamental ML problem](#part-d--the-fundamental-ml-problem) — loss, bias-variance, CV | 7 |
| **E** | [Feature engineering as a discipline](#part-e--feature-engineering-as-a-discipline) | 8 |
| **F** | [Supervised algorithms — from the math](#part-f--supervised-algorithms--from-the-math) | 7 |
| **G** | [Unsupervised algorithms](#part-g--unsupervised-algorithms) | 4 |
| **H** | [Model evaluation theory](#part-h--model-evaluation-theory) | 6 |
| **I** | [Hyperparameter optimization — the science](#part-i--hyperparameter-optimization--the-science) | 7 |
| **J** | [Spark from zero — distributed compute](#part-j--spark-from-zero) | 7 |
| **K** | [pyspark.ml in depth](#part-k--pysparkml-in-depth) | 6 |
| **L** | [Databricks platform & MLflow](#part-l--databricks-platform--mlflow) | 7 |
| **M** | [Capstone — full project + exam strategy](#part-m--capstone) | 2 |

---

## Part A — Why ML Exists

> **Goal:** Before any math, before any code, the reader should understand what problem machine learning was invented to solve, what it is and isn't, and the high-level shape of the workflow. Every later chapter assumes this framing.

| # | Chapter | What you'll be able to do after |
|---|---------|---------------------------------|
| 1 | [What is Machine Learning?](part_a_why_ml/01_what_is_ml.md) | Explain ML as function approximation; distinguish ML from rule-based programming; situate ML in the history of computing |
| 2 | [The Three Paradigms — Supervised, Unsupervised, Reinforcement](part_a_why_ml/02_three_paradigms.md) | Categorize any ML problem by paradigm; pick the right paradigm for a business problem; understand the scope of the ML Associate exam |
| 3 | [A Worked Example — Spam Detection End-to-End](part_a_why_ml/03_spam_end_to_end.md) | Walk through every step of an ML project at the conceptual level; use the vocabulary (features, labels, training, inference, accuracy, precision, recall, threshold, overfitting) correctly |
| 4 | [The ML Workflow / Lifecycle](part_a_why_ml/04_ml_lifecycle.md) | Name and sequence every step of a real ML project; identify what can go wrong at each step; preview where each step lives on Databricks |

---

## Part B — Probability & Statistics Primer

| # | Chapter |
|---|---------|
| 5 | Random variables, distributions, expectation, variance |
| 6 | The normal, binomial, Bernoulli, multinomial, Poisson distributions |
| 7 | Joint, marginal, conditional probability; independence |
| 8 | Bayes' theorem with worked applications |
| 9 | Sampling, the law of large numbers, the central limit theorem |
| 10 | Hypothesis testing, p-values, confidence intervals (and what they don't mean) |

## Part C — Linear Algebra & Calculus Essentials

| # | Chapter |
|---|---------|
| 11 | Vectors and matrices — geometric intuition |
| 12 | Dot products, projections, orthogonality |
| 13 | Matrix multiplication, inverse, determinant |
| 14 | Eigenvalues and eigenvectors (we'll need this for PCA) |
| 15 | Gradients and the chain rule (we'll need this for training) |

## Part D — The Fundamental ML Problem

| # | Chapter |
|---|---------|
| 16 | Loss functions and the optimization framing of ML |
| 17 | Gradient descent and its variants (SGD, mini-batch, momentum) |
| 18 | Capacity, overfitting, underfitting |
| 19 | The bias-variance decomposition (with full derivation) |
| 20 | Regularization — L1, L2, ElasticNet, with geometric intuition |
| 21 | Train / validation / test splits — what each is for |
| 22 | Cross-validation theory — k-fold, stratified, time-series CV, leakage |

## Part E — Feature Engineering as a Discipline

| # | Chapter |
|---|---------|
| 23 | EDA — what to look at and why |
| 24 | Missing data — MCAR, MAR, MNAR taxonomy; imputation strategies |
| 25 | Categorical encoding — ordinal vs nominal, OHE math, target encoding, hashing |
| 26 | Numerical transformations — scaling, normalization, log/Box-Cox/Yeo-Johnson |
| 27 | Outlier detection and treatment |
| 28 | Feature interactions, polynomial features, basis expansions |
| 29 | Feature selection — filter, wrapper, embedded methods |
| 30 | Feature stores in practice (preview before Part L) |

## Part F — Supervised Algorithms — From the Math

| # | Chapter |
|---|---------|
| 31 | Linear regression — OLS derivation, assumptions, residuals |
| 32 | Logistic regression — log-odds, MLE, decision boundary |
| 33 | Decision trees — Gini, entropy, recursive splitting, pruning |
| 34 | Random forests — bagging, OOB error, feature importance |
| 35 | Boosting from first principles — AdaBoost |
| 36 | Gradient boosted trees — GBM, XGBoost, LightGBM |
| 37 | Naive Bayes and k-nearest neighbors (lighter — completeness) |

## Part G — Unsupervised Algorithms

| # | Chapter |
|---|---------|
| 38 | K-means — algorithm, k-means++ init, choosing k (elbow, silhouette, gap) |
| 39 | Hierarchical clustering — agglomerative, dendrograms |
| 40 | PCA — derivation as eigendecomposition of covariance |
| 41 | Other dimensionality reduction — t-SNE, UMAP (light touch) |

## Part H — Model Evaluation Theory

| # | Chapter |
|---|---------|
| 42 | Classification metrics — confusion matrix, precision, recall, F1, F-beta |
| 43 | ROC and AUC — the geometric meaning |
| 44 | PR curves — when they tell the truth that ROC hides |
| 45 | Regression metrics — MSE, RMSE, MAE, MAPE, R², adjusted R² |
| 46 | Imbalanced classification — stratified sampling, class weights, threshold tuning, SMOTE |
| 47 | Multi-class and multi-label — one-vs-rest, micro/macro/weighted |

## Part I — Hyperparameter Optimization — The Science

| # | Chapter |
|---|---------|
| 48 | The HPO problem — search space, objective, budget |
| 49 | Grid search — complete and exhaustive — and why it fails |
| 50 | Random search — Bergstra & Bengio's argument |
| 51 | Bayesian optimization — surrogate models, acquisition functions |
| 52 | Tree-structured Parzen Estimator (TPE) — derivation |
| 53 | Hyperopt API — fmin, hp.*, SparkTrials, parallelism math |
| 54 | Optuna API — studies, samplers, pruners, multi-objective |

## Part J — Spark from Zero — Distributed Compute

| # | Chapter |
|---|---------|
| 55 | Why distributed at all — the data-too-big-for-one-machine problem |
| 56 | MapReduce — historical context and what Spark improved |
| 57 | Spark architecture — driver, executors, cluster manager |
| 58 | RDDs, DataFrames, Datasets — the API evolution |
| 59 | Catalyst optimizer and Tungsten execution engine |
| 60 | Partitioning, narrow vs wide, shuffle internals |
| 61 | AQE (Adaptive Query Execution) and tuning |

## Part K — pyspark.ml in Depth

| # | Chapter |
|---|---------|
| 62 | The Pipeline pattern — Transformers and Estimators |
| 63 | Common transformers — what each one computes |
| 64 | Common estimators — Spark-specific quirks of each algorithm |
| 65 | CrossValidator and TrainValidationSplit — with model-count math |
| 66 | Evaluators in Spark ML |
| 67 | Pipeline persistence, custom transformers, custom estimators |

## Part L — Databricks Platform & MLflow

| # | Chapter |
|---|---------|
| 68 | Databricks workspace anatomy and the DBR ML runtime |
| 69 | Clusters, Photon, driver/worker sizing — the cost-vs-speed tradeoff |
| 70 | Unity Catalog 3-level namespace and governance basics |
| 71 | Feature Engineering in UC — offline + online + point-in-time correctness |
| 72 | MLflow as a discipline — tracking, autologging, the MlflowClient API |
| 73 | Model Registry — UC aliases, the legacy-stages migration |
| 74 | AutoML — what it actually does, when to use it, when not |

## Part M — Capstone

| # | Chapter |
|---|---------|
| 75 | End-to-end project — Lending Club default prediction on Databricks |
| 76 | Exam-day strategy and self-assessment checklist |

---

The chapters are numbered consecutively (1 through 76) and intended to be read in order — later chapters assume earlier ones. Each chapter ends with exercises; do them cold before moving on.
