# docker/simulator/simulate_traffic.py
import random, time, os
import httpx, mlflow
from mlflow.types.schema import Schema
from sqlalchemy import create_engine, text

API_URL          = os.environ.get("API_URL", "http://api:8000/predict")
SLEEP_SEC        = float(os.environ.get("SLEEP_SEC", 2.0))
MLFLOW_TRACKING  = os.environ.get("MLFLOW_TRACKING_URI", "http://mlflow:5000")
DB_SOURCE_TABLE  = os.environ.get("DB_SOURCE_TABLE", "dbt_staging.flights_subset_intra_covid")
DB_URI           = "postgresql://vikmar:vikmar@postgres:5432/fastapi_db"

# -- Modell‑Auswahl: zuerst Env, sonst zentrale Config --
MODEL_NAME  = os.environ.get("MODEL_NAME") or None
MODEL_ALIAS = os.environ.get("MODEL_ALIAS") or None
if not MODEL_NAME or not MODEL_ALIAS:
    from flows.config import API_MODEL
    MODEL_NAME  = MODEL_NAME or API_MODEL["model_name"]
    MODEL_ALIAS = MODEL_ALIAS or API_MODEL["alias"]

def get_feature_columns():
    mlflow.set_tracking_uri(MLFLOW_TRACKING)
    model_uri = f"models:/{MODEL_NAME}@{MODEL_ALIAS}"
    model = mlflow.pyfunc.load_model(model_uri)
    return Schema.input_names(model.metadata.signature.inputs)

def main():
    feature_cols = get_feature_columns()
    print(f"Verwendetes Modell : {MODEL_NAME}@{MODEL_ALIAS}")
    print(f"Features           : {feature_cols}")

    engine = create_engine(DB_URI)
    cols = ", ".join(set(feature_cols) | {"flight_uid"})
    query = f"SELECT {cols} FROM {DB_SOURCE_TABLE}"
    with engine.connect() as conn:
        rows = conn.execute(text(query)).fetchall()
    samples = [dict(row._mapping) for row in rows]
    print(f"Samples geladen    : {len(samples)}")

    while True:
        sample = random.choice(samples)
        payload = {col: float(sample[col]) for col in feature_cols}
        payload["flight_uid"] = sample["flight_uid"]
        try:
            r = httpx.post(API_URL, json=payload, timeout=10)
            print(f"Status {r.status_code}, Predict: {r.json()}")
        except Exception as e:
            print(f"Fehler: {e}")
        time.sleep(SLEEP_SEC)

if __name__ == "__main__":
    main()