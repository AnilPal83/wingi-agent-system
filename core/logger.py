import logging
import sys

# Custom formatter for "neat and clean" output with emojis
class WingiFormatter(logging.Formatter):
    def format(self, record):
        prefix = ""
        if record.levelno == logging.INFO:
            prefix = "✨ "
        elif record.levelno == logging.WARNING:
            prefix = "⚠️  "
        elif record.levelno == logging.ERROR:
            prefix = "❌ "
        elif record.levelno == logging.DEBUG:
            prefix = "🔍 "
            
        record.msg = f"{prefix}{record.msg}"
        return super().format(record)

def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = WingiFormatter('%(asctime)s | %(name)s | %(message)s', datefmt='%H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger