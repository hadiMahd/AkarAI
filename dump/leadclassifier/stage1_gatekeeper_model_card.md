# Model Card: Stage 1 Gatekeeper

## Model Details

- **Model name:** `stage1_gatekeeper`
- **Model type:** Binary text classifier
- **Selected model:** `linear_svc`
- **Artifact:** `stage1_gatekeeper_best_model.joblib`
- **Created at UTC:** `2026-06-04T18:20:58.791048+00:00`
- **Framework:** scikit-learn

## Intended Use

This model classifies inbound text messages for a real-estate lead gatekeeper.

- `0` = spam / non-lead
- `1` = real-estate lead

Recommended use: Stage 1 routing. Messages predicted as leads should continue to downstream lead qualification or information extraction.

## Out-of-Scope Use

- Not a final sales qualification model.
- Not a legal, financial, or housing eligibility decision system.
- Not validated for unseen languages, new markets, or channels without additional evaluation.

## Dataset Fingerprint

- **Dataset path:** `stage1_gatekeeper_data.csv`
- **Rows:** `800`
- **Columns:** `['text', 'label']`
- **Label distribution:** `{'0': 400, '1': 400}`
- **Raw file SHA-256:** `e5f3b5dee61f94bcefa0441df41b36641b83693cb80a1bf64824ae791b366093`
- **Loaded content SHA-256:** `e5f3b5dee61f94bcefa0441df41b36641b83693cb80a1bf64824ae791b366093`
- **File size bytes:** `41474`
- **Duplicate text/label rows:** `0`

## Features and Preprocessing

Input column: `text`

Pipeline:

1. `SimpleImputer(strategy="constant", fill_value="")`
2. `FunctionTransformer(np.ravel)`
3. `TfidfVectorizer(lowercase=True, strip_accents="unicode", ngram_range=(1, 2), max_features=10000, min_df=2, max_df=0.95)`
4. Classifier: `linear_svc`

## Training Setup

- **Test size:** `0.2`
- **Split type:** Stratified train/test split
- **Random state:** `42`
- **Cross-validation:** StratifiedKFold, `5` folds
- **Model selection metric:** test F1 score

## Evaluation Summary

### Selected Model Test Metrics

- **Accuracy:** 0.9938
- **Precision:** 0.9877
- **Recall:** 1.0000
- **F1:** 0.9938

### Selected Model Cross-Validation Metrics

- **CV Accuracy Mean:** 0.9891
- **CV Precision Mean:** 0.9790
- **CV Recall Mean:** 1.0000
- **CV F1 Mean:** 0.9893

## All Model Test Results

| model               |   test_accuracy |   test_precision |   test_recall |   test_f1 |
|:--------------------|----------------:|-----------------:|--------------:|----------:|
| linear_svc          |         0.99375 |         0.987654 |             1 |  0.993789 |
| logistic_regression |         0.9875  |         0.97561  |             1 |  0.987654 |

## All Model Cross-Validation Results

| model               |   cv_accuracy_mean |   cv_precision_mean |   cv_recall_mean |   cv_f1_mean |
|:--------------------|-------------------:|--------------------:|-----------------:|-------------:|
| linear_svc          |           0.989062 |            0.979005 |          1       |     0.989288 |
| logistic_regression |           0.9875   |            0.981858 |          0.99375 |     0.987691 |

## Limitations

- The dataset is synthetic, so production language may differ from training examples.
- The model may over-rely on phrases seen in generated templates.
- False positives may send non-leads to downstream processing.
- False negatives may incorrectly block real leads.
- Performance should be revalidated once real app traffic is available.

## Monitoring Recommendations

- Log predictions and reviewed outcomes.
- Track false negatives for real leads.
- Track false positives for spam/non-leads.
- Review low-confidence or disputed predictions.
- Retrain when real production examples diverge from synthetic data.

## Retraining Recommendations

- Add reviewed real inbound messages after removing sensitive personal data.
- Add hard negatives that mention apartments but are not actionable leads.
- Add multilingual, shorthand, and transliterated examples if users send them.
- Re-run the training notebook and compare dataset hashes and evaluation metrics.

## Runtime

- **Python:** `3.12.13`
- **Platform:** `Linux-6.6.122+-x86_64-with-glibc2.35`
- **pandas:** `2.2.2`
- **numpy:** `2.0.2`
- **scikit-learn:** `1.6.1`
