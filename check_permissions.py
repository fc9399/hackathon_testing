#!/usr/bin/env python3
"""
UniMem AI 权限检查脚本
"""
import boto3
from botocore.exceptions import ClientError
from config import settings

def check_s3_permissions():
    """检查S3权限"""
    print("🔍 检查S3权限...")
    
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        
        bucket_name = settings.S3_BUCKET_NAME
        
        # 检查存储桶是否存在
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"✅ 存储桶存在: {bucket_name}")
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                print(f"❌ 存储桶不存在: {bucket_name}")
                print("   请创建存储桶或检查存储桶名称")
                return False
            else:
                print(f"❌ 无法访问存储桶: {e}")
                return False
        
        # 检查写入权限
        try:
            test_key = "test/permissions-check.txt"
            s3_client.put_object(
                Bucket=bucket_name,
                Key=test_key,
                Body=b"Permission test"
            )
            print(f"✅ S3写入权限正常")
            
            # 清理测试文件
            s3_client.delete_object(Bucket=bucket_name, Key=test_key)
            print(f"✅ S3删除权限正常")
            
        except ClientError as e:
            print(f"❌ S3写入权限不足: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ S3权限检查失败: {e}")
        return False

def check_dynamodb_permissions():
    """检查DynamoDB权限"""
    print("\n🔍 检查DynamoDB权限...")
    
    try:
        dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        
        table_name = f"unimem-memories-{settings.ENVIRONMENT}"
        
        # 检查表是否存在
        try:
            table = dynamodb.Table(table_name)
            table.load()
            print(f"✅ DynamoDB表存在: {table_name}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"❌ DynamoDB表不存在: {table_name}")
                print("   请手动创建表或添加CreateTable权限")
                return False
            else:
                print(f"❌ 无法访问DynamoDB表: {e}")
                return False
        
        # 检查写入权限
        try:
            table.put_item(Item={
                'id': 'permissions-test',
                'content': 'Permission test',
                'memory_type': 'test',
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-01-01T00:00:00Z'
            })
            print(f"✅ DynamoDB写入权限正常")
            
            # 清理测试数据
            table.delete_item(Key={'id': 'permissions-test'})
            print(f"✅ DynamoDB删除权限正常")
            
        except ClientError as e:
            print(f"❌ DynamoDB写入权限不足: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ DynamoDB权限检查失败: {e}")
        return False

def main():
    """主函数"""
    print("🔍 UniMem AI 权限检查")
    print("=" * 50)
    
    s3_ok = check_s3_permissions()
    dynamodb_ok = check_dynamodb_permissions()
    
    print("\n" + "=" * 50)
    
    if s3_ok and dynamodb_ok:
        print("✅ 所有权限检查通过！")
        print("🚀 可以正常使用系统了")
        return True
    else:
        print("❌ 权限检查失败")
        print("\n📝 解决方案：")
        print("1. 为AWS用户添加以下权限：")
        print("   - AmazonS3FullAccess (或自定义S3权限)")
        print("   - AmazonDynamoDBFullAccess (或自定义DynamoDB权限)")
        print("2. 或者手动创建所需的资源")
        return False

if __name__ == "__main__":
    main()
