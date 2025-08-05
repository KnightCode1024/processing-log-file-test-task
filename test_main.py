import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch
from main import LogProcessor, ReportGenerator


class TestLogProcessor:

    def setup_method(self):
        self.processor = LogProcessor()

    def test_load_logs_valid_file(self):
        log_data = [
            {
                "@timestamp": "2025-06-22T13:57:32+00:00",
                "status": 200,
                "url": "/api/test",
                "request_method": "GET",
                "response_time": 0.1,
                "http_user_agent": "test-agent",
            },
            {
                "@timestamp": "2025-06-22T13:57:33+00:00",
                "status": 200,
                "url": "/api/test2",
                "request_method": "POST",
                "response_time": 0.2,
                "http_user_agent": "test-agent",
            },
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            for log in log_data:
                f.write(json.dumps(log) + "\n")
            temp_file = f.name

        try:
            self.processor.load_logs([temp_file])
            assert len(self.processor.logs) == 2
            assert self.processor.logs[0]["url"] == "/api/test"
            assert self.processor.logs[1]["url"] == "/api/test2"
        finally:
            Path(temp_file).unlink()

    def test_load_logs_multiple_files(self):
        log_data1 = [
            {
                "@timestamp": "2025-06-22T13:57:32+00:00",
                "status": 200,
                "url": "/api/test1",
                "request_method": "GET",
                "response_time": 0.1,
                "http_user_agent": "test-agent",
            }
        ]

        log_data2 = [
            {
                "@timestamp": "2025-06-22T13:57:33+00:00",
                "status": 200,
                "url": "/api/test2",
                "request_method": "GET",
                "response_time": 0.2,
                "http_user_agent": "test-agent",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f1:
            for log in log_data1:
                f1.write(json.dumps(log) + "\n")
            temp_file1 = f1.name

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f2:
            for log in log_data2:
                f2.write(json.dumps(log) + "\n")
            temp_file2 = f2.name

        try:
            self.processor.load_logs([temp_file1, temp_file2])
            assert len(self.processor.logs) == 2
            urls = [log["url"] for log in self.processor.logs]
            assert "/api/test1" in urls
            assert "/api/test2" in urls
        finally:
            Path(temp_file1).unlink()
            Path(temp_file2).unlink()

    def test_load_logs_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write('{"valid": "json"}\n')
            f.write("invalid json line\n")
            f.write('{"another": "valid"}\n')
            temp_file = f.name

        try:
            with patch("sys.stderr") as mock_stderr:
                self.processor.load_logs([temp_file])
                assert len(self.processor.logs) == 2
                assert mock_stderr.write.called
        finally:
            Path(temp_file).unlink()

    def test_load_logs_nonexistent_file(self):
        with patch("sys.stderr") as mock_stderr:
            self.processor.load_logs(["nonexistent.log"])
            assert len(self.processor.logs) == 0
            assert mock_stderr.write.called

    def test_date_filtering(self):
        log_data = [
            {
                "@timestamp": "2025-06-22T13:57:32+00:00",
                "status": 200,
                "url": "/api/test",
                "request_method": "GET",
                "response_time": 0.1,
                "http_user_agent": "test-agent",
            },
            {
                "@timestamp": "2025-06-23T13:57:32+00:00",
                "status": 200,
                "url": "/api/test2",
                "request_method": "GET",
                "response_time": 0.2,
                "http_user_agent": "test-agent",
            },
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            for log in log_data:
                f.write(json.dumps(log) + "\n")
            temp_file = f.name

        try:
            self.processor.load_logs([temp_file], date_filter="2025-06-22")
            assert len(self.processor.logs) == 1
            assert self.processor.logs[0]["url"] == "/api/test"

            self.processor.load_logs([temp_file], date_filter="2025-06-23")
            assert len(self.processor.logs) == 1
            assert self.processor.logs[0]["url"] == "/api/test2"

            self.processor.load_logs([temp_file])
            assert len(self.processor.logs) == 2
        finally:
            Path(temp_file).unlink()

    def test_date_filtering_invalid_timestamp(self):
        log_data = [
            {
                "@timestamp": "invalid-timestamp",
                "status": 200,
                "url": "/api/test",
                "request_method": "GET",
                "response_time": 0.1,
                "http_user_agent": "test-agent",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            for log in log_data:
                f.write(json.dumps(log) + "\n")
            temp_file = f.name

        try:
            self.processor.load_logs([temp_file], date_filter="2025-06-22")
            assert len(self.processor.logs) == 0
        finally:
            Path(temp_file).unlink()

    def test_generate_average_report(self):
        self.processor.logs = [
            {"url": "/api/test1", "response_time": 0.1},
            {"url": "/api/test1", "response_time": 0.3},
            {"url": "/api/test2", "response_time": 0.2},
            {"url": "/api/test2", "response_time": 0.4},
        ]

        rows = self.processor.generate_average_report()
        assert len(rows) == 2

        assert rows[0][0] == "/api/test1"
        assert rows[1][0] == "/api/test2"

        assert rows[0][1] == 2
        assert rows[1][1] == 2

        assert rows[0][2] == "0.200"
        assert rows[1][2] == "0.300"

    def test_generate_average_report_empty_logs(self):
        self.processor.logs = []
        rows = self.processor.generate_average_report()
        assert len(rows) == 0

    def test_generate_average_report_missing_fields(self):
        self.processor.logs = [
            {"url": "/api/test1", "response_time": 0.1},
            {"url": "/api/test2"},
            {"response_time": 0.2},
            {"url": "/api/test3", "response_time": 0.3},
        ]

        rows = self.processor.generate_average_report()
        assert len(rows) == 2
        assert rows[0][0] == "/api/test1"
        assert rows[1][0] == "/api/test3"


class TestReportGenerator:

    def setup_method(self):
        self.processor = LogProcessor()
        self.generator = ReportGenerator(self.processor)

    def test_generate_average_report(self):
        self.processor.logs = [
            {"url": "/api/test1", "response_time": 0.1},
            {"url": "/api/test1", "response_time": 0.3},
        ]

        report = self.generator.generate_report("average")
        assert report is not None
        assert "handler" in report
        assert "total" in report
        assert "avg_response_time" in report
        assert "/api/test1" in report

    def test_generate_average_report_no_data(self):
        self.processor.logs = []
        report = self.generator.generate_report("average")
        assert report == "No data found for the specified criteria."

    def test_generate_unknown_report(self):
        report = self.generator.generate_report("unknown")
        assert report is None


class TestIntegration:

    def test_full_workflow(self):
        log_data = [
            {
                "@timestamp": "2025-06-22T13:57:32+00:00",
                "status": 200,
                "url": "/api/homeworks/...",
                "request_method": "GET",
                "response_time": 0.1,
                "http_user_agent": "test-agent",
            },
            {
                "@timestamp": "2025-06-22T13:57:33+00:00",
                "status": 200,
                "url": "/api/homeworks/...",
                "request_method": "GET",
                "response_time": 0.2,
                "http_user_agent": "test-agent",
            },
            {
                "@timestamp": "2025-06-22T13:57:34+00:00",
                "status": 200,
                "url": "/api/context/...",
                "request_method": "GET",
                "response_time": 0.05,
                "http_user_agent": "test-agent",
            },
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            for log in log_data:
                f.write(json.dumps(log) + "\n")
            temp_file = f.name

        try:
            processor = LogProcessor()
            processor.load_logs([temp_file])

            generator = ReportGenerator(processor)
            report = generator.generate_report("average")

            assert report is not None
            assert "/api/homeworks/..." in report
            assert "/api/context/..." in report
            assert "2" in report
            assert "1" in report
            assert "0.15" in report
            assert "0.05" in report
        finally:
            Path(temp_file).unlink()


if __name__ == "__main__":
    pytest.main([__file__])
