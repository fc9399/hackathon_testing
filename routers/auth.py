# 用户认证路由
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from services.auth_service import auth_service
from schemas import UserCreate, User, UserLogin, Token, UserUpdate

router = APIRouter(prefix="/api/auth", tags=["authentication"])
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """获取当前用户"""
    token = credentials.credentials
    token_data = auth_service.verify_token(token)
    user = await auth_service.get_user_by_username(token_data.username)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    return current_user

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    """用户注册"""
    try:
        return await auth_service.create_user(user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login(user_login: UserLogin):
    """用户登录"""
    try:
        return await auth_service.login_user(user_login)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """刷新访问令牌"""
    try:
        return await auth_service.refresh_access_token(refresh_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )

@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """获取当前用户信息"""
    return current_user

@router.put("/me", response_model=User)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """更新当前用户信息"""
    # 这里可以实现用户信息更新逻辑
    # 暂时返回当前用户信息
    return current_user

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """用户登出"""
    # 在实际应用中，可以将令牌加入黑名单
    # 这里只是返回成功消息
    return {"message": "Successfully logged out"}

@router.get("/health")
async def auth_health_check():
    """认证服务健康检查"""
    return auth_service.health_check()
