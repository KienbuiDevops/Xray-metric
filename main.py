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
    Entrypoint cho script
    """
    parser = argparse.ArgumentParser(description='X-Ray Prometheus Exporter')
    parser.add_argument('--port', type=int, help='Port to listen on', default=9092)
    parser.add_argument('--region', type=str, help='AWS Region', default=None)
    parser.add_argument('--profile', type=str, help='AWS Profile', default=None)
    parser.add_argument('--time-window', type=int, help='Time window in minutes', default=1)
    parser.add_argument('--data-dir', type=str, help='Directory to store state data', default=None)
    parser.add_argument('--log-level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                      help='Log level', default='INFO')

    args = parser.parse_args()

    # Thiết lập log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Khởi tạo collector
    collector = XRayMetricsCollector(
        region=args.region,
        profile=args.profile,
        time_window_minutes=args.time_window,
        data_dir=args.data_dir
    )

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
    logger.info(f"Metrics endpoint: http://localhost:{args.port}/metrics")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down server")
        server.server_close()

if __name__ == '__main__':
    main()
