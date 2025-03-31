"""
AWS X-Ray Prometheus Exporter - Processors Module (Optimized)
Xử lý dữ liệu từ X-Ray và chuyển đổi thành raw Prometheus metrics
"""
import json
import time
import logging
import boto3
from datetime import datetime
from collections import defaultdict
from botocore.exceptions import ClientError

logger = logging.getLogger('xray-exporter.processors')

class TraceProcessor:
    def __init__(self, region=None, profile=None):
        """
        Khởi tạo processor để xử lý dữ liệu X-Ray
        
        :param region: AWS Region
        :param profile: AWS Profile name
        """
        # Khởi tạo AWS session
        session = boto3.Session(profile_name=profile, region_name=region)
        self.xray_client = session.client('xray')
    def generate_all_metrics(self, counter_values):
        """
        Tạo tất cả counter metrics từ counter_values hiện tại
        Theo nguyên tắc Prometheus:
        - Counter metrics luôn được báo cáo
        - Gauge metrics (như latency) chỉ báo cáo khi có dữ liệu mới
        
        :param counter_values: Dictionary của các counter values hiện tại
        :return: List các metrics
        """
        logger.info("Generating metrics from existing counter values")
        
        metrics = []
        
        # Phân loại và xử lý counter metrics
        for key, value in counter_values.items():
            # Chỉ xử lý các counter metrics, bỏ qua các gauge metrics liên quan đến latency
            if any(key.startswith(prefix) for prefix in [
                'xray_service_requests_total_',
                'xray_service_errors_total_',
                'xray_service_faults_total_',
                'xray_service_throttles_total_',
                'xray_url_requests_total_',
                'xray_url_errors_total_',
                'xray_url_service_requests_total_',
                'xray_url_service_errors_total_',
                'xray_service_status_total_',
                'xray_service_method_total_',
                'xray_service_client_ip_total_',
                'xray_url_service_total_',
                'xray_url_method_total_',
                'xray_url_status_total_',
                'xray_service_dependency_total_'
            ]):
                # Extract metric name and labels from key
                parts = key.split('_')
                
                # Service requests
                if key.startswith('xray_service_requests_total_'):
                    service = key[len('xray_service_requests_total_'):]
                    metrics.append({
                        'name': 'xray_service_requests_total',
                        'labels': {'service': service},
                        'value': value,
                        'type': 'counter'
                    })
                # Service errors
                elif key.startswith('xray_service_errors_total_'):
                    service = key[len('xray_service_errors_total_'):]
                    metrics.append({
                        'name': 'xray_service_errors_total',
                        'labels': {'service': service},
                        'value': value,
                        'type': 'counter'
                    })
                # Service faults
                elif key.startswith('xray_service_faults_total_'):
                    service = key[len('xray_service_faults_total_'):]
                    metrics.append({
                        'name': 'xray_service_faults_total',
                        'labels': {'service': service},
                        'value': value,
                        'type': 'counter'
                    })
                # Service throttles
                elif key.startswith('xray_service_throttles_total_'):
                    service = key[len('xray_service_throttles_total_'):]
                    metrics.append({
                        'name': 'xray_service_throttles_total',
                        'labels': {'service': service},
                        'value': value,
                        'type': 'counter'
                    })
                # URL requests
                elif key.startswith('xray_url_requests_total_'):
                    url = key[len('xray_url_requests_total_'):]
                    metrics.append({
                        'name': 'xray_url_requests_total',
                        'labels': {'url': url},
                        'value': value,
                        'type': 'counter'
                    })
                # URL errors
                elif key.startswith('xray_url_errors_total_'):
                    url = key[len('xray_url_errors_total_'):]
                    metrics.append({
                        'name': 'xray_url_errors_total',
                        'labels': {'url': url},
                        'value': value,
                        'type': 'counter'
                    })
                # URL-Service requests
                elif key.startswith('xray_url_service_requests_total_'):
                    remaining = key[len('xray_url_service_requests_total_'):]
                    last_underscore = remaining.rfind('_')
                    if last_underscore != -1:
                        url = remaining[:last_underscore]
                        service = remaining[last_underscore+1:]
                        metrics.append({
                            'name': 'xray_url_service_requests_total',
                            'labels': {'url': url, 'service': service},
                            'value': value,
                            'type': 'counter'
                        })
                # URL-Service errors
                elif key.startswith('xray_url_service_errors_total_'):
                    remaining = key[len('xray_url_service_errors_total_'):]
                    last_underscore = remaining.rfind('_')
                    if last_underscore != -1:
                        url = remaining[:last_underscore]
                        service = remaining[last_underscore+1:]
                        metrics.append({
                            'name': 'xray_url_service_errors_total',
                            'labels': {'url': url, 'service': service},
                            'value': value,
                            'type': 'counter'
                        })
                # Service status codes
                elif key.startswith('xray_service_status_total_'):
                    remaining = key[len('xray_service_status_total_'):]
                    last_underscore = remaining.rfind('_')
                    if last_underscore != -1:
                        service = remaining[:last_underscore]
                        status_code = remaining[last_underscore+1:]
                        metrics.append({
                            'name': 'xray_service_status_total',
                            'labels': {'service': service, 'status_code': status_code},
                            'value': value,
                            'type': 'counter'
                        })
                # Service HTTP methods
                elif key.startswith('xray_service_method_total_'):
                    remaining = key[len('xray_service_method_total_'):]
                    last_underscore = remaining.rfind('_')
                    if last_underscore != -1:
                        service = remaining[:last_underscore]
                        method = remaining[last_underscore+1:]
                        metrics.append({
                            'name': 'xray_service_method_total',
                            'labels': {'service': service, 'method': method},
                            'value': value,
                            'type': 'counter'
                        })
                # Service dependencies
                elif key.startswith('xray_service_dependency_total_'):
                    remaining = key[len('xray_service_dependency_total_'):]
                    last_underscore = remaining.rfind('_')
                    if last_underscore != -1:
                        source = remaining[:last_underscore]
                        target = remaining[last_underscore+1:]
                        metrics.append({
                            'name': 'xray_service_dependency_total',
                            'labels': {'source': source, 'target': target},
                            'value': value,
                            'type': 'counter'
                        })
                        
        # Thêm heartbeat metric để kiểm tra kết nối
        counter_values['xray_exporter_heartbeat'] = counter_values.get('xray_exporter_heartbeat', 0) + 1
        metrics.append({
            'name': 'xray_exporter_heartbeat',
            'labels': {},
            'value': counter_values['xray_exporter_heartbeat'],
            'type': 'counter'
        })
        
        logger.info(f"Generated {len(metrics)} metrics from existing counter values")
        return metrics
    
    def get_traces(self, start_time, end_time, processed_trace_ids):
        """
        Lấy traces từ X-Ray trong khoảng thời gian chỉ định
        
        :param start_time: Thời gian bắt đầu thu thập
        :param end_time: Thời gian kết thúc thu thập
        :param processed_trace_ids: Set chứa các trace ID đã xử lý
        :return: List các traces
        """
        logger.info("Retrieving trace summaries")
        
        try:
            # Lấy trace summaries
            paginator = self.xray_client.get_paginator('get_trace_summaries')
            trace_summaries = []
            
            for page in paginator.paginate(
                StartTime=start_time,
                EndTime=end_time,
                TimeRangeType='TraceId',
                Sampling=False  # Lấy tất cả traces, không sampling
            ):
                trace_summaries.extend(page.get('TraceSummaries', []))
            
            logger.info(f"Retrieved {len(trace_summaries)} trace summaries")
            
            # Lọc ra các trace chưa được xử lý
            new_trace_ids = []
            for summary in trace_summaries:
                trace_id = summary['Id']
                if trace_id not in processed_trace_ids:
                    new_trace_ids.append(trace_id)
                    processed_trace_ids.add(trace_id)
            
            logger.info(f"Found {len(new_trace_ids)} new traces to process")
            
            if not new_trace_ids:
                return []
            
            # Lấy chi tiết traces cho các trace ID mới
            return self.get_trace_details(new_trace_ids)
            
        except ClientError as e:
            logger.error(f"Error retrieving trace summaries: {str(e)}")
            return []
    
    def get_trace_details(self, trace_ids):
        """
        Lấy chi tiết đầy đủ của traces từ trace IDs
        
        :param trace_ids: List các trace ID cần lấy chi tiết
        :return: List các traces với thông tin đầy đủ
        """
        logger.info(f"Retrieving details for {len(trace_ids)} traces")
        
        # X-Ray API chỉ cho phép lấy tối đa 5 traces mỗi lần gọi
        batch_size = 5
        all_traces = []
        
        for i in range(0, len(trace_ids), batch_size):
            batch = trace_ids[i:i + batch_size]
            try:
                response = self.xray_client.batch_get_traces(TraceIds=batch)
                all_traces.extend(response.get('Traces', []))
                
                # Tránh rate limit
                if i + batch_size < len(trace_ids):
                    time.sleep(0.1)  # 100ms delay giữa các batch
                    
            except ClientError as e:
                logger.error(f"Error retrieving trace details for batch {i//batch_size}: {str(e)}")
                # Tiếp tục với các batch khác
        
        return all_traces
    
    def process_trace_data(self, traces, start_time, end_time, counter_values):
        """
        Xử lý dữ liệu trace thành metrics tạm thời
        
        :param traces: List các traces để xử lý
        :param start_time: Thời gian bắt đầu
        :param end_time: Thời gian kết thúc
        :param counter_values: Dictionary lưu trữ giá trị các counters
        :return: List các metrics
        """
        # Khởi tạo các metric generators
        service_metrics_generator = ServiceMetricsGenerator(counter_values)
        url_metrics_generator = UrlMetricsGenerator(counter_values)
        dependency_metrics_generator = DependencyMetricsGenerator(counter_values)
        
        # Collectors cho service metrics
        service_metrics = defaultdict(lambda: {
            'request_count': 0,
            'error_count': 0,
            'fault_count': 0,
            'throttle_count': 0,
            'latencies': [],
            'response_sizes': [],
            'request_sizes': [],
            'status_codes': defaultdict(int),
            'urls': defaultdict(int),
            'downstream_calls': defaultdict(int),
            'methods': defaultdict(int),
            'client_ips': defaultdict(int)
        })
        
        # Collectors for URL metrics
        url_metrics = defaultdict(lambda: {
            'request_count': 0,
            'error_count': 0,
            'latencies': [],
            'services': defaultdict(int),
            'status_codes': defaultdict(int),
            'methods': defaultdict(int)
        })
        
        # Xử lý mỗi trace
        for trace in traces:
            trace_id = trace.get('Id', 'unknown')
            segments = trace.get('Segments', [])
            
            # Xử lý mỗi segment
            for segment in segments:
                try:
                    document = json.loads(segment.get('Document', '{}'))
                    
                    # Lấy thông tin cơ bản của segment
                    service_name = document.get('name', 'unknown')
                    
                    # Tính thời gian
                    start_time_segment = document.get('start_time', 0)
                    end_time_segment = document.get('end_time', 0)
                    duration_ms = (end_time_segment - start_time_segment) * 1000 if end_time_segment and start_time_segment else 0
                    
                    # Cập nhật service metrics
                    service_metrics[service_name]['request_count'] += 1
                    service_metrics[service_name]['latencies'].append(duration_ms)
                    
                    # Lấy thông tin HTTP
                    http = document.get('http', {})
                    request = http.get('request', {})
                    response = http.get('response', {})
                    
                    url = request.get('url', '')
                    method = request.get('method', '')
                    status_code = response.get('status', 0)
                    client_ip = request.get('client_ip', '')
                    
                    # Xử lý thông tin kích thước request/response
                    request_size = request.get('content_length', 0)
                    response_size = response.get('content_length', 0)
                    
                    if request_size:
                        service_metrics[service_name]['request_sizes'].append(request_size)
                    
                    if response_size:
                        service_metrics[service_name]['response_sizes'].append(response_size)
                    
                    # Xử lý lỗi và fault
                    error = document.get('error', False)
                    fault = document.get('fault', False)
                    throttle = document.get('throttle', False)
                    
                    if error or (status_code >= 400 and status_code < 500):
                        service_metrics[service_name]['error_count'] += 1
                    
                    if fault or status_code >= 500:
                        service_metrics[service_name]['fault_count'] += 1
                    
                    if throttle:
                        service_metrics[service_name]['throttle_count'] += 1
                    
                    # Cập nhật các counters theo service
                    if status_code:
                        service_metrics[service_name]['status_codes'][str(status_code)] += 1
                    
                    if url:
                        service_metrics[service_name]['urls'][url] += 1
                    
                    if method:
                        service_metrics[service_name]['methods'][method] += 1
                    
                    if client_ip:
                        service_metrics[service_name]['client_ips'][client_ip] += 1
                    
                    # Cập nhật URL metrics nếu có URL
                    if url:
                        url_metrics[url]['request_count'] += 1
                        url_metrics[url]['latencies'].append(duration_ms)
                        url_metrics[url]['services'][service_name] += 1
                        
                        if status_code:
                            url_metrics[url]['status_codes'][str(status_code)] += 1
                        
                        if method:
                            url_metrics[url]['methods'][method] += 1
                        
                        if error or fault or status_code >= 400:
                            url_metrics[url]['error_count'] += 1
                    
                    # Xử lý subsegments để tìm downstream calls
                    subsegments = document.get('subsegments', [])
                    for subsegment in subsegments:
                        if isinstance(subsegment, dict):
                            downstream_name = subsegment.get('name', '')
                            if downstream_name and downstream_name != service_name:
                                service_metrics[service_name]['downstream_calls'][downstream_name] += 1
                
                except (json.JSONDecodeError, KeyError) as e:
                    logger.error(f"Error processing segment for trace {trace_id}: {str(e)}")
                    continue
        
        # Tạo metrics từ service_metrics và url_metrics
        metrics = []
        metrics.extend(service_metrics_generator.generate(service_metrics))
        metrics.extend(url_metrics_generator.generate(url_metrics))
        metrics.extend(dependency_metrics_generator.generate(service_metrics))
        
        return metrics


