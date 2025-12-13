import logging
from datetime import datetime
from typing import Dict, Any
from src.MPXDecoder import MPXDecoder
from src.MPXConfig import MPXConfig

logger = logging.getLogger("mpx")


class MPXVerifier:
    def __init__(self, config: MPXConfig):
        self.config = config
        self.decoder = MPXDecoder(config)

    def verify(self, mpx_path: str) -> Dict[str, Any]:
        logger.info(f"Verifying: {mpx_path}")
        
        result = {
            "file": mpx_path,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "lsb_layer": {"status": "unknown"},
            "atom_layer": {"status": "unknown"},
            "overall": "unknown"
        }

        try:
            data = self.decoder.decode(mpx_path)
            
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