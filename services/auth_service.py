# 用户认证服务
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status
from config import settings
from schemas import UserCreate, UserInDB, User, UserLogin, Token, TokenData
import boto3
from botocore.exceptions import ClientError

class AuthService:
    """
    用户认证服务 - 处理用户注册、登录、JWT令牌管理
    使用DynamoDB存储用户信息
    """
    
    def __init__(self):
        # 密码加密上下文
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # 检查是否为测试模式
        if settings.ENVIRONMENT == "test":
            self.dynamodb = None
            self.users_table_name = None
            self.dynamodb_disabled = True
            print("🧪 认证服务运行在测试模式")
            return
        
        # 检查AWS配置
        if (not settings.AWS_ACCESS_KEY_ID or 
            settings.AWS_ACCESS_KEY_ID == "your_aws_access_key_here" or
            not settings.S3_BUCKET_NAME or
            settings.S3_BUCKET_NAME == "your-s3-bucket-name"):
            raise ValueError("AWS配置未完成，请设置AWS_ACCESS_KEY_ID、AWS_SECRET_ACCESS_KEY和S3_BUCKET_NAME环境变量")
        
        # DynamoDB 客户端
        self.dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        
        # 用户表名
        self.users_table_name = f"unimem-users-{settings.ENVIRONMENT}"
        
        # 初始化用户表
        self._init_users_table()
    
    def _init_users_table(self):
        """初始化用户表"""
        try:
            # 检查表是否存在
            try:
                self.dynamodb.Table(self.users_table_name).load()
                print(f"📋 Users table already exists: {self.users_table_name}")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    # 表不存在，尝试创建
                    print(f"🔨 Creating users table: {self.users_table_name}")
                    users_table = self.dynamodb.create_table(
                        TableName=self.users_table_name,
                        KeySchema=[
                            {'AttributeName': 'id', 'KeyType': 'HASH'}
                        ],
                        AttributeDefinitions=[
                            {'AttributeName': 'id', 'AttributeType': 'S'},
                            {'AttributeName': 'username', 'AttributeType': 'S'},
                            {'AttributeName': 'email', 'AttributeType': 'S'}
                        ],
                        GlobalSecondaryIndexes=[
                            {
                                'IndexName': 'username_index',
                                'KeySchema': [
                                    {'AttributeName': 'username', 'KeyType': 'HASH'}
                                ],
                                'Projection': {'ProjectionType': 'ALL'}
                            },
                            {
                                'IndexName': 'email_index',
                                'KeySchema': [
                                    {'AttributeName': 'email', 'KeyType': 'HASH'}
                                ],
                                'Projection': {'ProjectionType': 'ALL'}
                            }
                        ],
                        BillingMode='PAY_PER_REQUEST'
                    )
                    print(f"✅ Users table created: {self.users_table_name}")
                else:
                    print(f"❌ Error checking users table {self.users_table_name}: {e}")
                    raise
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDeniedException':
                print(f"⚠️  Access denied accessing DynamoDB. Please ensure your AWS user has DynamoDB permissions.")
                print(f"   Required permissions: CreateTable, DescribeTable, PutItem, GetItem, UpdateItem, DeleteItem, Query, Scan")
                print(f"   Or manually create table: {self.users_table_name}")
                raise
            else:
                print(f"❌ Error with users table: {e}")
                raise
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """生成密码哈希"""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """创建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> TokenData:
        """验证令牌"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            username: str = payload.get("sub")
            user_id: str = payload.get("user_id")
            token_type_claim: str = payload.get("type")
            
            if username is None or user_id is None or token_type_claim != token_type:
                raise credentials_exception
            
            token_data = TokenData(username=username, user_id=user_id)
            return token_data
            
        except JWTError:
            raise credentials_exception
    
    async def create_user(self, user: UserCreate) -> User:
        """创建新用户"""
        # 检查用户名是否已存在
        if await self.get_user_by_username(user.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # 检查邮箱是否已存在
        if await self.get_user_by_email(user.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # 创建用户ID
        user_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        # 准备用户数据
        user_data = {
            'id': user_id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name,
            'hashed_password': self.get_password_hash(user.password),
            'is_active': True,
            'created_at': now,
            'updated_at': now
        }
        
        try:
            # 存储到DynamoDB
            table = self.dynamodb.Table(self.users_table_name)
            table.put_item(Item=user_data)
            
            print(f"✅ User created: {user.username} ({user_id})")
            
            # 返回用户信息（不包含密码）
            return User(
                id=user_id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                is_active=True,
                created_at=datetime.fromisoformat(now),
                updated_at=datetime.fromisoformat(now)
            )
            
        except Exception as e:
            print(f"❌ Failed to create user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        try:
            table = self.dynamodb.Table(self.users_table_name)
            response = table.get_item(Key={'id': user_id})
            
            if 'Item' in response:
                item = response['Item']
                return User(
                    id=item['id'],
                    username=item['username'],
                    email=item['email'],
                    full_name=item.get('full_name'),
                    is_active=item.get('is_active', True),
                    created_at=datetime.fromisoformat(item['created_at']),
                    updated_at=datetime.fromisoformat(item['updated_at'])
                )
            return None
            
        except Exception as e:
            print(f"❌ Failed to get user by ID {user_id}: {e}")
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        try:
            table = self.dynamodb.Table(self.users_table_name)
            response = table.query(
                IndexName='username_index',
                KeyConditionExpression='username = :username',
                ExpressionAttributeValues={':username': username}
            )
            
            if response['Items']:
                item = response['Items'][0]
                return User(
                    id=item['id'],
                    username=item['username'],
                    email=item['email'],
                    full_name=item.get('full_name'),
                    is_active=item.get('is_active', True),
                    created_at=datetime.fromisoformat(item['created_at']),
                    updated_at=datetime.fromisoformat(item['updated_at'])
                )
            return None
            
        except Exception as e:
            print(f"❌ Failed to get user by username {username}: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        try:
            table = self.dynamodb.Table(self.users_table_name)
            response = table.query(
                IndexName='email_index',
                KeyConditionExpression='email = :email',
                ExpressionAttributeValues={':email': email}
            )
            
            if response['Items']:
                item = response['Items'][0]
                return User(
                    id=item['id'],
                    username=item['username'],
                    email=item['email'],
                    full_name=item.get('full_name'),
                    is_active=item.get('is_active', True),
                    created_at=datetime.fromisoformat(item['created_at']),
                    updated_at=datetime.fromisoformat(item['updated_at'])
                )
            return None
            
        except Exception as e:
            print(f"❌ Failed to get user by email {email}: {e}")
            return None
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """验证用户"""
        user = await self.get_user_by_username(username)
        if not user:
            return None
        
        # 获取完整用户信息（包含密码哈希）
        try:
            table = self.dynamodb.Table(self.users_table_name)
            response = table.get_item(Key={'id': user.id})
            
            if 'Item' in response:
                item = response['Item']
                if not self.verify_password(password, item['hashed_password']):
                    return None
                
                return User(
                    id=item['id'],
                    username=item['username'],
                    email=item['email'],
                    full_name=item.get('full_name'),
                    is_active=item.get('is_active', True),
                    created_at=datetime.fromisoformat(item['created_at']),
                    updated_at=datetime.fromisoformat(item['updated_at'])
                )
            
            return None
            
        except Exception as e:
            print(f"❌ Failed to authenticate user {username}: {e}")
            return None
    
    async def login_user(self, user_login: UserLogin) -> Token:
        """用户登录"""
        user = await self.authenticate_user(user_login.username, user_login.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        # 创建令牌
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            data={"sub": user.username, "user_id": user.id}, 
            expires_delta=access_token_expires
        )
        
        refresh_token = self.create_refresh_token(
            data={"sub": user.username, "user_id": user.id}
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    async def refresh_access_token(self, refresh_token: str) -> Token:
        """刷新访问令牌"""
        token_data = self.verify_token(refresh_token, "refresh")
        user = await self.get_user_by_username(token_data.username)
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # 创建新的访问令牌
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            data={"sub": user.username, "user_id": user.id}, 
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,  # 保持原刷新令牌
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 检查DynamoDB连接
            table = self.dynamodb.Table(self.users_table_name)
            self.dynamodb.meta.client.describe_table(TableName=self.users_table_name)
            
            return {
                'status': 'healthy',
                'service': 'auth',
                'dynamodb': 'connected',
                'table': self.users_table_name,
                'encryption': 'bcrypt'
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'service': 'auth',
                'error': str(e)
            }

# 全局实例
auth_service = AuthService()
