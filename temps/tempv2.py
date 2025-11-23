"""
MP5 - Enterprise-Grade Video Metadata CLI Tool (MVP Version)
Version: 1.0.0

Production-ready CLI for embedding AI metadata in video files using hybrid steganography.
Designed for enterprise integration with robust error handling, logging, and performance.
"""

import sys
import os
import json
import logging
import hashlib
import zlib
import base64
import click
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

# Try importing optional dependencies
try:
    from mutagen.mp4 import MP4
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    print("Warning: mutagen not installed. Atom layer will be disabled.")

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


# =============================================================================
# CONFIGURATION & CONSTANTS
# =============================================================================

class LogLevel(str, Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class MP5Config:
    """Global configuration for MP5 operations"""
    version: str = "1.0.0"
    atom_tag: str = "©mp5"
    lsb_redundancy: int = 5
    max_metadata_mb: int = 50
    compression_level: int = 6
    hash_algorithm: str = "sha256"
    temp_dir: str = "/tmp/mp5"
    max_workers: int = 4
    chunk_size: int = 8192
    supported_formats: List[str] = None
    
    def __post_init__(self):
        if self.supported_formats is None:
            self.supported_formats = ['.mp4', '.mov', '.m4v', '.avi']
    
    @classmethod
    def from_file(cls, config_path: str) -> 'MP5Config':
        """Load configuration from YAML or JSON file"""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(path, 'r') as f:
            if path.suffix in ['.yaml', '.yml'] and YAML_AVAILABLE:
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        
        return cls(**data)


# =============================================================================
# LOGGING SETUP
# =============================================================================

class ColoredFormatter(logging.Formatter):
    """Colored console output for better readability"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """Configure logging with console and optional file output"""
    logger = logging.getLogger("mp5")
    logger.setLevel(getattr(logging, level))
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level))
    console_formatter = ColoredFormatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


logger = logging.getLogger("mp5")


# =============================================================================
# EXCEPTION HIERARCHY
# =============================================================================

class MP5Error(Exception):
    """Base exception for MP5 operations"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict:
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


class ValidationError(MP5Error):
    """Input validation failed"""
    pass


class EncodingError(MP5Error):
    """Encoding operation failed"""
    pass


class DecodingError(MP5Error):
    """Decoding operation failed"""
    pass


class IntegrityError(MP5Error):
    """Integrity verification failed"""
    pass


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

class HashUtils:
    """Cryptographic hash utilities"""
    
    @staticmethod
    def hash_data(data: bytes, algorithm: str = "sha256") -> str:
        """Calculate hash of data"""
        h = hashlib.new(algorithm)
        h.update(data)
        return h.hexdigest()
    
    @staticmethod
    def hash_file(filepath: str, algorithm: str = "sha256", 
                  chunk_size: int = 8192) -> str:
        """Calculate hash of file with chunked reading"""
        h = hashlib.new(algorithm)
        with open(filepath, 'rb') as f:
            while chunk := f.read(chunk_size):
                h.update(chunk)
        return h.hexdigest()
    
    @staticmethod
    def verify_hash(data: bytes, expected_hash: str, 
                    algorithm: str = "sha256") -> bool:
        """Verify data matches expected hash"""
        return HashUtils.hash_data(data, algorithm) == expected_hash


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
    def compress_json(data: Dict, level: int = 6) -> bytes:
        """Compress JSON data"""
        json_str = json.dumps(data, separators=(',', ':'), sort_keys=True)
        json_bytes = json_str.encode('utf-8')
        compressed = zlib.compress(json_bytes, level=level)
        return base64.b64encode(compressed)
    
    @staticmethod
    def decompress_json(data: bytes) -> Dict:
        """Decompress and parse JSON data"""
        compressed = base64.b64decode(data)
        json_bytes = zlib.decompress(compressed)
        return json.loads(json_bytes.decode('utf-8'))


class VideoUtils:
    """Video processing utilities"""
    
    @staticmethod
    def get_video_info(video_path: str) -> Dict[str, Any]:
        """Extract video metadata using OpenCV"""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValidationError(f"Cannot open video: {video_path}")
        
        info = {
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "codec": int(cap.get(cv2.CAP_PROP_FOURCC)),
            "duration": cap.get(cv2.CAP_PROP_FRAME_COUNT) / (cap.get(cv2.CAP_PROP_FPS) or 1)
        }
        
        cap.release()
        return info
    
    @staticmethod
    def validate_video(video_path: str, config: MP5Config) -> bool:
        """Validate video file"""
        path = Path(video_path)
        
        if not path.exists():
            raise ValidationError(f"Video file not found: {video_path}")
        
        if path.suffix.lower() not in config.supported_formats:
            raise ValidationError(
                f"Unsupported format: {path.suffix}. "
                f"Supported: {config.supported_formats}"
            )
        
        # Try to open with OpenCV
        try:
            VideoUtils.get_video_info(video_path)
        except Exception as e:
            raise ValidationError(f"Invalid video file: {str(e)}")
        
        return True


# =============================================================================
# ATOM LAYER (MP4 Metadata)
# =============================================================================

class AtomLayer:
    """MP4 metadata atom operations"""
    
    def __init__(self, config: MP5Config):
        self.config = config
        if not MUTAGEN_AVAILABLE:
            logger.warning("Mutagen not available - atom layer disabled")
    
    def write(self, video_path: str, metadata: bytes, output_path: str) -> bool:
        """Write metadata to MP4 atom"""
        if not MUTAGEN_AVAILABLE:
            raise EncodingError("Mutagen library required for atom layer")
        
        try:
            # Copy file first to preserve original
            if video_path != output_path:
                shutil.copy2(video_path, output_path)
            
            # Open and modify
            video = MP4(output_path)
            video[self.config.atom_tag] = metadata.decode('utf-8')
            video.save()
            
            logger.info(f"Atom layer written: {len(metadata)} bytes")
            return True
            
        except Exception as e:
            raise EncodingError(f"Failed to write atom layer: {str(e)}")
    
    def read(self, video_path: str) -> Optional[bytes]:
        """Read metadata from MP4 atom"""
        if not MUTAGEN_AVAILABLE:
            raise DecodingError("Mutagen library required for atom layer")
        
        try:
            video = MP4(video_path)
            
            if self.config.atom_tag not in video:
                return None
            
            metadata_str = video[self.config.atom_tag][0]
            metadata_bytes = metadata_str.encode('utf-8')
            
            logger.info(f"Atom layer read: {len(metadata_bytes)} bytes")
            return metadata_bytes
            
        except Exception as e:
            raise DecodingError(f"Failed to read atom layer: {str(e)}")
    
    def has_metadata(self, video_path: str) -> bool:
        """Check if video has MP5 metadata"""
        if not MUTAGEN_AVAILABLE:
            return False
        
        try:
            video = MP4(video_path)
            return self.config.atom_tag in video
        except:
            return False
    
    def remove(self, video_path: str, output_path: str) -> bool:
        """Remove MP5 metadata atom"""
        if not MUTAGEN_AVAILABLE:
            raise DecodingError("Mutagen library required")
        
        try:
            if video_path != output_path:
                shutil.copy2(video_path, output_path)
            
            video = MP4(output_path)
            if self.config.atom_tag in video:
                del video[self.config.atom_tag]
                video.save()
                logger.info("Atom layer removed")
            
            return True
            
        except Exception as e:
            raise DecodingError(f"Failed to remove atom layer: {str(e)}")


# =============================================================================
# LSB LAYER (Steganography)
# =============================================================================

class LSBLayer:
    """LSB steganography operations"""
    
    def __init__(self, config: MP5Config):
        self.config = config
    
    @staticmethod
    def _text_to_binary(text: str) -> str:
        """Convert text to binary string"""
        return ''.join(format(ord(char), '08b') for char in text)
    
    @staticmethod
    def _binary_to_text(binary: str) -> str:
        """Convert binary string to text"""
        chars = [binary[i:i+8] for i in range(0, len(binary), 8)]
        return ''.join(chr(int(c, 2)) for c in chars if len(c) == 8)
    
    def _embed_in_frame(self, frame: np.ndarray, data_binary: str) -> np.ndarray:
        """Embed binary data in frame using LSB"""
        data_len = len(data_binary)
        flat = frame.flatten().copy()
        
        # Embed length (32 bits)
        length_bin = format(data_len, '032b')
        for i in range(32):
            flat[i] = (flat[i] & 0xFE) | int(length_bin[i])
        
        # Embed data
        for i in range(min(data_len, len(flat) - 32)):
            flat[32 + i] = (flat[32 + i] & 0xFE) | int(data_binary[i])
        
        return flat.reshape(frame.shape)
    
    def _extract_from_frame(self, frame: np.ndarray) -> str:
        """Extract binary data from frame"""
        flat = frame.flatten()
        
        # Extract length
        length_bin = ''.join(str(flat[i] & 1) for i in range(32))
        data_len = int(length_bin, 2)
        
        if data_len <= 0 or data_len > len(flat) - 32:
            return ""
        
        # Extract data
        return ''.join(str(flat[32 + i] & 1) for i in range(data_len))
    
    def write(self, video_path: str, metadata: bytes, output_path: str) -> bool:
        """Write metadata to video frames using LSB"""
        try:
            # Prepare data
            data_str = metadata.decode('utf-8')
            data_bin = self._text_to_binary(data_str)
            
            logger.info(f"LSB encoding: {len(data_str)} chars → {len(data_bin)} bits")
            
            # Open video
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Create temp file
            temp_output = output_path + '.lsb_temp.mp4'
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))
            
            # Process frames
            frame_count = 0
            embedded = 0
            
            with click.progressbar(
                length=total_frames,
                label='Encoding LSB layer',
                show_eta=True
            ) as bar:
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # Embed in first N frames
                    if frame_count < self.config.lsb_redundancy:
                        frame = self._embed_in_frame(frame, data_bin)
                        embedded += 1
                    
                    out.write(frame)
                    frame_count += 1
                    bar.update(1)
            
            cap.release()
            out.release()
            
            # Re-encode with audio using ffmpeg
            logger.info("Re-encoding with audio...")
            import subprocess
            result = subprocess.run([
                'ffmpeg', '-i', temp_output, '-i', video_path,
                '-c:v', 'copy', '-c:a', 'copy',
                '-map', '0:v:0', '-map', '1:a:0?',
                output_path, '-y', '-loglevel', 'error'
            ], capture_output=True)
            
            # Cleanup
            os.remove(temp_output)
            
            if result.returncode != 0:
                raise EncodingError(f"FFmpeg error: {result.stderr.decode()}")
            
            logger.info(f"LSB layer written: {embedded} frames embedded")
            return True
            
        except Exception as e:
            raise EncodingError(f"Failed to write LSB layer: {str(e)}")
    
    def read(self, video_path: str, frame_index: int = 0) -> Optional[bytes]:
        """Read metadata from video frame"""
        try:
            cap = cv2.VideoCapture(video_path)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return None
            
            data_bin = self._extract_from_frame(frame)
            if not data_bin:
                return None
            
            data_str = self._binary_to_text(data_bin)
            data_bytes = data_str.encode('utf-8')
            
            logger.info(f"LSB layer read: {len(data_bytes)} bytes from frame {frame_index}")
            return data_bytes
            
        except Exception as e:
            raise DecodingError(f"Failed to read LSB layer: {str(e)}")


