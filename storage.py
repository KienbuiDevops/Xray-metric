"""
AWS X-Ray Prometheus Exporter - Storage Module
Quản lý lưu trữ trạng thái và cấu hình
"""
import os
import pickle
import logging
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger('xray-exporter.storage')

class StateStorage:
    """
    Lớp quản lý lưu trữ và khôi phục trạng thái của exporter
    """
    def __init__(self, data_dir=None):
        """
        Khởi tạo state storage
        
        :param data_dir: Thư mục để lưu trữ dữ liệu trạng thái
        """
        self.data_dir = data_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        
        # Tạo thư mục data nếu không tồn tại
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # Files để lưu trạng thái
        self.last_timestamp_file = os.path.join(self.data_dir, 'last_timestamp.txt')
        self.processed_trace_ids_file = os.path.join(self.data_dir, 'processed_trace_ids.pickle')
        self.counter_values_file = os.path.join(self.data_dir, 'counter_values.pickle')
    
    def cleanup_processed_trace_ids(self, max_age_hours=24):
        """
        Làm sạch danh sách trace IDs đã xử lý, giữ lại chỉ các ID mới
        
        :param max_age_hours: Số giờ tối đa để giữ lại trace IDs (không dùng vì không có timestamp)
        """
        logger.info("Cleaning up processed trace IDs")
        
        try:
            # Đơn giản là xóa hết và bắt đầu lại
            logger.info("Clearing processed trace IDs")
            self.save_processed_trace_ids(set())
        except Exception as e:
            logger.error(f"Error cleaning up processed trace IDs: {str(e)}")
    def load_last_timestamp(self, time_window_minutes):
        """
        Tải timestamp của lần chạy cuối cùng
        
        :param time_window_minutes: Khoảng thời gian mặc định (phút) nếu không có timestamp
        :return: datetime object đại diện cho timestamp
        """
        if os.path.exists(self.last_timestamp_file):
            try:
                with open(self.last_timestamp_file, 'r') as f:
                    timestamp_str = f.read().strip()
                    if timestamp_str:
                        return datetime.fromisoformat(timestamp_str)
            except Exception as e:
                logger.error(f"Error loading last timestamp: {str(e)}")
        
        # Nếu không có hoặc lỗi, trả về thời gian hiện tại trừ time window
        return datetime.utcnow() - timedelta(minutes=time_window_minutes)
    
    def save_last_timestamp(self, timestamp):
        """
        Lưu timestamp của lần chạy hiện tại
        
        :param timestamp: datetime object đại diện cho timestamp cần lưu
        """
        try:
            with open(self.last_timestamp_file, 'w') as f:
                f.write(timestamp.isoformat())
        except Exception as e:
            logger.error(f"Error saving last timestamp: {str(e)}")
    
    def load_processed_trace_ids(self):
        """
        Tải danh sách trace IDs đã xử lý
        
        :return: Set chứa các trace ID đã xử lý
        """
        if os.path.exists(self.processed_trace_ids_file):
            try:
                with open(self.processed_trace_ids_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                logger.error(f"Error loading processed trace IDs: {str(e)}")
        
        return set()
    
    def save_processed_trace_ids(self, processed_trace_ids):
        """
        Lưu danh sách trace IDs đã xử lý
        
        :param processed_trace_ids: Set chứa các trace ID đã xử lý
        """
        try:
            # Giới hạn kích thước của set để tránh quá lớn
            if len(processed_trace_ids) > 1000000:  # Tăng giới hạn từ 100,000 lên 1,000,000
                # Giữ lại 500,000 trace IDs gần đây nhất (nếu có thể xác định thứ tự thêm vào)
                processed_trace_ids = set(list(processed_trace_ids)[-500000:])
                logger.warning(f"Limited processed_trace_ids size to 500,000 entries")
            
            with open(self.processed_trace_ids_file, 'wb') as f:
                pickle.dump(processed_trace_ids, f)
        except Exception as e:
            logger.error(f"Error saving processed trace IDs: {str(e)}")
    
    def load_counter_values(self):
        """
        Tải giá trị counters
        
        :return: defaultdict chứa các giá trị counter
        """
        if os.path.exists(self.counter_values_file):
            try:
                with open(self.counter_values_file, 'rb') as f:
                    counter_values = pickle.load(f)
                    return defaultdict(float, counter_values)
            except Exception as e:
                logger.error(f"Error loading counter values: {str(e)}")
        
        return defaultdict(float)
    
    def save_counter_values(self, counter_values):
        """
        Lưu giá trị counters
        
        :param counter_values: Dict chứa các giá trị counter
        """
        try:
            with open(self.counter_values_file, 'wb') as f:
                pickle.dump(dict(counter_values), f)
        except Exception as e:
            logger.error(f"Error saving counter values: {str(e)}")