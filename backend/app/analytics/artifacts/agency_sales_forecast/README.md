# Agency Sales Forecast Artifacts

Place the next-month agency sales forecast assets for backend inference here.

Expected contents can include:

- model weights or serialized model files
- model card
- preprocessing artifacts
- feature schema
- label mapping
- calibration metadata
- example input/output files

This folder is for the agency dashboard metric:

- `forecasted_possible_sales_next_month`

Once the artifacts are added, the inference code should be implemented in `backend/app/analytics/` and should load from this folder rather than from ad hoc paths.
