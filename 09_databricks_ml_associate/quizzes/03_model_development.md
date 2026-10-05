# Quiz 03 — Model Development (Domain 3, 31%)

> ~45 questions covering algorithm selection, estimators/transformers, Hyperopt, cross-validation, grid search math, evaluation metrics, bias/variance, class imbalance.
>
> Take cold. Budget ~85 minutes (45 × 1m 52s).

---

## Recall

1. The Hyperopt function that minimizes an objective: `____`.
2. To do Bayesian search in Hyperopt: `algo=____`.
3. To do random search in Hyperopt: `algo=____`.
4. The Hyperopt `Trials` subclass that parallelizes across a Spark cluster: `____`.
5. The Hyperopt return type from an objective is a dict with keys `loss` and `____`.
6. The Spark ML class for k-fold cross-validation: `____`.
7. The Spark ML class for single hold-out validation: `____`.
8. The Spark ML class that builds a hyperparameter grid: `____`.
9. The default `numFolds` for `CrossValidator` is ____.
10. The `BinaryClassificationEvaluator`'s default metric: `____`.
11. The `MulticlassClassificationEvaluator`'s default metric: `____`.
12. The `RegressionEvaluator`'s default metric: `____`.
13. To weight classes in Spark ML's `LogisticRegression`: pass `____Col="weight"`.
14. The `hp.*` distribution for a float on log scale: `hp.____`.
15. The `hp.*` distribution for picking from a list of options: `hp.____`.
16. `pyspark.mllib` (RDD-based) is in `____` mode since Spark 3.0.

## Apply

17. Grid: `numTrees ∈ {50, 100}, maxDepth ∈ {5, 10, 15}, minInstancesPerNode ∈ {1, 5}`. 4-fold CV. How many model fits during CV?
18. Same grid, but using `TrainValidationSplit`. How many fits?
19. Convert this Hyperopt search to Optuna:
    ```python
    space = {
        'lr': hp.loguniform('lr', math.log(1e-5), math.log(1e-1)),
        'depth': hp.quniform('depth', 3, 15, 1),
    }
    ```
20. Your objective in Hyperopt returns `{'loss': 0.92, 'status': STATUS_OK}` where 0.92 is AUC. Hyperopt picks the trial with `loss=0.65`. Is this the best AUC?
21. You want to maximize ROC AUC in Optuna without negation. What's the `create_study` argument?
22. A model with 95% accuracy on 5% fraud rate data — which two metrics should you report instead?
23. You're tuning a Spark ML `GBTClassifier`. Should you use `SparkTrials` or `Trials()`?
24. You're tuning a single-node sklearn model. Should you use `SparkTrials` or `Trials()`?
25. You want grid search over `regParam ∈ {0.01, 0.1}, elasticNetParam ∈ {0.0, 0.5, 1.0}`. Which Spark ML class do you use?
26. Same as Q25, but include 5-fold CV. How many model fits during CV?
27. A regression problem on house prices. You've log-transformed the target. After predicting, what must you do before reporting RMSE in dollars?
28. Class imbalance: 1% positive class. List four mitigation techniques.
29. Which of the four mitigations from Q28 is the Databricks-preferred native technique?
30. Pick the right algorithm: "Predict whether a credit card transaction is fraudulent given 50 numeric features, want best accuracy at the cost of training time."
31. Pick the right algorithm: "Cluster 1M users into 8 segments based on their feature vectors."
32. Pick the right algorithm: "Recommend products to users from a 100M-row user-item interaction table."
33. Write the Hyperopt objective function for tuning sklearn's `RandomForestClassifier` to maximize ROC AUC.
34. `hp.choice('opt', ['adam', 'sgd', 'rmsprop'])` — `best['opt']` returns `1`. What optimizer did you choose?

## Diagnose

35. Train AUC = 0.97, validation AUC = 0.68. Diagnose and suggest two fixes.
36. Train RMSE = 12.3, validation RMSE = 12.5. Diagnose.
37. CV's best model averages AUC=0.85 across folds. The refit best model evaluated on a held-out test set gives AUC=0.62. Diagnose.
38. You set `algo=tpe.suggest, max_evals=100` and see only ~30 trials before Hyperopt stops. Diagnose.
39. `CrossValidator` with `parallelism=8` is *slower* than `parallelism=1` on the same grid. Diagnose.
40. A linear model's coefficients are unexpectedly all zero (or near zero). Diagnose.

## Defend

41. Argue why ROC AUC is more reliable than accuracy for picking the best binary classifier on imbalanced data.
42. Defend the use of `CrossValidator` over `TrainValidationSplit` on a 5,000-row training set.
43. Argue against using a neural network for tabular 50-feature classification, in favor of GBT.
44. Defend the choice of MAE over RMSE for regression on house prices in a market with rare luxury outliers.
45. A teammate says "Hyperopt is deprecated, we should use Optuna." Argue why you should still learn Hyperopt for the exam.

---

## Answers

1. `fmin`.
2. `tpe.suggest`.
3. `rand.suggest`.
4. `SparkTrials`.
5. `status` (typically `STATUS_OK`).
6. `CrossValidator`.
7. `TrainValidationSplit`.
8. `ParamGridBuilder`.
9. **3.**
10. `areaUnderROC`.
11. `f1`.
12. `rmse`.
13. `weightCol="weight"`.
14. `hp.loguniform`.
15. `hp.choice`.
16. **Frozen** (maintenance only since Spark 2.0; explicitly frozen in 3.0).
17. `2 × 3 × 2 = 12` grid points × `4` folds = **48 CV fits** (plus 1 refit = 49 total).
18. `2 × 3 × 2 = 12` fits during TVS (plus 1 refit = 13 total).
19. ```python
    def objective(trial):
        lr = trial.suggest_float('lr', 1e-5, 1e-1, log=True)
        depth = trial.suggest_int('depth', 3, 15)
        ...
    ```
