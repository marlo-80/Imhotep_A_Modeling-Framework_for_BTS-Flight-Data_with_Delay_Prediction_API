# docker/simulator/simulate_traffic.py
import random, time, os
import httpx
import mlflow
from mlflow.types import DataType
from sqlalchemy import create_engine, text
import pandas as pd
import numpy as np

API_URL = os.environ.get("API_URL", "http://api:8000/predict")
SLEEP_SEC = float(os.environ.get("SLEEP_SEC", 2.0))
MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://mlflow:5000")
DB_URI = "postgresql://vikmar:vikmar@postgres:5432/fastapi_db"
DB_SOURCE_TABLE = os.environ.get("DB_SOURCE_TABLE", "dbt_staging.flights_subset_intra_covid")

# Modell-Auswahl: zuerst Environment, dann zentrale Config
MODEL_NAME  = os.environ.get("MODEL_NAME")
MODEL_ALIAS = os.environ.get("MODEL_ALIAS")
if not MODEL_NAME or not MODEL_ALIAS:
    from flows.config import API_MODELS
    MODEL_NAME  = MODEL_NAME or API_MODELS["regression"]["model_name"]
    MODEL_ALIAS = MODEL_ALIAS or API_MODELS["regression"]["alias"]

def enforce_schema(df: pd.DataFrame, signature) -> pd.DataFrame:
    """Konvertiert alle Spalten eines DataFrame exakt in die von der MLflow-Signatur verlangten Typen."""
    df = df.copy()
    for col in signature.inputs.inputs:
        name = col.name
        if name not in df.columns:
            continue
        dtype = col.type
        if dtype in (DataType.double, DataType.float):
            df[name] = pd.to_numeric(df[name], errors='coerce').astype('float64')
        elif dtype == DataType.string:
            df[name] = df[name].astype(str)
        elif dtype in (DataType.long, DataType.integer):
            df[name] = pd.to_numeric(df[name], errors='coerce').astype('int64')
    return df

def main():
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    model_uri = f"models:/{MODEL_NAME}@{MODEL_ALIAS}"
    model = mlflow.pyfunc.load_model(model_uri)

    # Spalten aus der Signatur des Modells auslesen
    feature_cols = [col.name for col in model.metadata.signature.inputs.inputs]
    print(f"Verwendetes Modell : {MODEL_NAME}@{MODEL_ALIAS}")
    print(f"Features           : {feature_cols}")

    engine = create_engine(DB_URI)
    # Alle benötigten Spalten + flight_uid, sowie Ground-Truth-Spalten laden
    cols = ", ".join(set(feature_cols) | {"flight_uid", "arr_delay_minutes", "arr_del15"})
    query = f"SELECT {cols} FROM {DB_SOURCE_TABLE}"
    with engine.connect() as conn:
        rows = conn.execute(text(query)).fetchall()
    samples = [dict(row._mapping) for row in rows]
    print(f"Samples geladen    : {len(samples)}")

    while True:
        sample = random.choice(samples)
        # Einzeiligen DataFrame bauen und Schema-Enforcement anwenden
        df_sample = pd.DataFrame([sample])
        df_sample = enforce_schema(df_sample, model.metadata.signature)
        # Payload aus dem DataFrame (nur die Signatur-Spalten) mit nativen Python-Typen
        raw = df_sample.iloc[0].to_dict()
        payload = {}
        sig_map = {col.name: col.type for col in model.metadata.signature.inputs.inputs}
        for col, val in raw.items():
            dtype = sig_map.get(col, None)
            if dtype in (DataType.double, DataType.float):
                payload[col] = float(val)
            elif dtype in (DataType.long, DataType.integer):
                payload[col] = int(val)
            elif dtype == DataType.string:
                payload[col] = str(val)
            else:
                payload[col] = val
        payload["flight_uid"] = sample.get("flight_uid")
        # Ground‑Truth mitschicken (die API speichert sie in der ground_truth‑Spalte)
        payload["ground_truth"] = {
            "arr_delay_minutes": float(sample.get("arr_delay_minutes", 0.0)),
            "arr_del15": int(sample.get("arr_del15", 0))
        }
        try:
            r = httpx.post(API_URL, json=payload, timeout=10)
            print(f"Status {r.status_code}, Predict: {r.json()}")
        except Exception as e:
            print(f"Fehler: {e}")
        time.sleep(SLEEP_SEC)

if __name__ == "__main__":
    main()