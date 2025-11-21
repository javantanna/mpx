import hashlib

# UTILITY FUNCTIONS
class HashUtils:
    """Cryptographic hash utilities"""

    @staticmethod
    def hash_data(data: bytes, algorithm: str = "sha256") -> str:
        """Calculate hash of data"""
        h = hashlib.new(algorithm)
        h.update(data)
        return h.hexdigest()


    @staticmethod
    def hash_file(filepath: str ,algorithm: str = "sha256", chunk_size: int = 8192) -> str:
        """Calculate hash of file with chunked reading"""
        h= hashlib.new(algorithm)
        with open(filepath,'rb') as f:
            while chunk := f.read(chunk_size):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def verify_hash(data: bytes, expeted_hash: str, algorithm: str = "sha256") -> bool:
        """Verify data matches expected hash"""
        return HashUtils.hash_data(data,algorithm) == expeted_hash