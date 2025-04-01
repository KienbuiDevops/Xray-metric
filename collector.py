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
    def __init__(self, region=None, profile=None, time_window_minutes=1, data_dir=None, 
                max_traces=None, parallel_workers=20, batch_size=5, retry_attempts=3,
                force_full_collection=False, max_trace_ids=1000000, retention_days=30):
        """
        Khởi tạo X-Ray Metrics Collector với các tùy chọn nâng cao
        
        :param region: AWS Region
        :param profile: AWS Profile name
        :param time_window_minutes: Time window in minutes to fetch X-Ray data
        :param data_dir: Directory to store state data
        :param max_traces: Maximum number of traces to process per run
        :param parallel_workers: Number of parallel workers for trace processing
        :param batch_size: Batch size for API calls
        :param retry_attempts: Number of retry attempts for API calls
        :param force_full_collection: Ignore processed trace IDs for this run
        :param max_trace_ids: Maximum number of trace IDs to store
        :param retention_days: Number of days to retain trace IDs
        """
        self.time_window_minutes = time_window_minutes
        self.max_traces = max_traces
        self.parallel_workers = parallel_workers
        self.batch_size = batch_size
        self.retry_attempts = retry_attempts
        self.force_full_collection = force_full_collection

        # Khởi tạo storage để lưu/đọc trạng thái với tùy chọn mới
        self.storage = StateStorage(
            data_dir=data_dir,
            max_trace_ids=max_trace_ids,
            retention_days=retention_days
        )

        # Khởi tạo processor xử lý dữ liệu trace với các tùy chọn mới
        self.processor = TraceProcessor(
            region=region, 
            profile=profile,
            batch_size=self.batch_size,
            parallel_workers=self.parallel_workers,
            retry_attempts=self.retry_attempts
        )

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
        if self.force_full_collection:
            # Nếu force full collection, bắt đầu với set rỗng
            self.processed_trace_ids = set()
            logger.info("Forced full collection mode enabled - ignoring previously processed trace IDs")
        else:
            self.processed_trace_ids = self.storage.load_processed_trace_ids()

        # Dictionary để lưu giá trị counter
        self.counter_values = self.storage.load_counter_values()
        
        # Dictionary để lưu trữ gauge metrics
        self.gauge_values = {
            'errors': {},
            'faults': {},
            'throttles': {}
        }

        logger.info(f"Initialized collector with time window: {time_window_minutes} minute(s)")
        logger.info(f"Last timestamp: {self.last_timestamp}")
        logger.info(f"Number of processed trace IDs: {len(self.processed_trace_ids)}")
        logger.info(f"Advanced options: max_traces={max_traces}, parallel_workers={parallel_workers}, batch_size={batch_size}")
        logger.info(f"Trace storage options: max_trace_ids={max_trace_ids}, retention_days={retention_days}")

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
                    # Thêm một trường để lưu trữ thời gian thu thập metrics
                    new_metrics = self.collect_metrics()
                    
                    # Thêm timestamp cho mỗi metric để Prometheus có thể xác định metrics cũ
                    timestamp_ms = int(current_time.timestamp() * 1000)
                    for metric in new_metrics:
                        metric['timestamp_ms'] = timestamp_ms
                    
                    self.metrics_cache = new_metrics
                    self.last_update = current_time
                except Exception as e:
                    logger.error(f"Error collecting metrics: {str(e)}")
                    # Nếu lỗi, giữ lại metrics cũ nhưng không cập nhật last_update
            else:
                logger.debug("Using cached metrics")

            return self.metrics_cache

    def collect_metrics(self):
        """
        Thu thập metrics từ X-Ray với xử lý trace trùng lặp tối ưu
        """
        logger.info("Starting X-Ray metrics collection")

        # Tính toán khoảng thời gian cho X-Ray query
        end_time = datetime.utcnow()
        start_time = self.last_timestamp

        # Tăng thời gian tối đa có thể query
        max_time_window = self.time_window_minutes * 60 * 10  # Tăng từ 5 lên 10 lần time_window
        if (end_time - start_time).total_seconds() > max_time_window:
            logger.warning(f"Time window too large ({(end_time - start_time).total_seconds() / 60} minutes), "
                        f"limiting to {self.time_window_minutes * 10} minutes")
            start_time = end_time - timedelta(minutes=self.time_window_minutes * 10)

        logger.info(f"Collecting data from {start_time} to {end_time}")

        # Reset các gauge metrics trước mỗi lần thu thập mới
        self.gauge_values = {
            'errors': {},
            'faults': {},
            'throttles': {}
        }

        # Thu thập traces từ X-Ray, truyền thêm storage để lưu trace IDs
        traces = self.processor.get_traces(
            start_time, 
            end_time, 
            self.processed_trace_ids,
            storage=self.storage  # Truyền storage để lưu trace IDs liên tục
        )

        if not traces:
            logger.warning("No traces found in the specified time window")
            # Cập nhật timestamp để lần sau không lấy lại khoảng thời gian này
            self.storage.save_last_timestamp(end_time)
            self.last_timestamp = end_time
            
            # Tạo metrics cho các services đã biết
            # Điều này đảm bảo rằng gauge metrics vẫn được báo cáo với giá trị 0
            known_services = set()
            for key in self.counter_values.keys():
                if key.startswith('xray_service_requests_total_'):
                    service_name = key[len('xray_service_requests_total_'):]
                    known_services.add(service_name)
            
            # Tạo empty metrics list
            metrics = []
            
            # Thêm gauge metrics với giá trị 0 cho tất cả services đã biết
            for service_name in known_services:
                metrics.append({
                    'name': 'xray_service_errors_count',
                    'labels': {'service': service_name},
                    'value': 0,
                    'type': 'gauge'
                })
                
                metrics.append({
                    'name': 'xray_service_faults_count',
                    'labels': {'service': service_name},
                    'value': 0,
                    'type': 'gauge'
                })
                
                metrics.append({
                    'name': 'xray_service_throttles_count',
                    'labels': {'service': service_name},
                    'value': 0,
                    'type': 'gauge'
                })
            
            return metrics

        # Giới hạn số lượng trace nếu đã cấu hình max_traces
        if self.max_traces and len(traces) > self.max_traces:
            logger.info(f"Limiting processing to {self.max_traces} traces out of {len(traces)}")
            traces = traces[:self.max_traces]
        else:
            logger.info(f"Processing all {len(traces)} collected traces")

        # Xử lý trace data thành metrics
        metrics = self.processor.process_trace_data(
            traces, start_time, end_time, self.counter_values, self.gauge_values
        )

        # Cập nhật timestamp
        self.storage.save_last_timestamp(end_time)
        self.last_timestamp = end_time

        # Lưu giá trị counters
        self.storage.save_counter_values(self.counter_values)

        logger.info(f"Generated {len(metrics)} metrics")
        return metrics