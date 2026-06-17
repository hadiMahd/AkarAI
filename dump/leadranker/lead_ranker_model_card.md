# Model Card: Lead Ranker Hot vs Normal

## Model Details

- **Model name:** `lead_ranker_hot_normal`
- **Model type:** Transformer sequence classifier
- **Selected model:** `answerdotai/ModernBERT-base`
- **Selected model key:** `modernbert_base`
- **Exported model directory:** `lead_ranker_best_transformer_model`
- **Created at UTC:** `2026-06-04T20:58:43.824915+00:00`

## Intended Use

This model ranks real-estate leads as either:

- `0` = normal
- `1` = hot

It should be used after the Stage 1 gatekeeper has already decided that a message is a lead.

Recommended use: prioritize agent follow-up, routing, alerts, and CRM urgency.

## Out-of-Scope Use

- Not a spam detector.
- Not a final sales qualification system.
- Not for legal, financial, credit, or housing eligibility decisions.
- Not validated for production traffic without monitoring and review.

## Dataset Fingerprint

- **Dataset path:** `lead_ranker_hot_normal_data.csv`
- **Rows:** `1000`
- **Columns:** `['text', 'label']`
- **Label distribution:** `{'0': 500, '1': 500}`
- **Raw file SHA-256:** `df054fae9859f4a8ede1f02f66d5ba36b8147bd5b1767c8ced08154d5f8142f5`
- **Loaded content SHA-256:** `8ec03c40cc96c2c75f2014d7660a4a3a789ae468063337d64b82719fe60e79fd`
- **File size bytes:** `64088`
- **Duplicate text rows:** `0`

## Data Splits

- **Train rows:** `700`
- **Validation rows:** `150`
- **Test rows:** `150`
- **Train label distribution:** `{'0': 350, '1': 350}`
- **Validation label distribution:** `{'0': 75, '1': 75}`
- **Test label distribution:** `{'0': 75, '1': 75}`

## Training Configuration

- **Max sequence length:** `128`
- **Epochs:** `4`
- **Train batch size:** `8`
- **Eval batch size:** `16`
- **Gradient accumulation steps:** `2`
- **Learning rate:** `2e-05`
- **Weight decay:** `0.01`
- **Random state:** `42`
- **Selection metric:** `test_f1`

## Models Compared

| model_key        | hugging_face_model          |
|:-----------------|:----------------------------|
| deberta_v3_small | microsoft/deberta-v3-small  |
| modernbert_base  | answerdotai/ModernBERT-base |

## Evaluation Results

| model_key        | model_name                  | saved_model_dir                                           |   validation_accuracy |   validation_precision |   validation_recall |   validation_f1 |   test_accuracy |   test_precision |   test_recall |   test_f1 |
|:-----------------|:----------------------------|:----------------------------------------------------------|----------------------:|-----------------------:|--------------------:|----------------:|----------------:|-----------------:|--------------:|----------:|
| modernbert_base  | answerdotai/ModernBERT-base | lead_ranker_transformer_runs/modernbert_base/final_model  |                   1   |                      1 |                   1 |               1 |             1   |                1 |             1 |         1 |
| deberta_v3_small | microsoft/deberta-v3-small  | lead_ranker_transformer_runs/deberta_v3_small/final_model |                   0.5 |                      0 |                   0 |               0 |             0.5 |                0 |             0 |         0 |

## Selected Model Metrics

- **Validation F1:** 1.0000
- **Test Accuracy:** 1.0000
- **Test Precision:** 1.0000
- **Test Recall:** 1.0000
- **Test F1:** 1.0000

## Limitations

- The dataset is synthetic, so real app traffic may contain phrasing not represented here.
- The model may learn template-specific patterns.
- Hot-vs-normal ranking is subjective and should be reviewed against business outcomes.
- A hot prediction should prioritize follow-up, not guarantee deal quality.
- The model was not validated on multilingual production messages unless such messages are added to the dataset.

## Monitoring Recommendations

- Log prediction, hot probability, message length, timestamp, and downstream outcome.
- Review false hot predictions that waste agent time.
- Review false normal predictions that later became high-value leads.
- Track class distribution drift over time.
- Retrain with real reviewed leads once available.

## Retraining Recommendations

- Add real production messages with reviewed hot/normal labels.
- Add borderline cases such as `price please` vs `ready to pay deposit today`.
- Include multilingual and shorthand user messages if expected in the app.
- Keep a held-out real-world evaluation set separate from synthetic training data.

## Runtime

- **Python:** `3.12.13`
- **Platform:** `Linux-6.6.122+-x86_64-with-glibc2.35`
- **PyTorch:** `2.11.0+cu128`
- **CUDA available:** `True`
