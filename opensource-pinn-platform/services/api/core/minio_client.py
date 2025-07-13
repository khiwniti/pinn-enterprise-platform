"""
MinIO client configuration
"""

from minio import Minio
from minio.error import S3Error
import io
import json
import logging
from typing import Optional, BinaryIO

from .config import settings

logger = logging.getLogger(__name__)

class MinIOClient:
    """MinIO client wrapper"""
    
    def __init__(self):
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure
        )
        self.bucket_name = "pinn-models"
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """Ensure the bucket exists"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
            else:
                logger.info(f"Bucket exists: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Failed to ensure bucket: {e}")
            raise
    
    def upload_file(self, object_name: str, file_path: str, content_type: str = "application/octet-stream") -> bool:
        """Upload a file to MinIO"""
        try:
            self.client.fput_object(
                self.bucket_name,
                object_name,
                file_path,
                content_type=content_type
            )
            logger.info(f"Uploaded file: {object_name}")
            return True
        except S3Error as e:
            logger.error(f"Failed to upload file {object_name}: {e}")
            return False
    
    def upload_data(self, object_name: str, data: bytes, content_type: str = "application/octet-stream") -> bool:
        """Upload data to MinIO"""
        try:
            data_stream = io.BytesIO(data)
            self.client.put_object(
                self.bucket_name,
                object_name,
                data_stream,
                length=len(data),
                content_type=content_type
            )
            logger.info(f"Uploaded data: {object_name}")
            return True
        except S3Error as e:
            logger.error(f"Failed to upload data {object_name}: {e}")
            return False
    
    def upload_json(self, object_name: str, data: dict) -> bool:
        """Upload JSON data to MinIO"""
        try:
            json_data = json.dumps(data, indent=2).encode('utf-8')
            return self.upload_data(object_name, json_data, "application/json")
        except Exception as e:
            logger.error(f"Failed to upload JSON {object_name}: {e}")
            return False
    
    def download_file(self, object_name: str, file_path: str) -> bool:
        """Download a file from MinIO"""
        try:
            self.client.fget_object(self.bucket_name, object_name, file_path)
            logger.info(f"Downloaded file: {object_name}")
            return True
        except S3Error as e:
            logger.error(f"Failed to download file {object_name}: {e}")
            return False
    
    def download_data(self, object_name: str) -> Optional[bytes]:
        """Download data from MinIO"""
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            logger.info(f"Downloaded data: {object_name}")
            return data
        except S3Error as e:
            logger.error(f"Failed to download data {object_name}: {e}")
            return None
    
    def download_json(self, object_name: str) -> Optional[dict]:
        """Download JSON data from MinIO"""
        try:
            data = self.download_data(object_name)
            if data:
                return json.loads(data.decode('utf-8'))
            return None
        except Exception as e:
            logger.error(f"Failed to download JSON {object_name}: {e}")
            return None
    
    def delete_object(self, object_name: str) -> bool:
        """Delete an object from MinIO"""
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"Deleted object: {object_name}")
            return True
        except S3Error as e:
            logger.error(f"Failed to delete object {object_name}: {e}")
            return False
    
    def object_exists(self, object_name: str) -> bool:
        """Check if an object exists"""
        try:
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error:
            return False
    
    def list_objects(self, prefix: str = "") -> list:
        """List objects with optional prefix"""
        try:
            objects = self.client.list_objects(self.bucket_name, prefix=prefix)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            logger.error(f"Failed to list objects: {e}")
            return []
    
    def get_object_url(self, object_name: str, expires: int = 3600) -> Optional[str]:
        """Get a presigned URL for an object"""
        try:
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=expires
            )
            return url
        except S3Error as e:
            logger.error(f"Failed to get object URL {object_name}: {e}")
            return None
    
    def bucket_exists(self, bucket_name: str) -> bool:
        """Check if bucket exists"""
        try:
            return self.client.bucket_exists(bucket_name)
        except S3Error as e:
            logger.error(f"Failed to check bucket {bucket_name}: {e}")
            return False
    
    def make_bucket(self, bucket_name: str) -> bool:
        """Create a new bucket"""
        try:
            self.client.make_bucket(bucket_name)
            logger.info(f"Created bucket: {bucket_name}")
            return True
        except S3Error as e:
            logger.error(f"Failed to create bucket {bucket_name}: {e}")
            return False

# Global MinIO client instance
minio_client = MinIOClient()