20. **No.** `fmin` minimizes loss. `loss=0.65` is smaller than `loss=0.92`, so it picked 0.65 = lower AUC. To get the best AUC, return `-AUC` from the objective so smaller loss = larger AUC.
21. `direction="maximize"`.
22. **F1** and **PR AUC** (or **ROC AUC**). Accuracy is meaningless on heavy imbalance.
23. **`Trials()`** (sequential). Spark ML's GBT already uses the cluster; SparkTrials would double-parallelize and thrash.
24. **`SparkTrials(parallelism=K)`**. Each trial is single-node; the cluster's workers each take one trial.
25. `ParamGridBuilder` + `CrossValidator` (or `TrainValidationSplit`). Hyperopt does not have native grid search.
26. `2 × 3 = 6` grid points × `5` folds = **30 CV fits** (plus 1 refit = 31 total).
27. Exponentiate predictions back to the original scale using `np.expm1(y_pred_log)`, then compute RMSE against the original-scale targets. Reporting log-space RMSE is in log units, not dollars.
28. (a) `weightCol` (cost-sensitive), (b) random oversampling minority, (c) random undersampling majority, (d) SMOTE (synthetic minority oversampling), (e) threshold tuning. (Any four.)
29. **`weightCol`** (cost-sensitive learning) — native to Spark ML estimators (LR, RF, GBT, NaiveBayes all accept it). Doesn't require resampling, doesn't lose data, doesn't generate synthetic samples.
30. **GBT** (`GBTClassifier`) — tabular + accuracy-focused. XGBoost would be an excellent non-Spark-ML alternative.
31. **k-means** (`KMeans` with `k=8`).
32. **ALS** (`pyspark.ml.recommendation.ALS`).
33. ```python
    def objective(params):
        params['n_estimators'] = int(params['n_estimators'])
        params['max_depth'] = int(params['max_depth'])
        rf = RandomForestClassifier(**params, random_state=42)
        scores = cross_val_score(rf, X_train, y_train, cv=5, scoring='roc_auc')
        return {'loss': -scores.mean(), 'status': STATUS_OK}
    ```
34. `hp.choice` returns the **index**, not the value. Index 1 = `'sgd'`. Use `space_eval(space, best)` to get the actual value.
35. **Overfitting** (low bias, high variance). Fixes: (a) reduce model complexity (lower `maxDepth`, fewer trees, more regularization via `regParam`), (b) get more training data, (c) feature selection to remove noise, (d) cross-validation to detect this earlier.
36. **Just right** — training and val metrics are close and both are at the same level. The model generalizes well. No bias-variance issue.
37. The CV's validation folds may not be representative of the test set distribution. Or the held-out test set has different data quality / time period / distribution. Investigate: (a) is test from a different time window? (b) is the train/CV/test split stratified? (c) data drift since training?
38. `SparkTrials` propagates errors when too many trials fail. Or `max_evals` was reached. Or the experiment was timed out. Check trial states in MLflow.
39. Each model fit is large enough to use the whole cluster. With `parallelism=8`, 8 fits compete for the same executors, each running slower. The total wall-clock time is worse than sequential. Use `parallelism=1` for compute-heavy fits.
40. Heavy regularization (high `regParam`, especially with `elasticNetParam=1.0` = Lasso). Lasso shrinks coefficients to exact zero. Reduce regularization or use ElasticNet with lower `elasticNetParam`.
41. Accuracy on 99% imbalanced data is dominated by predicting the majority class — you can hit 99% accuracy with no learning. ROC AUC measures ranking quality across all thresholds and is more sensitive to actual model performance on the minority class. Plus, ROC AUC is threshold-independent — the right metric for comparing models when downstream threshold tuning is separate.
42. 5,000 rows is small. A single hold-out (e.g., 1,000 val rows) has high variance — depending on which 1,000 you pick, the validation metric swings 5%+. 5-fold CV averages over 5 different hold-outs of 1,000 rows each, giving a much more stable signal of true performance for HPO.
43. (a) NNs need significant data to outperform GBT; 50 features + tabular doesn't have enough nonlinear interaction structure to justify the architecture. (b) GBT has lower tuning burden — RandomForest defaults often perform well, XGBoost has small grid sweet spots. (c) GBT outputs feature importances natively. (d) GBT is interpretable via SHAP. (e) Training time and operational cost are orders of magnitude smaller. (f) Empirically, GBT wins most tabular benchmarks vs NN.
44. MAE is robust to outliers — it weighs each error equally. RMSE squares errors, so the luxury outliers dominate the RMSE metric and may steer the model toward fitting those few outliers at the expense of the bulk of the data. MAE optimizes for the median absolute error, which is what most homeowners care about.
45. The March 1, 2025 exam guide explicitly lists "Use Hyperopt's `fmin` operation" as a Section 3 objective. Exam content lags platform deprecations by 6-18 months. Until the guide is revised, Hyperopt is in scope and questions will use Hyperopt syntax. Knowing both Hyperopt and Optuna is a one-evening investment.
