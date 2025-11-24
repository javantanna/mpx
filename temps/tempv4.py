#!/usr/bin/env python3
"""
MP5 - Enterprise-Grade Video Metadata CLI Tool
Version: 1.0.0

Auto-generates video features and stores them in LSB layer for stealth.
Production-ready CLI using sys.argv.
"""

import sys
import os
import json
import logging
import hashlib
import zlib
import base64
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
import tempfile
import shutil

# Optional dependencies
try:
    from mutagen.mp4 import MP4
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class MP5Config:
    """Global configuration"""
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
        path = Path(config_path)
        with open(path, 'r') as f:
            if path.suffix in ['.yaml', '.yml'] and YAML_AVAILABLE:
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        return cls(**data)


# =============================================================================
# LOGGING
# =============================================================================

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    logger = logging.getLogger("mp5")
    logger.setLevel(getattr(logging, level))
    logger.handlers.clear()
    
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(getattr(logging, level))
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    console.setFormatter(formatter)
    logger.addHandler(console)
    
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


logger = logging.getLogger("mp5")


# =============================================================================
# EXCEPTIONS
# =============================================================================

class MP5Error(Exception):
    pass

class ValidationError(MP5Error):
    pass

class EncodingError(MP5Error):
    pass

class DecodingError(MP5Error):
    pass

class IntegrityError(MP5Error):
    pass


# =============================================================================
# UTILITIES
# =============================================================================

class HashUtils:
    @staticmethod
    def hash_data(data: bytes, algorithm: str = "sha256") -> str:
        h = hashlib.new(algorithm)
        h.update(data)
        return h.hexdigest()
    
    @staticmethod
    def hash_file(filepath: str, algorithm: str = "sha256", chunk_size: int = 8192) -> str:
        h = hashlib.new(algorithm)
        with open(filepath, 'rb') as f:
            while chunk := f.read(chunk_size):
                h.update(chunk)
        return h.hexdigest()


class CompressionUtils:
    @staticmethod
    def compress_json(data: Dict, level: int = 6) -> bytes:
        json_str = json.dumps(data, separators=(',', ':'), sort_keys=True)
        json_bytes = json_str.encode('utf-8')
        compressed = zlib.compress(json_bytes, level=level)
        return base64.b64encode(compressed)
    
    @staticmethod
    def decompress_json(data: bytes) -> Dict:
        compressed = base64.b64decode(data)
        json_bytes = zlib.decompress(compressed)
        return json.loads(json_bytes.decode('utf-8'))


class VideoUtils:
    @staticmethod
    def get_video_info(video_path: str) -> Dict[str, Any]:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValidationError(f"Cannot open video: {video_path}")
        
        info = {
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "duration": cap.get(cv2.CAP_PROP_FRAME_COUNT) / (cap.get(cv2.CAP_PROP_FPS) or 1)
        }
        cap.release()
        return info
    
    @staticmethod
    def validate_video(video_path: str, config: MP5Config) -> bool:
        path = Path(video_path)
        if not path.exists():
            raise ValidationError(f"Video file not found: {video_path}")
        if path.suffix.lower() not in config.supported_formats:
            raise ValidationError(f"Unsupported format: {path.suffix}")
        try:
            VideoUtils.get_video_info(video_path)
        except Exception as e:
            raise ValidationError(f"Invalid video file: {str(e)}")
        return True


class ProgressBar:
    def __init__(self, total: int, label: str = "Progress"):
        self.total = total
        self.current = 0
        self.label = label
    
    def update(self, n: int = 1):
        self.current += n
        percent = (self.current / self.total) * 100
        bar_len = 40
        filled = int(bar_len * self.current / self.total)
        bar = '█' * filled + '░' * (bar_len - filled)
        print(f'\r{self.label}: |{bar}| {percent:.1f}% ({self.current}/{self.total})', end='', flush=True)
        if self.current >= self.total:
            print()


