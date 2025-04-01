#!/usr/bin/env python3
"""
AWS X-Ray Prometheus Exporter - Main Entry Point
"""
import argparse
import logging
from http.server import HTTPServer

from collector import XRayMetricsCollector
from handlers import create_handler

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('xray-exporter')

def main():
    """
    Entrypoint cho script với các tùy chọn tối ưu
    """
    parser = argparse.ArgumentParser(description='X-Ray Prometheus Exporter')
    parser.add_argument('--port', type=int, help='Port to listen on', default=9092)
    parser.add_argument('--region', type=str, help='AWS Region', default=None)
    parser.add_argument('--profile', type=str, help='AWS Profile', default=None)
    parser.add_argument('--time-window', type=int, help='Time window in minutes', default=1)
    parser.add_argument('--data-dir', type=str, help='Directory to store state data', default=None)
    parser.add_argument('--log-level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                      help='Log level', default='INFO')
    
    # Thêm tùy chọn xử lý trace
    parser.add_argument('--max-traces', type=int, help='Maximum number of traces to process per run', default=None)
    parser.add_argument('--parallel-workers', type=int, help='Number of parallel workers for trace processing', default=20)
    parser.add_argument('--batch-size', type=int, help='Batch size for API calls', default=5)
    parser.add_argument('--retry-attempts', type=int, help='Number of retry attempts for API calls', default=3)
    parser.add_argument('--force-full-collection', action='store_true', help='Ignore processed trace IDs for this run')
    
    # Tùy chọn mới cho xử lý trace trùng lặp
    parser.add_argument('--max-trace-ids', type=int, help='Maximum number of trace IDs to store', default=1000000)
    parser.add_argument('--retention-days', type=int, help='Number of days to retain trace IDs', default=30)
    parser.add_argument('--clean-trace-ids', action='store_true', help='Clean up old processed trace IDs')
    parser.add_argument('--cleanup-age-hours', type=int, help='Maximum age in hours for trace IDs when cleaning up', default=24)

    args = parser.parse_args()

    # Thiết lập log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Khởi tạo collector với các tùy chọn mở rộng
    collector = XRayMetricsCollector(
        region=args.region,
        profile=args.profile,
        time_window_minutes=args.time_window,
        data_dir=args.data_dir,
        max_traces=args.max_traces,
        parallel_workers=args.parallel_workers,
        batch_size=args.batch_size,
        retry_attempts=args.retry_attempts,
        force_full_collection=args.force_full_collection,
        max_trace_ids=args.max_trace_ids,
        retention_days=args.retention_days
    )

    # Làm sạch processed trace IDs nếu được yêu cầu
    if args.clean_trace_ids:
        collector.storage.cleanup_processed_trace_ids(max_age_hours=args.cleanup_age_hours)
        logger.info(f"Cleaned up processed trace IDs older than {args.cleanup_age_hours} hours")

    # Khởi tạo metrics ban đầu
    try:
        collector.get_metrics()
    except Exception as e:
        logger.error(f"Error initializing metrics: {str(e)}")

    # Tạo HTTP server
    handler = create_handler(collector)
    server = HTTPServer(('0.0.0.0', args.port), handler)

    logger.info(f"Starting X-Ray Prometheus Exporter on port {args.port}")
    logger.info(f"Configuration: region={args.region or 'default'}, time-window={args.time_window}m")
    logger.info(f"Advanced options: max_traces={args.max_traces}, parallel={args.parallel_workers}, batch={args.batch_size}")
    logger.info(f"Trace storage options: max_trace_ids={args.max_trace_ids}, retention_days={args.retention_days}")
    logger.info(f"Metrics endpoint: http://localhost:{args.port}/metrics")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down server")
        server.server_close()
if __name__ == '__main__':
    main()
