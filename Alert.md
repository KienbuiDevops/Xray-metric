# Cấu hình Alert Rules cho Hệ thống Giám sát X-Ray

Các alert rules sau đây được thiết kế để giám sát hiệu suất hệ thống dựa trên dữ liệu X-Ray và thông báo khi có sự cố. Bạn có thể cài đặt các alert rules này trong Grafana hoặc Prometheus Alertmanager.

## 1. High Error Rate Alert

Kích hoạt khi tỷ lệ lỗi của một service vượt quá ngưỡng cho phép trong khoảng thời gian cụ thể.

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

## 2. Latency Spike Alert

Kích hoạt khi thời gian phản hồi trung bình của một service tăng đột biến.

```yaml
alert: HighServiceLatency
expr: sum(rate(xray_service_latency_sum_ms[5m])) by (service) / sum(rate(xray_service_latency_count[5m])) by (service) > 1000
for: 2m
labels:
  severity: warning
annotations:
  summary: "High latency on {{ $labels.service }}"
  description: "Service {{ $labels.service }} has high latency: {{ $value | printf \"%.2f\" }}ms (threshold: 1000ms)"
```

## 3. Service Fault Rate Alert

Kích hoạt khi tỷ lệ faults (lỗi server 5xx) của một service vượt quá ngưỡng cho phép.

```yaml
alert: HighServiceFaultRate
expr: sum(rate(xray_service_faults_total[5m])) by (service) / sum(rate(xray_service_requests_total[5m])) by (service) * 100 > 2
for: 2m
labels:
  severity: critical
annotations:
  summary: "High fault rate on {{ $labels.service }}"
  description: "Service {{ $labels.service }} has high fault rate: {{ $value | printf \"%.2f\" }}% (threshold: 2%)"
```

## 4. Traffic Drop Alert

Kích hoạt khi lưu lượng của một service giảm đột ngột so với khoảng thời gian trước đó.

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

## 5. URL Error Rate Alert

Kích hoạt khi tỷ lệ lỗi của một URL cụ thể vượt quá ngưỡng cho phép.

```yaml
alert: HighURLErrorRate
expr: sum(rate(xray_url_errors_total[5m])) by (url) / sum(rate(xray_url_requests_total[5m])) by (url) * 100 > 10
for: 2m
labels:
  severity: warning
annotations:
  summary: "High error rate on URL {{ $labels.url }}"
  description: "URL {{ $labels.url }} has high error rate: {{ $value | printf \"%.2f\" }}% (threshold: 10%)"
```

## 6. Service Dependency Health Alert

Kích hoạt khi sức khỏe của một service dependency giảm xuống dưới ngưỡng.

```yaml
alert: ServiceDependencyProblem
expr: sum(rate(xray_service_dependency_total[5m])) by (source, target) > 0 and (sum(rate(xray_service_errors_total{service=~"$target"}[5m])) / sum(rate(xray_service_requests_total{service=~"$target"}[5m]))) * 100 > 10
for: 2m
labels:
  severity: warning
annotations:
  summary: "Dependency issue: {{ $labels.source }} -> {{ $labels.target }}"
  description: "Service {{ $labels.source }} depends on {{ $labels.target }} which has high error rate: {{ $value | printf \"%.2f\" }}% (threshold: 10%)"
```

## 7. No Traffic Alert

Kích hoạt khi một service không nhận được bất kỳ traffic nào trong khoảng thời gian cụ thể.

```yaml
alert: NoServiceTraffic
expr: sum(rate(xray_service_requests_total[15m])) by (service) == 0
for: 15m
labels:
  severity: warning
annotations:
  summary: "No traffic on {{ $labels.service }}"
  description: "Service {{ $labels.service }} has not received any requests in the last 15 minutes"
```

## 8. Throttling Alert

Kích hoạt khi một service bị throttle nhiều lần.

```yaml
alert: ServiceThrottling
expr: sum(rate(xray_service_throttles_total[5m])) by (service) > 1
for: 2m
labels:
  severity: warning
annotations:
  summary: "Throttling on {{ $labels.service }}"
  description: "Service {{ $labels.service }} is being throttled: {{ $value | printf \"%.2f\" }} requests/sec"
```

## Cài đặt các Alert Rules

1. Lưu các alert rules trên vào một file YAML, ví dụ `xray-alerts.yml`
2. Thêm file này vào cấu hình Prometheus hoặc Alertmanager
3. Khai báo trong Prometheus configuration:

```yaml
rule_files:
  - "xray-alerts.yml"
```

4. Khởi động lại Prometheus và Alertmanager để áp dụng cấu hình mới
5. Trong Grafana, bạn có thể thiết lập một Alert dashboard để theo dõi các alerts đang hoạt động
