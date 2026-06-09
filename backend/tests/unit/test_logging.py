import logging


class TestLogging:
    def test_setup_logging_configures_root(self):
        from app.common.logging import setup_logging

        setup_logging()
        root = logging.getLogger()
        assert root.level in (logging.DEBUG, logging.INFO)
        assert len(root.handlers) > 0

    def test_formatter_includes_request_id(self):
        from app.common.logging import setup_logging

        setup_logging()
        root = logging.getLogger()
        formatter = root.handlers[0].formatter
        assert formatter is not None
        assert "request_id" in formatter._fmt

    def test_request_id_filter_default(self):
        from app.common.logging import RequestIDFilter

        f = RequestIDFilter()
        record = logging.LogRecord("test", logging.INFO, "", 0, "hello", (), None)
        assert f.filter(record)
        assert record.request_id == "-"
