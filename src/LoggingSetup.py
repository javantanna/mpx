import logging
import sys
from typing import Optional

# LOGGING SETUP
class Colors:
    CYAN = '\033[36m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RED = '\033[31m'
    MAGENTA = '\033[35m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

class ColoredFormatter(logging.Formatter):
    """Colored console output for better readability"""
    COLORS={
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'

    }

    def format(self,record):
        color =self.COLORS.get(record.levelname,self.COLORS['RESET'])
        record.levelname=f"{color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)

def setup_logging(level:str="INFO",log_file:Optional[str]=None):
    """Configure logging with console and optional file output"""

    logger=logging.getLogger("mp5")
    logger.setLevel(getattr(logging,level))

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging,level))
    console_formatter = ColoredFormatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    if log_file:
        file_handler=logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger
