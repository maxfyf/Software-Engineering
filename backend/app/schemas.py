from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

# 任务状态枚举
class TaskStatus(str, Enum):
    TODO = "待办"
    IN_PROGRESS = "进行中"
    COMPLETED = "已完成"

# 任务优先级枚举
class TaskPriority(str, Enum):
    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"

# ===================== 通用响应模型 =====================
class BaseResponse(BaseModel):
    code: int
    msg: str
    data: Optional[dict | list] = None

# ===================== 用户相关模型 =====================
class UserRegisterRequest(BaseModel):
    username: str = Field(description="用户名，仅允许字母、数字、下划线，长度4-20位")
    password: str = Field(description="密码，长度不少于6位，必须同时包含字母和数字")

class UserLoginRequest(BaseModel):
    username: str
    password: str

class UserInfo(BaseModel):
    id: int
    username: str
    is_active: bool

    class Config:
        orm_mode = True

# ===================== 任务相关模型 =====================
class TaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100, description="任务标题")
    description: Optional[str] = Field(default=None, description="任务描述")
    status: TaskStatus = Field(default=TaskStatus.TODO, description="任务状态")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="任务优先级")
    deadline: Optional[datetime] = Field(default=None, description="任务截止时间")

class TaskUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None)
    status: Optional[TaskStatus] = Field(default=None)
    priority: Optional[TaskPriority] = Field(default=None)
    deadline: Optional[datetime] = Field(default=None)

class TaskInfo(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    deadline: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True