# =============================================================================
# FEATURE EXTRACTION (Mathematical - No AI Models)
# =============================================================================

class FeatureExtractor:
    """Extract video features using OpenCV and NumPy"""
    
    @staticmethod
    def extract_all_features(video_path: str) -> Dict[str, Any]:
        """Extract all features from video"""
        logger.info("Extracting video features...")
        
        cap = cv2.VideoCapture(video_path)
        features = {
            "blur_score": 0.0,
            "noise_level": 0.0,
            "dynamic_range": 0.0,
            "edge_density": 0.0,
            "texture_complexity": 0.0,
            "letterbox_ratio": 0.0,
            "rule_of_thirds_score": 0.0,
            "motion_intensity": 0.0,
            "static_frame_ratio": 0.0,
            "camera_shake": 0.0,
            "scene_cut_count": 0,
            "volume_rms": 0.0,
            "audio_peak": 0.0,
            "silence_ratio": 0.0
        }
        
        frame_count = 0
        prev_frame = None
        motion_scores = []
        blur_scores = []
        static_frames = 0
        scene_cuts = 0
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        sample_rate = max(1, total_frames // 30)  # Sample 30 frames
        
        progress = ProgressBar(total_frames, "Analyzing video")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Sample frames to save processing time
            if frame_count % sample_rate == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Blur detection (Laplacian variance)
                laplacian = cv2.Laplacian(gray, cv2.CV_64F)
                blur_score = laplacian.var()
                blur_scores.append(blur_score)
                
                # Edge density
                edges = cv2.Canny(gray, 50, 150)
                edge_density = np.count_nonzero(edges) / edges.size
                features["edge_density"] += edge_density
                
                # Texture complexity (standard deviation)
                features["texture_complexity"] += gray.std()
                
                # Dynamic range
                features["dynamic_range"] += gray.max() - gray.min()
                
                # Letterbox detection (check top/bottom rows)
                top_row = gray[0:int(gray.shape[0]*0.1), :].mean()
                bottom_row = gray[int(gray.shape[0]*0.9):, :].mean()
                if top_row < 20 and bottom_row < 20:
                    features["letterbox_ratio"] += 1
                
                # Rule of thirds (check if content in center vs edges)
                h, w = gray.shape
                center = gray[h//3:2*h//3, w//3:2*w//3].mean()
                full = gray.mean()
                if full > 0:
                    features["rule_of_thirds_score"] += center / full
                
                # Motion detection
                if prev_frame is not None:
                    diff = cv2.absdiff(prev_frame, gray)
                    motion_score = diff.mean()
                    motion_scores.append(motion_score)
                    
                    # Static frame detection
                    if motion_score < 5:
                        static_frames += 1
                    
                    # Scene cut detection
                    if motion_score > 30:
                        scene_cuts += 1
                    
                    # Camera shake (high-frequency motion)
                    features["camera_shake"] += diff.std()
                
                prev_frame = gray.copy()
            
            frame_count += 1
            progress.update(1)
        
        cap.release()
        
        # Average out accumulated features
        sampled_frames = frame_count // sample_rate
        if sampled_frames > 0:
            features["blur_score"] = float(np.mean(blur_scores)) if blur_scores else 0.0
            features["noise_level"] = float(np.std(blur_scores)) if blur_scores else 0.0
            features["edge_density"] = features["edge_density"] / sampled_frames
            features["texture_complexity"] = features["texture_complexity"] / sampled_frames
            features["dynamic_range"] = features["dynamic_range"] / sampled_frames
            features["letterbox_ratio"] = features["letterbox_ratio"] / sampled_frames
            features["rule_of_thirds_score"] = features["rule_of_thirds_score"] / sampled_frames
            features["motion_intensity"] = float(np.mean(motion_scores)) if motion_scores else 0.0
            features["static_frame_ratio"] = static_frames / sampled_frames
            features["camera_shake"] = features["camera_shake"] / sampled_frames
            features["scene_cut_count"] = scene_cuts
        
        # Compression artifacts (blocking detection)
        features["compression_artifacts"] = FeatureExtractor._detect_blocking(video_path)
        
        # Audio features (if available)
        audio_features = FeatureExtractor._extract_audio_features(video_path)
        features.update(audio_features)
        
        logger.info("✓ Feature extraction complete")
        return features
    
    @staticmethod
    def _detect_blocking(video_path: str) -> float:
        """Detect JPEG-like blocking artifacts"""
        cap = cv2.VideoCapture(video_path)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return 0.0
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Check for 8x8 block boundaries (JPEG artifacts)
        block_size = 8
        h, w = gray.shape
        block_scores = []
        
        for i in range(0, h - block_size, block_size):
            for j in range(0, w - block_size, block_size):
                block = gray[i:i+block_size, j:j+block_size]
                # Edge detection at block boundaries
                edge_strength = np.abs(np.diff(block, axis=0)).mean() + np.abs(np.diff(block, axis=1)).mean()
                block_scores.append(edge_strength)
        
        return float(np.std(block_scores)) if block_scores else 0.0
    
    @staticmethod
    def _extract_audio_features(video_path: str) -> Dict[str, float]:
        """Extract basic audio features (if audio present)"""
        # Note: Full audio analysis requires additional libraries
        # This is a placeholder that can be expanded
        return {
            "volume_rms": 0.0,
            "audio_peak": 0.0,
            "silence_ratio": 0.0
        }


# =============================================================================
# ATOM LAYER (File Info Only)
# =============================================================================

class AtomLayer:
    def __init__(self, config: MP5Config):
        self.config = config
        if not MUTAGEN_AVAILABLE:
            logger.warning("Mutagen not available - atom layer disabled")
    
    def write(self, video_path: str, metadata: bytes, output_path: str) -> bool:
        if not MUTAGEN_AVAILABLE:
            raise EncodingError("Mutagen library required")
        
        if video_path != output_path:
            shutil.copy2(video_path, output_path)
        
        video = MP4(output_path)
        video[self.config.atom_tag] = metadata.decode('utf-8')
        video.save()
        
        logger.info(f"Atom layer written: {len(metadata)} bytes")
        return True
    
    def read(self, video_path: str) -> Optional[bytes]:
        if not MUTAGEN_AVAILABLE:
            raise DecodingError("Mutagen library required")
        
        video = MP4(video_path)
        if self.config.atom_tag not in video:
            return None
        
        metadata_str = video[self.config.atom_tag][0]
        return metadata_str.encode('utf-8')
    
    def has_metadata(self, video_path: str) -> bool:
        if not MUTAGEN_AVAILABLE:
            return False
        try:
            video = MP4(video_path)
            return self.config.atom_tag in video
        except:
            return False


# =============================================================================
# LSB LAYER (AI Metadata Storage - Hidden)
# =============================================================================

class LSBLayer:
    def __init__(self, config: MP5Config):
        self.config = config
    
    @staticmethod
    def _text_to_binary(text: str) -> str:
        return ''.join(format(ord(char), '08b') for char in text)
    
    @staticmethod
    def _binary_to_text(binary: str) -> str:
        chars = [binary[i:i+8] for i in range(0, len(binary), 8)]
        return ''.join(chr(int(c, 2)) for c in chars if len(c) == 8)
    
    def _embed_in_frame(self, frame: np.ndarray, data_binary: str) -> np.ndarray:
        data_len = len(data_binary)
        flat = frame.flatten().copy()
        
        length_bin = format(data_len, '032b')
        for i in range(32):
            flat[i] = (flat[i] & 0xFE) | int(length_bin[i])
        
        for i in range(min(data_len, len(flat) - 32)):
            flat[32 + i] = (flat[32 + i] & 0xFE) | int(data_binary[i])
        
        return flat.reshape(frame.shape)
    
    def _extract_from_frame(self, frame: np.ndarray) -> str:
        flat = frame.flatten()
        length_bin = ''.join(str(flat[i] & 1) for i in range(32))
        data_len = int(length_bin, 2)
        
        if data_len <= 0 or data_len > len(flat) - 32:
            return ""
        
        return ''.join(str(flat[32 + i] & 1) for i in range(data_len))
    
    def write(self, video_path: str, metadata: bytes, output_path: str) -> bool:
        data_str = metadata.decode('utf-8')
        data_bin = self._text_to_binary(data_str)
        
        logger.info(f"LSB encoding: {len(data_str)} chars → {len(data_bin)} bits")
        
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        temp_output = output_path + '.lsb_temp.mp4'
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))
        
        frame_count = 0
        embedded = 0
        progress = ProgressBar(total_frames, "Encoding LSB")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count < self.config.lsb_redundancy:
                frame = self._embed_in_frame(frame, data_bin)
                embedded += 1
            
            out.write(frame)
            frame_count += 1
            progress.update(1)
        
        cap.release()
        out.release()
        
        logger.info("Re-encoding with audio...")
        import subprocess
        result = subprocess.run([
            'ffmpeg', '-i', temp_output, '-i', video_path,
            '-c:v', 'copy', '-c:a', 'copy',
            '-map', '0:v:0', '-map', '1:a:0?',
            output_path, '-y', '-loglevel', 'error'
        ], capture_output=True)
        
        os.remove(temp_output)
        
        if result.returncode != 0:
            raise EncodingError(f"FFmpeg error: {result.stderr.decode()}")
        
        logger.info(f"LSB layer written: {embedded} frames")
        return True
    
    def read(self, video_path: str, frame_index: int = 0) -> Optional[bytes]:
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
        return data_str.encode('utf-8')


