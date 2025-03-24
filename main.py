#!/usr/bin/env python3
"""
AWS X-Ray Prometheus Exporter - Main Entry Point (Optimized)
"""
import argparse
import logging
from http.server import HTTPServer
import threading
import time

from collector import XRayMetricsCollector
from handlers import create_handler

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('xray-exporter')

def background_collector(collector, interval_seconds):
    """
    Thread thu thập dữ liệu định kỳ trong nền
    
    :param collector: XRayMetricsCollector instance
    :param interval_seconds: Số giây giữa các lần thu thập
    """
    logger.info(f"Starting background collector thread with interval: {interval_seconds}s")
    while True:
        try:
            logger.info("Background collector triggering metrics collection")
            collector.get_metrics()
            time.sleep(interval_seconds)
        except Exception as e:
            logger.error(f"Error in background collector: {str(e)}")
            time.sleep(5)  # Ngắn hơn nếu có lỗi để thử lại sớm hơn

def main():
    """
    Entrypoint cho script với cải tiến về thu thập dữ liệu
    """
    parser = argparse.ArgumentParser(description='X-Ray Prometheus Exporter')
    parser.add_argument('--port', type=int, help='Port để lắng nghe', default=9092)
    parser.add_argument('--region', type=str, help='AWS Region', default=None)
    parser.add_argument('--profile', type=str, help='AWS Profile', default=None)
    parser.add_argument('--time-window', type=int, help='Khoảng thời gian thu thập (phút)', default=2)
    parser.add_argument('--collection-interval', type=int, help='Khoảng thời gian giữa các lần thu thập (giây)', default=60)
    parser.add_argument('--data-dir', type=str, help='Thư mục lưu trữ trạng thái', default=None)
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
    
    # Khởi động thread thu thập dữ liệu nền
    bg_thread = threading.Thread(
        target=background_collector,
        args=(collector, args.collection_interval),
        daemon=True
    )
    bg_thread.start()
    
    # Tạo HTTP server
    handler = create_handler(collector)
    server = HTTPServer(('0.0.0.0', args.port), handler)
    
    logger.info(f"Starting X-Ray Prometheus Exporter on port {args.port}")
    logger.info(f"Configuration: region={args.region or 'default'}, time-window={args.time_window}m, collection-interval={args.collection_interval}s")
    logger.info(f"Metrics endpoint: http://localhost:{args.port}/metrics")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down server")
        server.server_close()

if __name__ == '__main__':
    main()
