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