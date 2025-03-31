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
        self.cache_ttl_seconds = 30  # Refresh metrics every 1 minute

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
        Đảm bảo luôn đẩy counter metrics lên Prometheus, ngay cả khi không có trace mới
        """
        logger.info("Starting X-Ray metrics collection")
    
        # Tính toán khoảng thời gian cho X-Ray query
        end_time = datetime.utcnow()
        start_time = self.last_timestamp
    
        # Thêm logic xử lý overlapping ở đây
        # Thêm một khoảng thời gian chồng lấn nhỏ để tránh bỏ sót traces
        overlap_seconds = 5
        if start_time > end_time - timedelta(seconds=overlap_seconds):
            # Nếu khoảng thời gian quá nhỏ, không cần thêm overlap
            pass
        else:
            # Lùi thời điểm bắt đầu thêm một chút để đảm bảo bắt được các trace có độ trễ
            start_time = start_time - timedelta(seconds=overlap_seconds)
            logger.debug(f"Added {overlap_seconds}s overlap. New start_time: {start_time}")
    
        # Đảm bảo khoảng thời gian không quá lớn để tránh quá tải
        max_time_window = self.time_window_minutes * 60 * 5  # 5 lần time_window
        if (end_time - start_time).total_seconds() > max_time_window:
            logger.warning(f"Time window too large ({(end_time - start_time).total_seconds() / 60} minutes), "
                         f"limiting to {self.time_window_minutes * 5} minutes")
            start_time = end_time - timedelta(minutes=self.time_window_minutes * 5)
    
        logger.info(f"Collecting data from {start_time} to {end_time}")
    
        # Thu thập traces từ X-Ray
        traces = self.processor.get_traces(start_time, end_time, self.processed_trace_ids)
    
        # Xử lý dữ liệu trace nếu có
        if traces:
            logger.info(f"Collected {len(traces)} traces")
            # Xử lý trace data thành metrics mới và cập nhật counter_values
            self.processor.process_trace_data(
                traces, start_time, end_time, self.counter_values
            )
            
            # Lưu danh sách trace IDs đã xử lý
            self.storage.save_processed_trace_ids(self.processed_trace_ids)
        else:
            logger.warning("No traces found in the specified time window")
        
        # Bất kể có trace mới hay không, luôn tạo metrics từ counter_values hiện tại
        # Đây là bước quan trọng để đảm bảo counter metrics luôn được đẩy lên
        metrics = self.processor.generate_all_metrics(self.counter_values)
        
        # Thêm heartbeat metric để kiểm tra kết nối
        self.counter_values['xray_exporter_heartbeat'] = self.counter_values.get('xray_exporter_heartbeat', 0) + 1
        metrics.append({
            'name': 'xray_exporter_heartbeat',
            'labels': {},
            'value': self.counter_values['xray_exporter_heartbeat'],
            'type': 'counter'
        })
    
        # Cập nhật timestamp
        self.storage.save_last_timestamp(end_time)
        self.last_timestamp = end_time
    
        # Lưu giá trị counters
        self.storage.save_counter_values(self.counter_values)
    
        logger.info(f"Generated {len(metrics)} metrics")
        return metrics

    def format_metrics_for_prometheus(self, metrics):
        """
        Chuyển đổi metrics thành định dạng Prometheus
        """
        return self.formatter.format_metrics_for_prometheus(metrics)
