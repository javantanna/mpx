import hashlib

class HashUtils:
    """Cryptographic hash utilities"""

    @staticmethod
    def hash_file(filepath: str ,algorithm: str = "sha256", chunk_size: int = 8192) -> str:
        """Calculate hash of file with chunked reading"""
        h= hashlib.new(algorithm)
        with open(filepath,'rb') as f:
            while chunk := f.read(chunk_size):
                h.update(chunk)
        return h.hexdigest()