"""
MP5 - Enterprise-Grade Video Metadata CLI Tool
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
            "duration": cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
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
        output_path: str,
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
# CLI INTERFACE
# =============================================================================

@click.group()
@click.version_option(version="1.0.0", prog_name="mp5")
@click.option('--config', type=click.Path(exists=True), help='Config file path')
@click.option('--log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']), 
              default='INFO', help='Logging level')
@click.option('--log-file', type=click.Path(), help='Log file path')
@click.pass_context
def cli(ctx, config, log_level, log_file):
    """
    MP5 - Enterprise Video Metadata Tool
    
    Embed AI metadata in video files using hybrid steganography.
    """
    # Setup logging
    setup_logging(log_level, log_file)
    
    # Load configuration
    if config:
        ctx.obj = MP5Config.from_file(config)
    else:
        ctx.obj = MP5Config()


@cli.command()
@click.argument('input_video', type=click.Path(exists=True))
@click.option('-m', '--metadata', type=click.Path(exists=True), required=True,
              help='Metadata JSON/YAML file')
@click.option('-o', '--output', type=click.Path(), required=True,
              help='Output MP5 file')
@click.option('--no-lsb', is_flag=True, help='Disable LSB layer')
@click.option('--no-verify', is_flag=True, help='Skip verification after encoding')
@click.option('--json-output', type=click.Path(), help='Save results to JSON file')
@click.pass_obj
def encode(config, input_video, metadata, output, no_lsb, no_verify, json_output):
    """Encode video with MP5 metadata"""
    
    try:
        # Load metadata
        with open(metadata, 'r') as f:
            if metadata.endswith(('.yaml', '.yml')) and YAML_AVAILABLE:
                metadata_data = yaml.safe_load(f)
            else:
                metadata_data = json.load(f)
        
        # Encode
        encoder = MP5Encoder(config)
        result = encoder.encode(
            input_video,
            metadata_data,
            output,
            use_lsb=not no_lsb,
            verify=not no_verify
        )
        
        # Display results
        click.echo("\n" + "="*60)
        click.secho("✓ ENCODING SUCCESSFUL", fg='green', bold=True)
        click.echo("="*60)
        click.echo(f"Output file: {result['output_file']}")
        click.echo(f"Input size:  {result['input_size_mb']:.2f} MB")
        click.echo(f"Output size: {result['output_size_mb']:.2f} MB")
        click.echo(f"Size increase: {result['size_increase_percent']:.3f}%")
        click.echo(f"Encoding time: {result['encoding_time_seconds']:.2f}s")
        click.echo(f"Layers: {', '.join(result['layers_used'])}")
        click.echo("="*60 + "\n")
        
        # Save JSON output if requested
        if json_output:
            with open(json_output, 'w') as f:
                json.dump(result, f, indent=2)
            click.echo(f"Results saved to: {json_output}")
        
        sys.exit(0)
        
    except MP5Error as e:
        click.secho(f"\n✗ ERROR: {e.message}", fg='red', bold=True, err=True)
        if e.details:
            click.echo(json.dumps(e.details, indent=2), err=True)
        sys.exit(1)
    except Exception as e:
        click.secho(f"\n✗ UNEXPECTED ERROR: {str(e)}", fg='red', bold=True, err=True)
        logger.exception("Unexpected error during encoding")
        sys.exit(1)


@cli.command()
@click.argument('input_mp5', type=click.Path(exists=True))
@click.option('-o', '--output-metadata', type=click.Path(),
              help='Save extracted metadata to file')
@click.option('-v', '--extract-video', type=click.Path(),
              help='Extract clean video to file')
@click.option('--format', type=click.Choice(['json', 'yaml']), default='json',
              help='Output format for metadata')
@click.pass_obj
def decode(config, input_mp5, output_metadata, extract_video, format):
    """Decode MP5 file and extract metadata"""
    
    try:
        # Decode
        decoder = MP5Decoder(config)
        result = decoder.decode(
            input_mp5,
            extract_video=extract_video is not None,
            output_video_path=extract_video
        )
        
        # Display results
        click.echo("\n" + "="*60)
        click.secho("✓ DECODING SUCCESSFUL", fg='green', bold=True)
        click.echo("="*60)
        click.echo(f"MP5 Version: {result['mp5_version']}")
        click.echo(f"Created: {result['created']}")
        click.echo(f"Original Hash: {result['original_hash'][:16]}...")
        
        if result.get('video_info'):
            vi = result['video_info']
            click.echo(f"Video: {vi['width']}x{vi['height']}, "
                      f"{vi['fps']:.2f} fps, {vi['duration']:.2f}s")
        
        layers = result.get('layers', {})
        click.echo(f"Layers: {', '.join(layers.keys())}")
        
        if result.get('lsb_verification'):
            click.secho("✓ LSB verification layer present", fg='green')
        
        click.echo("="*60 + "\n")
        
        # Display metadata
        if not output_metadata:
            click.echo("Metadata:")
            click.echo(json.dumps(result['metadata'], indent=2))
        
        # Save metadata if requested
        if output_metadata:
            with open(output_metadata, 'w') as f:
                if format == 'yaml' and YAML_AVAILABLE:
                    yaml.dump(result['metadata'], f, default_flow_style=False)
                else:
                    json.dump(result['metadata'], f, indent=2)
            click.echo(f"Metadata saved to: {output_metadata}")
        
        # Show extracted video path
        if extract_video:
            click.echo(f"Clean video extracted to: {extract_video}")
        
        sys.exit(0)
        
    except MP5Error as e:
        click.secho(f"\n✗ ERROR: {e.message}", fg='red', bold=True, err=True)
        sys.exit(1)
    except Exception as e:
        click.secho(f"\n✗ UNEXPECTED ERROR: {str(e)}", fg='red', bold=True, err=True)
        logger.exception("Unexpected error during decoding")
        sys.exit(1)


@cli.command()
@click.argument('input_mp5', type=click.Path(exists=True))
@click.option('--json-output', type=click.Path(), help='Save results to JSON file')
@click.pass_obj
def verify(config, input_mp5, json_output):
    """Verify MP5 file integrity"""
    
    try:
        # Verify
        verifier = MP5Verifier(config)
        result = verifier.verify(input_mp5)
        
        # Display results
        click.echo("\n" + "="*60)
        
        overall = result['overall']
        if overall == 'verified':
            click.secho("✓ VERIFICATION PASSED", fg='green', bold=True)
            color = 'green'
        elif overall == 'partial':
            click.secho("⚠ PARTIAL VERIFICATION", fg='yellow', bold=True)
            color = 'yellow'
        else:
            click.secho("✗ VERIFICATION FAILED", fg='red', bold=True)
            color = 'red'
        
        click.echo("="*60)
        click.echo(f"File: {result['file']}")
        click.echo(f"Timestamp: {result['timestamp']}")
        click.echo(f"\nAtom Layer: {result['atom_layer']['status']}")
        click.echo(f"LSB Layer: {result['lsb_layer']['status']}")
        click.echo(f"Cross-Verification: {result['cross_verification']['status']}")
        click.echo(f"\nOverall Status: ", nl=False)
        click.secho(overall.upper(), fg=color, bold=True)
        click.echo("="*60 + "\n")
        
        # Save JSON output if requested
        if json_output:
            with open(json_output, 'w') as f:
                json.dump(result, f, indent=2)
            click.echo(f"Results saved to: {json_output}")
        
        sys.exit(0 if overall == 'verified' else 1)
        
    except MP5Error as e:
        click.secho(f"\n✗ ERROR: {e.message}", fg='red', bold=True, err=True)
        sys.exit(1)
    except Exception as e:
        click.secho(f"\n✗ UNEXPECTED ERROR: {str(e)}", fg='red', bold=True, err=True)
        logger.exception("Unexpected error during verification")
        sys.exit(1)


@cli.command()
@click.argument('input_mp5', type=click.Path(exists=True))
@click.pass_obj
def info(config, input_mp5):
    """Show detailed information about MP5 file"""
    
    try:
        # Decode to get full info
        decoder = MP5Decoder(config)
        result = decoder.decode(input_mp5)
        
        # Verify integrity
        verifier = MP5Verifier(config)
        verification = verifier.verify(input_mp5)
        
        # Display comprehensive info
        click.echo("\n" + "="*60)
        click.secho("MP5 FILE INFORMATION", fg='cyan', bold=True)
        click.echo("="*60)
        
        click.echo(f"\n📄 File: {input_mp5}")
        click.echo(f"   Size: {Path(input_mp5).stat().st_size / (1024*1024):.2f} MB")
        
        click.echo(f"\n🔖 MP5 Metadata:")
        click.echo(f"   Version: {result['mp5_version']}")
        click.echo(f"   Created: {result['created']}")
        click.echo(f"   Original Hash: {result['original_hash']}")
        
        if result.get('video_info'):
            vi = result['video_info']
            click.echo(f"\n🎬 Video Properties:")
            click.echo(f"   Resolution: {vi['width']}x{vi['height']}")
            click.echo(f"   Frame Rate: {vi['fps']:.2f} fps")
            click.echo(f"   Duration: {vi['duration']:.2f} seconds")
            click.echo(f"   Total Frames: {vi['frame_count']}")
        
        layers = result.get('layers', {})
        click.echo(f"\n📦 Storage Layers:")
        for layer_name, layer_info in layers.items():
            click.echo(f"   {layer_name.upper()}: {layer_info}")
        
        click.echo(f"\n🔒 Integrity Status:")
        status_color = {
            'verified': 'green',
            'partial': 'yellow',
            'invalid': 'red',
            'error': 'red'
        }.get(verification['overall'], 'white')
        click.echo(f"   Overall: ", nl=False)
        click.secho(verification['overall'].upper(), fg=status_color, bold=True)
        
        click.echo(f"\n💾 Embedded Metadata Preview:")
        metadata_str = json.dumps(result['metadata'], indent=2)
        # Show first 500 chars
        if len(metadata_str) > 500:
            click.echo(metadata_str[:500] + "\n   ... (truncated)")
        else:
            click.echo(metadata_str)
        
        click.echo("\n" + "="*60 + "\n")
        
        sys.exit(0)
        
    except MP5Error as e:
        click.secho(f"\n✗ ERROR: {e.message}", fg='red', bold=True, err=True)
        sys.exit(1)
    except Exception as e:
        click.secho(f"\n✗ UNEXPECTED ERROR: {str(e)}", fg='red', bold=True, err=True)
        logger.exception("Unexpected error")
        sys.exit(1)


@cli.command()
@click.argument('input_dir', type=click.Path(exists=True))
@click.option('-o', '--output-dir', type=click.Path(), required=True,
              help='Output directory for MP5 files')
@click.option('-m', '--metadata-template', type=click.Path(exists=True),
              help='Template metadata file')
@click.option('--workers', type=int, default=4, help='Number of parallel workers')
@click.option('--no-lsb', is_flag=True, help='Disable LSB layer')
@click.pass_obj
def batch(config, input_dir, output_dir, metadata_template, workers, no_lsb):
    """Batch process multiple videos"""
    
    try:
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Find all video files
        video_files = [
            f for f in input_path.iterdir()
            if f.suffix.lower() in config.supported_formats
        ]
        
        if not video_files:
            click.secho(f"No video files found in {input_dir}", fg='yellow')
            sys.exit(0)
        
        click.echo(f"\nFound {len(video_files)} video(s) to process")
        
        # Load metadata template
        metadata_template_data = {}
        if metadata_template:
            with open(metadata_template, 'r') as f:
                if metadata_template.endswith(('.yaml', '.yml')) and YAML_AVAILABLE:
                    metadata_template_data = yaml.safe_load(f)
                else:
                    metadata_template_data = json.load(f)
        
        # Process function
        def process_video(video_file):
            try:
                # Customize metadata
                metadata = metadata_template_data.copy()
                metadata["filename"] = video_file.name
                metadata["batch_processed"] = True
                metadata["processed_at"] = datetime.utcnow().isoformat() + "Z"
                
                # Output path
                output_file = output_path / f"{video_file.stem}.mp5"
                
                # Encode
                encoder = MP5Encoder(config)
                result = encoder.encode(
                    str(video_file),
                    metadata,
                    str(output_file),
                    use_lsb=not no_lsb,
                    verify=False  # Skip verification for speed
                )
                
                return {
                    "status": "success",
                    "input": str(video_file),
                    "output": str(output_file),
                    "size_mb": result['output_size_mb'],
                    "time_seconds": result['encoding_time_seconds']
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "input": str(video_file),
                    "error": str(e)
                }
        
        # Process in parallel
        results = []
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(process_video, vf): vf for vf in video_files}
            
            with click.progressbar(
                length=len(video_files),
                label='Processing videos',
                show_eta=True
            ) as bar:
                for future in as_completed(futures):
                    result = future.result()
                    results.append(result)
                    
                    if result["status"] == "success":
                        click.echo(f"  ✓ {Path(result['input']).name} → "
                                 f"{Path(result['output']).name}")
                    else:
                        click.echo(f"  ✗ {Path(result['input']).name}: "
                                 f"{result['error']}", err=True)
                    
                    bar.update(1)
        
        # Summary
        success_count = sum(1 for r in results if r["status"] == "success")
        total_time = sum(r.get("time_seconds", 0) for r in results if r["status"] == "success")
        
        click.echo("\n" + "="*60)
        click.secho("BATCH PROCESSING COMPLETE", fg='cyan', bold=True)
        click.echo("="*60)
        click.echo(f"Total: {len(video_files)}")
        click.echo(f"Success: {success_count}")
        click.echo(f"Failed: {len(video_files) - success_count}")
        click.echo(f"Total time: {total_time:.2f}s")
        click.echo(f"Average: {total_time/success_count:.2f}s per video" if success_count > 0 else "")
        click.echo("="*60 + "\n")
        
        # Save results log
        results_log = output_path / "batch_results.json"
        with open(results_log, 'w') as f:
            json.dump({
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "input_dir": str(input_dir),
                "output_dir": str(output_dir),
                "total": len(video_files),
                "success": success_count,
                "failed": len(video_files) - success_count,
                "results": results
            }, f, indent=2)
        
        click.echo(f"Results log saved to: {results_log}")
        
        sys.exit(0 if success_count == len(video_files) else 1)
        
    except Exception as e:
        click.secho(f"\n✗ BATCH ERROR: {str(e)}", fg='red', bold=True, err=True)
        logger.exception("Unexpected error during batch processing")
        sys.exit(1)


@cli.command()
@click.option('--output', type=click.Path(), help='Output config file path')
@click.pass_obj
def config_template(config, output):
    """Generate configuration template file"""
    
    template = {
        "version": "1.0.0",
        "atom_tag": "©mp5",
        "lsb_redundancy": 5,
        "max_metadata_mb": 50,
        "compression_level": 6,
        "hash_algorithm": "sha256",
        "temp_dir": "/tmp/mp5",
        "max_workers": 4,
        "chunk_size": 8192,
        "supported_formats": [".mp4", ".mov", ".m4v", ".avi"]
    }
    
    if output:
        with open(output, 'w') as f:
            if output.endswith(('.yaml', '.yml')) and YAML_AVAILABLE:
                yaml.dump(template, f, default_flow_style=False)
            else:
                json.dump(template, f, indent=2)
        click.echo(f"Config template saved to: {output}")
    else:
        click.echo(json.dumps(template, indent=2))
    
    sys.exit(0)


if __name__ == '__main__':
    cli()