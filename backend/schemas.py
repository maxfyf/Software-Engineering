from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

# 用于接收 API 层传来的注册数据
class UserCreate(BaseModel):
    # 基础长度兜底，防止数据库溢出
    username: str = Field(..., min_length=4, max_length=20)
    password: str = Field(..., min_length=6)
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    email: str | None = None

# 用于将用户信息返回给 API 层（不包含密码）
class UserResponse(BaseModel):
    username: str
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    email: str | None = None

    class Config:
        from_attributes = True  # 允许直接从 SQLAlchemy 模型转换

# 用于返回生成的 Token
class Token(BaseModel):
    access_token: str
    token_type: str

# 用于接收创建任务的数据
class TaskCreate(BaseModel):
    title: str = Field(..., max_length=100)
    description: Optional[str] = None
    status: str = "待办"
    priority: str = "中"
    due_date: Optional[datetime] = None

# 用于接收更新任务的数据
class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None

# 用于返回任务详情给前端
class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    priority: str
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    owner_username: str

    class Config:
        from_attributes = True

# 统一接口返回格式
class BaseResponse(BaseModel):
    code: int
    msg: str
    data: Optional[dict | list | None] = None    
