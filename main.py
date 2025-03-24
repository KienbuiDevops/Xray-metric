from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all
import time
import logging
import boto3

# Thiết lập logging chi tiết
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logging.getLogger('aws_xray_sdk').setLevel(logging.DEBUG)

# Đặt region cho boto3
session = boto3.session.Session(region_name='ap-southeast-1')
xray_client = session.client('xray')

# Cấu hình X-Ray
xray_recorder.configure(
    service='my-python-service',
    daemon_address='xray-deamon-test.gotit.vn:443',
    context_missing='LOG_ERROR'
)

patch_all()

# Bắt đầu ghi trace
@xray_recorder.capture('my_python_service_operation')
def do_work():
    xray_recorder.put_annotation('env', 'test')
    xray_recorder.put_metadata('description', 'Test trace from Python')
    logger.info("Doing some work...")
    time.sleep(1)
    logger.info("Work completed!")

if __name__ == "__main__":
    logger.info("Starting X-Ray tracing...")
    logger.info("X-Ray configured with daemon address: 172.21.1.63:2000")
    
    with xray_recorder.in_segment('xray') as segment:
        if segment:
            segment.service = {'name': 'my-python-service', 'version': '1.0'}  # Thêm thông tin service
            segment.put_annotation('step', 'start')
            logger.info(f"Segment ID: {segment.id}")
            do_work()
            segment.put_annotation('step', 'end')
        else:
            logger.error("Failed to create segment!")
    
    logger.info("Trace sent to X-Ray daemon!")