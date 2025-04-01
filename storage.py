"""
AWS X-Ray Prometheus Exporter - Storage Module
Quản lý lưu trữ trạng thái và cấu hình với cơ chế xử lý trace tốt hơn
"""
import os
import time
import pickle
import logging
from datetime import datetime, timedelta
from collections import OrderedDict
from collections import defaultdict

logger = logging.getLogger('xray-exporter.storage')

class StateStorage:
    """
    Lớp quản lý lưu trữ và khôi phục trạng thái của exporter với cải tiến
    để xử lý trace trùng lặp tốt hơn
    """
    def __init__(self, data_dir=None, max_trace_ids=1000000, retention_days=30):
        """
        Khởi tạo state storage với các tùy chọn nâng cao
        
        :param data_dir: Thư mục để lưu trữ dữ liệu trạng thái
        :param max_trace_ids: Số lượng tối đa trace ID lưu trữ
        :param retention_days: Số ngày giữ lại trace ID
        """
        self.data_dir = data_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        self.max_trace_ids = max_trace_ids
        self.retention_days = retention_days
        
        # Tạo thư mục data nếu không tồn tại
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # Files để lưu trạng thái
        self.last_timestamp_file = os.path.join(self.data_dir, 'last_timestamp.txt')
        self.processed_trace_ids_file = os.path.join(self.data_dir, 'processed_trace_ids.pickle')
        self.timed_trace_ids_file = os.path.join(self.data_dir, 'timed_trace_ids.pickle')  # File mới cho timed trace IDs
        self.counter_values_file = os.path.join(self.data_dir, 'counter_values.pickle')
    
    def cleanup_processed_trace_ids(self, max_age_hours=24):
        """
        Làm sạch danh sách trace IDs đã xử lý, giữ lại chỉ các ID mới
        
        :param max_age_hours: Số giờ tối đa để giữ lại trace IDs
        """
        logger.info("Cleaning up processed trace IDs")
        
        # Tải timed_trace_ids (nếu có)
        timed_trace_ids = self.load_timed_trace_ids()
        
        if timed_trace_ids:
            # Tính timestamp giới hạn
            cutoff_time = time.time() - (max_age_hours * 3600)
            
            # Lọc ra các trace ID mới hơn cutoff_time
            new_timed_trace_ids = {trace_id: timestamp for trace_id, timestamp in timed_trace_ids.items() 
                                  if timestamp > cutoff_time}
            
            logger.info(f"Removed {len(timed_trace_ids) - len(new_timed_trace_ids)} old trace IDs")
            logger.info(f"Kept {len(new_timed_trace_ids)} recent trace IDs")
            
            # Lưu lại timed_trace_ids đã lọc
            self.save_timed_trace_ids(new_timed_trace_ids)
            
            # Cập nhật processed_trace_ids từ timed_trace_ids
            self.save_processed_trace_ids(set(new_timed_trace_ids.keys()))
        else:
            # Nếu không có timed_trace_ids, xóa toàn bộ processed_trace_ids
            logger.info("No timed trace IDs found, clearing processed trace IDs")
            self.save_processed_trace_ids(set())
    
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
    
    def load_timed_trace_ids(self):
        """
        Tải danh sách trace IDs đã xử lý kèm timestamp
        
        :return: Dictionary ánh xạ từ trace ID đến timestamp
        """
        if os.path.exists(self.timed_trace_ids_file):
            try:
                with open(self.timed_trace_ids_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                logger.error(f"Error loading timed trace IDs: {str(e)}")
        
        return OrderedDict()
    
    def save_processed_trace_ids(self, processed_trace_ids):
        """
        Lưu danh sách trace IDs đã xử lý
        
        :param processed_trace_ids: Set chứa các trace ID đã xử lý
        """
        try:
            with open(self.processed_trace_ids_file, 'wb') as f:
                pickle.dump(processed_trace_ids, f)
        except Exception as e:
            logger.error(f"Error saving processed trace IDs: {str(e)}")
    
    def save_timed_trace_ids(self, timed_trace_ids):
        """
        Lưu danh sách trace IDs kèm timestamp
        
        :param timed_trace_ids: Dictionary ánh xạ từ trace ID đến timestamp
        """
        try:
            with open(self.timed_trace_ids_file, 'wb') as f:
                pickle.dump(timed_trace_ids, f)
        except Exception as e:
            logger.error(f"Error saving timed trace IDs: {str(e)}")
    
    def add_trace_ids(self, trace_ids):
        """
        Thêm nhiều trace ID mới vào danh sách đã xử lý
        
        :param trace_ids: List các trace ID mới
        :return: Set danh sách processed_trace_ids đã cập nhật
        """
        # Tải dữ liệu hiện có
        processed_trace_ids = self.load_processed_trace_ids()
        timed_trace_ids = self.load_timed_trace_ids()
        
        # Thêm trace ID mới với timestamp hiện tại
        current_time = time.time()
        for trace_id in trace_ids:
            if trace_id not in processed_trace_ids:
                processed_trace_ids.add(trace_id)
                timed_trace_ids[trace_id] = current_time
        
        # Kiểm soát kích thước nếu vượt quá giới hạn
        if len(processed_trace_ids) > self.max_trace_ids:
            # Sắp xếp theo timestamp và giữ lại các trace ID mới nhất
            sorted_items = sorted(timed_trace_ids.items(), key=lambda x: x[1])
            
            # Xác định số lượng phần tử cần xóa
            items_to_remove = len(processed_trace_ids) - (self.max_trace_ids // 2)
            
            # Xóa các phần tử cũ nhất
            oldest_items = sorted_items[:items_to_remove]
            for trace_id, _ in oldest_items:
                del timed_trace_ids[trace_id]
                processed_trace_ids.remove(trace_id)
            
            logger.warning(f"Limited processed_trace_ids size: removed {items_to_remove} oldest entries, kept {len(processed_trace_ids)}")
        
        # Lưu lại cả hai cấu trúc dữ liệu
        self.save_processed_trace_ids(processed_trace_ids)
        self.save_timed_trace_ids(timed_trace_ids)
        
        return processed_trace_ids
    
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