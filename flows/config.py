# flows/config.py

# Default values for prediction model
API_MODEL = {
    "model_name": "test_name",
    "alias": "champion",
}


######################################################################################################
#                                            Simple Training                                         #
######################################################################################################

DEFAULT_CONFIG = {
    "run_name": "small_rf",

    # Data Definitions (Logging only)
    "dataset_query": "SELECT * FROM dbt_staging.flights_subset",
    "dataset_name": "flights_subset_2019-2020",
    "dataset_start_date": "2019-01-01",
    "dataset_end_date": "2020-01-01",
    "dataset_sample_size": 100000,
    "dataset_random_seed": 0.42,
    "dataset_source": "dbt_staging.flights_subset",
    
    # Feature Definitions 
    "target": "arr_delay_minutes",
    "numeric_cols": [
        "year", "quarter", "month", "day_of_month", "day_of_week",
        "crs_dep_time", "crs_arr_time", "crs_elapsed_time",
        "distance", "distance_group",
    ],
    "categorical_cols": [
    ],

    # Preprocessing Definition
    "impute_num": "median",
    "impute_cat": "most_frequent",

    # Model Definitions
    "model_type": "RandomForestRegressor",
    "model_params": {"n_estimators": 10, "max_depth": 4, "random_state": 42},
    



    # Registration and Evaluation
    "register": False,
    "model_name": "flight-delay-prediction",
    "alias": "champion",               # Will only be set if promotion metric is bested 
    "promotion_metric": "rmse",        # welche Metrik
    "promotion_mode": "minimize",      # "minimize" oder "maximize"
    #delay_threshold": 15,
}


######################################################################################################
#                                         Optuna Training                                            #
######################################################################################################

# flows/config.py
OPTUNA_CONFIG = {
    # Experiment & Tuning Control
    "run_name": "rf-baseline-tuning",
    "n_trials": 30,
    "direction": "minimize",          # "minimize" für RMSE

    # Data Definition
    "dataset_query": "SELECT * FROM dbt_staging.flights_subset",
    "dataset_source": "dbt_staging.flights_subset",
    "dataset_name": "flights_subset_2019-2020",
    "dataset_start_date": "2019-01-01",
    "dataset_end_date": "2020-01-01",
    "dataset_sample_size": 100000,
    "dataset_random_seed": 0.42,

    # Feature Definition
    "target": "arr_delay",
    "numeric_cols": [
        "year", "quarter", "month", "day_of_month", "day_of_week",
        "crs_dep_time", "crs_arr_time", "crs_elapsed_time",
        "distance", "distance_group",
    ],
    "categorical_cols": [
    ],

    # Preprocessor Definitions
    "impute_num": "median",
    "impute_cat": "most_frequent",
    
    # Model Definition
    "model_type": "RandomForestRegressor",
    "param_ranges": {
        "n_estimators": {"type": "int", "low": 5, "high": 50},
        "max_depth":     {"type": "int", "low": 2, "high": 6},
    },

    # Registration and Evaluation
    "register": False,
    "model_name": "flight-delay-baseline",
    "alias": "",
    #"delay_threshold": 15,
}


######################################################################################################
#                                             Tests                                                  #
######################################################################################################

PRE_COVID = {
    "run_name": "rf_pre-covid",

    # Data Definitions (Logging only)
    "dataset_query": "SELECT * FROM dbt_staging.flights_subset_pre_covid",
    "dataset_name": "flights_subset_pre-covid",
    "dataset_start_date": "2018-01-01",
    "dataset_end_date": "2020-01-01",
    "dataset_sample_size": 100000,
    "dataset_random_seed": 0.42,
    "dataset_source": "dbt_staging.flights_subset_pre_covid",
    
    # Feature Definitions 
    "target": "arr_delay_minutes",
    "numeric_cols": [
        "year", "quarter", "month", "day_of_month", "day_of_week",
        "crs_dep_time", "crs_arr_time", "crs_elapsed_time",
        "distance", "distance_group",
    ],
    "categorical_cols": [
    ],

    # Preprocessing Definition
    "impute_num": "median",
    "impute_cat": "most_frequent",

    # Model Definitions
    "model_type": "RandomForestRegressor",
    "model_params": {"n_estimators": 1, "max_depth": 1, "random_state": 42},
    



    # Registration and Evaluation
    "register": True,
    "model_name": "test_name",
    "alias": "champion",
    "promotion_metric": "rmse",        # welche Metrik
    "promotion_mode": "minimize",      # "minimize" oder "maximize"
    #"delay_threshold": 15,
}









