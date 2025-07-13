"""
Storage client for workers
"""

import os
import json
import logging
from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)

class StorageClient:
    """MinIO storage client for workers"""
    
    def __init__(self):
        self.client = Minio(
            os.getenv("MINIO_ENDPOINT", "minio:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "secure123"),
            secure=False
        )
        self.bucket_name = "pinn-models"
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """Ensure bucket exists"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except S3Error as e:
            logger.error(f"Failed to ensure bucket: {e}")
    
    def upload_file(self, object_name: str, file_path: str) -> bool:
        """Upload file to storage"""
        try:
            self.client.fput_object(self.bucket_name, object_name, file_path)
            return True
        except S3Error as e:
            logger.error(f"Failed to upload {object_name}: {e}")
            return False
    
    def upload_json(self, object_name: str, data: dict) -> bool:
        """Upload JSON data to storage"""
        try:
            import io
            json_data = json.dumps(data, indent=2).encode('utf-8')
            data_stream = io.BytesIO(json_data)
            self.client.put_object(
                self.bucket_name,
                object_name,
                data_stream,
                length=len(json_data),
                content_type="application/json"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to upload JSON {object_name}: {e}")
            return False