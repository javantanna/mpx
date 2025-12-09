import json
from dataclasses import dataclass
from typing import List
from pathlib import Path
import yaml


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
    def from_file(cls,config_path:str)->'MP5Config':
        """Load configuration from YAML or JSON file"""
        path=Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")


        with open(path,'r') as f:
            if path.suffix in ['.yaml','.yml']:
                data=yaml.safe_load(f)
            else:
                data=json.load(f)
        return cls(**data)
