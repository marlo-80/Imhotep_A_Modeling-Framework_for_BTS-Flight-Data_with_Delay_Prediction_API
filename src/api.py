# src/api.py
import pandas as pd
import os
import json
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator
import mlflow
from mlflow.tracking import MlflowClient
from sqlalchemy import create_engine, text

from flows.config import API_MODELS

# --- Umgebungsvariablen ---------------------------------------------------
MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://mlflow:5000")
DB_URI = os.environ.get("DB_URI", "postgresql://vikmar:vikmar@postgres:5432/fastapi_db")
engine = create_engine(DB_URI)


# --- Lifespan: Modelle beim Start laden ------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lädt Regressor und Classifier aus der MLflow‑Registry."""
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = MlflowClient()

    for task, cfg in API_MODELS.items():
        model_name = cfg["model_name"]
        alias = cfg["alias"]
        model_uri = f"models:/{model_name}@{alias}"
        try:
            pipeline = mlflow.pyfunc.load_model(model_uri)
            mv = client.get_model_version_by_alias(model_name, alias)
            version_str = f"{model_name}_v{mv.version}@{alias}"
            setattr(app.state, f"{task}_pipeline", pipeline)
            setattr(app.state, f"{task}_version", version_str)
            print(f"Modell '{task}' geladen: {version_str}")
        except Exception as e:
            print(f"WARNUNG: Modell '{task}' nicht geladen – {e}")
            setattr(app.state, f"{task}_pipeline", None)
            setattr(app.state, f"{task}_version", "not_loaded")

    yield

    # Aufräumen
    for task in API_MODELS:
        delattr(app.state, f"{task}_pipeline")


# --- FastAPI‑App -----------------------------------------------------------
app = FastAPI(
    title="Flight Delay Prediction API",
    description="Liefert Regressions- und Klassifikationsvorhersage",
    version="2.0",
    lifespan=lifespan,
)
Instrumentator().instrument(app).expose(app)


class PredictionOutput(BaseModel):
    regression_prediction: float
    classification_prediction: int
    classification_proba: float | None = None


# --- Endpunkte -------------------------------------------------------------
@app.post("/predict", response_model=PredictionOutput)
async def predict(request: Request):
    if app.state.regression_pipeline is None or app.state.classification_pipeline is None:
        raise HTTPException(status_code=503, detail="Model pipelines not loaded.")

    try:
        input_data = await request.json()
        flight_uid = input_data.pop("flight_uid", None)
        df = pd.DataFrame([input_data])

        # Regression
        reg_pred = app.state.regression_pipeline.predict(df)[0]

        # Klassifikation
        class_pred = app.state.classification_pipeline.predict(df)[0]
        try:
            class_proba = app.state.classification_pipeline.predict_proba(df)[0, 1]
        except Exception:
            class_proba = None

        # DB-Logging
        log_to_db = input_data.copy()
        log_to_db["flight_uid"] = flight_uid
        with engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO api.predictions
                        (flight_uid, input_features, prediction_reg, prediction_class,
                         model_version_reg, model_version_class)
                    VALUES (:flight_uid, :features, :pred_reg, :pred_class,
                            :version_reg, :version_class)
                """),
                {
                    "flight_uid": flight_uid,
                    "features": json.dumps(log_to_db),
                    "pred_reg": float(reg_pred),
                    "pred_class": int(class_pred),
                    "version_reg": app.state.regression_version,
                    "version_class": app.state.classification_version,
                }
            )
            conn.commit()

        return PredictionOutput(
            regression_prediction=float(reg_pred),
            classification_prediction=int(class_pred),
            classification_proba=class_proba,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")


@app.post("/admin/reload-model")
async def reload_model():
    """Lädt beide Modelle neu aus der Registry."""
    client = MlflowClient()
    for task, cfg in API_MODELS.items():
        model_uri = f"models:/{cfg['model_name']}@{cfg['alias']}"
        try:
            pipeline = mlflow.pyfunc.load_model(model_uri)
            mv = client.get_model_version_by_alias(cfg["model_name"], cfg["alias"])
            version_str = f"{cfg['model_name']}_v{mv.version}@{cfg['alias']}"
            setattr(app.state, f"{task}_pipeline", pipeline)
            setattr(app.state, f"{task}_version", version_str)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Reload failed for {task}: {e}")
    return {"status": "reloaded"}


@app.get("/health")
def health_check():
    return {
        "regression_loaded": app.state.regression_pipeline is not None,
        "classification_loaded": app.state.classification_pipeline is not None,
    }