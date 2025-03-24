"""
AWS X-Ray Prometheus Exporter - Collector Module (Optimized)
Chịu trách nhiệm chính về thu thập dữ liệu từ AWS X-Ray và tạo metrics phù hợp cho Prometheus
"""
import logging
import threading
import json
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
        # Giảm cache TTL để cập nhật metrics thường xuyên hơn
        self.cache_ttl_seconds = 30  # Refresh metrics every 30 seconds
        
        # Đọc timestamp của lần chạy trước
        self.last_timestamp = self.storage.load_last_timestamp(self.time_window_minutes)
        
        # Set để lưu trace IDs đã xử lý
        self.processed_trace_ids = self.storage.load_processed_trace_ids()
        
        # Dictionary để lưu giá trị counter
        self.counter_values = self.storage.load_counter_values()
        
        # Lưu thời gian các metrics được tạo
        self.metrics_timestamps = {}
        
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
        Thu thập metrics từ X-Ray với cải tiến để tạo dữ liệu mượt hơn cho Prometheus
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
        
        # Tạo các time buckets để phân phối traces
        time_range_seconds = (end_time - start_time).total_seconds()
        num_buckets = min(10, max(1, int(time_range_seconds / 60)))  # Mỗi bucket ~ 1 phút
        
        logger.info(f"Creating {num_buckets} time buckets for smoother metrics")
        
        # Tạo bucket thời gian
        buckets = []
        for i in range(num_buckets):
            bucket_start = start_time + timedelta(seconds=i * time_range_seconds / num_buckets)
            bucket_end = start_time + timedelta(seconds=(i + 1) * time_range_seconds / num_buckets)
            buckets.append((bucket_start, bucket_end))
        
        # Phân phối traces vào các buckets
        trace_buckets = [[] for _ in range(num_buckets)]
        
        for trace in traces:
            # Trích xuất thời gian từ trace nếu có
            trace_time = None
            for segment in trace.get('Segments', []):
                try:
                    document = segment.get('Document')
                    if document:
                        doc_data = json.loads(document)
                        trace_time = datetime.fromtimestamp(doc_data.get('start_time', 0))
                        break
                except:
                    pass
            
            # Nếu không lấy được thời gian, phân phối đều
            if not trace_time:
                bucket_idx = len(trace_buckets) // 2  # Mặc định ở giữa
            else:
                # Tìm bucket phù hợp dựa trên thời gian
                bucket_idx = 0
                for i, (bucket_start, bucket_end) in enumerate(buckets):
                    if bucket_start <= trace_time <= bucket_end:
                        bucket_idx = i
                        break
            
            trace_buckets[bucket_idx].append(trace)
        
        # Xử lý từng bucket và tạo metrics
        all_metrics = []
        for i, (bucket_start, bucket_end) in enumerate(buckets):
            bucket_traces = trace_buckets[i]
            if not bucket_traces:
                continue
                
            logger.info(f"Processing bucket {i+1}/{num_buckets} with {len(bucket_traces)} traces")
            
            # Tạo metrics cho bucket này
            bucket_metrics = self.processor.process_trace_data(
                bucket_traces, bucket_start, bucket_end, self.counter_values
            )
            
            # Thêm timestamp cho mỗi metric
            bucket_timestamp = int(bucket_end.timestamp() * 1000)
            for metric in bucket_metrics:
                metric_key = f"{metric['name']}_{'-'.join([f'{k}:{v}' for k, v in metric['labels'].items()])}"
                self.metrics_timestamps[metric_key] = bucket_timestamp
                metric['timestamp'] = bucket_timestamp
            
            all_metrics.extend(bucket_metrics)
        
        # Cập nhật timestamp
        self.storage.save_last_timestamp(end_time)
        self.last_timestamp = end_time
        
        # Lưu danh sách trace IDs đã xử lý
        self.storage.save_processed_trace_ids(self.processed_trace_ids)
        
        # Lưu giá trị counters
        self.storage.save_counter_values(self.counter_values)
        
        logger.info(f"Generated {len(all_metrics)} metrics across {num_buckets} time buckets")
        return all_metrics
    
    def format_metrics_for_prometheus(self, metrics):
        """
        Chuyển đổi metrics thành định dạng Prometheus với timestamps
        """
        return self.formatter.format_metrics_for_prometheus(metrics, self.metrics_timestamps)
