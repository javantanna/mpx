from CompressionUtils import CompressionUtils
from AtomLayer import AtomLayer
from LSBLayer import LSBLayer
import logging
from typing import Dict, Any, Optional
from MP5Config import MP5Config


logger = logging.getLogger("mp5")


class MP5Decoder:
    def __init__(self,config:MP5Config):
        self.config=config
        self.atom_layer=AtomLayer(config)
        self.lsb_layer=LSBLayer(config)
        self.compression=CompressionUtils()

    def decode(self, mp5_path: str, extract_video: bool = False, output_video_path: Optional[str] = None) -> Dict[str, Any]:
        """Decode MP5 file"""
        logger.info(f"Decoding MP5 file: {mp5_path}")

        result={}

        # Extract LSB Layer (Primary Ai- metadata)
        logger.info("Extracting LSB layer (hidden AI metadata)...")
        try:
            lsb_compressed=self.lsb_layer.read(mp5_path)
            if lsb_compressed:
                lsb_data=self.compression.decompress_json(lsb_compressed)
                result["ai_metadata"]=lsb_data
                result["auto_features"]=lsb_data.get("auto_features",{})
                result["user_metadata"]=lsb_data.get("user_metadata",{})
                logger.info(f"LSB extraction successful")
            else:
                logger.warning("LSB layer not found")
        except Exception as e:
            logger.warning(f"LSB extraction failed: {str(e)}")
        
        # Extract atom layer (Secondary - file info)
        if(self.atom_layer.has_metadata(mp5_path)):
            logger.info("Extracting atom layer (public file info)")
            try:
                atom_compressed = self.atom_layer.read(mp5_path)
                atom_data = self.compression.decompress_json(atom_compressed)
                result["file_info"] = atom_data
            except Exception as e:
                logger.warning(f"Atom layer extraction failed: {str(e)}")

        logger.info("✓ Decoding complete")
        return result