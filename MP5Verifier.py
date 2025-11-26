import logging
from datetime import datetime
from typing import Dict, Any
from MP5Decoder import MP5Decoder
from MP5Config import MP5Config

logger = logging.getLogger("mp5")


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