class ServiceMetricsGenerator:
    """
    Tạo metrics liên quan đến services
    """
    def __init__(self, counter_values):
        self.counter_values = counter_values
    
    def generate(self, service_metrics):
        """
        Tạo metrics từ service metrics collectors
        Focus on collecting raw data for Prometheus/Grafana calculations
        """
        metrics = []
        
        for service_name, data in service_metrics.items():
            # Tạo counter keys
            service_request_key = f"xray_service_requests_total_{service_name}"
            service_error_key = f"xray_service_errors_total_{service_name}"
            service_fault_key = f"xray_service_faults_total_{service_name}"
            service_throttle_key = f"xray_service_throttles_total_{service_name}"
            
            # Cập nhật counters
            self.counter_values[service_request_key] += data['request_count']
            self.counter_values[service_error_key] += data['error_count']
            self.counter_values[service_fault_key] += data['fault_count']
            self.counter_values[service_throttle_key] += data['throttle_count']
            
            # Thêm counter metrics (nguyên liệu thô cho Prometheus)
            metrics.append({
                'name': 'xray_service_requests_total',
                'labels': {'service': service_name},
                'value': self.counter_values[service_request_key],
                'type': 'counter'
            })
            
            metrics.append({
                'name': 'xray_service_errors_total',
                'labels': {'service': service_name},
                'value': self.counter_values[service_error_key],
                'type': 'counter'
            })
            
            metrics.append({
                'name': 'xray_service_faults_total',
                'labels': {'service': service_name},
                'value': self.counter_values[service_fault_key],
                'type': 'counter'
            })
            
            metrics.append({
                'name': 'xray_service_throttles_total',
                'labels': {'service': service_name},
                'value': self.counter_values[service_throttle_key],
                'type': 'counter'
            })
            
            # Latency observations - raw data for Prometheus/Grafana calculations
            if data['latencies']:
                # Tính toán tổng và số lượng
                latency_sum = sum(data['latencies'])
                latency_count = len(data['latencies'])
                
                # Lưu trữ giá trị vào counter_values - THÊM DÒNG NÀY
                self.counter_values[f'xray_service_latency_sum_ms_{service_name}'] = latency_sum
                self.counter_values[f'xray_service_latency_count_{service_name}'] = latency_count
                
                # Cung cấp raw latency data
                for latency in data['latencies']:
                    metrics.append({
                        'name': 'xray_service_latency_ms',
                        'labels': {'service': service_name},
                        'value': latency,
                        'type': 'gauge'
                    })
                
                # Cũng cung cấp giá trị tổng và số lượng để thuận tiện
                metrics.append({
                    'name': 'xray_service_latency_sum_ms',
                    'labels': {'service': service_name},
                    'value': latency_sum,
                    'type': 'gauge'
                })
                
                metrics.append({
                    'name': 'xray_service_latency_count',
                    'labels': {'service': service_name},
                    'value': latency_count,
                    'type': 'gauge'
                })
            
            # Status code distribution
            for status, count in data['status_codes'].items():
                # Counter key
                status_key = f"xray_service_status_total_{service_name}_{status}"
                self.counter_values[status_key] += count
                
                metrics.append({
                    'name': 'xray_service_status_total',
                    'labels': {'service': service_name, 'status_code': status},
                    'value': self.counter_values[status_key],
                    'type': 'counter'
                })
            
            # HTTP method distribution
            for method, count in data['methods'].items():
                # Counter key
                method_key = f"xray_service_method_total_{service_name}_{method}"
                self.counter_values[method_key] += count
                
                metrics.append({
                    'name': 'xray_service_method_total',
                    'labels': {'service': service_name, 'method': method},
                    'value': self.counter_values[method_key],
                    'type': 'counter'
                })
            
            # Client IP distribution (top 10)
            top_ips = sorted(data['client_ips'].items(), key=lambda x: x[1], reverse=True)[:10]
            for client_ip, count in top_ips:
                # Counter key
                ip_key = f"xray_service_client_ip_total_{service_name}_{client_ip}"
                self.counter_values[ip_key] += count
                
                metrics.append({
                    'name': 'xray_service_client_ip_total',
                    'labels': {'service': service_name, 'client_ip': client_ip},
                    'value': self.counter_values[ip_key],
                    'type': 'counter'
                })
            
            # Payload size metrics - raw data
            if data['request_sizes']:
                for size in data['request_sizes']:
                    metrics.append({
                        'name': 'xray_service_request_size_bytes',
                        'labels': {'service': service_name},
                        'value': size,
                        'type': 'gauge'
                    })
            
            if data['response_sizes']:
                for size in data['response_sizes']:
                    metrics.append({
                        'name': 'xray_service_response_size_bytes',
                        'labels': {'service': service_name},
                        'value': size,
                        'type': 'gauge'
                    })
        
        return metrics


