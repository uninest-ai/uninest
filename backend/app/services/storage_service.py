import boto3
import os
from botocore.exceptions import ClientError
from fastapi import UploadFile
from uuid import uuid4

class S3ImageService:
    def __init__(self):
        # 从环境变量获取AWS凭证
        self.aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
        self.bucket_name = os.environ.get("S3_BUCKET_NAME", "horizonhome-property-images")
        self.region = os.environ.get("AWS_REGION", "us-east-2")  # 确保与你的应用区域一致
        
        # 初始化S3客户端
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            region_name=self.region
        )
    
    async def upload_image(self, file: UploadFile, property_id: int, landlord_id: int) -> str:
        """上传图片到S3并返回公共URL"""
        try:
            # 读取文件内容
            contents = await file.read()
            
            # 生成唯一文件名（使用UUID避免冲突）
            file_ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
            unique_filename = f"properties/{landlord_id}/{property_id}/{uuid4()}{file_ext}"
            
            # 上传到S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=unique_filename,
                Body=contents,
                ContentType=file.content_type or "image/jpeg"
            )
            
            # 构建并返回图片URL
            return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{unique_filename}"
        
        except ClientError as e:
            print(f"S3上传错误: {e}")
            raise Exception(f"图片上传失败: {str(e)}")
        finally:
            # 确保文件指针重置，以防后续需要使用
            await file.seek(0)