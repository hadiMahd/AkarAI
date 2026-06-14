# Quickstart & Validation: RAG Retrieval and Reranking

## Prerequisites

- Docker Compose services are running.
- Vault has Azure OpenAI embedding secrets and OpenRouter reranking secrets configured.
- At least one agency has processed policy documents from Phase 8.
- Evaluation fixtures live at `backend/tests/fixtures/rag_eval/policy_retrieval_baseline.jsonl`.

## Validation Scenarios

### 1. Agency Policy Q&A Happy Path

1. Sign in to the agency app as an Agency Admin.
2. Open `Policy Documents`.
3. Confirm at least one PDF status is `processed`.
4. Open the policy Q&A screen.
5. Ask a question that is answered in the uploaded policy PDF.
6. Verify the page shows an answer, citations, ranked evidence/debug fields, and no cross-tenant sources.

Expected result: The answer is grounded in the agency's processed policy documents and includes document/page citations.

### 2. Support Employee Scope

1. Sign in as a Support Employee for the same agency.
2. Ask a policy question covered by processed documents.
3. Ask a question requesting an admin-only action.

Expected result: Policy retrieval works for allowed policy questions, and admin-only requests are refused or limited.

### 3. Tenant Isolation

1. Create or use two agencies with separate processed policy documents.
2. Ask as Agency A for content that exists only in Agency B's document.

Expected result: Agency A receives insufficient-evidence fallback and no Agency B citations or evidence.

### 4. Reranker Fallback

1. Temporarily run with reranking unavailable or disabled.
2. Ask a policy question.

Expected result: Retrieval still returns a bounded response or fallback, and debug fields record that reranking was not used.

### 5. Evaluation Baseline

1. Run the retrieval evaluation command:
   ```bash
   docker compose exec backend python scripts/ci/run_rag_eval.py --tenant-id <fixture-tenant-uuid>
   ```
2. The script loads 25 policy retrieval examples from `backend/tests/fixtures/rag_eval/policy_retrieval_baseline.jsonl`.
3. Each example runs through the full retrieval pipeline (embedding → vector search → reranking → assembly).
4. Results are scored against `expected_behavior` ("answer" → status is `answered`/`fallback`; "refuse" → status is `insufficient_evidence`) and `expected_source_labels`.
5. A summary with pass rate, latency metrics (min/max/avg/p50/p95), and violations is printed and persisted as a `RagEvaluationRun`.
6. Review failed examples via the persisted summary JSON in the evaluation run record.

Expected result: The run records comparable baseline quality results, highlights weak retrieval/grounding cases, and enforces the latency threshold (default 5000ms). Exit code 0 on all-pass; non-zero on failures or latency violations.

### 6. Replace During Retrieval

1. Start a retrieval request against a processed policy document.
2. Replace the same policy document while retrieval is in progress.
3. Repeat the same policy query after replacement finishes.

Expected result: The response remains bounded and tenant-safe during replacement, and later queries use the latest processed document version without cross-version corruption.

### 7. Retrieval Latency Validation

1. Run a small batch of policy queries through the evaluation command:
   ```bash
   docker compose exec backend python scripts/ci/run_rag_eval.py --tenant-id <uuid> --latency-max-ms 5000
   ```
2. The script records per-query timing and prints aggregate latency: min, max, avg, p50, p95.
3. Latency is enforced: any query exceeding `--latency-max-ms` causes a non-zero exit.

Expected result: 95% of retrieval requests complete within 5 seconds under local development data volume. Violations are reported and fail the run.

## Evaluation Dataset Format

The baseline dataset at `backend/tests/fixtures/rag_eval/policy_retrieval_baseline.jsonl` is newline-delimited JSON with one example per line:

```json
{"id":"example-001","query":"What is the policy on visitor parking?","tenant_fixture":"agency-a","expected_behavior":"answer","expected_source_labels":["policy-page-1"],"notes":"Baseline placeholder example."}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique example identifier |
| `query` | string | The policy question to ask |
| `tenant_fixture` | string | Logical tenant name for the fixture |
| `expected_behavior` | string | `"answer"` — retrieval should return grounded answer; `"refuse"` — retrieval should return `insufficient_evidence` |
| `expected_source_labels` | string[] | Source labels that should appear in citations |
| `notes` | string | Optional context about the example |

Scoring logic:
- **behavior_ok**: For `"answer"` examples, status must be `"answered"` or `"fallback"`. For `"refuse"` examples, status must be `"insufficient_evidence"`.
- **sources_ok**: All `expected_source_labels` must appear in the returned citations.
- **passed**: Both `behavior_ok` and `sources_ok` must be true.

## Suggested Test Commands

```bash
docker compose exec backend pytest tests/unit/test_rag_retrieval.py tests/unit/test_openrouter_reranker.py
docker compose exec backend pytest tests/integration/test_rag_retrieval_api.py tests/rbac/test_rag_retrieval_tenant_isolation.py
docker compose exec agency-app npm test -- --run
docker compose exec agency-app npm run build
docker compose exec backend python scripts/ci/run_rag_eval.py --tenant-id <fixture-tenant-uuid>
```
