# AWS X-Ray Prometheus Exporter

Công cụ thu thập dữ liệu trace từ AWS X-Ray và hiển thị dưới dạng Prometheus metrics để giám sát và theo dõi hiệu suất ứng dụng.

## Tính năng

- Thu thập dữ liệu từ AWS X-Ray API trong thời gian thực
- Phân tích dữ liệu trace thành metrics theo services và URLs
- Xử lý thông minh trace trùng lặp và quản lý bộ nhớ hiệu quả
- Hỗ trợ counter metrics tích lũy và gauge metrics
- Cung cấp endpoint `/metrics` chuẩn Prometheus
- Hỗ trợ xử lý dữ liệu song song và retry
- Lưu trữ trạng thái để khôi phục sau khi khởi động lại
- Tích hợp dễ dàng với Grafana dashboards

## Metrics cung cấp

### Service-based Metrics
- `xray_service_requests_total` (counter): Tổng số requests theo service
- `xray_service_errors_total` (counter): Tổng số lỗi theo service
- `xray_service_faults_total` (counter): Tổng số fault theo service
- `xray_service_throttles_total` (counter): Tổng số throttle theo service
- `xray_service_errors_count` (gauge): Số lượng lỗi theo service
- `xray_service_faults_count` (gauge): Số lượng fault theo service
- `xray_service_throttles_count` (gauge): Số lượng throttle theo service
- `xray_service_latency_avg_ms` (gauge): Thời gian phản hồi trung bình theo service
- `xray_service_latency_p50_ms` (gauge): Thời gian phản hồi p50 theo service
- `xray_service_latency_p90_ms` (gauge): Thời gian phản hồi p90 theo service
- `xray_service_latency_p99_ms` (gauge): Thời gian phản hồi p99 theo service
- `xray_service_status_total` (counter): Số lượng status code theo service
- `xray_service_method_total` (counter): Số lượng HTTP method theo service
- `xray_service_client_ip_total` (counter): Số lượng client IP theo service

### URL-based Metrics
- `xray_url_requests_total` (counter): Tổng số requests theo URL
- `xray_url_errors_total` (counter): Tổng số lỗi theo URL
- `xray_url_error_rate` (gauge): Tỷ lệ lỗi theo URL
- `xray_url_latency_avg_ms` (gauge): Thời gian phản hồi trung bình theo URL
- `xray_url_latency_sum_ms` (gauge): Tổng thời gian phản hồi theo URL
- `xray_url_latency_count` (gauge): Số lượng mẫu latency theo URL
- `xray_url_status_total` (counter): Số lượng HTTP status code theo URL
- `xray_url_method_total` (counter): Số lượng HTTP method theo URL

### URL-Service Metrics
- `xray_url_service_total` (counter): Số lượng requests theo URL và service
- `xray_url_service_requests_total` (counter): Số lượng requests chi tiết theo URL và service
- `xray_url_service_errors_total` (counter): Số lượng lỗi theo URL và service
- `xray_url_service_latency_sum_ms` (gauge): Tổng thời gian phản hồi theo URL và service
- `xray_url_service_latency_count` (gauge): Số lượng mẫu latency theo URL và service
- `xray_url_service_status_total` (counter): Số lượng HTTP status code theo URL và service
- `xray_url_service_method_total` (counter): Số lượng HTTP method theo URL và service

### Service Dependency Metrics
- `xray_service_dependency_total` (counter): Số lượng gọi giữa các services
- `xray_service_dependency_health` (gauge): Mức độ health của service dependency

## Cài đặt

### Cài đặt thủ công

1. Clone repository:
   ```bash
   git clone https://github.com/yourusername/xray-prometheus-exporter.git
   cd xray-prometheus-exporter
   ```

2. Cài đặt thư viện phụ thuộc:
   ```bash
   pip install -r requirements.txt
   ```

3. Chạy exporter:
   ```bash
   python main.py --port 9092 --region ap-southeast-1 --time-window 1
   ```

### Cài đặt tự động

Sử dụng script cài đặt:
```bash
chmod +x install.sh
./install.sh
```

Script sẽ:
- Cài đặt các file cần thiết vào `/opt/xray-exporter`
- Cài đặt thư viện phụ thuộc
- Tạo và bật systemd service

## Sử dụng

### Tham số dòng lệnh

| Tham số | Mô tả | Giá trị mặc định |
|---------|-------|-----------------|
| `--port` | Port để lắng nghe | 9092 |
| `--region` | AWS Region | Lấy từ AWS config |
| `--profile` | AWS Profile | Lấy từ AWS config |
| `--time-window` | Khoảng thời gian (phút) thu thập dữ liệu | 1 |
| `--data-dir` | Thư mục lưu trữ trạng thái | ./data/ |
| `--log-level` | Cấp độ log (DEBUG, INFO, WARNING, ERROR) | INFO |
| `--max-traces` | Số lượng trace tối đa xử lý mỗi lần | None (không giới hạn) |
| `--parallel-workers` | Số lượng worker xử lý song song | 20 |
| `--batch-size` | Kích thước batch cho API calls | 5 |
| `--retry-attempts` | Số lần thử lại cho API calls | 3 |
| `--force-full-collection` | Bỏ qua trace IDs đã xử lý trước đó | False |
| `--max-trace-ids` | Số lượng trace ID tối đa lưu trữ | 1,000,000 |
| `--retention-days` | Số ngày giữ lại trace IDs | 30 |
| `--clean-trace-ids` | Làm sạch trace IDs cũ | False |
| `--cleanup-age-hours` | Độ tuổi tối đa (giờ) khi làm sạch trace IDs | 24 |

