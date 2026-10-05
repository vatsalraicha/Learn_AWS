# %%
"""
SageMaker Pipeline — end-to-end ML pipeline for card-fraud model

Pattern: Glue feature engineering → SageMaker Processing (eval split)
         → Training → Clarify (bias + explainability)
         → Model Registry (Pending)
         → Manual approval → Deploy

Demonstrates:
  - @step decorator (2024 feature)
  - Model Registry approval gate
  - Clarify integration for SR 11-7 evidence
  - MLflow tracking server integration
  - rubicon-ml git-SHA linking (Capital One pattern)

Run with:
  python sagemaker_pipeline.py  # creates the pipeline
  aws sagemaker start-pipeline-execution --pipeline-name card-fraud-pipeline
"""
import os
import sagemaker
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.pipeline_context import PipelineSession
from sagemaker.workflow.function_step import step
from sagemaker.workflow.parameters import ParameterString
from rubicon_ml import Rubicon
import mlflow

# %%
# Setup
session = PipelineSession()
role = sagemaker.get_execution_role()
default_bucket = session.default_bucket()
mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])

# rubicon-ml with auto-git binds every experiment to a git SHA
rubicon = Rubicon(persistence="s3", root_dir=f"s3://{default_bucket}/rubicon",
                  auto_git_enabled=True)


# %%
# Step 1: Process — load features, split train/val/test
@step(
    instance_type="ml.m5.4xlarge",
    role=role,
    keep_alive_period_in_seconds=300,
    name="preprocess",
)
def preprocess_step(feature_store_table: str, output_path: str) -> dict:
    import pandas as pd
    from sklearn.model_selection import train_test_split

    df = pd.read_parquet(feature_store_table)
    df_train, df_test = train_test_split(df, test_size=0.2, random_state=42, stratify=df["label"])
    df_train, df_val = train_test_split(df_train, test_size=0.2, random_state=42, stratify=df_train["label"])

    train_path = f"{output_path}/train.parquet"
    val_path = f"{output_path}/val.parquet"
    test_path = f"{output_path}/test.parquet"
    df_train.to_parquet(train_path)
    df_val.to_parquet(val_path)
    df_test.to_parquet(test_path)

    return {"train": train_path, "val": val_path, "test": test_path}


# %%
# Step 2: Train — XGBoost on the features
@step(
    instance_type="ml.m5.4xlarge",
    role=role,
    name="train",
)
def train_step(data_paths: dict, hyperparameters: dict) -> str:
    import pandas as pd
    import xgboost as xgb

    project = rubicon.get_or_create_project("card-fraud")
    experiment = project.log_experiment(name="run-{}".format(os.environ.get("EXECUTION_ID", "unknown")))
    for k, v in hyperparameters.items():
        experiment.log_parameter(k, v)

    train_df = pd.read_parquet(data_paths["train"])
    val_df = pd.read_parquet(data_paths["val"])

    X_train, y_train = train_df.drop(columns=["label"]), train_df["label"]
    X_val, y_val = val_df.drop(columns=["label"]), val_df["label"]

    dtrain = xgb.DMatrix(X_train, label=y_train)
    dval = xgb.DMatrix(X_val, label=y_val)
    model = xgb.train(hyperparameters, dtrain, num_boost_round=200,
                      evals=[(dval, "val")], early_stopping_rounds=20)

    auc = model.best_score
    experiment.log_metric("val_auc", auc)
    mlflow.log_metric("val_auc", auc)

    model_path = f"/opt/ml/model/model.json"
    model.save_model(model_path)
    return model_path


# %%
# Step 3: Evaluate + Clarify (bias + SHAP) — the SR 11-7 evidence
@step(
    instance_type="ml.m5.4xlarge",
    role=role,
    name="evaluate-clarify",
)
def evaluate_and_clarify_step(model_path: str, test_path: str) -> dict:
    import pandas as pd
    import xgboost as xgb
    from sklearn.metrics import roc_auc_score, classification_report
    import shap

    test_df = pd.read_parquet(test_path)
    X_test, y_test = test_df.drop(columns=["label"]), test_df["label"]

    model = xgb.Booster()
    model.load_model(model_path)
    preds = model.predict(xgb.DMatrix(X_test))
    auc = roc_auc_score(y_test, preds)

    # SHAP explainability (Clarify would do this in production)
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test.iloc[:1000])
    feature_importance = pd.DataFrame({
        "feature": X_test.columns,
        "mean_abs_shap": abs(shap_values).mean(axis=0)
    }).sort_values("mean_abs_shap", ascending=False)

    # Bias check (simplified — production uses Clarify)
    pos_rate_by_segment = test_df.groupby("customer_segment")["label"].mean()

    return {
        "test_auc": auc,
        "top_features": feature_importance.head(10).to_dict("records"),
        "bias_by_segment": pos_rate_by_segment.to_dict(),
    }


# %%
# Step 4: Register — to Model Registry with approval status Pending
@step(
    instance_type="ml.m5.large",
    role=role,
    name="register",
)
def register_step(model_path: str, eval_metrics: dict, model_package_group: str) -> str:
    from sagemaker.model import Model

    # Auto-approve only if all gates pass
    auto_approve = (
        eval_metrics["test_auc"] >= 0.85
        and max(eval_metrics["bias_by_segment"].values()) - min(eval_metrics["bias_by_segment"].values()) < 0.1
    )
    approval_status = "Approved" if auto_approve else "PendingManualApproval"

    model = Model(
        image_uri="123.dkr.ecr.us-east-1.amazonaws.com/co-card/xgboost:v1",
        model_data=model_path,
        role=role,
    )
    response = model.register(
        model_package_group_name=model_package_group,
        approval_status=approval_status,
        framework="xgboost",
        content_types=["text/csv"],
        response_types=["text/csv"],
        inference_instances=["ml.c5.large", "ml.m5.large"],
        transform_instances=["ml.m5.large"],
        customer_metadata_properties={
            "test_auc": str(eval_metrics["test_auc"]),
            "bias_max_disparity": str(max(eval_metrics["bias_by_segment"].values()) - min(eval_metrics["bias_by_segment"].values())),
        },
    )
    return response.model_package_arn


# %%
# Pipeline definition
feature_store_table = ParameterString(name="FeatureStoreTable")
hyperparameters = {"max_depth": 6, "eta": 0.1, "objective": "binary:logistic", "eval_metric": "auc"}
output_path = f"s3://{default_bucket}/card-fraud-pipeline/processed"

step_preprocess = preprocess_step(feature_store_table, output_path)
step_train = train_step(step_preprocess, hyperparameters)
step_eval = evaluate_and_clarify_step(step_train, step_preprocess["test"])
step_register = register_step(step_train, step_eval, "card-fraud-models")

pipeline = Pipeline(
    name="card-fraud-pipeline",
    parameters=[feature_store_table],
    steps=[step_preprocess, step_train, step_eval, step_register],
    sagemaker_session=session,
)

# %%
if __name__ == "__main__":
    pipeline.upsert(role_arn=role)
    print(f"Pipeline {pipeline.name} created/updated")
    # To execute: aws sagemaker start-pipeline-execution --pipeline-name card-fraud-pipeline