# =============================================================================
# CORE ENCODER
# =============================================================================

class MP5Encoder:
    """Enterprise-grade MP5 encoder"""
    
    def __init__(self, config: MP5Config):
        self.config = config
        self.atom_layer = AtomLayer(config)
        self.lsb_layer = LSBLayer(config)
        self.hash_utils = HashUtils()
        self.compression = CompressionUtils()
    
    def encode(
        self,
        video_path: str,
        metadata: Dict[str, Any],
        output_path: str= "output.mp5",
        use_lsb: bool = True,
        verify: bool = True
    ) -> Dict[str, Any]:
        """
        Encode MP5 file with metadata
        
        Returns:
            Dict with encoding results and statistics
        """
        start_time = datetime.now()
        
        logger.info(f"Starting MP5 encoding: {video_path}")
        
        # Validate inputs
        VideoUtils.validate_video(video_path, self.config)
        
        # Get video info
        video_info = VideoUtils.get_video_info(video_path)
        logger.info(f"Video: {video_info['width']}x{video_info['height']}, "
                   f"{video_info['fps']:.2f} fps, {video_info['duration']:.2f}s")
        
        # Calculate original hash
        logger.info("Calculating video hash...")
        original_hash = self.hash_utils.hash_file(video_path, chunk_size=self.config.chunk_size)
        
        # Prepare metadata structure
        atom_metadata = {
            "mp5_version": self.config.version,
            "created": datetime.utcnow().isoformat() + "Z",
            "original_hash": original_hash,
            "video_info": video_info,
            "metadata": metadata,
            "layers": {
                "atom": {
                    "location": f"moov.udta.{self.config.atom_tag}",
                    "compression": "zlib+base64"
                }
            }
        }
        
        if use_lsb:
            # Prepare LSB verification data
            atom_json = json.dumps(atom_metadata, sort_keys=True)
            atom_checksum = self.hash_utils.hash_data(atom_json.encode())
            
            lsb_metadata = {
                "mp5_version": self.config.version,
                "atom_checksum": atom_checksum,
                "timestamp": atom_metadata["created"]
            }
            
            lsb_json = json.dumps(lsb_metadata, sort_keys=True)
            lsb_checksum = self.hash_utils.hash_data(lsb_json.encode())
            
            atom_metadata["layers"]["lsb"] = {
                "frames": list(range(self.config.lsb_redundancy)),
                "redundancy": self.config.lsb_redundancy,
                "checksum": lsb_checksum
            }
        
        # Compress metadata
        logger.info("Compressing metadata...")
        atom_compressed = self.compression.compress_json(
            atom_metadata,
            level=self.config.compression_level
        )
        
        original_size = len(json.dumps(atom_metadata))
        compressed_size = len(atom_compressed)
        ratio = original_size / compressed_size if compressed_size > 0 else 0
        logger.info(f"Compression: {original_size} → {compressed_size} bytes ({ratio:.1f}x)")
        
        if use_lsb:
            lsb_compressed = self.compression.compress_json(
                lsb_metadata,
                level=self.config.compression_level
            )
            
            # Write LSB layer first
            logger.info("Writing LSB layer...")
            temp_path = output_path + '.mp5_lsb_temp.mp4'
            self.lsb_layer.write(video_path, lsb_compressed, temp_path)
            
            # Write atom layer
            logger.info("Writing atom layer...")
            self.atom_layer.write(temp_path, atom_compressed, output_path)
            
            # Cleanup
            os.remove(temp_path)
        else:
            # Write only atom layer
            logger.info("Writing atom layer...")
            self.atom_layer.write(video_path, atom_compressed, output_path)
        
        # Verify if requested
        if verify:
            logger.info("Verifying encoded file...")
            verifier = MP5Verifier(self.config)
            verification = verifier.verify(output_path)
            
            if verification["overall"] != "verified" and verification["overall"] != "partial":
                raise IntegrityError("Verification failed after encoding")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Calculate file sizes
        input_size = Path(video_path).stat().st_size
        output_size = Path(output_path).stat().st_size
        size_increase = ((output_size - input_size) / input_size) * 100
        
        result = {
            "success": True,
            "input_file": video_path,
            "output_file": output_path,
            "input_size_mb": input_size / (1024 * 1024),
            "output_size_mb": output_size / (1024 * 1024),
            "size_increase_percent": size_increase,
            "encoding_time_seconds": duration,
            "layers_used": ["atom", "lsb"] if use_lsb else ["atom"],
            "original_hash": original_hash
        }
        
        logger.info(f"✓ Encoding complete in {duration:.2f}s "
                   f"(+{size_increase:.3f}% size increase)")
        
        return result


