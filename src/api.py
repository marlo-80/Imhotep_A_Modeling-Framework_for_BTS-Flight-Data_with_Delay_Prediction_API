import pandas as pd
import os

from fastapi import FastAPI, HTTPException, Response, Request
from pydantic import BaseModel, Field
from typing import List

from contextlib import asynccontextmanager
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

import mlflow
from mlflow.tracking import MlflowClient

import json

from sqlalchemy import create_engine, text



MODEL_NAME = os.environ.get("MODEL_NAME", "flight-delay-baseline")
MODEL_ALIAS = os.environ.get("MODEL_ALIAS", "champion")
model_uri = f"models:/{MODEL_NAME}@{MODEL_ALIAS}"

mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://mlflow:5000"))

DB_URI = os.environ.get("DB_URI", "postgresql://vikmar:vikmar@postgres:5432/fastapi_db")
engine = create_engine(DB_URI)

@asynccontextmanager
async def lifespan(app: FastAPI):
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://mlflow:5000"))
    model_uri = f"models:/{MODEL_NAME}@{MODEL_ALIAS}"
    try:
        app.state.model_pipeline = mlflow.pyfunc.load_model(model_uri)
        mv = MlflowClient().get_model_version_by_alias(MODEL_NAME, MODEL_ALIAS)
        app.state.model_version = f"{MODEL_NAME}_v{mv.version}@{MODEL_ALIAS}"
        print(f"Modell geladen: {app.state.model_version}")
    except Exception as e:
        print(f"WARNUNG: Modell nicht geladen – {e}")
        app.state.model_pipeline = None   # API bleibt trotzdem erreichbar
    yield
    del app.state.model_pipeline


app = FastAPI(
    title="Flight Delay Prediction API",
    description="API for Predicting Flight Delays",
    version="1.0",
    lifespan=lifespan
)
Instrumentator().instrument(app).expose(app)

# Define the expected incoming JSON structure using Pydantic
#class Flight(BaseModel):
#    # Categorical target encoded features
#    Origin: str = Field(..., examples=["JFK"])
#    Dest: str = Field(..., examples=["LAX"])
#    OriginAirportID: int = Field(..., examples=[12478])
#    DestAirportID: int = Field(..., examples=[12892])
#    Airline: str = Field(..., examples=["AA"])
#    Operating_Airline: str = Field(..., examples=["AA"])
#    Flight_Number_Marketing_Airline: int = Field(..., examples=[101])
#    Tail_Number: str = Field(..., examples=["N789AA"])
#    
#    # Numeric features
#    Year: int = Field(..., examples=[2026])
#    Month: int = Field(..., examples=[5])
#    DayofMonth: int = Field(..., examples=[13])
#   DayOfWeek: int = Field(..., examples=[3])
#    CRSDeptHrs: int = Field(..., examples=[14])
#    CRSDepMins: int = Field(..., examples=[30])
#    CRSArrHrs: int = Field(..., examples=[17])
#    CRSArrMins: int = Field(..., examples=[45])
#    Distance: float = Field(..., examples=[2475.0])

class PredictionOutput(BaseModel):
    prediction: float

@app.post("/predict", response_model=PredictionOutput)
async def predict(request: Request):                    # kein Pydantic-Modell mehr
    if app.state.model_pipeline is None:
        raise HTTPException(status_code=503, detail="Model pipeline is not loaded.")
    try:
        input_data = await request.json()               # Roh-JSON als dict
        flight_uid = input_data.pop("flight_uid", None)

        df = pd.DataFrame([input_data])
        prediction = app.state.model_pipeline.predict(df)[0]

        # DB-Logging (wie gehabt)
        log_to_db = input_data.copy()
        log_to_db["flight_uid"] = flight_uid
        with engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO api.predictions (flight_uid, input_features, prediction, model_version)
                    VALUES (:flight_uid, :features, :pred, :version)
                """),
                {
                    "flight_uid": flight_uid,
                    "features": json.dumps(log_to_db),
                    "pred": float(prediction),
                    "version": app.state.model_version,
                }
            )
            conn.commit()

        return PredictionOutput(prediction=float(prediction))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")
 

# src/api.py – ergänze nach den anderen Endpunkten
@app.post("/admin/reload-model")
async def reload_model():
    """Lädt das Modell für MODEL_NAME@MODEL_ALIAS neu aus MLflow."""
    model_uri = f"models:/{MODEL_NAME}@{MODEL_ALIAS}"
    try:
        app.state.model_pipeline = mlflow.pyfunc.load_model(model_uri)
        client = mlflow.tracking.MlflowClient()
        mv = client.get_model_version_by_alias(MODEL_NAME, MODEL_ALIAS)
        app.state.model_version = f"{MODEL_NAME}_v{mv.version}@{MODEL_ALIAS}"
        return {"status": "reloaded", "version": app.state.model_version}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reload failed: {e}")    



@app.get("/health")
def health_check():
    if app.state.model_pipeline is None:
        return {"status": "no model loaded", "model_loaded": False}
    return {"status": "healthy", "model_loaded": True}
