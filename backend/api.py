from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional, Dict, Any
import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 数据库配置
SQLALCHEMY_DATABASE_URL = "sqlite:///test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# FastAPI应用初始化
app = FastAPI(title="软工Lab1 - 整合版API层", debug=True)

# 模型定义
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# 用户请求模型
class UserRequest(BaseModel):
    username: str
    password: str

# 任务模型
class TaskCreate(BaseModel):
    title: str
    content: str
    status: Optional[str] = "pending"

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None

# 通用响应模型
class ApiResponse(BaseModel):
    success: bool
    msg: str
    data: Optional[Dict[str, Any]] = None


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login")

# 数据库会话依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

DBDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]

# 工具函数
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: TokenDep, db: DBDep):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="登录状态已过期，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    # 模拟数据库查询用户
    if token_data.username is None:
        raise credentials_exception
    return {"username": token_data.username, "id": 1}

UserDep = Annotated[Dict[str, Any], Depends(get_current_user)]

# 路由定义
# 用户模块路由
user_router = APIRouter(prefix="/user", tags=["用户模块"])
# 任务模块路由
task_router = APIRouter(prefix="/task", tags=["任务模块"])

# 用户模块接口
@user_router.post("/register", response_model=ApiResponse)
def register(user: UserRequest, db: DBDep):
    # 后端打印请求信息
    print(f"【注册接口】收到请求 - 用户名：{user.username}，密码：{user.password}")
    # 校验逻辑
    if not user.username or not user.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名和密码不能为空"
        )
    # 返回前端可显示的响应
    return ApiResponse(
        success=True,
        msg="注册成功",
        data=None
    )

@user_router.post("/login", response_model=ApiResponse)
def login(user: UserRequest, db: DBDep):
    # 后端打印请求信息
    print(f"【登录接口】收到请求 - 用户名：{user.username}，密码：{user.password}")
    # 校验逻辑
    if len(user.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码长度不能少于6位"
        )
    # 生成Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    # 返回前端可显示的响应
    return ApiResponse(
        success=True,
        msg="登录成功",
        data={"token": access_token}
    )

@user_router.post("/logout", response_model=ApiResponse)
def logout(current_user: UserDep, db: DBDep):
    # 后端打印请求信息
    print(f"【登出接口】收到请求 - 用户名：{current_user['username']}")
    # 返回前端响应
    return ApiResponse(
        success=True,
        msg="登出成功",
        data=None
    )

@user_router.get("/info", response_model=ApiResponse)
def get_user_info(current_user: UserDep, db: DBDep):
    # 后端打印请求信息
    print(f"【用户信息接口】收到请求 - 用户名：{current_user['username']}")
    # 模拟用户信息
    user_info = {
        "username": current_user["username"],
        "id": current_user["id"],
        "email": f"{current_user['username']}@test.com"
    }
    # 返回前端响应
    return ApiResponse(
        success=True,
        msg="获取用户信息成功",
        data=user_info
    )

@user_router.delete("/cancel", response_model=ApiResponse)
def cancel_account(current_user: UserDep, db: DBDep):
    # 后端打印请求信息
    print(f"【注销账号接口】收到请求 - 用户名：{current_user['username']}")
    # 返回前端响应
    return ApiResponse(
        success=True,
        msg="账号注销成功",
        data=None
    )

# 任务模块接口
@task_router.get("/list", response_model=ApiResponse)
def get_task_list(current_user: UserDep, db: DBDep):
    # 后端打印请求信息
    print(f"【任务列表接口】收到请求 - 用户名：{current_user['username']}")
    # 模拟任务列表数据
    task_list = [
        {"id": 1, "title": "任务1", "content": "完成Lab1", "status": "pending"},
        {"id": 2, "title": "任务2", "content": "整合前后端", "status": "done"}
    ]
    # 返回前端响应
    return ApiResponse(
        success=True,
        msg="获取任务列表成功",
        data=task_list
    )

@task_router.get("/{taskId}", response_model=ApiResponse)
def get_task_by_id(taskId: int, current_user: UserDep, db: DBDep):
    # 后端打印请求信息
    print(f"【任务详情接口】收到请求 - 用户名：{current_user['username']},任务ID:{taskId}")
    # 模拟任务数据
    task_detail = {
        "id": taskId,
        "title": f"任务{taskId}",
        "content": f"这是任务{taskId}的详情",
        "status": "pending",
        "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    # 返回前端响应
    return ApiResponse(
        success=True,
        msg=f"获取任务{taskId}详情成功",
        data=task_detail
    )

@task_router.post("/create", response_model=ApiResponse)
def create_task(task: TaskCreate, current_user: UserDep, db: DBDep):
    # 后端打印请求信息
    print(f"【创建任务接口】收到请求 - 用户名：{current_user['username']}，任务标题：{task.title}")
    # 模拟创建任务
    new_task = {
        "id": 999,
        "title": task.title,
        "content": task.content,
        "status": task.status,
        "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    # 返回前端响应
    return ApiResponse(
        success=True,
        msg="任务创建成功",
        data=new_task
    )

@task_router.put("/{taskId}", response_model=ApiResponse)
def update_task(taskId: int, task: TaskUpdate, current_user: UserDep, db: DBDep):
    # 后端打印请求信息
    print(f"【更新任务接口】收到请求 - 用户名：{current_user['username']},任务ID:{taskId}，更新内容:{task.dict()}")
    # 模拟更新后的数据
    updated_task = {
        "id": taskId,
        "title": task.title or f"任务{taskId}",
        "content": task.content or f"这是任务{taskId}的原始内容",
        "status": task.status or "pending",
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    # 返回前端响应
    return ApiResponse(
        success=True,
        msg=f"任务{taskId}更新成功",
        data=updated_task
    )

@task_router.delete("/{taskId}", response_model=ApiResponse)
def delete_task(taskId: int, current_user: UserDep, db: DBDep):
    # 后端打印请求信息
    print(f"【删除任务接口】收到请求 - 用户名：{current_user['username']}，任务ID：{taskId}")
    # 返回前端响应
    return ApiResponse(
        success=True,
        msg=f"任务{taskId}删除成功",
        data=None
    )

# 挂载路由
app.include_router(user_router)
app.include_router(task_router)

# 启动入口
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)