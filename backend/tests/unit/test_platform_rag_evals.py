from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.admin.service import PlatformAdminService


def _service() -> PlatformAdminService:
    return PlatformAdminService(SimpleNamespace())


class TestPlatformRagEvalSerialization:
    def test_serialize_eval_run_normalizes_summary(self):
        run = SimpleNamespace(
            id=uuid4(),
            run_label="ragas-blocking-20260618-080834",
            created_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            total_examples=20,
            passed_examples=20,
            failed_examples=0,
            summary={
                "mode": "blocking",
                "judge_failures": 0,
                "threshold_failures": [],
                "metrics": {
                    "faithfulness": 0.88,
                    "context_precision": 0.97,
                    "context_recall": 1.0,
                    "answer_relevancy": 0.86,
                    "hit_at_1": 1.0,
                    "hit_at_5": 1.0,
                    "tenant_leakage_count": 0,
                },
                "latency_ms": {"p95": 3666.7},
            },
        )

        payload = _service()._serialize_eval_run(run)

        assert payload.mode == "blocking"
        assert payload.faithfulness == 0.88
        assert payload.hit_at_5 == 1.0
        assert payload.tenant_leakage_count == 0
        assert payload.p95_latency_ms == 3666.7
        assert payload.passed is True
        assert payload.run_classification == "full_suite"

    def test_serialize_eval_run_marks_test_and_ad_hoc_rows(self):
        test_run = SimpleNamespace(
            id=uuid4(),
            run_label="ragas-test-run-1234",
            created_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            total_examples=2,
            passed_examples=2,
            failed_examples=0,
            summary={"mode": "blocking", "judge_failures": 0, "threshold_failures": [], "metrics": {}, "latency_ms": {}},
        )
        ad_hoc_run = SimpleNamespace(
            id=uuid4(),
            run_label="manual-spot-check",
            created_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            total_examples=5,
            passed_examples=5,
            failed_examples=0,
            summary={"mode": "manual", "judge_failures": 0, "threshold_failures": [], "metrics": {}, "latency_ms": {}},
        )

        test_payload = _service()._serialize_eval_run(test_run)
        ad_hoc_payload = _service()._serialize_eval_run(ad_hoc_run)

        assert test_payload.run_classification == "test"
        assert ad_hoc_payload.run_classification == "ad_hoc"

    def test_serialize_eval_example_normalizes_summary(self):
        example = SimpleNamespace(
            id="ex-1",
            query="How do I request PTO?",
            tenant_fixture="tenant_a",
            expected_behavior="answer",
            passed=False,
            summary={
                "latency_ms": 2100.4,
                "failure_reasons": ["context_precision"],
                "leaked_sources": [],
                "answer": {"status": "answered"},
                "metrics": {
                    "faithfulness": 0.72,
                    "context_precision": 0.42,
                    "context_recall": 1.0,
                    "answer_relevancy": 0.66,
                    "hit_at_1": False,
                    "hit_at_5": True,
                    "expected_source_match": False,
                },
            },
        )

        payload = _service()._serialize_eval_example(example)

        assert payload.example_id == "ex-1"
        assert payload.answer_status == "answered"
        assert payload.context_precision == 0.42
        assert payload.hit_at_1 is False
        assert payload.hit_at_5 is True
        assert payload.failure_reasons == ["context_precision"]