### Cấu hình Prometheus

Thêm cấu hình sau vào file `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'xray_metrics'
    scrape_interval: 30s
    metrics_path: /metrics
    static_configs:
      - targets: ['localhost:9092']
```

### Truy cập endpoints

- Prometheus metrics: http://localhost:9092/metrics
- Trang thông tin: http://localhost:9092/
- Health check: http://localhost:9092/health

## Grafana Dashboards

### Cấu hình Grafana Dashboard

Bạn có thể import trực tiếp file JSON `grafana.json` vào Grafana hoặc sử dụng các PromQL query sau để tạo dashboard:

#### Tổng quan hệ thống
```
# Tổng số Requests
sum(xray_service_requests_total)

# Tỷ lệ lỗi toàn hệ thống
sum(xray_service_errors_total) / sum(xray_service_requests_total) * 100

# Thời gian phản hồi trung bình
sum(xray_service_latency_sum_ms) / sum(xray_service_latency_count)
```

#### Theo dõi Service
```
# Lưu lượng Request theo Service
sum(rate(xray_service_requests_total[5m])) by (service)

# Tỷ lệ lỗi theo Service
sum(rate(xray_service_errors_total[5m])) by (service) / sum(rate(xray_service_requests_total[5m])) by (service) * 100

# Thời gian phản hồi theo Service
sum(rate(xray_service_latency_sum_ms[5m])) by (service) / sum(rate(xray_service_latency_count[5m])) by (service)
```

#### Phân tích URL/API
```
# Top URLs theo lưu lượng
topk(10, sum by (url) (rate(xray_url_requests_total[5m])))

# Latency trung bình theo URL
sum by (url) (rate(xray_url_latency_sum_ms[5m])) / sum by (url) (rate(xray_url_latency_count[5m]))

# HTTP Status theo URL
sum by (url, status_code) (xray_url_status_total)
```

#### Phụ thuộc Service
```
# Service Dependency
sum by (source, target) (xray_service_dependency_total) > 0
```

## Cấu hình Alert Rules

Bạn có thể sử dụng các alert rules từ file `Alert.md` để cấu hình cảnh báo. Ví dụ:

### High Error Rate Alert
```yaml
alert: HighServiceErrorRate
expr: sum(rate(xray_service_errors_total[5m])) by (service) / sum(rate(xray_service_requests_total[5m])) by (service) * 100 > 5
for: 2m
labels:
  severity: critical
annotations:
  summary: "High error rate on {{ $labels.service }}"
  description: "Service {{ $labels.service }} has high error rate: {{ $value | printf \"%.2f\" }}% (threshold: 5%)"
```

### Traffic Drop Alert
```yaml
alert: ServiceTrafficDrop
expr: (sum(rate(xray_service_requests_total[1h])) by (service) < bool sum(rate(xray_service_requests_total[1h] offset 1d)) by (service) * 0.2) and sum(rate(xray_service_requests_total[1h] offset 1d)) by (service) > 0
for: 10m
labels:
  severity: warning
annotations:
  summary: "Traffic drop on {{ $labels.service }}"
  description: "Service {{ $labels.service }} has significant traffic drop (>80% compared to same time yesterday)"
```

## Cấu trúc thư mục

```
.
├── main.py                # Entry point
├── collector.py           # X-Ray metrics collector
├── processors.py          # Xử lý dữ liệu trace và tạo metrics
├── handlers.py            # HTTP handlers
├── storage.py             # Lưu trữ và khôi phục trạng thái
├── __init__.py            # Package initialization
├── requirements.txt       # Thư viện phụ thuộc
├── Alert.md               # Mẫu alert rules
├── metric.md              # Tài liệu queries Prometheus
├── grafana.json           # Grafana dashboard template
└── data/                  # Thư mục lưu trữ trạng thái
    ├── last_timestamp.txt
    ├── processed_trace_ids.pickle
    ├── timed_trace_ids.pickle
    └── counter_values.pickle
```

## Hiệu suất và Tối ưu hóa

- **Xử lý song song**: Sử dụng multiple workers để tăng tốc độ lấy dữ liệu từ X-Ray API
- **Bộ nhớ đệm**: Cache kết quả metrics trong khoảng thời gian ngắn để giảm tải API
- **Quản lý trace IDs**: Giới hạn số lượng trace IDs lưu trữ và tự động xóa các trace IDs cũ
- **Retry mechanism**: Tự động thử lại khi gặp lỗi API
- **Batch processing**: Xử lý trace theo batches để tối ưu bộ nhớ