# =============================================================================
# ENCODER (AI Metadata in LSB)
# =============================================================================

class MP5Encoder:
    def __init__(self, config: MP5Config):
        self.config = config
        self.atom_layer = AtomLayer(config)
        self.lsb_layer = LSBLayer(config)
        self.hash_utils = HashUtils()
        self.compression = CompressionUtils()
        self.feature_extractor = FeatureExtractor()
    
    def encode(self, video_path: str, user_metadata: Dict[str, Any], 
               output_path: str, use_lsb: bool = True, verify: bool = True) -> Dict[str, Any]:
        start_time = datetime.now()
        
        logger.info(f"Starting MP5 encoding: {video_path}")
        
        VideoUtils.validate_video(video_path, self.config)
        video_info = VideoUtils.get_video_info(video_path)
        
        logger.info(f"Video: {video_info['width']}x{video_info['height']}, "
                   f"{video_info['fps']:.2f} fps, {video_info['duration']:.2f}s")
        
        logger.info("Calculating video hash...")
        original_hash = self.hash_utils.hash_file(video_path)
        
        # AUTO-EXTRACT FEATURES
        logger.info("\nAuto-extracting video features...")
        auto_features = self.feature_extractor.extract_all_features(video_path)
        
        # PREPARE ATOM METADATA (Public file info only)
        atom_metadata = {
            "mp5_version": self.config.version,
            "created": datetime.utcnow().isoformat() + "Z",
            "original_hash": original_hash,
            "video_info": video_info,
            "note": "AI training data stored in LSB layer",
            "layers": {
                "atom": {"location": f"moov.udta.{self.config.atom_tag}"}
            }
        }
        
        # PREPARE LSB METADATA (Hidden AI training payload)
        lsb_metadata = {
            "mp5_version": self.config.version,
            "timestamp": atom_metadata["created"],
            "payload_type": "ai_training_data",
            "auto_features": auto_features,  # Auto-generated features
            "user_metadata": user_metadata    # User-provided metadata
        }
        
        logger.info("Compressing metadata...")
        atom_compressed = self.compression.compress_json(atom_metadata)
        lsb_compressed = self.compression.compress_json(lsb_metadata)
        
        original_size = len(json.dumps(lsb_metadata))
        compressed_size = len(lsb_compressed)
        logger.info(f"LSB payload: {original_size} → {compressed_size} bytes ({original_size/compressed_size:.1f}x)")
        
        if use_lsb:
            # Write LSB layer (HIDDEN AI METADATA)
            logger.info("\nWriting LSB layer (Hidden AI metadata)...")
            temp_path = output_path + '.mp5_lsb_temp.mp4'
            #TODO: complete here
            self.lsb_layer.write(video_path, lsb_compressed, temp_path)
            
            # Write Atom layer (Public file info)
            logger.info("\nWriting atom layer (Public headers)...")
            self.atom_layer.write(temp_path, atom_compressed, output_path)
            os.remove(temp_path)
        else:
            logger.warning("LSB disabled - storing in atom layer instead")
            atom_metadata["ai_metadata"] = lsb_metadata
            atom_compressed = self.compression.compress_json(atom_metadata)
            self.atom_layer.write(video_path, atom_compressed, output_path)
        
        if verify:
            logger.info("\nVerifying...")
            verifier = MP5Verifier(self.config)
            verification = verifier.verify(output_path)
            if verification["overall"] not in ["verified", "partial"]:
                raise IntegrityError("Verification failed")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
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
            "storage_layer": "LSB (hidden)" if use_lsb else "Atom (visible)",
            "features_extracted": len(auto_features),
            "original_hash": original_hash
        }
        
        logger.info(f"\n✓ Encoding complete in {duration:.2f}s (+{size_increase:.3f}% size)")
        
        return result


