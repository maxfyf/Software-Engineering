from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import re

from .database import get_db
from .models import DBUser

# ===================== 配置项 =====================
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120  # 登录状态2小时有效

# ===================== 工具实例 =====================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ===================== 密码相关 =====================
def hash_password(password: str) -> str:
    """将明文密码加密为哈希值"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码与哈希值是否匹配"""
    return pwd_context.verify(plain_password, hashed_password)

# ===================== 格式校验 =====================
def validate_username(username: str) -> bool:
    """校验用户名格式：仅允许字母、数字、下划线，长度4-20位"""
    pattern = r'^[a-zA-Z0-9_]{4,20}$'
    return re.match(pattern, username) is not None

def validate_password(password: str) -> bool:
    """校验密码格式：长度不少于6位，同时包含字母和数字"""
    if len(password) < 6:
        return False
    has_letter = re.search(r'[a-zA-Z]', password) is not None
    has_number = re.search(r'[0-9]', password) is not None
    return has_letter and has_number

# ===================== JWT Token相关 =====================
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """生成JWT访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)]
) -> DBUser:
    """从Token中获取当前登录用户，用于接口认证"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="登录状态无效，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user