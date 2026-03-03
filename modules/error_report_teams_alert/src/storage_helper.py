from google.cloud import storage
from typing import Optional


class StorageHelper:
    def __init__(self, bucket_name: str, blob_name: str = "cache/cache.proto"):
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        self.cache_blob = self.bucket.blob(blob_name)

    def get_last_cache_file_as_bytes(self) -> Optional[bytes]:
        return self.cache_blob.download_as_bytes() if self.cache_blob.exists() else None

    def save_bytes_to_cache(self, data: bytes) -> None:
        self.cache_blob.upload_from_string(data)