# =============================================================================
# DECODER (Extract from LSB)
# =============================================================================

class MP5Decoder:
    def __init__(self, config: MP5Config):
        self.config = config
        self.atom_layer = AtomLayer(config)
        self.lsb_layer = LSBLayer(config)
        self.compression = CompressionUtils()
    
    def decode(self, mp5_path: str, extract_video: bool = False, 
               output_video_path: Optional[str] = None) -> Dict[str, Any]:
        logger.info(f"Decoding MP5 file: {mp5_path}")
        
        result = {}
        
        # Extract LSB layer (Primary - AI metadata)
        logger.info("Extracting LSB layer (hidden AI metadata)...")
        try:
            lsb_compressed = self.lsb_layer.read(mp5_path)
            if lsb_compressed:
                lsb_data = self.compression.decompress_json(lsb_compressed)
                result["ai_metadata"] = lsb_data
                result["auto_features"] = lsb_data.get("auto_features", {})
                result["user_metadata"] = lsb_data.get("user_metadata", {})
                logger.info("✓ LSB payload extracted")
            else:
                logger.warning("No LSB payload found")
        except Exception as e:
            logger.warning(f"LSB extraction failed: {str(e)}")
        
        # Extract atom layer (Secondary - file info)
        if self.atom_layer.has_metadata(mp5_path):
            logger.info("Extracting atom layer (file info)...")
            try:
                atom_compressed = self.atom_layer.read(mp5_path)
                atom_data = self.compression.decompress_json(atom_compressed)
                result["file_info"] = atom_data
            except Exception as e:
                logger.warning(f"Atom extraction failed: {str(e)}")
        
        logger.info("✓ Decoding complete")
        return result


