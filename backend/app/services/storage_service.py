import boto3
import os
from botocore.exceptions import ClientError
from fastapi import UploadFile
from uuid import uuid4

class S3ImageService:
    def __init__(self):
        # get key from .env
        self.aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
        self.bucket_name = os.environ.get("S3_BUCKET_NAME", "horizonhome-property-images")
        self.region = os.environ.get("AWS_REGION", "us-east-2") # need to be same region
        
        # Init storage client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            region_name=self.region
        )
    
    async def upload_image(self, file: UploadFile, property_id: int, landlord_id: int) -> str:
        """Upload image to S3 and return public URL"""
        try:
            # read file
            contents = await file.read()
            
            # Generate a unique filename (use UUID to avoid conflicts)
            file_ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
            unique_filename = f"properties/{landlord_id}/{property_id}/{uuid4()}{file_ext}"
            
            # put to S3 storage
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=unique_filename,
                Body=contents,
                ContentType=file.content_type or "image/jpeg"
            )
            
            # Construct and return the image URL
            return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{unique_filename}"
        
        except ClientError as e:
            print(f"S3 Upload fail: {e}")
            raise Exception(f"Image upload fail: {str(e)}")
        finally:
            # Reset file pointer for future use
            await file.seek(0)