from src.MP5Config import MP5Config
from mutagen.mp4 import MP4
from mutagen import MutagenError
from src.Exceptions import DecodingError,EncodingError
import shutil
from typing import Optional
import logging


logger=logging.getLogger("mp5")



class AtomLayer:
    """MP4 metadata atom operations"""
    
    def __init__(self,config:MP5Config):
        self.config=config

    def write(self,video_path:str,metadata:bytes,output_path:str)->bool:
        """Write metadata to MP5 atom layer"""
        try:
            # Copy file first to preserve original
            if video_path != output_path:
                shutil.copyfile(video_path,output_path)
            
            # Open and modify
            video=MP4(output_path)
            video[self.config.atom_tag]=metadata.decode('utf-8')
            video.save(output_path)
            logger.info(f"Atom layer written: {len(metadata)} bytes")
            return True
        except Exception as e:
            raise EncodingError(f"Faild to write atom layer: {str(e)}")


    def read(self,video_path:str)->Optional[bytes]:
        """Read metadata from MP5 atom layer"""
        try:
            video=MP4(video_path)
            if self.config.atom_tag not in video:
                return None
            
            metadata_str=video[self.config.atom_tag][0]
            metadata_bytes=metadata_str.encode('utf-8')
            logger.info(f"Atom layer read: {len(metadata_bytes)} bytes")
            return metadata_bytes
        except Exception as e:
            raise DecodingError(f"Faild to read atom layer: {str(e)}")

    def has_metadata(self,video_path:str)->bool:
        """Check if metadata exists in MP5 atom layer"""
        try:
            video=MP4(video_path)
            return self.config.atom_tag in video
        except Exception as e:
            return False