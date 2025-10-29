# S3服务
import boto3
from fastapi import UploadFile, HTTPException
from datetime import datetime
from urllib.parse import quote
from config import settings

class S3Service:
    """S3文件上传服务"""
    
    def __init__(self):
        # 检查AWS配置
        if (not settings.AWS_ACCESS_KEY_ID or 
            settings.AWS_ACCESS_KEY_ID == "your_aws_access_key_here" or
            not settings.S3_BUCKET_NAME or
            settings.S3_BUCKET_NAME == "your-s3-bucket-name"):
            raise ValueError("S3配置未完成，请设置AWS_ACCESS_KEY_ID、AWS_SECRET_ACCESS_KEY和S3_BUCKET_NAME环境变量")
        
        self.client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.S3_BUCKET_NAME
    
    def validate_file(self, file: UploadFile) -> bool:
        """验证文件格式和大小"""
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename cannot be empty")
        
        extension = file.filename.split(".")[-1].lower()
        if extension not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        return True
    
    async def upload_file(self, file: UploadFile) -> dict:
        """
        上传文件到S3
        
        Args:
            file: 上传的文件
            
        Returns:
            dict: 文件信息
        """
        # 验证文件
        self.validate_file(file)
        
        try:
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_filename = file.filename
            s3_key = f"uploads/{timestamp}_{original_filename}"
            
            print(f"📤 Starting upload: {original_filename}")
            
            # 读取文件内容
            file_content = await file.read()
            file_size = len(file_content)
            
            print(f"📊 File size: {file_size / 1024:.2f} KB")
            
            # 上传到S3
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=file.content_type or 'application/octet-stream',
                Metadata={
                    'original_filename': quote(original_filename),
                    'upload_timestamp': timestamp
                }
            )
            file_url = f"s3://{self.bucket_name}/{s3_key}"
            
            print(f"✅ Upload successful: {s3_key}")
            
            return {
                "original_filename": original_filename,
                "s3_key": s3_key,
                "file_url": file_url,
                "file_size": file_size,
                "file_extension": original_filename.split(".")[-1].lower(),
                "upload_time": timestamp
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Upload failed: {error_msg}")
            
            # 提供更详细的错误信息
            if "Access Denied" in error_msg:
                raise HTTPException(
                    status_code=403, 
                    detail=f"S3访问被拒绝。请确保您的AWS用户有S3存储桶 '{self.bucket_name}' 的写入权限。"
                )
            elif "NoSuchBucket" in error_msg:
                raise HTTPException(
                    status_code=404,
                    detail=f"S3存储桶 '{self.bucket_name}' 不存在。请检查存储桶名称或创建存储桶。"
                )
            else:
                raise HTTPException(status_code=500, detail=f"Upload failed: {error_msg}")
    
    def health_check(self) -> dict:
        """检查S3连接是否正常"""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            return {
                "status": "healthy",
                "bucket": self.bucket_name
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# 全局实例
s3_service = S3Service()