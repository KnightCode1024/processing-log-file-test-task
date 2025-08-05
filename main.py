import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict

import tabulate


class LogProcessor:

    def __init__(self):
        self.logs = []

    def load_logs(
        self, file_paths: List[str], date_filter: Optional[str] = None
    ) -> None:
        self.logs = []

        for file_path in file_paths:
            path = Path(file_path)
            if not path.exists():
                print(
                    f"Warning: File {file_path} does not exist, skipping.",
                    file=sys.stderr,
                )
                continue

            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line:
                            continue

                        try:
                            log_entry = json.loads(line)
                            if self._should_include_log(
                                log_entry,
                                date_filter,
                            ):
                                self.logs.append(log_entry)
                        except json.JSONDecodeError as e:
                            print(
                                "Warning: Invalid JSON in"
                                + f"{file_path}:{line_num}: {e}",
                                file=sys.stderr,
                            )
                            continue

            except Exception as e:
                print(f"Error reading file {file_path}: {e}", file=sys.stderr)
                continue

    def load_logs_from_data(
        self, log_data: List[Dict], date_filter: Optional[str] = None
    ) -> None:
        self.logs = []

        for log_entry in log_data:
            if self._should_include_log(log_entry, date_filter):
                self.logs.append(log_entry)

    def _should_include_log(
        self, log_entry: Dict[str, Any], date_filter: Optional[str]
    ) -> bool:
        if not date_filter:
            return True

        try:
            timestamp = log_entry.get("@timestamp")
            if not timestamp:
                return False

            log_date = datetime.fromisoformat(
                timestamp.replace("Z", "+00:00"),
            ).date()
            filter_date = datetime.strptime(date_filter, "%Y-%m-%d").date()

            return log_date == filter_date
        except (ValueError, TypeError):
            return False

    def generate_average_report(self) -> List[List]:
        endpoint_stats = defaultdict(lambda: {"count": 0, "total_time": 0.0})

        for log in self.logs:
            url = log.get("url")
            response_time = log.get("response_time")

            if url and response_time is not None:
                endpoint_stats[url]["count"] += 1
                endpoint_stats[url]["total_time"] += response_time

        rows = []
        for url, stats in sorted(endpoint_stats.items()):
            avg_time = stats["total_time"] / stats["count"]
            rows.append([url, stats["count"], f"{avg_time:.3f}"])

        return rows


class ReportGenerator:

    def __init__(self, processor: LogProcessor):
        self.processor = processor

    def generate_report(self, report_type: str) -> Optional[str]:
        if report_type == "average":
            rows = self.processor.generate_average_report()
            if not rows:
                return "No data found for the specified criteria."

            headers = ["handler", "total", "avg_response_time"]
            return tabulate.tabulate(rows, headers=headers, tablefmt="grid")

        return None


def main():
    parser = argparse.ArgumentParser(
        description="Process log files and generate reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --file log1.log log2.log --report average
  python main.py --file log1.log --report average --date 2025-06-22
        """,
    )

    parser.add_argument(
        "--file", nargs="+", required=True, help="Log file(s) to process"
    )

    parser.add_argument(
        "--report",
        required=True,
        help="Report type to generate (e.g., average)",
    )

    parser.add_argument(
        "--date",
        help="Filter logs by date (YYYY-MM-DD format)",
    )

    args = parser.parse_args()

    if args.date:
        try:
            datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print(
                "Error: Invalid date format. Use YYYY-MM-DD",
                file=sys.stderr,
            )
            sys.exit(1)

    processor = LogProcessor()
    processor.load_logs(args.file, args.date)

    if not processor.logs:
        print("No valid log entries found.", file=sys.stderr)
        sys.exit(1)

    generator = ReportGenerator(processor)
    report = generator.generate_report(args.report)

    if report is None:
        print(
            f"Error: Unknown report type '{args.report}'",
            file=sys.stderr,
        )
        sys.exit(1)

    print(report)


if __name__ == "__main__":
    main()
