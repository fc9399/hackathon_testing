# 上传路由
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.s3_service import s3_service
from services.parser_service import parser_service
from services.auth_service import auth_service
from schemas import FileUploadResponse, User
from typing import Optional

router = APIRouter(prefix="/api", tags=["upload"])

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> User:
    """获取当前用户"""
    token = credentials.credentials
    token_data = auth_service.verify_token(token)
    user = await auth_service.get_user_by_username(token_data.username)
    
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    parse_and_store: bool = True,
    current_user: User = Depends(get_current_user)
):
    """
    上传文件到S3并可选解析存储为记忆
    
    Parameters:
        file: 上传的文件
        parse_and_store: 是否解析并存储为记忆单元
    
    Returns:
        JSON响应包含文件信息和记忆ID
    """
    try:
        # 上传到S3
        file_data = await s3_service.upload_file(file)
        
        response_data = {
            "success": True,
            "message": "File uploaded successfully",
            "data": file_data
        }
        
        # 如果启用解析，则解析文件并创建记忆
        if parse_and_store:
            try:
                parse_result = await parser_service.parse_file(file, file_data, current_user.id)
                response_data["memory"] = {
                    "memory_id": parse_result["memory_id"],
                    "parsed_content": parse_result["parsed_content"],
                    "embedding_dimension": parse_result["embedding_dimension"]
                }
                response_data["message"] = "File uploaded and parsed successfully"
            except Exception as parse_error:
                # 解析失败不影响上传，但记录错误
                response_data["parse_error"] = str(parse_error)
                response_data["message"] = "File uploaded but parsing failed"
        
        return JSONResponse(
            status_code=200,
            content=response_data
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/upload/text")
async def upload_text(
    text: str = Query(..., description="要上传的文本内容"),
    source: Optional[str] = Query(None, description="来源标识"),
    current_user: User = Depends(get_current_user)
):
    """
    直接上传文本内容并创建记忆
    
    Parameters:
        text: 文本内容
        source: 来源标识
    
    Returns:
        JSON响应包含记忆ID
    """
    try:
        parse_result = await parser_service.parse_text_input(text, source, current_user.id)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Text uploaded and stored as memory",
                "memory_id": parse_result["memory_id"],
                "content": parse_result["content"],
                "embedding_dimension": parse_result["embedding_dimension"]
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text upload failed: {str(e)}")

@router.get("/upload/supported-types")
async def get_supported_types():
    """
    获取支持的文件类型列表
    """
    try:
        supported_types = parser_service.get_supported_types()
        
        return {
            "supported_types": supported_types,
            "total": len(supported_types)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get supported types: {str(e)}")

@router.get("/upload/health")
async def upload_health_check():
    """检查上传和解析服务健康状态"""
    try:
        s3_health = s3_service.health_check()
        parser_health = parser_service.health_check()
        
        overall_status = "healthy" if (
            s3_health["status"] == "healthy" and 
            parser_health["status"] == "healthy"
        ) else "unhealthy"
        
        return {
            "status": overall_status,
            "services": {
                "s3": s3_health,
                "parser": parser_health
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }