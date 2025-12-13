from utils.CompressionUtils import CompressionUtils
from layers.AtomLayer import AtomLayer
from layers.LSBLayer import LSBLayer
import logging
from typing import Dict, Any, Optional
from src.MPXConfig import MPXConfig


logger = logging.getLogger("mpx")


class MPXDecoder:
    def __init__(self,config:MPXConfig):
        self.config=config
        self.atom_layer=AtomLayer(config)
        self.lsb_layer=LSBLayer(config)
        self.compression=CompressionUtils()

    def decode(self, mpx_path: str, extract_video: bool = False, output_video_path: Optional[str] = None) -> Dict[str, Any]:
        """Decode MPX file"""
        logger.info(f"Decoding MPX file: {mpx_path}")

        result={}

        # Extract LSB Layer (Primary Ai- metadata)
        logger.info("Extracting LSB layer (hidden AI metadata)...")
        try:
            lsb_compressed=self.lsb_layer.read(mpx_path)
            if lsb_compressed:
                lsb_data=self.compression.decompress_json(lsb_compressed)
                result["ai_metadata"]=lsb_data
                # result["auto_features"]=lsb_data.get("auto_features",{})
                # result["user_metadata"]=lsb_data.get("user_metadata",{})
                logger.info(f"LSB extraction successful")
            else:
                logger.warning("LSB layer not found")
        except Exception as e:
            logger.warning(f"LSB extraction failed: {str(e)}")
        
        # Extract atom layer (Secondary - file info)
        if(self.atom_layer.has_metadata(mpx_path)):
            logger.info("Extracting atom layer (public file info)")
            try:
                atom_compressed = self.atom_layer.read(mpx_path)
                atom_data = self.compression.decompress_json(atom_compressed)
                result["file_info"] = atom_data
            except Exception as e:
                logger.warning(f"Atom layer extraction failed: {str(e)}")

        logger.info("✓ Decoding complete")
        return result