"""
AWS X-Ray Prometheus Exporter - Collector Module
Chịu trách nhiệm chính về thu thập dữ liệu từ AWS X-Ray
"""
import logging
import threading
from datetime import datetime, timedelta

from storage import StateStorage
from processors import TraceProcessor, MetricsFormatter

logger = logging.getLogger('xray-exporter.collector')

class XRayMetricsCollector:
    def __init__(self, region=None, profile=None, time_window_minutes=1, data_dir=None):
        """
        Khởi tạo X-Ray Metrics Collector

        :param region: AWS Region
        :param profile: AWS Profile name
        :param time_window_minutes: Time window in minutes to fetch X-Ray data
        :param data_dir: Directory to store state data
        """
        self.time_window_minutes = time_window_minutes

        # Khởi tạo storage để lưu/đọc trạng thái
        self.storage = StateStorage(data_dir=data_dir)

        # Khởi tạo processor xử lý dữ liệu trace
        self.processor = TraceProcessor(region=region, profile=profile)

        # Khởi tạo formatter để format metrics cho Prometheus
        self.formatter = MetricsFormatter()

        # Cache cho metrics
        self.metrics_cache = []
        self.last_update = datetime.min
        self.cache_lock = threading.Lock()
        self.cache_ttl_seconds = 60  # Refresh metrics every 1 minute

        # Đọc timestamp của lần chạy trước
        self.last_timestamp = self.storage.load_last_timestamp(self.time_window_minutes)

        # Set để lưu trace IDs đã xử lý
        self.processed_trace_ids = self.storage.load_processed_trace_ids()

        # Dictionary để lưu giá trị counter
        self.counter_values = self.storage.load_counter_values()

        logger.info(f"Initialized collector with time window: {time_window_minutes} minute(s)")
        logger.info(f"Last timestamp: {self.last_timestamp}")
        logger.info(f"Number of processed trace IDs: {len(self.processed_trace_ids)}")

    def get_metrics(self):
        """
        Lấy metrics từ cache hoặc thu thập mới nếu cache đã hết hạn
        """
        with self.cache_lock:
            current_time = datetime.now()
            # Kiểm tra nếu cache đã hết hạn
            if (current_time - self.last_update).total_seconds() > self.cache_ttl_seconds:
                logger.info("Cache expired, collecting new metrics")
                try:
                    self.metrics_cache = self.collect_metrics()
                    self.last_update = current_time
                except Exception as e:
                    logger.error(f"Error collecting metrics: {str(e)}")
                    # Nếu lỗi, giữ lại metrics cũ nhưng không cập nhật last_update
            else:
                logger.debug("Using cached metrics")

            return self.metrics_cache

    def collect_metrics(self):
        """
        Thu thập metrics từ X-Ray
        """
        logger.info("Starting X-Ray metrics collection")

        # Tính toán khoảng thời gian cho X-Ray query
        end_time = datetime.utcnow()
        start_time = self.last_timestamp

        # Đảm bảo khoảng thời gian không quá lớn để tránh quá tải
        max_time_window = self.time_window_minutes * 60 * 5  # 5 lần time_window
        if (end_time - start_time).total_seconds() > max_time_window:
            logger.warning(f"Time window too large ({(end_time - start_time).total_seconds() / 60} minutes), "
                         f"limiting to {self.time_window_minutes * 5} minutes")
            start_time = end_time - timedelta(minutes=self.time_window_minutes * 5)

        logger.info(f"Collecting data from {start_time} to {end_time}")

        # Thu thập traces từ X-Ray
        traces = self.processor.get_traces(start_time, end_time, self.processed_trace_ids)

        if not traces:
            logger.warning("No traces found in the specified time window")
            # Cập nhật timestamp để lần sau không lấy lại khoảng thời gian này
            self.storage.save_last_timestamp(end_time)
            self.last_timestamp = end_time
            return []

        logger.info(f"Collected {len(traces)} traces")

        # Xử lý trace data thành metrics
        metrics = self.processor.process_trace_data(
            traces, start_time, end_time, self.counter_values
        )

        # Cập nhật timestamp
        self.storage.save_last_timestamp(end_time)
        self.last_timestamp = end_time

        # Lưu danh sách trace IDs đã xử lý
        self.storage.save_processed_trace_ids(self.processed_trace_ids)

        # Lưu giá trị counters
        self.storage.save_counter_values(self.counter_values)

        logger.info(f"Generated {len(metrics)} metrics")
        return metrics

    def format_metrics_for_prometheus(self, metrics):
        """
        Chuyển đổi metrics thành định dạng Prometheus
        """
        return self.formatter.format_metrics_for_prometheus(metrics)