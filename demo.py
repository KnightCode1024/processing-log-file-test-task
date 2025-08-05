from main import LogProcessor, ReportGenerator


def main():
    print("=== Log File Processing Demo ===\n")

    sample_logs = [
        {
            "@timestamp": "2025-06-22T13:57:32+00:00",
            "status": 200,
            "url": "/api/homeworks/...",
            "request_method": "GET",
            "response_time": 0.1,
            "http_user_agent": "Mozilla/5.0...",
        },
        {
            "@timestamp": "2025-06-22T13:57:33+00:00",
            "status": 200,
            "url": "/api/homeworks/...",
            "request_method": "GET",
            "response_time": 0.2,
            "http_user_agent": "Mozilla/5.0...",
        },
        {
            "@timestamp": "2025-06-22T13:57:34+00:00",
            "status": 200,
            "url": "/api/context/...",
            "request_method": "GET",
            "response_time": 0.05,
            "http_user_agent": "Mozilla/5.0...",
        },
        {
            "@timestamp": "2025-06-23T13:57:35+00:00",
            "status": 200,
            "url": "/api/users/...",
            "request_method": "GET",
            "response_time": 0.15,
            "http_user_agent": "Mozilla/5.0...",
        },
    ]

    processor = LogProcessor()
    processor.logs = sample_logs

    print("Sample log data loaded:")
    print(f"Total log entries: {len(processor.logs)}")
    print(
        "Unique endpoints:"
        + f"{len(set(log['url'] for log in processor.logs))}\n",
    )

    generator = ReportGenerator(processor)
    report = generator.generate_report("average")

    print("Average Response Time Report:")
    print("=" * 50)
    print(report)
    print()

    print("Date Filtering Demo:")
    print("=" * 50)

    processor_filtered = LogProcessor()
    processor_filtered.load_logs_from_data(
        sample_logs,
        date_filter="2025-06-22",
    )

    print(f"Logs for 2025-06-22: {len(processor_filtered.logs)} entries")

    if processor_filtered.logs:
        generator_filtered = ReportGenerator(processor_filtered)
        report_filtered = generator_filtered.generate_report("average")
        print(report_filtered)
    else:
        print("No logs found for the specified date.")

    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    main()