# =============================================================================
# VERIFIER
# =============================================================================

class MP5Verifier:
    def __init__(self, config: MP5Config):
        self.config = config
        self.decoder = MP5Decoder(config)
    
    def verify(self, mp5_path: str) -> Dict[str, Any]:
        logger.info(f"Verifying: {mp5_path}")
        
        result = {
            "file": mp5_path,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "lsb_layer": {"status": "unknown"},
            "atom_layer": {"status": "unknown"},
            "overall": "unknown"
        }
        
        try:
            data = self.decoder.decode(mp5_path)
            
            # Check LSB layer
            if data.get("ai_metadata"):
                result["lsb_layer"]["status"] = "present"
                result["lsb_layer"]["features_count"] = len(data.get("auto_features", {}))
                result["overall"] = "verified"
            else:
                result["lsb_layer"]["status"] = "absent"
                result["overall"] = "partial"
            
            # Check atom layer
            if data.get("file_info"):
                result["atom_layer"]["status"] = "present"
            else:
                result["atom_layer"]["status"] = "absent"
        
        except Exception as e:
            result["overall"] = "error"
            result["error"] = str(e)
        
        logger.info(f"Verification: {result['overall']}")
        return result


# =============================================================================
# CLI (sys.argv)
# =============================================================================

def print_header():
    print(f"\n{Colors.CYAN}{Colors.BOLD}MP5 - Enterprise Video Metadata Tool{Colors.RESET}")
    print(f"{Colors.CYAN}Version 1.0.0 - Auto Feature Extraction{Colors.RESET}\n")


