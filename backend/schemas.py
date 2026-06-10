from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

# 用于接收 API 传来的注册数据
class UserCreate(BaseModel):
    """用户注册请求的数据模型。"""

    # 基础长度兜底，防止数据库溢出
    username: str = Field(..., min_length=4, max_length=20, description="注册用户名。")
    password: str = Field(..., min_length=6, description="注册密码。")
    first_name: str | None = Field(None, description="名字，可为空。")
    last_name: str | None = Field(None, description="姓氏，可为空。")
    phone_number: str | None = Field(None, description="联系电话，可为空。")
    email: str | None = Field(None, description="邮箱地址，可为空。")

# 用于将用户信息返回给 API （不包含密码）
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

TeamRoleValue = Literal["Owner", "Admin", "Member"]

class TeamCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=10)

class TeamResponse(BaseModel):
    id: int
    name: str
    owner_username: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TeamMemberCreate(BaseModel):
    username: str = Field(..., min_length=4, max_length=20)

class TeamMemberRoleUpdate(BaseModel):
    role: Literal["Admin", "Member"]

class TeamMemberResponse(BaseModel):
    id: int
    team_id: int
    username: str
    role: TeamRoleValue
    joined_at: datetime

    class Config:
        from_attributes = True

# 用于接收创建任务的数据
class TaskCreate(BaseModel):
    """团队任务创建接口使用的数据模型。"""

    title: str = Field(..., max_length=100, description="任务标题。")
    description: Optional[str] = Field(None, description="任务描述。")
    status: str = Field("待办", description="任务状态。")
    priority: str = Field("中", description="任务优先级。")
    due_date: Optional[datetime] = Field(None, description="任务截止时间。")

    #任务归属ID
    team_id: Optional[int] = Field(None, description="归属团队 ID。")
    assignee_username: Optional[str] = Field(None, description="负责人用户名。")

# 用于接收更新任务的数据
class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None

# 用于返回任务详情给前端
class TaskResponse(BaseModel):
    """任务详情响应的数据模型。"""

    id: int
    title: str
    description: Optional[str]
    status: str
    priority: str
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    owner_username: str
    #任务归属ID，如果是团队任务则有值，否则为null
    team_id: Optional[int] = None
    assignee_username: Optional[str] = None
    class Config:
        from_attributes = True

# 统一接口返回格式
class BaseResponse(BaseModel):
    code: int
    msg: str
    data: Optional[dict | list | None] = None


# ---------- 任务依赖相关 ----------
class TaskDependencyBase(BaseModel):
    predecessor_id: int
    successor_id: int

class TaskDependencyCreate(TaskDependencyBase):
    pass

class TaskDependencyOut(TaskDependencyBase):
    id: int
    class Config:
        from_attributes = True

class UpdatePredecessorsRequest(BaseModel):
    """更新前置任务列表"""
    predecessor_ids: list[int]

# ---------- 团队管理扩展 ----------
class TransferOwnerRequest(BaseModel):
    """转让团队所有权"""
    new_owner_id: str

class LeaveTeamRequest(BaseModel):
    """主动离开团队"""
    pass


from typing import Optional, Dict, Any, List

class OperationObject(BaseModel):
    id: int
    title: str
    type: str          # 固定 "task"
    deleted: bool

class OperationScope(BaseModel):
    type: str          # "personal" 或 "team"
    id: Optional[int] = None
    title: str

class OperationLogOut(BaseModel):
    id: int
    operator: str
    type: str
    object: OperationObject
    operatedAt: str    # ISO格式时间字符串
    description: str
    scope: OperationScope

    class Config:
        orm_mode = True

# 用于通用API响应包装
class OperationLogListResponse(BaseModel):
    success: bool
    data: List[OperationLogOut]