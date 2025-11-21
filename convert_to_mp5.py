import sys
import os
import json
import logging
import hashlib
# import click
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile
import shutil
from MP5Config import MP5Config
from LoggingSetup import ColoredFormatter,setup_logging
from Exceptions import MP5Error,ValidationError,ValidationError,EncodingError,DecodingError,IntegrityError
from HashUtil import HashUtils
from CompressionUtils import CompressionUtils

try:
    from mutagen.mp4 import MP4
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    print("Warning: mutagen not installed. Atom layer will be disabled.")
    
class LogLevel(str,Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


logger=logging.getLogger("mp5")










    