def print_separator():
    print("=" * 60)


def show_help():
    print("""
Usage:
    python mp5.py encode <input.mp4> <user_metadata.json> <output.mp5> [--no-lsb] [--no-verify]
    python mp5.py decode <input.mp5> [--output metadata.json]
    python mp5.py verify <input.mp5>
    python mp5.py info <input.mp5>
    python mp5.py help

Commands:
    encode    Auto-extract features and embed in video (LSB layer)
    decode    Extract hidden AI metadata from video
    verify    Verify integrity and presence of hidden metadata
    info      Show detailed file information
    help      Show this help message

Examples:
    # Encode (auto-generates features)
    python mp5.py encode video.mp4 metadata.json output.mp5
    
    # Decode
    python mp5.py decode output.mp5
    
    # Verify
    python mp5.py verify output.mp5

Features Auto-Extracted:
    - blur_score, noise_level, compression_artifacts
    - dynamic_range, edge_density, texture_complexity
    - letterbox_ratio, rule_of_thirds_score
    - motion_intensity, static_frame_ratio, camera_shake
    - scene_cut_count, volume_rms, audio_peak, silence_ratio
""")


def cmd_encode(args):
    """Encode command"""
    if len(args) < 3:
        print("Error: encode requires <input.mp4> <metadata.json> <output.mp5>")
        print("Usage: python mp5.py encode input.mp4 metadata.json output.mp5 [--no-lsb] [--no-verify]")
        return 1
    
    input_video = args[0]
    metadata_file = args[1]
    output = args[2]
    no_lsb = "--no-lsb" in args
    no_verify = "--no-verify" in args
    
    print_header()
    
    # Load user metadata
    try:
        with open(metadata_file, 'r') as f:
            if metadata_file.endswith(('.yaml', '.yml')) and YAML_AVAILABLE:
                user_metadata = yaml.safe_load(f)
            else:
                user_metadata = json.load(f)
    except Exception as e:
        print(f"{Colors.RED}Error loading metadata: {str(e)}{Colors.RESET}")
        return 1
    
    # Encode
    config = MP5Config()
    encoder = MP5Encoder(config)
    
    try:
        result = encoder.encode(input_video, user_metadata, output, 
                               use_lsb=not no_lsb, verify=not no_verify)
        
        # Display results
        print_separator()
        print(f"{Colors.GREEN}{Colors.BOLD}✓ ENCODING SUCCESSFUL{Colors.RESET}")
        print_separator()
        print(f"Output: {result['output_file']}")
        print(f"Input size:  {result['input_size_mb']:.2f} MB")
        print(f"Output size: {result['output_size_mb']:.2f} MB")
        print(f"Size increase: {result['size_increase_percent']:.3f}%")
        print(f"Encoding time: {result['encoding_time_seconds']:.2f}s")
        print(f"Storage: {result['storage_layer']}")
        print(f"Features extracted: {result['features_extracted']}")
        print_separator()
        print()
        
        return 0
    
    except Exception as e:
        print(f"\n{Colors.RED}✗ Encoding failed: {str(e)}{Colors.RESET}")
        return 1


