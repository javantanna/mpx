from layers.AtomLayer import AtomLayer
from layers.LSBLayer import LSBLayer
from utils.HashUtils import HashUtils
from utils.CompressionUtils import CompressionUtils
from datetime import datetime
from typing import Dict, Any
from utils.VideoUtils import VideoUtils
import json
from src.Exceptions import IntegrityError
from utils.FeatureExtractor import FeatureExtractor
from src.MPXConfig import MPXConfig
from src.MPXVerifier import MPXVerifier
import logging
import os

logger = logging.getLogger("mpx")

class MPXEncoder:
    """MPX Encoder"""
    def __init__(self,config:MPXConfig):
        self.config=config
        self.atom_layer=AtomLayer(config)
        self.lsb_layer=LSBLayer(config)
        self.hash_utils=HashUtils()
        self.compression=CompressionUtils()
        self.feature_extractor = FeatureExtractor()

    def encode(
        self,
        video_path: str,
        user_metadata: Dict[str, Any],
        output_path: str= "outputs/output.mpx",
        use_lsb: bool = True,
        verify: bool = True
    ) -> Dict[str, Any]:
        """
        Encode MPX file with metadata
        
        Returns:
            Dict with encoding results and statistics
        """

        start_time=datetime.now()
        logger.info(f"🚀 Spinning up encoding for {video_path}")

        # Validate Input File
        VideoUtils.validate_video(video_path,self.config)

        # Get video info
        video_info=VideoUtils.get_video_info(video_path)
        logger.info(f"📹 Video specs: {video_info['width']}x{video_info['height']}, "
                   f"{video_info['fps']:.2f} fps, {video_info['duration']:.2f}s")
        
        # Calculate Original hash
        logger.info("🔐 Computing hash (trust but verify)...")
        original_hash=self.hash_utils.hash_file(video_path, chunk_size=self.config.chunk_size)

        # AUTO-EXTRACT FEATURES
        logger.info("\n🧠 Analyzing your video for feature extraction (this is the cool part)...")
        auto_features = self.feature_extractor.extract_all_features(video_path)

        # PREPARE ATOM METADATA (Public file info only)
        # Prepare metadata structure
        atom_metadata={
            "mpx_version": self.config.version,
            "created": datetime.now().isoformat() + "Z",
            "original_hash": original_hash,
            "video_info": video_info,
            "notes": "AI Metadata stored in lsb layer",
            "layers":{
                "atom": {
                    "location": f"moov.udta.{self.config.atom_tag}"
                }
            }
        }


       
        # PREPARE LSB METADATA (Hidden AI training payload)
        lsb_metadata = {
            "mpx_version": self.config.version,
            "timestamp": atom_metadata["created"],
            "payload_type": "ai_training_data",
            "auto_features": auto_features,  # Auto-generated features
            "user_metadata": user_metadata    # User-provided metadata
        }
        logger.info("📦 Compressing metadata (making it smol)...")
        atom_compressed = self.compression.compress_json(atom_metadata)
        lsb_compressed = self.compression.compress_json(lsb_metadata)
        
        original_size=len(json.dumps(lsb_metadata))
        compressed_size = len(lsb_compressed)
        ratio=original_size/compressed_size if compressed_size>0 else 0
        logger.info(f"Compression: {original_size} → {compressed_size} bytes ({ratio:.1f}x)")

        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Created output directory: {output_dir}")


        if use_lsb:
             # Write LSB layer (HIDDEN AI METADATA)
            logger.info("\n🔒 Injecting hidden data into pixels (stealth mode)...")
            temp_path = output_path + 'mpx_lsb_temp.mp4'

             #TODO: complete from here
            self.lsb_layer.write(video_path, lsb_compressed, temp_path)
            
            # Write in atom Layer (PUBLIC FILE INFO)
            logger.info("\n📝 Writing public metadata (the stuff people can see)")
            self.atom_layer.write(temp_path,atom_compressed,output_path)
            os.remove(temp_path)


            # if not use_lsb
        else:
            # Write in atom Layer (PUBLIC FILE INFO)
            logger.warning("LSB disabled - storing in atom layer instead")
            atom_metadata["ai_metadata"] = lsb_metadata
            atom_compressed = self.compression.compress_json(atom_metadata)
            self.atom_layer.write(video_path, atom_compressed, output_path)

        if verify:
            logger.info("\n🔍 Double-checking our work...")
            verifier=MPXVerifier(self.config)

            verification =verifier.verify(output_path)
            logger.info(f"Verification result: {verification['overall']}")

            if verification['overall'] not in ["verified","partial"]:
                if 'error' in verification:
                    logger.error(f"Verification details: {verification['error']}")
                raise IntegrityError("Verification failed")
            

        end_time=datetime.now()
        duration=(end_time - start_time).total_seconds()
        logger.info(f"Encoding completed in {duration:.2f} seconds")

        input_size = os.path.getsize(video_path)
        output_size = os.path.getsize(output_path)
        size_increase = ((output_size - input_size) / input_size) * 100 if input_size > 0 else 0

        result={
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

        logger.info(f"\n🎉 Encoding Time {duration:.2f}s (+{size_increase:.1f}% storage, totally worth it)")

        return result
            