class UrlMetricsGenerator:
    """
    Tạo metrics liên quan đến URLs
    """
    def __init__(self, counter_values):
        self.counter_values = counter_values
    
    def generate(self, url_metrics):
        """
        Tạo metrics từ URL metrics collectors
        """
        metrics = []
        
        for url, data in url_metrics.items():
            # Tạo counter keys
            url_request_key = f"xray_url_requests_total_{url}"
            url_error_key = f"xray_url_errors_total_{url}"
            
            # Cập nhật counters
            self.counter_values[url_request_key] += data['request_count']
            self.counter_values[url_error_key] += data['error_count']
            
            # Thêm counter metrics - Global URL metrics (không phân theo service)
            metrics.append({
                'name': 'xray_url_requests_total',
                'labels': {'url': url},
                'value': self.counter_values[url_request_key],
                'type': 'counter'
            })
            
            metrics.append({
                'name': 'xray_url_errors_total',
                'labels': {'url': url},
                'value': self.counter_values[url_error_key],
                'type': 'counter'
            })
            
            # Thêm URL requests/errors phân theo service
            for service, count in data['services'].items():
                service_url_request_key = f"xray_url_service_requests_total_{url}_{service}"
                self.counter_values[service_url_request_key] += count
                
                metrics.append({
                    'name': 'xray_url_service_requests_total',
                    'labels': {'url': url, 'service': service},
                    'value': self.counter_values[service_url_request_key],
                    'type': 'counter'
                })
            
            # Latency raw data for Prometheus calculations
            if data['latencies']:
                # Điều chỉnh URL metrics thu thập để phân tách theo service
                # Lưu trữ latency theo service và URL
                latencies_by_service = defaultdict(list)
                
                # Thu thập latency theo service
                for service in data['services'].keys():
                    # Lấy mẫu latency từ service nếu có
                    # Trong thực tế, đây là ước lượng vì chúng ta không có thông tin chi tiết về từng request
                    # Tốt nhất là thu thập trực tiếp từ X-Ray trong hàm process_trace_data
                    for latency in data['latencies']:
                        latencies_by_service[service].append(latency)
                
                # Global URL latency
                for latency in data['latencies']:
                    metrics.append({
                        'name': 'xray_url_latency_ms',
                        'labels': {'url': url},
                        'value': latency,
                        'type': 'gauge'
                    })
                
                # Tổng và số lượng cho tính trung bình trong Prometheus
                metrics.append({
                    'name': 'xray_url_latency_sum_ms',
                    'labels': {'url': url},
                    'value': sum(data['latencies']),
                    'type': 'gauge'
                })
                
                metrics.append({
                    'name': 'xray_url_latency_count',
                    'labels': {'url': url},
                    'value': len(data['latencies']),
                    'type': 'gauge'
                })
                
                # Thêm latency theo service và URL
                for service, service_latencies in latencies_by_service.items():
                    if service_latencies:
                        # Thêm latency sum và count cho Prometheus
                        metrics.append({
                            'name': 'xray_url_service_latency_sum_ms',
                            'labels': {'url': url, 'service': service},
                            'value': sum(service_latencies),
                            'type': 'gauge'
                        })
                        
                        metrics.append({
                            'name': 'xray_url_service_latency_count',
                            'labels': {'url': url, 'service': service},
                            'value': len(service_latencies),
                            'type': 'gauge'
                        })
            
            # Service distribution
            for service, count in data['services'].items():
                # Counter key
                service_key = f"xray_url_service_total_{url}_{service}"
                self.counter_values[service_key] += count
                
                # Track services handling this URL
                metrics.append({
                    'name': 'xray_url_service_total',
                    'labels': {'url': url, 'service': service},
                    'value': self.counter_values[service_key],
                    'type': 'counter'
                })
                
                # Estimate error count by service for this URL
                # Ước tính số lỗi theo service dựa trên tỷ lệ requests
                if data['error_count'] > 0 and data['request_count'] > 0:
                    service_ratio = count / data['request_count']
                    estimated_errors = int(data['error_count'] * service_ratio)
                    if estimated_errors > 0:
                        service_error_key = f"xray_url_service_errors_total_{url}_{service}"
                        self.counter_values[service_error_key] += estimated_errors
                        
                        metrics.append({
                            'name': 'xray_url_service_errors_total',
                            'labels': {'url': url, 'service': service},
                            'value': self.counter_values[service_error_key],
                            'type': 'counter'
                        })


            # HTTP method distribution
            for method, count in data['methods'].items():
                # Counter key (global)
                method_key = f"xray_url_method_total_{url}_{method}"
                self.counter_values[method_key] += count
                
                # Global method metric
                metrics.append({
                    'name': 'xray_url_method_total',
                    'labels': {'url': url, 'method': method},
                    'value': self.counter_values[method_key],
                    'type': 'counter'
                })
                
                # Method by service - ước tính dựa trên tỷ lệ service
                for service, service_count in data['services'].items():
                    service_ratio = service_count / data['request_count'] if data['request_count'] > 0 else 0
                    estimated_method_count = int(count * service_ratio)
                    
                    if estimated_method_count > 0:
                        service_method_key = f"xray_url_service_method_total_{url}_{service}_{method}"
                        self.counter_values[service_method_key] += estimated_method_count
                        
                        metrics.append({
                            'name': 'xray_url_service_method_total',
                            'labels': {'url': url, 'service': service, 'method': method},
                            'value': self.counter_values[service_method_key],
                            'type': 'counter'
                        })

            # Status code distribution
            for status, count in data['status_codes'].items():
                # Counter key (global)
                status_key = f"xray_url_status_total_{url}_{status}"
                self.counter_values[status_key] += count
                
                # Global status code metric
                metrics.append({
                    'name': 'xray_url_status_total',
                    'labels': {'url': url, 'status_code': status},
                    'value': self.counter_values[status_key],
                    'type': 'counter'
                })
                
                # Status code by service - ước tính dựa trên tỷ lệ service
                for service, service_count in data['services'].items():
                    service_ratio = service_count / data['request_count'] if data['request_count'] > 0 else 0
                    estimated_status_count = int(count * service_ratio)
                    
                    if estimated_status_count > 0:
                        service_status_key = f"xray_url_service_status_total_{url}_{service}_{status}"
                        self.counter_values[service_status_key] += estimated_status_count
                        
                        metrics.append({
                            'name': 'xray_url_service_status_total',
                            'labels': {'url': url, 'service': service, 'status_code': status},
                            'value': self.counter_values[service_status_key],
                            'type': 'counter'
                        })
            
            # HTTP method distribution
            for method, count in data['methods'].items():
                # Counter key
                method_key = f"xray_url_method_total_{url}_{method}"
                self.counter_values[method_key] += count
                
                metrics.append({
                    'name': 'xray_url_method_total',
                    'labels': {'url': url, 'method': method},
                    'value': self.counter_values[method_key],
                    'type': 'counter'
                })
        
        return metrics