def cmd_decode(args):
    """Decode command"""
    if len(args) < 1:
        print("Error: decode requires <input.mp5>")
        print("Usage: python mp5.py decode input.mp5 [--output metadata.json]")
        return 1
    
    input_mp5 = args[0]
    output_file = None
    
    if "--output" in args:
        idx = args.index("--output")
        if idx + 1 < len(args):
            output_file = args[idx + 1]
    
    print_header()
    
    config = MP5Config()
    decoder = MP5Decoder(config)
    
    try:
        result = decoder.decode(input_mp5)
        
        print_separator()
        print(f"{Colors.GREEN}{Colors.BOLD}✓ DECODING SUCCESSFUL{Colors.RESET}")
        print_separator()
        
        if result.get("file_info"):
            info = result["file_info"]
            print(f"MP5 Version: {info.get('mp5_version')}")
            print(f"Created: {info.get('created')}")
            print(f"Original Hash: {info.get('original_hash', '')[:16]}...")
        
        print()
        
        if result.get("ai_metadata"):
            print(f"{Colors.CYAN}Hidden AI Metadata Found:{Colors.RESET}")
            print(f"  Auto-features: {len(result.get('auto_features', {}))} features")
            print(f"  User metadata: {len(result.get('user_metadata', {}))} keys")
        else:
            print(f"{Colors.YELLOW}⚠ No hidden AI metadata found{Colors.RESET}")
        
        print_separator()
        
        # Save or display
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\nMetadata saved to: {output_file}")
        else:
            print("\nExtracted Data:")
            print(json.dumps(result, indent=2))
        
        print()
        return 0
    
    except Exception as e:
        print(f"\n{Colors.RED}✗ Decoding failed: {str(e)}{Colors.RESET}")
        return 1


def cmd_verify(args):
    """Verify command"""
    if len(args) < 1:
        print("Error: verify requires <input.mp5>")
        print("Usage: python mp5.py verify input.mp5")
        return 1
    
    input_mp5 = args[0]
    
    print_header()
    
    config = MP5Config()
    verifier = MP5Verifier(config)
    
    try:
        result = verifier.verify(input_mp5)
        
        print_separator()
        
        overall = result['overall']
        if overall == 'verified':
            print(f"{Colors.GREEN}{Colors.BOLD}✓ VERIFICATION PASSED{Colors.RESET}")
        elif overall == 'partial':
            print(f"{Colors.YELLOW}{Colors.BOLD}⚠ PARTIAL VERIFICATION{Colors.RESET}")
        else:
            print(f"{Colors.RED}{Colors.BOLD}✗ VERIFICATION FAILED{Colors.RESET}")
        
        print_separator()
        print(f"File: {result['file']}")
        print(f"LSB Layer: {result['lsb_layer']['status']}")
        
        if result['lsb_layer'].get('features_count'):
            print(f"  Features: {result['lsb_layer']['features_count']}")
        
        print(f"Atom Layer: {result['atom_layer']['status']}")
        print(f"Overall: {overall.upper()}")
        print_separator()
        print()
        
        return 0 if overall == 'verified' else 1
    
    except Exception as e:
        print(f"\n{Colors.RED}✗ Verification failed: {str(e)}{Colors.RESET}")
        return 1


