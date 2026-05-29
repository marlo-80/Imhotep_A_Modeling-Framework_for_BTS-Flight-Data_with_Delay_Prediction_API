# docker/scripts/batch_inject.py
import sys
import pandas as pd
import mlflow
from sqlalchemy import create_engine, text
import json

# --- Parameter -------------------------------------------------------------
if len(sys.argv) != 4:
    print("Usage: batch_inject.py <start_date> <end_date> <approx_rows>")
    sys.exit(1)

start_date = sys.argv[1]
end_date   = sys.argv[2]
approx_rows = int(sys.argv[3])

# --- Konfiguration ---------------------------------------------------------
MLFLOW_URI = "http://mlflow:5000"
DB_URI = "postgresql://vikmar:vikmar@postgres:5432/fastapi_db"
SOURCE_TABLE = "dbt_staging.flights_subset_intra_covid"

print(f"Lade exakt {approx_rows} Zeilen aus {SOURCE_TABLE} (Zeitraum {start_date} – {end_date}) ...")

# --- Modelle laden ---------------------------------------------------------
mlflow.set_tracking_uri(MLFLOW_URI)
reg = mlflow.pyfunc.load_model("models:/regressor@champion")
cls = mlflow.pyfunc.load_model("models:/classifier@champion")

# --- Daten mit ORDER BY random() + LIMIT laden -----------------------------
engine = create_engine(DB_URI)
query = f"""
    SELECT *
    FROM {SOURCE_TABLE}
    WHERE flight_date >= '{start_date}'
      AND flight_date <  '{end_date}'
    ORDER BY random()
    LIMIT {approx_rows}
"""
df = pd.read_sql(query, engine)
print(f"Geladene Zeilen: {len(df)}")

# --- Features auf Modell-Spalten reduzieren --------------------------------
feature_cols = [
    "year", "quarter", "month", "day_of_month", "day_of_week",
    "crs_dep_time", "crs_arr_time", "crs_elapsed_time",
    "distance", "distance_group",
]
uids = df["flight_uid"].copy()
features = df[feature_cols].astype(float)

# --- Batch-Predictions -----------------------------------------------------
print("Führe Batch‑Predictions durch ...")
reg_preds = reg.predict(features)
cls_preds = cls.predict(features)

# --- In Datenbank schreiben ------------------------------------------------
print("Schreibe in api.predictions ...")
with engine.connect() as conn:
    for i, row in features.iterrows():
        uid = uids[i] if i in uids.index else None
        conn.execute(
            text("""
                INSERT INTO api.predictions
                    (flight_uid, input_features, prediction_reg, prediction_class,
                     model_version_reg, model_version_class)
                VALUES (:uid, :feat, :reg, :cls, 'regressor@champion', 'classifier@champion')
            """),
            {
                "uid": uid,
                "feat": json.dumps(row.to_dict()),
                "reg": float(reg_preds[i]),
                "cls": int(cls_preds[i]),
            }
        )
    conn.commit()

print(f"{len(features)} Predictions in api.predictions geschrieben.")