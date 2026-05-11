# Capstone2-Delay_Prediction_For_US_Flights_2013-2018
This is the capstone project of Viktor and Markus. The projects goal is to predict flight delays for domestic flights in the US as a use case for a complete Machine Learning Engineering setup. 

All services needed run in a Docker-based local stack. To start the local services execute this from the repository root: <br><br>
`docker compose -f docker/compose.yml up -d`

<br><br>
When the stack is running, the local endpoints are:
- `FastAPI/Uvicorn`: `http://127.0.0.1:8000`
- `Grafana`: `http://127.0.0.1:4200`
- `MLflow`: `http://127.0.0.1:5001`
- `Prefect`: `http://127.0.0.1:4200`
- `Postgres`: `http://127.0.0.1:5432`
- `Prometheus`: `http://127.0.0.1:9090`
