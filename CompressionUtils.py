import zlib
import base64
import json
from typing import Dict


class CompressionUtils:
    """Data compression utilities"""

    @staticmethod
    def compress(data: bytes, level: int = 6) -> bytes:
        """Compress data using zlib"""
        return zlib.compress(data, level=level)

    @staticmethod
    def decompress(data: bytes) -> bytes:
        """Decompress zlib data"""
        return zlib.decompress(data)

    @staticmethod
    def compress_json(data: Dict, level: int = 6)->bytes:
        """Compress JSON data"""
        json_str = json.dumps(data,separators=(',',':'), sort_keys=True)
        json_bytes = json_str.encode('utf-8')
        compressed = zlib.compress(json_bytes, level=level)
        return base64.b64encode(compressed)

    @staticmethod
    def decompress_json(data: bytes)->Dict:
        """Decompress JSON data"""
        compressed=base64.b64decode(data)
        json_bytes = zlib.decompress(compressed)
        json_str = json_bytes.decode('utf-8')
        return json.loads(json_str)