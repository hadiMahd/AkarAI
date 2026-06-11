# Model Card: Monthly Average Transactions Forecaster

## Model overview
- **Selected model:** `lightgbm`
- **Task:** Forecast `Avg Transactions per Agency` at monthly frequency.
- **Modeling approach:** Supervised time-series regression using calendar, trend, lag, and rolling-window features.
- **Selection rule:** Lowest MAE on the chronological eval split.
- **Created at:** 2026-06-04T11:33:10.772475+00:00

## Dataset
- **Source file:** `LEB3443M022026-range - Number of Real Estate Transactions - augmented-1000-rows.xlsx`
- **Sheet:** `3443_augmented`
- **Dataset SHA-256:** `7da629266f117913322ac9799766eb3bd390e3fbf6f33c61bfcd96fb9d433a43`
- **Full period:** 2011-08-01 to 2094-11-01
- **Rows:** 1000
- **Target:** `Avg Transactions per Agency`

## Split strategy
Chronological split, no shuffling.

| Split | Period | Rows |
|---|---:|---:|
| Train | 2011-08-01 to 2069-11-01 | 700 |
| Test | 2069-12-01 to 2082-05-01 | 150 |
| Eval | 2082-06-01 to 2094-11-01 | 150 |

## Features
- Calendar features: year, month, quarter
- Trend feature: sequential month index
- Seasonality features: month sine/cosine
- Lag features: [1, 2, 3, 6, 12]
- Rolling windows: [3, 6, 12]
- Same-month raw columns are excluded to avoid leakage.

## Model comparison by MAE
| model    |   eval |   test |   train |
|:---------|-------:|-------:|--------:|
| lightgbm | 0.5697 | 0.6227 |  0.4975 |
| xgboost  | 0.5745 | 0.6388 |  0.365  |
| ridge    | 0.6622 | 0.6862 |  0.8364 |

## Full metrics
| model    | split   |    mae |   rmse |   mape_pct |     r2 |
|:---------|:--------|-------:|-------:|-----------:|-------:|
| lightgbm | eval    | 0.5697 | 0.6936 |     9.4534 | 0.7044 |
| xgboost  | eval    | 0.5745 | 0.7049 |     9.6256 | 0.6947 |
| ridge    | eval    | 0.6622 | 0.7989 |    11.0247 | 0.6078 |
| lightgbm | test    | 0.6227 | 0.7867 |     9.8917 | 0.6217 |
| xgboost  | test    | 0.6388 | 0.8142 |    10.1928 | 0.5948 |
| ridge    | test    | 0.6862 | 0.8632 |    10.9909 | 0.5446 |
| xgboost  | train   | 0.365  | 0.4613 |     6.419  | 0.9318 |
| lightgbm | train   | 0.4975 | 0.6572 |     9.3172 | 0.8616 |
| ridge    | train   | 0.8364 | 1.2133 |    17.8453 | 0.5283 |

## Intended use
Use for monthly forecasting of `Avg Transactions per Agency` when historical monthly observations are available and the future period is similar to the historical/synthetic training distribution.

## Limitations and risks
- The file appears to contain augmented/synthetic future rows through 2094, so real-world generalization should be validated on non-augmented historical data.
- Recursive multi-month forecasts can accumulate error.
- The model does not include macroeconomic drivers, policy changes, season shocks, or known future events.
- Same-month transaction/listing columns were intentionally excluded to avoid leakage.

## Production notes
- Store the raw file hash with every training run.
- Recompute metrics after each retrain.
- Monitor prediction drift and MAE over recent months.
- Refit only after confirming eval performance is stable on real non-synthetic data.

## Saved artifacts
- Model bundle: `lightgbm_winner_model.joblib`
- Metrics: `model_metrics.csv`
- Predictions: `model_predictions.csv`
