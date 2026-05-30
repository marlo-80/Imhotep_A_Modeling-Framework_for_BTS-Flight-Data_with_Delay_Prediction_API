#!/bin/bash
set -e

# ------------------------------------------------------------------
# Demo‑Skript: Schrittweise Daten injizieren und Drift live beobachten
# ------------------------------------------------------------------
echo "Leere Tabelle api.predictions …"
docker compose -f docker/compose.yml exec postgres psql -U vikmar -d fastapi_db \
  -c "TRUNCATE TABLE api.predictions RESTART IDENTITY;"

echo ""
echo "==============================================" 
echo "  Batch 1: Pre‑COVID (Referenz selbst)"
echo "=============================================="
docker compose -f docker/compose.yml exec -e PYTHONPATH=/app api python docker/scripts/batch_inject.py \
  2018-01-01 2020-01-01 500 dbt_staging.flights_subset_pre_covid

echo "Führe Drift‑Flow aus …"
docker compose -f docker/compose.yml exec -e PYTHONPATH=/app -e PYTHONUNBUFFERED=1 api python flows/drift_flow.py
echo "Warte 20 Sekunden (Prometheus aktualisiert alle 5 s) …"
sleep 7

echo ""
echo "=============================================="
echo "  Batch 2: COVID Frühling 2020"
echo "=============================================="
docker compose -f docker/compose.yml exec -e PYTHONPATH=/app api python docker/scripts/batch_inject.py \
  2020-04-01 2020-07-01 500

echo "Führe Drift‑Flow aus …"
docker compose -f docker/compose.yml exec -e PYTHONPATH=/app -e PYTHONUNBUFFERED=1 api python flows/drift_flow.py
echo "Warte 20 Sekunden …"
sleep 7

echo ""
echo "=============================================="
echo "  Batch 3: COVID Sommer 2020"
echo "=============================================="
docker compose -f docker/compose.yml exec -e PYTHONPATH=/app api python docker/scripts/batch_inject.py \
  2020-07-01 2020-10-01 500

echo "Führe Drift‑Flow aus …"
docker compose -f docker/compose.yml exec -e PYTHONPATH=/app -e PYTHONUNBUFFERED=1 api python flows/drift_flow.py
echo "Warte 20 Sekunden …"
sleep 7

echo ""
echo "=============================================="
echo "  Batch 4: COVID Herbst 2020"
echo "=============================================="
docker compose -f docker/compose.yml exec -e PYTHONPATH=/app api python docker/scripts/batch_inject.py \
  2020-10-01 2021-01-01 500

echo "Führe Drift‑Flow aus …"
docker compose -f docker/compose.yml exec -e PYTHONPATH=/app -e PYTHONUNBUFFERED=1 api python flows/drift_flow.py
echo "Warte 20 Sekunden …"
sleep 7

echo ""
echo "=============================================="
echo "  Batch 5: COVID Winter 2021"
echo "=============================================="
docker compose -f docker/compose.yml exec -e PYTHONPATH=/app api python docker/scripts/batch_inject.py \
  2021-01-01 2021-04-01 500

echo "Führe Drift‑Flow aus …"
docker compose -f docker/compose.yml exec -e PYTHONPATH=/app -e PYTHONUNBUFFERED=1 api python flows/drift_flow.py
echo "Warte 20 Sekunden …"
sleep 7

echo ""
echo "=============================================="
echo "  Batch 6: COVID Frühling 2021"
echo "=============================================="
docker compose -f docker/compose.yml exec -e PYTHONPATH=/app api python docker/scripts/batch_inject.py \
  2021-04-01 2021-07-01 500

echo "Führe Drift‑Flow aus …"
docker compose -f docker/compose.yml exec -e PYTHONPATH=/app -e PYTHONUNBUFFERED=1 api python flows/drift_flow.py
echo "Warte 20 Sekunden …"
sleep 7

echo ""
echo "=============================================="
echo "  Batch 7: COVID Sommer 2021"
echo "=============================================="
docker compose -f docker/compose.yml exec -e PYTHONPATH=/app api python docker/scripts/batch_inject.py \
  2021-07-01 2021-10-01 500

echo "Führe Drift‑Flow aus …"
docker compose -f docker/compose.yml exec -e PYTHONPATH=/app -e PYTHONUNBUFFERED=1 api python flows/drift_flow.py
echo "Warte 20 Sekunden …"
sleep 7

echo ""
echo "=============================================="
echo "  Batch 8: Normalisierung 2021/2022"
echo "=============================================="
docker compose -f docker/compose.yml exec -e PYTHONPATH=/app api python docker/scripts/batch_inject.py \
  2021-10-01 2022-01-01 500

echo "Führe Drift‑Flow aus …"
docker compose -f docker/compose.yml exec -e PYTHONPATH=/app -e PYTHONUNBUFFERED=1 api python flows/drift_flow.py

echo ""
echo "=============================================="
echo " Demo beendet. Beobachte den data_drift_score in Grafana."
echo "=============================================="