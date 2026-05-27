# flows/train_flow.py
import pandas as pd
from prefect import flow, task
from src.data import load_subset_table
from src.preprocessing import build_preprocessor
from src.train import train_and_log
from sklearn.ensemble import RandomForestRegressor

from flows.config import DEFAULT_CONFIG
from src.data import load_subset_table, convert_integers_to_float

import requests
from mlflow.tracking import MlflowClient

import httpx
from mlflow.tracking import MlflowClient


@task
def load_and_clean_data(query: str, numeric_cols: list[str]) -> pd.DataFrame:
    df = load_subset_table(query)
    df = convert_integers_to_float(df, numeric_cols)
    return df

@task
def split_data(df: pd.DataFrame, target: str) -> tuple:
    """Chronologischer Split (Tabelle ist bereits nach flight_date sortiert)."""
    n = len(df)
    train_end = int(n * 0.7)
    val_end   = int(n * 0.85)
    train = df.iloc[:train_end]
    val   = df.iloc[train_end:val_end]
    test  = df.iloc[val_end:]
    return train, val, test

@task
def build_model(model_type: str, model_params: dict):
    if model_type == "RandomForestRegressor":
        return RandomForestRegressor(**model_params)
    raise ValueError(f"Unbekannter model_type: {model_type}")

@task
def run_training(train_df, val_df, config: dict):
    # Preprocessor und Modell erstellen
    preprocessor = build_preprocessor(
        numeric_cols=config["numeric_cols"],
        categorical_cols=config["categorical_cols"],
        impute_num=config.get("impute_num", "median"),
        impute_cat=config.get("impute_cat", "most_frequent"),
    )
    model = build_model.fn(config["model_type"], config["model_params"])

    pipeline, rmse = train_and_log(train_df, val_df, preprocessor, model, config)
    return pipeline, rmse

@task
def promote_if_better(config: dict, new_rmse: float):
    """
    Vergleicht die RMSE des neuen Modells mit dem aktuellen Champion (falls vorhanden)
    und setzt den Alias nur, wenn das neue Modell besser ist.
    Triggert danach den API‑Webhook zum Neuladen.
    """
    model_name = config.get("model_name")
    alias = config.get("alias")
    if not alias or not config.get("register", False):
        return  # Kein Alias gewünscht → nichts tun

    client = MlflowClient()
    # Aktuellen Champion suchen
    try:
        current_mv = client.get_model_version_by_alias(model_name, alias)
        # RMSE des aktuellen Champions aus dessen Run holen
        current_run = client.get_run(current_mv.run_id)
        current_rmse = current_run.data.metrics.get("rmse", None)
    except Exception:
        current_rmse = None

    # Entscheiden, ob das neue Modell den Champion ersetzen soll
    promote = False
    if current_rmse is None:
        promote = True          # Noch kein Champion
    else:
        # Besser = kleinerer RMSE
        if new_rmse < current_rmse:
            promote = True

    if promote:
        # Alias auf neue Version setzen (die zuletzt registrierte)
        new_mv = client.get_latest_versions(model_name, stages=["None"])[0]
        client.set_registered_model_alias(model_name, alias, new_mv.version)
        print(f"Neuer Champion: {model_name} v{new_mv.version} (RMSE {new_rmse:.2f}), Alter Champion: (RMSE {current_rmse:.2f})")
        # API‑Reload triggern
        api_url = "http://api:8000/admin/reload-model"   # intern im Docker‑Netz
        try:
            requests.post(api_url, timeout=5)
        except Exception as e:
            print(f"Webhook failed: {e}")
    else:
        print(f"Kein Wechsel – Champion RMSE {current_rmse:.2f}, Challenger RMSE {new_rmse:.2f}")


@flow(name="flight-delay-training")
def training_pipeline(config: dict = DEFAULT_CONFIG):
    df = load_and_clean_data(config["dataset_query"], config["numeric_cols"])
    train, val, test = split_data(df, config["target"])
    pipeline, rmse = run_training(train, val, config)   # run_training muss den rmse zurückgeben!
    if config.get("alias"):                              # nur wenn Alias gesetzt
        promote_if_better(config, rmse)
    return pipeline







if __name__ == "__main__":
    import sys
    from flows.config import DEFAULT_CONFIG

    config_name = sys.argv[1] if len(sys.argv) > 1 else "DEFAULT_CONFIG"
    import flows.config as cfg_module
    config = getattr(cfg_module, config_name, DEFAULT_CONFIG)
    training_pipeline(config)        