class DependencyMetricsGenerator:
    """
    Tạo metrics liên quan đến service dependencies
    """
    def __init__(self, counter_values):
        self.counter_values = counter_values
    
    def generate(self, service_metrics):
        """
        Tạo metrics về service dependencies
        """
        metrics = []
        
        # Service dependency graph - raw data
        for service_name, data in service_metrics.items():
            for downstream, count in data['downstream_calls'].items():
                # Counter key
                dependency_key = f"xray_service_dependency_total_{service_name}_{downstream}"
                self.counter_values[dependency_key] += count
                
                metrics.append({
                    'name': 'xray_service_dependency_total',
                    'labels': {'source': service_name, 'target': downstream},
                    'value': self.counter_values[dependency_key],
                    'type': 'counter'
                })
        
        return metrics


class MetricsFormatter:
    """
    Format metrics cho Prometheus
    """
    def format_metrics_for_prometheus(self, metrics):
        """
        Chuyển đổi metrics thành định dạng Prometheus
        """
        # Nhóm metrics theo tên để xuất hiệu quả hơn
        metrics_by_name_and_type = {}
        for metric in metrics:
            name = metric['name']
            metric_type = metric.get('type', 'gauge')
            key = (name, metric_type)

            if key not in metrics_by_name_and_type:
                metrics_by_name_and_type[key] = []

            metrics_by_name_and_type[key].append(metric)

        prometheus_data = []

        # Chuyển đổi metrics sang định dạng Prometheus
        for (metric_name, metric_type), metric_items in metrics_by_name_and_type.items():
            # Thêm thông tin kiểu metric (gauge hoặc counter)
            prometheus_data.append(f"# TYPE {metric_name} {metric_type}")

            if metric_name == 'xray_url_service_total':
                prometheus_data.append(f"# HELP {metric_name} Total count of requests to URLs handled by specific services")
            elif metric_name == 'xray_url_service_requests_total':
                prometheus_data.append(f"# HELP {metric_name} Total count of requests to URLs handled by specific services (detailed)")
            elif metric_name == 'xray_url_service_errors_total':
                prometheus_data.append(f"# HELP {metric_name} Total count of errors for URLs handled by specific services")
            elif metric_name == 'xray_url_service_latency_sum_ms':
                prometheus_data.append(f"# HELP {metric_name} Sum of latencies for URLs handled by specific services")
            elif metric_name == 'xray_url_service_latency_count':
                prometheus_data.append(f"# HELP {metric_name} Count of latency observations for URLs handled by specific services")
            elif metric_name == 'xray_url_service_status_total':
                prometheus_data.append(f"# HELP {metric_name} Total count of HTTP status codes for URLs handled by specific services")
            elif metric_name == 'xray_url_service_method_total':
                prometheus_data.append(f"# HELP {metric_name} Total count of HTTP methods for URLs handled by specific services")
            elif metric_name.endswith('_total'):
                prometheus_data.append(f"# HELP {metric_name} Total count of {metric_name[:-6]} from X-Ray traces")
            elif metric_name.endswith('_ms'):
                prometheus_data.append(f"# HELP {metric_name} Duration in milliseconds from X-Ray traces")
            elif metric_name.endswith('_bytes'):
                prometheus_data.append(f"# HELP {metric_name} Size in bytes from X-Ray traces")

            # Thêm giá trị metric
            for item in metric_items:
                # Format labels
                labels = item['labels']
                labels_str = ','.join([f'{k}="{v}"' for k, v in labels.items() if v])

                if labels_str:
                    prometheus_data.append(f'{metric_name}{{{labels_str}}} {item["value"]}')
                else:
                    prometheus_data.append(f'{metric_name} {item["value"]}')

        # Thêm timestamp hiện tại
        timestamp = str(int(datetime.now().timestamp() * 1000))
        prometheus_data.append(f"# TIMESTAMP {timestamp}")

        # Nối tất cả dòng với newlines
        return '\n'.join(prometheus_data)
