# Cấu trúc Dashboard và Prometheus Queries

## 1. Tổng quan hệ thống

Dashboard được chia thành nhiều trang để giám sát toàn diện hệ thống:

### Trang 1: Service Overview

Hiển thị các chỉ số tổng quan quan trọng về hệ thống:

| Panel | Mô tả | PromQL Query |
|-------|-------|-------------|
| Tổng số Requests | Hiển thị tổng số requests xử lý bởi tất cả services | `sum(xray_service_requests_total)` |
| Tỷ lệ lỗi toàn hệ thống | Hiển thị phần trăm requests gặp lỗi | `sum(xray_service_errors_total) / sum(xray_service_requests_total) * 100` |
| Thời gian phản hồi trung bình | Hiển thị thời gian phản hồi trung bình của tất cả services | `sum(xray_service_latency_sum_ms) / sum(xray_service_latency_count)` |
| Số lượng service hoạt động | Số lượng service đang được giám sát | `count(count by (service) (xray_service_requests_total))` |
| Lưu lượng Request theo Service | Biểu đồ hiển thị lưu lượng request theo service theo thời gian | `sum(rate(xray_service_requests_total[5m])) by (service)` |
| Tỷ lệ lỗi theo Service | Biểu đồ hiển thị tỷ lệ lỗi theo service theo thời gian | `sum(rate(xray_service_errors_total[5m])) by (service) / sum(rate(xray_service_requests_total[5m])) by (service) * 100` |
| Faults và Throttles theo Service | Biểu đồ hiển thị số lượng faults và throttles theo service | `sum(rate(xray_service_faults_total[5m])) by (service)` và `sum(rate(xray_service_throttles_total[5m])) by (service)` |
| Top 5 Service với lưu lượng cao nhất | Biểu đồ hiển thị top 5 service có lưu lượng cao nhất | `topk(5, sum(rate(xray_service_requests_total[5m])) by (service))` |

### Trang 2: Service Health

Giám sát sức khỏe chi tiết của từng service:

| Panel | Mô tả | PromQL Query |
|-------|-------|-------------|
| Service Health Status | Bảng hiển thị trạng thái sức khỏe của từng service | Kết hợp nhiều query: <br>`sum by (service) (rate(xray_service_requests_total[5m]))` <br>`sum by (service) (rate(xray_service_errors_total[5m])) / sum by (service) (rate(xray_service_requests_total[5m])) * 100` <br>`sum by (service) (rate(xray_service_latency_sum_ms[5m])) / sum by (service) (rate(xray_service_latency_count[5m]))` |
| Tỷ lệ lỗi theo Service (%) | Biểu đồ thanh hiển thị tỷ lệ lỗi theo service | `sum by (service) (rate(xray_service_errors_total[5m])) / sum by (service) (rate(xray_service_requests_total[5m])) * 100` |
| Thời gian phản hồi trung bình theo Service | Biểu đồ gauge hiển thị thời gian phản hồi trung bình theo service | `sum by (service) (rate(xray_service_latency_sum_ms[5m])) / sum by (service) (rate(xray_service_latency_count[5m]))` |

### Trang 3: URL/API Endpoints

Theo dõi hiệu suất các endpoint API:

| Panel | Mô tả | PromQL Query |
|-------|-------|-------------|
| Top URLs (by Request Volume) | Bảng hiển thị các URL hàng đầu theo lượng request | Kết hợp các query: <br>`topk(15, sum by (url) (rate(xray_url_requests_total[5m])))` <br>`sum by (url) (rate(xray_url_errors_total[5m])) / sum by (url) (rate(xray_url_requests_total[5m])) * 100` <br>`sum by (url) (rate(xray_url_latency_sum_ms[5m])) / sum by (url) (rate(xray_url_latency_count[5m]))` |
| URL Latency Heatmap | Biểu đồ heatmap hiển thị độ trễ theo URL | `sum by (url) (rate(xray_url_latency_sum_ms[5m])) / sum by (url) (rate(xray_url_latency_count[5m]))` |
| Top URL-Service Combinations | Bảng hiển thị các kết hợp URL-Service hàng đầu | Kết hợp các query: <br>`topk(10, sum by (url, service) (rate(xray_url_service_requests_total[5m])))` <br>`sum by (url, service) (rate(xray_url_service_errors_total[5m]))` <br>`sum by (url, service) (rate(xray_url_service_latency_sum_ms[5m])) / sum by (url, service) (rate(xray_url_service_latency_count[5m]))` |

### Trang 4: Service Dependencies

Phân tích phụ thuộc giữa các service:

| Panel | Mô tả | PromQL Query |
|-------|-------|-------------|
| Top Service Dependencies | Bảng hiển thị các phụ thuộc service hàng đầu | `topk(20, sum by (source, target) (rate(xray_service_dependency_total[5m])))` |
| Top 5 Service Dependencies Over Time | Biểu đồ hiển thị top 5 phụ thuộc service theo thời gian | `topk(5, sum by (source, target) (rate(xray_service_dependency_total[5m])))` |
| Service Dependency Graph | Biểu đồ mạng lưới hiển thị quan hệ giữa các service | `sum by (source, target) (xray_service_dependency_total) > 0` |

### Trang 5: Client Analysis

Phân tích thông tin về client:

| Panel | Mô tả | PromQL Query |
|-------|-------|-------------|
| HTTP Methods Distribution | Biểu đồ tròn hiển thị phân bố HTTP methods | `topk(5, sum(xray_service_method_total) by (method))` |
| HTTP Status Codes Distribution | Biểu đồ tròn hiển thị phân bố HTTP status codes | `topk(10, sum(xray_service_status_total) by (status_code))` |
| Top Client IPs | Bảng hiển thị các client IP hàng đầu | `topk(10, sum by (client_ip) (xray_service_client_ip_total))` |
