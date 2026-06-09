import pytest

from app.common.storage import (
    build_object_path,
    check_minio_bucket_exists,
    check_minio_connectivity,
    ensure_bucket_exists,
)

from app.common.config import settings


class TestStorageFoundation:
    @pytest.mark.integration
    def test_minio_connectivity(self):
        assert check_minio_connectivity() is True

    @pytest.mark.integration
    def test_rag_bucket_exists(self):
        assert check_minio_bucket_exists(settings.minio_bucket_rag) is True

    @pytest.mark.integration
    def test_media_bucket_exists(self):
        assert check_minio_bucket_exists(settings.minio_bucket_media) is True

    def test_build_object_path(self):
        assert build_object_path("rag-vault", "test.pdf") == "rag-vault/test.pdf"
        assert build_object_path("/rag-vault/", "test.pdf") == "rag-vault/test.pdf"
        assert build_object_path("", "file.txt") == "file.txt"
