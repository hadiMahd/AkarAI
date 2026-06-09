import pytest

from app.common.storage import (
    build_object_path,
    delete_object,
    download_object,
    ensure_bucket_exists,
    upload_object,
)

TEST_BUCKET = "property-media"
TEST_PATH = "__test__/smoke.txt"
TEST_DATA = b"hello storage"


class TestStorageHelpers:
    @pytest.mark.integration
    def test_upload_download_delete(self):
        ensure_bucket_exists(TEST_BUCKET)

        upload_object(TEST_BUCKET, TEST_PATH, TEST_DATA, content_type="text/plain")
        downloaded = download_object(TEST_BUCKET, TEST_PATH)
        assert downloaded == TEST_DATA

        delete_object(TEST_BUCKET, TEST_PATH)

    @pytest.mark.integration
    def test_presigned_url(self):
        from app.common.storage import presigned_get_url
        ensure_bucket_exists(TEST_BUCKET)
        upload_object(TEST_BUCKET, TEST_PATH, TEST_DATA)
        url = presigned_get_url(TEST_BUCKET, TEST_PATH, expires_seconds=60)
        assert url.startswith("http")
        delete_object(TEST_BUCKET, TEST_PATH)
