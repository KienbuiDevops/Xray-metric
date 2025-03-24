# AWS X-Ray Prometheus Exporter

Công cụ thu thập dữ liệu trace từ AWS X-Ray và hiển thị dưới dạng Prometheus metrics để giám sát và theo dõi hiệu suất ứng dụng.

## Tính năng

- Thu thập dữ liệu từ AWS X-Ray API trong thời gian thực
- Nhóm metrics theo services và URLs
- Tránh trùng lặp dữ liệu giữa các lần thu thập
- Hỗ trợ counter metrics tích lũy và gauge metrics
- Cung cấp endpoint `/metrics` cho Prometheus scrape
- Dễ dàng cài đặt và cấu hình

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

- `--port`: Port để lắng nghe (mặc định: 9092)
- `--region`: AWS Region (nếu không chỉ định sẽ dùng region từ AWS config)
- `--profile`: AWS Profile (nếu không chỉ định sẽ dùng profile từ AWS config)
- `--time-window`: Khoảng thời gian (phút) để thu thập dữ liệu (mặc định: 1)
- `--data-dir`: Thư mục để lưu trạng thái (mặc định: ./data/)
- `--log-level`: Cấp độ log (DEBUG, INFO, WARNING, ERROR) (mặc định: INFO)

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

### Xem metrics

- Prometheus metrics: http://localhost:9092/metrics
- Trang thông tin: http://localhost:9092/
- Health check: http://localhost:9092/health

## Metrics

### Service-based Metrics

- `xray_service_requests_total` (counter): Tổng số requests theo service
- `xray_service_errors_total` (counter): Tổng số lỗi theo service
- `xray_service_faults_total` (counter): Tổng số fault theo service
- `xray_service_throttles_total` (counter): Tổng số throttle theo service
- `xray_service_error_rate` (gauge): Tỷ lệ lỗi theo service
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
- `xray_url_latency_p50_ms` (gauge): Thời gian phản hồi p50 theo URL
- `xray_url_latency_p90_ms` (gauge): Thời gian phản hồi p90 theo URL
- `xray_url_latency_p99_ms` (gauge): Thời gian phản hồi p99 theo URL

### Service Dependency Metrics

- `xray_service_dependency_total` (counter): Số lượng gọi giữa các services
- `xray_service_dependency_health` (gauge): Mức độ health của service dependency

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
├── install.sh             # Script cài đặt
└── data/                  # Thư mục lưu trữ trạng thái
    ├── last_timestamp.txt
    ├── processed_trace_ids.pickle
    └── counter_values.pickle
```

## License

MIT