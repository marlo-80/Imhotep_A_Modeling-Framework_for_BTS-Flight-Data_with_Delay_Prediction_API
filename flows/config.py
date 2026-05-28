# flows/config.py

# Default values for prediction model
API_MODELS = {
    "regression": {
        "model_name": "regressor",
        "alias": "champion",
    },
    "classification": {
        "model_name": "classifier",
        "alias": "champion",
    },
}

######################################################################################################
#                                              Default CONFIG                                        #
######################################################################################################
# This is only a fallback with default values. But it needs to be defined

# Minimale Fallback‑Konfiguration – wird nur geladen, falls kein anderer Name übergeben wird.
DEFAULT_CONFIG = {
    "run_name": "optuna-fallback",
    "n_trials": 5,
    "tuning_direction": "minimize",
    "task": "regression",
    "target": "arr_delay_minutes",
    "numeric_cols": [],
    "categorical_cols": [],
    "model_type": "RandomForestRegressor",
    "param_ranges": {},
    "register": False,
    "alias": "",

    # Optuna‑Defaults (nur relevant, wenn der Flow ohne explizite Config gestartet wird)
    "n_trials": 5,
    "tuning_direction": "minimize",
    "param_ranges": {},
    "fixed_model_params": {},
}


######################################################################################################
#                                            Simple Regression                                       #
######################################################################################################

REG = {
    "run_name": "rf_reg",

    # Set task to regression
    "task": "regression",

    # Preprocessing (unverändert)
    "impute_num": "median",
    "impute_cat": "most_frequent", 

    # Model Definitions (Regressor statt Classifier)
    "model_type": "RandomForestRegressor",
    "model_params": {"n_estimators": 20, "max_depth": 5, "random_state": 42},

    # Feature Definitions (unverändert)
    "target": "arr_delay_minutes",          # ← stetiges Target
    "numeric_cols": [
        "year", "quarter", "month", "day_of_month", "day_of_week",
        "crs_dep_time", "crs_arr_time", "crs_elapsed_time",
        "distance", "distance_group",
    ],
    "categorical_cols": [],    
    
    # Dataset parameter, logging only (unverändert)
    "dataset_query": "SELECT * FROM dbt_staging.flights_subset_pre_covid",
    "dataset_name": "flights_subset_pre-covid",
    "dataset_start_date": "2018-01-01",
    "dataset_end_date": "2020-01-01",
    "dataset_sample_size": 100000,
    "dataset_random_seed": 0.42,
    "dataset_source": "dbt_staging.flights_subset_pre_covid",

    # Registration and Evaluation
    "register": False,
    "model_name": "regressor",
    "alias": "champion",
    "promotion_metric": "rmse",           # ← klassisches Regressionsmaß
    "promotion_mode": "minimize",         # ← kleiner ist besser
}


######################################################################################################
#                                            Simple Classification                                   #
######################################################################################################

CLASS = {
    "run_name": "rf_class",

    # Set task to classification for classification or regression for regression
    "task": "classification",

    # Preprocessing
    "impute_num": "median",
    "impute_cat": "most_frequent", 

    # Model Definitions
    "model_type": "RandomForestClassifier",
    "model_params": {"n_estimators": 200, "max_depth": 10, "class_weight": "balanced", "random_state": 42},        

    # Feature Definitions
    "target": "arr_del15",            # ← binäres Target
    "numeric_cols": [
        "year", "quarter", "month", "day_of_month", "day_of_week",
        "crs_dep_time", "crs_arr_time", "crs_elapsed_time",
        "distance", "distance_group",
    ],
    "categorical_cols": [],    
    
    # Datset parameter, logging only
    "dataset_query": "SELECT * FROM dbt_staging.flights_subset_pre_covid",
    "dataset_name": "flights_subset_pre-covid",
    "dataset_start_date": "2018-01-01",
    "dataset_end_date": "2020-01-01",
    "dataset_sample_size": 100000,
    "dataset_random_seed": 0.42,
    "dataset_source": "dbt_staging.flights_subset_pre_covid",

    # Registration and Evaluation
    "register": False,
    "model_name": "classifier",
    "alias": "champion",
    "promotion_metric": "f1",         # ← für Klassifikation
    "promotion_mode": "maximize",     # ← F1 soll möglichst groß sein
}



