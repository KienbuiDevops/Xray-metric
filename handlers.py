"""
AWS X-Ray Prometheus Exporter - Handlers Module
HTTP handlers for Prometheus exporter
"""
import logging
from http.server import BaseHTTPRequestHandler

logger = logging.getLogger('xray-exporter.handlers')

class PrometheusExporterHandler(BaseHTTPRequestHandler):
    """
    HTTP Handler cho Prometheus exporter
    """
    def __init__(self, collector, *args, **kwargs):
        self.collector = collector
        # Không thể gọi __init__ trực tiếp do BaseHTTPRequestHandler sử dụng một cách khởi tạo đặc biệt
        # __init__ sẽ được gọi bởi HTTPServer
    
    def do_GET(self):
        """
        Xử lý GET request
        """
        if self.path == '/metrics':
            # Lấy metrics từ collector
            metrics = self.collector.get_metrics()
            metrics_text = self.collector.format_metrics_for_prometheus(metrics)
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(metrics_text.encode('utf-8'))
            
            logger.debug(f"Served metrics request with {len(metrics)} metrics")
        
        elif self.path == '/':
            # Hiển thị trang chủ đơn giản
            html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>X-Ray Prometheus Exporter</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                        h1 { color: #333; }
                        ul { list-style-type: square; }
                        .endpoint { font-family: monospace; background: #f4f4f4; padding: 2px 5px; }
                        .metrics-list { max-height: 300px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; }
                        .metric-type { color: #555; font-size: 0.9em; }
                    </style>
                </head>
                <body>
                    <h1>X-Ray Prometheus Exporter</h1>
                    <p>This exporter collects AWS X-Ray trace data and exposes it as Prometheus metrics.</p>
                    
                    <h2>Endpoints:</h2>
                    <ul>
                        <li><a href="/metrics" class="endpoint">/metrics</a> - Prometheus metrics endpoint</li>
                    </ul>
                    
                    <h2>Available Metrics:</h2>
                    <div class="metrics-list">
                        <!-- Thay đổi phần hiển thị metrics trong trang chủ -->
                    <ul>
                        <li><code>xray_service_requests_total</code> <span class="metric-type">(counter)</span> - Total number of requests by service</li>
                        <li><code>xray_service_errors_total</code> <span class="metric-type">(counter)</span> - Total number of errors by service</li>
                        <li><code>xray_service_faults_total</code> <span class="metric-type">(counter)</span> - Total number of faults by service</li>
                        <li><code>xray_service_throttles_total</code> <span class="metric-type">(counter)</span> - Total number of throttles by service</li>
                        <li><code>xray_service_errors_count</code> <span class="metric-type">(gauge)</span> - Count of error observations by service</li>
                        <li><code>xray_service_faults_count</code> <span class="metric-type">(gauge)</span> - Count of fault observations by service</li>
                        <li><code>xray_service_throttles_count</code> <span class="metric-type">(gauge)</span> - Count of throttle observations by service</li>
                        <li><code>xray_service_error_rate</code> <span class="metric-type">(gauge)</span> - Error rate by service</li>
                        <li><code>xray_service_latency_avg_ms</code> <span class="metric-type">(gauge)</span> - Average latency by service</li>
                        <li><code>xray_service_latency_p50_ms</code> <span class="metric-type">(gauge)</span> - 50th percentile latency by service</li>
                        <li><code>xray_service_latency_p90_ms</code> <span class="metric-type">(gauge)</span> - 90th percentile latency by service</li>
                        <li><code>xray_service_latency_p99_ms</code> <span class="metric-type">(gauge)</span> - 99th percentile latency by service</li>
                        <li><code>xray_url_requests_total</code> <span class="metric-type">(counter)</span> - Total number of requests by URL</li>
                        <li><code>xray_url_errors_total</code> <span class="metric-type">(counter)</span> - Total number of errors by URL</li>
                        <li><code>xray_url_error_rate</code> <span class="metric-type">(gauge)</span> - Error rate by URL</li>
                        <li><code>xray_url_latency_avg_ms</code> <span class="metric-type">(gauge)</span> - Average latency by URL</li>
                        <li><code>xray_url_status_total</code> <span class="metric-type">(counter)</span> - HTTP status codes by URL</li>
                        <li><code>xray_url_method_total</code> <span class="metric-type">(counter)</span> - HTTP methods by URL</li>
                        <li><code>xray_url_service_total</code> <span class="metric-type">(counter)</span> - Total number of requests by URL and service</li>
                        <li><code>xray_url_service_requests_total</code> <span class="metric-type">(counter)</span> - Total number of requests by URL and service (detailed)</li>
                        <li><code>xray_url_service_errors_total</code> <span class="metric-type">(counter)</span> - Total number of errors by URL and service</li>
                        <li><code>xray_url_service_status_total</code> <span class="metric-type">(counter)</span> - HTTP status codes by URL and service</li>
                        <li><code>xray_url_service_method_total</code> <span class="metric-type">(counter)</span> - HTTP methods by URL and service</li>
                        <li><code>xray_service_dependency_total</code> <span class="metric-type">(counter)</span> - Total calls between services</li>
                        <li><code>xray_service_dependency_health</code> <span class="metric-type">(gauge)</span> - Health of service dependency</li>
                    </ul>
                    </div>
                    
                    <h2>Prometheus Configuration Example:</h2>
                    <pre><code>scrape_configs:
  - job_name: 'xray_metrics'
    scrape_interval: 30s
    metrics_path: /metrics
    static_configs:
      - targets: ['localhost:9092']</code></pre>
                </body>
                </html>
            """
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
            
            logger.debug("Served index page")
        
        elif self.path == '/health':
            # Health check endpoint
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
            
            logger.debug("Served health check")
        
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
            
            logger.debug(f"404 Not Found: {self.path}")
    
    def log_message(self, format, *args):
        """Override log_message để sử dụng logger thay vì stderr"""
        logger.debug("%s - - [%s] %s" %
                     (self.address_string(),
                      self.log_date_time_string(),
                      format % args))

def create_handler(collector):
    """
    Tạo handler với collector được truyền vào
    
    :param collector: Đối tượng collector để lấy metrics
    :return: Handler class có gắn collector
    """
    class Handler(PrometheusExporterHandler):
        def __init__(self, *args, **kwargs):
            self.collector = collector
            BaseHTTPRequestHandler.__init__(self, *args, **kwargs)
    
    return Handler