# =============================================================================
# CORE DECODER
# =============================================================================

class MP5Decoder:
    """Enterprise-grade MP5 decoder"""
    
    def __init__(self, config: MP5Config):
        self.config = config
        self.atom_layer = AtomLayer(config)
        self.lsb_layer = LSBLayer(config)
        self.compression = CompressionUtils()
    
    def decode(
        self,
        mp5_path: str,
        extract_video: bool = False,
        output_video_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Decode MP5 file and extract metadata"""
        
        logger.info(f"Decoding MP5 file: {mp5_path}")
        
        # Check if file has MP5 metadata
        if not self.atom_layer.has_metadata(mp5_path):
            raise DecodingError("File does not contain MP5 metadata")
        
        # Extract atom layer
        logger.info("Extracting atom layer...")
        atom_compressed = self.atom_layer.read(mp5_path)
        atom_metadata = self.compression.decompress_json(atom_compressed)
        
        result = {
            "mp5_version": atom_metadata.get("mp5_version"),
            "created": atom_metadata.get("created"),
            "original_hash": atom_metadata.get("original_hash"),
            "video_info": atom_metadata.get("video_info"),
            "metadata": atom_metadata.get("metadata"),
            "layers": atom_metadata.get("layers")
        }
        
        # Try to extract LSB layer if present
        if "lsb" in atom_metadata.get("layers", {}):
            logger.info("Extracting LSB layer...")
            try:
                lsb_compressed = self.lsb_layer.read(mp5_path)
                if lsb_compressed:
                    lsb_metadata = self.compression.decompress_json(lsb_compressed)
                    result["lsb_verification"] = lsb_metadata
            except Exception as e:
                logger.warning(f"LSB layer extraction failed: {str(e)}")
                result["lsb_verification"] = None
        
        # Extract clean video if requested
        if extract_video and output_video_path:
            logger.info("Extracting clean video...")
            self.atom_layer.remove(mp5_path, output_video_path)
            result["extracted_video"] = output_video_path
        
        logger.info("✓ Decoding complete")
        
        return result


# =============================================================================
# VERIFIER
# =============================================================================

class MP5Verifier:
    """Integrity verification for MP5 files"""
    
    def __init__(self, config: MP5Config):
        self.config = config
        self.decoder = MP5Decoder(config)
        self.hash_utils = HashUtils()
    
    def verify(self, mp5_path: str) -> Dict[str, Any]:
        """Verify integrity of MP5 file"""
        
        logger.info(f"Verifying MP5 file: {mp5_path}")
        
        result = {
            "file": mp5_path,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "atom_layer": {"status": "unknown"},
            "lsb_layer": {"status": "unknown"},
            "cross_verification": {"status": "unknown"},
            "overall": "unknown"
        }
        
        try:
            # Decode file
            data = self.decoder.decode(mp5_path)
            
            # Check atom layer
            result["atom_layer"]["status"] = "present"
            result["atom_layer"]["version"] = data.get("mp5_version")
            
            # Check LSB layer
            if data.get("lsb_verification"):
                lsb_data = data["lsb_verification"]
                
                # Verify checksum
                atom_json = json.dumps({
                    k: v for k, v in data.items()
                    if k not in ["lsb_verification", "extracted_video"]
                }, sort_keys=True)
                
                expected = self.hash_utils.hash_data(atom_json.encode())
                actual = lsb_data.get("atom_checksum")
                
                if expected == actual:
                    result["lsb_layer"]["status"] = "verified"
                    result["cross_verification"]["status"] = "passed"
                else:
                    result["lsb_layer"]["status"] = "tampered"
                    result["cross_verification"]["status"] = "failed"
            else:
                result["lsb_layer"]["status"] = "absent"
            
            # Overall status
            if result["cross_verification"]["status"] == "passed":
                result["overall"] = "verified"
            elif result["atom_layer"]["status"] == "present":
                result["overall"] = "partial"
            else:
                result["overall"] = "invalid"
        
        except Exception as e:
            result["overall"] = "error"
            result["error"] = str(e)
            logger.error(f"Verification error: {str(e)}")
        
        logger.info(f"Verification result: {result['overall']}")
        
        return result


# =============================================================================
# MAIN (MVP)
# =============================================================================

if __name__ == "__main__":
    setup_logging()
    
    if len(sys.argv) < 2:
        print("\nMP5 MVP Utility")
        print("Usage:")
        print("  Encode: python mp5.py encode <input.mp4> <metadata.json>")
        print("  Decode: python mp5.py decode <input.mp5>")
        print("  Verify: python mp5.py verify <input.mp5>")
        sys.exit(1)

    command = sys.argv[1].lower()
    config = MP5Config()

    try:
        if command == "encode":
            if len(sys.argv) != 4:
                print("Error: Usage is `encode <input.mp4> <json_file>`")
                sys.exit(1)
            
            input_video, meta_file= sys.argv[2], sys.argv[3]
            
            with open(meta_file, 'r') as f:
                metadata = json.load(f)
                
            encoder = MP5Encoder(config)
            res = encoder.encode(input_video, metadata)
            print(json.dumps(res, indent=2))

        elif command == "decode":
            if len(sys.argv) != 3:
                print("Error: Usage is `decode <input_file>`")
                sys.exit(1)
                
            decoder = MP5Decoder(config)
            res = decoder.decode(sys.argv[2])
            print(json.dumps(res, indent=2))

        elif command == "verify":
            if len(sys.argv) != 3:
                print("Error: Usage is `verify <input_file>`")
                sys.exit(1)

            verifier = MP5Verifier(config)
            res = verifier.verify(sys.argv[2])
            print(json.dumps(res, indent=2))

        else:
            print(f"Unknown command: {command}")

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)