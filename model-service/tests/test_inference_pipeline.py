"""Model service inference pipeline tests for spam and Hot/Normal classification."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


class TestSpamClassifier:
    def test_empty_message_is_spam(self):
        from app.predictors import classify_spam
        result = classify_spam("")
        assert result["status"] == "completed"
        assert result["label"] == "spam"
        assert result["score"] == 1.0
        assert result["details"]["reason"] == "empty_message"

    def test_whitespace_only_message_is_spam(self):
        from app.predictors import classify_spam
        result = classify_spam("   \n  \t  ")
        assert result["label"] == "spam"
        assert result["details"]["reason"] == "empty_message"

    def test_fail_open_when_model_unavailable(self):
        from app.predictors import classify_spam
        with patch("app.predictors._load_spam_pipeline", return_value=None):
            result = classify_spam("I want to buy this property")
            assert result["status"] == "completed"
            assert result["label"] == "not_spam"
            assert result["details"]["reason"] == "model_unavailable_fail_open"

    def test_linear_svc_pipeline_uses_decision_function(self):
        from app.predictors import classify_spam

        class DecisionOnlyPipeline:
            classes_ = [0, 1]

            def decision_function(self, texts):
                assert len(texts) == 1
                return [2.0]

            def predict(self, texts):
                assert len(texts) == 1
                return [1]

        pipeline = DecisionOnlyPipeline()

        with patch("app.predictors._load_spam_pipeline", return_value=pipeline):
            result = classify_spam("Need to buy a real apartment this week")

        assert result["status"] == "completed"
        assert result["label"] == "not_spam"
        assert result["details"]["score_source"] == "decision_function"
        assert result["details"]["lead_probability"] > 0.5

    def test_predict_proba_pipeline_preserves_probability_path(self):
        from app.predictors import classify_spam

        pipeline = MagicMock()
        pipeline.classes_ = [0, 1]
        pipeline.predict_proba.return_value = [[0.2, 0.8]]

        with patch("app.predictors._load_spam_pipeline", return_value=pipeline):
            result = classify_spam("Need to buy a real apartment this week")

        assert result["status"] == "completed"
        assert result["label"] == "not_spam"
        assert result["details"]["lead_probability"] == pytest.approx(0.8)

    def test_loader_unwraps_model_from_artifact_dict(self):
        from app.predictors import _load_spam_pipeline

        pipeline = MagicMock()
        artifact = {"model": pipeline}

        with patch("app.predictors.os.path.exists", return_value=True):
            with patch("joblib.load", return_value=artifact):
                with patch("app.predictors._spam_pipeline", None), patch("app.predictors._spam_unavailable", False):
                    loaded = _load_spam_pipeline()

        assert loaded is pipeline


class TestLevelClassifier:
    def test_fail_open_when_model_unavailable(self):
        from app.predictors import classify_level
        with patch("app.predictors._load_level_transformer", return_value=(None, None)):
            result = classify_level("Interested in the 3BR apartment")
            assert result["status"] == "completed"
            assert result["level"] == "normal"
            assert result["details"]["reason"] == "model_unavailable_fail_open"


class TestClassifyLeadOrchestration:
    @pytest.mark.asyncio
    async def test_non_spam_gets_level_result(self):
        from app.service import classify_lead

        lead_id = uuid4()
        tenant_id = uuid4()

        with patch("app.service._send_callback", new=AsyncMock()):
            with patch("app.service.classify_spam", return_value={
                "status": "completed",
                "label": "not_spam",
                "score": 0.1,
                "details": None,
            }):
                with patch("app.service.classify_level", return_value={
                    "status": "completed",
                    "level": "hot",
                    "score": 0.85,
                    "details": None,
                }):
                    result = await classify_lead(
                        lead_id=lead_id,
                        tenant_id=tenant_id,
                        message="I need this property urgently",
                        name="Buyer",
                    )
                    assert result.spam_result.label == "not_spam"
                    assert result.level_result is not None
                    assert result.level_result.label == "hot"

    @pytest.mark.asyncio
    async def test_spam_skips_level_result(self):
        from app.service import classify_lead

        lead_id = uuid4()
        tenant_id = uuid4()

        with patch("app.service._send_callback", new=AsyncMock()):
            with patch("app.service.classify_spam", return_value={
                "status": "completed",
                "label": "spam",
                "score": 0.95,
                "details": None,
            }):
                result = await classify_lead(
                    lead_id=lead_id,
                    tenant_id=tenant_id,
                    message="Buy cheap pills now!!!",
                )
                assert result.spam_result.label == "spam"
                assert result.level_result is None


class TestSchemas:
    def test_classify_request_accepts_empty_message(self):
        from app.schemas import ClassifyRequest
        req = ClassifyRequest(
            lead_id=uuid4(),
            tenant_id=uuid4(),
            message="",
        )
        assert req.message == ""

    def test_classify_response_structure(self):
        from app.schemas import ClassifyResponse, StageResult
        resp = ClassifyResponse(
            lead_id=uuid4(),
            tenant_id=uuid4(),
            spam_result=StageResult(stage="spam", status="completed", label="not_spam"),
            level_result=StageResult(stage="level", status="completed", label="hot"),
        )
        assert resp.spam_result.stage == "spam"
        assert resp.level_result.stage == "level"

    def test_callback_payload_structure(self):
        from app.schemas import CallbackPayload
        payload = CallbackPayload(
            lead_id=uuid4(),
            tenant_id=uuid4(),
            stage="spam",
            status="completed",
            label="not_spam",
            score=0.2,
            retry_count=1,
        )
        assert payload.stage == "spam"
        assert payload.retry_count == 1
