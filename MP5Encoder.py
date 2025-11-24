from AtomLayer import AtomLayer
from LSBLayer import LSBLayer
from HashUtils import HashUtils
from CompressionUtils import CompressionUtils
from datetime import datetime
from typing import Dict, Any
from VideoUtils import VideoUtils
import json

class MP5Encoder:
    """MP5 Encoder"""
    def __init__(self,config:MP5Config):
        self.config=config
        self.atom_layer=AtomLayer(config)
        self.lsb_layer=LSBLayer(config)
        self.hash_utils=HashUtils()
        self.compression=CompressionUtils()

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

        start_time=datetime.now()
        logger.info(f"Starting encoding process for {video_path}")

        # Validate Input File
        VideoUtils.validate_input_file(video_path,self.config)

        # Get video info
        video_info=VideoUtils.get_video_info(video_path)
        logger.info(f"Video info: {video_info['width']}x{video_info['height']}, "
                   f"{video_info['fps']:.2f} fps, {video_info['duration']:.2f}s")
        
        # Calculate Original hash
        logger.info("Calculating original hash...")
        original_hash=self.hash_utils.calculate_hash(video_path,chunk_size=self.config.hash_chunk_size)

        # AUTO-EXTRACT FEATURES
        logger.info("\nAuto-extracting video features...")
        auto_features = self.feature_extractor.extract_all_features(video_path)

        # PREPARE ATOM METADATA (Public file info only)
        # Prepare metadata structure
        atom_metadata={
            "mp5_version": self.config.version,
            "createdon": datetime.now().isoformat() + "Z",
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
            "mp5_version": self.config.version,
            "timestamp": atom_metadata["created"],
            "payload_type": "ai_training_data",
            "auto_features": auto_features,  # Auto-generated features
            "user_metadata": user_metadata    # User-provided metadata
        }
        logger.info("Compressing metadata...")
        atom_compressed = self.compression.compress_json(atom_metadata)
        lsb_compressed = self.compression.compress_json(lsb_metadata)
        
        original_size=len(json.dumps(lsb_metadata))
        compressed_size = len(lsb_compressed)
        ratio=original_size/compressed_size if compressed_size>0 else 0
        logger.info(f"Compression: {original_size} → {compressed_size} bytes ({ratio:.1f}x)")

        if use_lsb:
             # Write LSB layer (HIDDEN AI METADATA)
            logger.info("\nWriting LSB layer (Hidden AI metadata)...")
            temp_path = output_path + 'mp5_lsb_temp.mp4'

             #TODO: complete from here
            self.lsb_layer.write(video_path, lsb_compressed, temp_path)
            






            atom_json=json.dumps(atom_metadata,sort_keys=True)
            # we are converting '{"key":"value"}' to b'{"key":"value"}'
            atom_checksum=self.hash_utils.hash_data(atom_json.encode())
            lsb_metadata={
                "mp5_version": self.config.version,
                "atom_checksum": atom_checksum,
                "timestamp": atom_metadata["createdon"]
            }

            lsb_json=json.dumps(lsb_metadata,sort_keys=True)
            lsb_checksum=self.hash_utils.hash_data(lsb_json.encode())

            atom_metadata["layers"]["lsb"]={
                "frames": list(range(self.config.lsb_redundancy)),
                "redundancy": self.config.lsb_redundancy,
                "checksum": lsb_checksum
            }

            # Compressing metadata
            logger.info("Compressing metadata...")
            atom_compressed=self.compression.compress_data(atom_metadata,level=self.config.compression_level)

            original_size=len(json.dumps(atom_metadata))
            compressed_size=len(atom_compressed)
            ratio=original_size/compressed_size if compressed_size>0 else 0
            logger.info(f"Compression: {original_size} → {compressed_size} bytes ({ratio:.1f}x)")


            if use_lsb:
                lsb_compressed=self.compression.compress_json(lsb_metadata,level=self.config.compression_level) 

                # Write LSB layer first
                logger.info("Writing LSB layer...")
                temp_path=output_path + ".lsb"
                self.lsb_layer.write_lsb_layer(video_path,lsb_compressed,temp_path)
        