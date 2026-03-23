from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

# 路由定义
router = APIRouter(prefix="/api/auth", tags=["用户认证"])

# 请求参数模型
class UserRequest(BaseModel):
    username: str
    password: str

# 1. 注册接口
@router.post("/register")
def register(user: UserRequest):
    if not user.username or not user.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名和密码不能为空"
        )
    # 返回标准JSON
    return {"code": 200, "msg": "注册接口调用成功", "data": None}

# 2. 登录接口
@router.post("/login")
def login(user: UserRequest):
    if len(user.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码长度不能少于6位"
        )
    # 返回标准JSON（包含token）
    return {
        "code": 200,
        "msg": "登录成功",
        "data": {"token": "user_login_token"}
    }