def cmd_info(args):
    """Info command"""
    if len(args) < 1:
        print("Error: info requires <input.mp5>")
        print("Usage: python mp5.py info input.mp5")
        return 1
    
    input_mp5 = args[0]
    
    print_header()
    
    config = MP5Config()
    decoder = MP5Decoder(config)
    
    try:
        result = decoder.decode(input_mp5)
        
        print_separator()
        print(f"{Colors.CYAN}{Colors.BOLD}MP5 FILE INFORMATION{Colors.RESET}")
        print_separator()
        
        print(f"\n📄 File: {input_mp5}")
        print(f"   Size: {Path(input_mp5).stat().st_size / (1024*1024):.2f} MB")
        
        if result.get("file_info"):
            info = result["file_info"]
            print(f"\n🔖 MP5 Info:")
            print(f"   Version: {info.get('mp5_version')}")
            print(f"   Created: {info.get('created')}")
            print(f"   Hash: {info.get('original_hash')}")
            
            if info.get("video_info"):
                vi = info["video_info"]
                print(f"\n🎬 Video:")
                print(f"   Resolution: {vi['width']}x{vi['height']}")
                print(f"   FPS: {vi['fps']:.2f}")
                print(f"   Duration: {vi['duration']:.2f}s")
                print(f"   Frames: {vi['frame_count']}")
        
        if result.get("ai_metadata"):
            print(f"\n🤖 AI Metadata (Hidden in LSB):")
            print(f"   Storage: LSB Steganography")
            print(f"   Payload Type: {result['ai_metadata'].get('payload_type')}")
            
            if result.get("auto_features"):
                print(f"\n📊 Auto-Extracted Features ({len(result['auto_features'])}):")
                features = result['auto_features']
                
                # Display key features
                print(f"   Blur Score: {features.get('blur_score', 0):.2f}")
                print(f"   Edge Density: {features.get('edge_density', 0):.4f}")
                print(f"   Motion Intensity: {features.get('motion_intensity', 0):.2f}")
                print(f"   Scene Cuts: {features.get('scene_cut_count', 0)}")
                print(f"   Static Frames: {features.get('static_frame_ratio', 0):.2%}")
                print(f"   Compression Artifacts: {features.get('compression_artifacts', 0):.4f}")
            
            if result.get("user_metadata"):
                print(f"\n💾 User Metadata:")
                user_meta = result['user_metadata']
                if len(json.dumps(user_meta)) > 200:
                    print(f"   {json.dumps(user_meta, indent=2)[:200]}...")
                else:
                    print(f"   {json.dumps(user_meta, indent=2)}")
        
        print(f"\n{Colors.RESET}")
        print_separator()
        print()
        
        return 0
    
    except Exception as e:
        print(f"\n{Colors.RED}✗ Error: {str(e)}{Colors.RESET}")
        return 1


def main():
    """Main entry point"""
    
    if len(sys.argv) < 2:
        show_help()
        return 0
    
    command = sys.argv[1].lower()
    args = sys.argv[2:]
    
    # Setup logging
    log_level = "INFO"
    log_file = None
    
    if "--log-level" in args:
        idx = args.index("--log-level")
        if idx + 1 < len(args):
            log_level = args[idx + 1].upper()
            args = [a for a in args if a not in ["--log-level", args[idx + 1]]]
    
    if "--log-file" in args:
        idx = args.index("--log-file")
        if idx + 1 < len(args):
            log_file = args[idx + 1]
            args = [a for a in args if a not in ["--log-file", args[idx + 1]]]
    
    setup_logging(log_level, log_file)
    
    # Execute command
    try:
        if command == "encode":
            return cmd_encode(args)
        elif command == "decode":
            return cmd_decode(args)
        elif command == "verify":
            return cmd_verify(args)
        elif command == "info":
            return cmd_info(args)
        elif command in ["help", "--help", "-h"]:
            show_help()
            return 0
        else:
            print(f"Error: Unknown command '{command}'")
            print("Run 'python mp5.py help' for usage information")
            return 1
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 130
    except Exception as e:
        print(f"\n{Colors.RED}Error: {str(e)}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())