######################################################################################################
#                                         Optuna Regression                                          #
######################################################################################################

REG_OPTUNA = {
    # Experiment & Tuning Control
    "run_name": "optuna_rf_reg",

    # Set task to regression
    "task": "regression",

    # Optuna Parameters
    "n_trials": 2,
    "tuning_metric": "rmse",
    "tuning_direction": "minimize",          # RMSE soll minimiert werden

    # Preprocessing Definition (unverändert)
    "impute_num": "median",
    "impute_cat": "most_frequent",

    # Model Definition (Regressor statt Classifier)
    "model_type": "RandomForestRegressor",
    "param_ranges": {
        "n_estimators": {"type": "int", "low": 50, "high": 300},
        "max_depth":     {"type": "int", "low": 5, "high": 20},
    },
    "fixed_model_params": {"random_state": 42},   # class_weight entfällt

    # Feature Definitions (stetiges Target)
    "target": "arr_delay_minutes",
    "numeric_cols": [
        "year", "quarter", "month", "day_of_month", "day_of_week",
        "crs_dep_time", "crs_arr_time", "crs_elapsed_time",
        "distance", "distance_group",
    ],
    "categorical_cols": [],

    # Data Definitions (Logging only, unverändert)
    "dataset_query": "SELECT * FROM dbt_staging.flights_subset_pre_covid",
    "dataset_name": "flights_subset_pre-covid",
    "dataset_start_date": "2018-01-01",
    "dataset_end_date": "2020-01-01",
    "dataset_sample_size": 100000,
    "dataset_random_seed": 0.42,
    "dataset_source": "dbt_staging.flights_subset_pre_covid",

    # Registration and Evaluation (Regressionsmetrik)
    "register": False,
    "model_name": "regressor",
    "alias": "champion",
    "promotion_metric": "rmse",
    "promotion_mode": "minimize",
}

######################################################################################################
#                                         Optuna Classification                                      #
######################################################################################################

CLASS_OPTUNA = {
    # Experiment & Tuning Control
    "run_name": "optuna_rf_class",

    # Set task to classification for classification or regression for regression
    "task": "classification",

    # Optuna Parameters
    "n_trials": 2,
    "tuning_metric": "f1",
    "tuning_direction": "maximize",              # F1 soll maximiert werden

    # Preprocessing Definition
    "impute_num": "median",
    "impute_cat": "most_frequent",

    # Model Definition
    "model_type": "RandomForestClassifier",
    "param_ranges": {
        "n_estimators": {"type": "int", "low": 50, "high": 300},
        "max_depth":     {"type": "int", "low": 5, "high": 15},
    },
    "fixed_model_params": {"class_weight": "balanced", "random_state": 42},

    # Feature Definitions
    "target": "arr_del15",
    "numeric_cols": [
        "year", "quarter", "month", "day_of_month", "day_of_week",
        "crs_dep_time", "crs_arr_time", "crs_elapsed_time",
        "distance", "distance_group",
    ],
    "categorical_cols": [],

    # Data Definitions (Logging only)
    "dataset_query": "SELECT * FROM dbt_staging.flights_subset_pre_covid",
    "dataset_name": "flights_subset_pre-covid",
    "dataset_start_date": "2018-01-01",
    "dataset_end_date": "2020-01-01",
    "dataset_sample_size": 100000,
    "dataset_random_seed": 0.42,
    "dataset_source": "dbt_staging.flights_subset_pre_covid",

    # Registration and Evaluation
    "register": False,
    "model_name": "classifier",
    "alias": "champion",
    "promotion_metric": "f1",
    "promotion_mode": "maximize",
}





