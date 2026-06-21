import logging
import os
from logging.handlers import RotatingFileHandler
from threading import Lock
from common.handler import reportHandler

class URLFilter(logging.Filter):
    def filter(self, record):
        return "llm-proxy.us-east-2.int.infra.intelligence.webex.com" not in record.getMessage()

class SequenceNumberFormatter(logging.Formatter):
    sequence_number = 0
    lock = Lock()

    def format(self, record):
        with self.lock:
            if not hasattr(record, 'sequence_number_applied'):
                SequenceNumberFormatter.sequence_number += 1
                record.msg = f" {SequenceNumberFormatter.sequence_number}  {record.msg}"
                record.sequence_number_applied = True
        return super().format(record)

def setup_logging(log_file_path=r'src\report\result\fcc-report.md'):
    
    log_format = '%(message)s'
    
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    
    file_handler = RotatingFileHandler(log_file_path, maxBytes=5*1024*1024, backupCount=2, encoding='utf-8')
    
    formatter = SequenceNumberFormatter(log_format)
    file_handler.setFormatter(formatter)
    
    url_filter = URLFilter()
    file_handler.addFilter(url_filter)
    logger = logging.getLogger("reporter")
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)

def generate_logs():
    logging.info("This is an info message.")
    logging.warning("This is a warning message.")
    logging.error("This is an error message.")

if __name__ == '__main__':
    setup_logging()
    generate_logs()