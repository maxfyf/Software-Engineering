from datetime import timedelta
from typing import Annotated, Optional
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from .database import engine, get_db
from .models import Base
from .schemas import (
    BaseResponse, UserRegisterRequest, UserLoginRequest, UserInfo,
    TaskCreateRequest, TaskUpdateRequest, TaskInfo, TaskStatus, TaskPriority
)
from .security import (
    get_current_user, create_access_token, hash_password, verify_password,
    validate_username, validate_password, ACCESS_TOKEN_EXPIRE_MINUTES
)
from .models import DBUser, DBTask

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 初始化FastAPI应用
app = FastAPI(title="任务管理系统API", debug=True)

# 依赖项简写
DBDep = Annotated[Session, Depends(get_db)]
CurrentUserDep = Annotated[DBUser, Depends(get_current_user)]

# ===================== 用户相关接口 =====================
@app.post("/register", response_model=BaseResponse, summary="用户注册")
async def register(user: UserRegisterRequest, db: DBDep):
    """新用户注册，包含格式校验与密码加密"""
    # 校验用户名格式
    if not validate_username(user.username):
        return BaseResponse(
            code=400,
            msg="用户名只能包含字母、数字、下划线，长度为4-20位"
        )
    # 校验密码格式
    if not validate_password(user.password):
        return BaseResponse(
            code=400,
            msg="密码长度不少于6位，必须同时包含字母和数字"
        )
    # 检查用户名是否已存在
    db_user = db.query(DBUser).filter(DBUser.username == user.username).first()
    if db_user:
        return BaseResponse(code=400, msg="用户已存在")
    # 创建新用户
    new_user = DBUser(
        username=user.username,
        hashed_password=hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return BaseResponse(
        code=200,
        msg="注册成功",
        data={"user_id": new_user.id, "username": new_user.username}
    )

@app.post("/login", response_model=BaseResponse, summary="用户登录")
async def login(user: UserLoginRequest, db: DBDep):
    """用户登录，返回JWT Token用于后续认证"""
    # 检查用户是否存在
    db_user = db.query(DBUser).filter(DBUser.username == user.username).first()
    if not db_user:
        return BaseResponse(code=404, msg="用户不存在")
    # 校验密码
    if not verify_password(user.password, db_user.hashed_password):
        return BaseResponse(code=401, msg="密码错误")
    # 生成Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.id}, expires_delta=access_token_expires
    )
    # 登录成功
    return BaseResponse(
        code=200,
        msg="登录成功",
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": db_user.id,
            "username": db_user.username
        }
    )

@app.get("/users/me", response_model=BaseResponse, summary="获取当前用户信息")
async def get_my_info(current_user: CurrentUserDep):
    """验证登录状态并获取当前用户信息"""
    return BaseResponse(
        code=200,
        msg="获取成功",
        data=UserInfo.from_orm(current_user).dict()
    )

# ===================== 任务相关接口 =====================
@app.post("/tasks", response_model=BaseResponse, summary="创建任务")
async def create_task(task: TaskCreateRequest, current_user: CurrentUserDep, db: DBDep):
    """登录用户创建个人任务"""
    new_task = DBTask(
        user_id=current_user.id,
        title=task.title,
        description=task.description,
        status=task.status.value,
        priority=task.priority.value,
        deadline=task.deadline
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return BaseResponse(
        code=200,
        msg="任务创建成功",
        data=TaskInfo.from_orm(new_task).dict()
    )

@app.get("/tasks", response_model=BaseResponse, summary="获取任务列表")
async def get_task_list(
    current_user: CurrentUserDep,
    db: DBDep,
    page: int = 1,
    page_size: int = 10,
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None
):
    """获取当前用户的任务列表，支持分页与筛选"""
    # 基础查询：仅当前用户的任务
    query = db.query(DBTask).filter(DBTask.user_id == current_user.id)
    # 可选筛选
    if status:
        query = query.filter(DBTask.status == status.value)
    if priority:
        query = query.filter(DBTask.priority == priority.value)
    # 分页
    total = query.count()
    tasks = query.order_by(DBTask.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()

    return BaseResponse(
        code=200,
        msg="获取成功",
        data={
            "total": total,
            "page": page,
            "page_size": page_size,
            "tasks": [TaskInfo.from_orm(task).dict() for task in tasks]
        }
    )

@app.get("/tasks/{task_id}", response_model=BaseResponse, summary="获取任务详情")
async def get_task_detail(task_id: int, current_user: CurrentUserDep, db: DBDep):
    """获取指定任务的详情，仅能查看自己的任务"""
    task = db.query(DBTask).filter(DBTask.id == task_id).first()
    if not task:
        return BaseResponse(code=404, msg="任务不存在")
    if task.user_id != current_user.id:
        return BaseResponse(code=403, msg="无权访问此任务")
    
    return BaseResponse(
        code=200,
        msg="获取成功",
        data=TaskInfo.from_orm(task).dict()
    )

@app.put("/tasks/{task_id}", response_model=BaseResponse, summary="修改任务")
async def update_task(task_id: int, task_update: TaskUpdateRequest, current_user: CurrentUserDep, db: DBDep):
    """修改指定任务，仅能修改自己的任务"""
    task = db.query(DBTask).filter(DBTask.id == task_id).first()
    if not task:
        return BaseResponse(code=404, msg="任务不存在")
    if task.user_id != current_user.id:
        return BaseResponse(code=403, msg="无权修改此任务")
    
    # 更新字段
    update_data = task_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key in ["status", "priority"]:
            setattr(task, key, value.value)
        else:
            setattr(task, key, value)
    
    db.commit()
    db.refresh(task)

    return BaseResponse(
        code=200,
        msg="修改成功",
        data=TaskInfo.from_orm(task).dict()
    )

@app.delete("/tasks/{task_id}", response_model=BaseResponse, summary="删除任务")
async def delete_task(task_id: int, current_user: CurrentUserDep, db: DBDep):
    """删除指定任务，仅能删除自己的任务"""
    task = db.query(DBTask).filter(DBTask.id == task_id).first()
    if not task:
        return BaseResponse(code=404, msg="任务不存在")
    if task.user_id != current_user.id:
        return BaseResponse(code=403, msg="无权删除此任务")
    
    db.delete(task)
    db.commit()

    return BaseResponse(code=200, msg="删除成功")