# backend/api.py - 统一的 FastAPI 后端入口

from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from database import get_db, Base, engine
from models import User, Task
from schemas import UserCreate
from security import verify_password, get_password_hash, create_access_token
import crud

# ===================== 初始化数据库 =====================
Base.metadata.create_all(bind=engine)

# ===================== 创建应用 =====================
app = FastAPI(title="协作式任务管理系统 API")

# CORS 配置 - 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== Pydantic 请求模型 =====================

class LoginRequest(BaseModel):
    username: str
    password: str

class TaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    status: str = "待办"
    priority: str = "中"
    deadline: Optional[str] = None

class TaskUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    deadline: Optional[str] = None

# ===================== 统一响应格式 =====================

def success_response(msg: str, data=None):
    return {"success": True, "msg": msg, "data": data}

def error_response(msg: str):
    return {"success": False, "msg": msg, "data": None}

# ===================== 依赖：获取当前用户 =====================

def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    """从 Authorization header 获取当前用户"""
    from jose import jwt
    from security import SECRET_KEY, ALGORITHM
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录"
        )
    
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="无效Token")
    except Exception:
        raise HTTPException(status_code=401, detail="登录已过期")
    
    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    
    return user

# ===================== 用户模块 =====================

@app.post("/api/user/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    if crud.get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 检查邮箱是否已存在
    if user.email and crud.get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="该邮箱已被注册")
    
    # 创建用户
    db_user = crud.create_user(db, user)
    
    return success_response("注册成功", {"username": db_user.username})

@app.post("/api/user/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    user, error_msg = crud.authenticate_user(db, request.username, request.password)
    if not user:
        if error_msg == "用户不存在":
            raise HTTPException(status_code=404, detail=error_msg)
        if error_msg == "密码错误":
            raise HTTPException(status_code=401, detail=error_msg)
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 生成 Token
    token = create_access_token({"sub": user.username})
    
    return success_response("登录成功", {
        "token": token,
        "userInfo": {
            "username": user.username,
            "firstName": user.first_name,
            "lastName": user.last_name,
            "phone": user.phone_number,
            "email": user.email
        }
    })

@app.post("/api/user/logout")
def logout():
    """用户登出"""
    return success_response("登出成功")

@app.get("/api/user/info")
def get_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return success_response("获取成功", {
        "username": current_user.username,
        "firstName": current_user.first_name,
        "lastName": current_user.last_name,
        "phone": current_user.phone_number,
        "email": current_user.email
    })

@app.delete("/api/user/cancel")
def cancel_account(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """注销账号"""
    db.delete(current_user)
    db.commit()
    return success_response("账号已注销")

# ===================== 任务模块 =====================

@app.get("/api/task/list")
def get_task_list(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取任务列表 - 仅当前用户的任务"""
    tasks = db.query(Task).filter(Task.owner_username == current_user.username).all()
    
    task_list = []
    for task in tasks:
        task_list.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "deadline": task.due_date.strftime("%Y-%m-%d") if task.due_date else None,
            "createdAt": task.created_at.strftime("%Y-%m-%d %H:%M:%S") if task.created_at else None,
            "updatedAt": task.updated_at.strftime("%Y-%m-%d %H:%M:%S") if task.updated_at else None,
            "owner": task.owner_username
        })
    
    return success_response("获取成功", task_list)

@app.get("/api/task/{task_id}")
def get_task(task_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取任务详情 - 仅自己的任务"""
    task = db.query(Task).filter(Task.id == task_id, Task.owner_username == current_user.username).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或无权限查看")
    
    return success_response("获取成功", {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "deadline": task.due_date.strftime("%Y-%m-%d") if task.due_date else None,
        "createdAt": task.created_at.strftime("%Y-%m-%d %H:%M:%S") if task.created_at else None,
        "updatedAt": task.updated_at.strftime("%Y-%m-%d %H:%M:%S") if task.updated_at else None,
        "owner": task.owner_username
    })

@app.post("/api/task/create")
def create_task(task: TaskCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """创建任务"""
    db_task = Task(
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        owner_username=current_user.username
    )
    
    if task.deadline:
        try:
            db_task.due_date = datetime.strptime(task.deadline, "%Y-%m-%d")
        except:
            pass
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    return success_response("创建成功", {
        "id": db_task.id,
        "title": db_task.title,
        "description": db_task.description,
        "status": db_task.status,
        "priority": db_task.priority,
        "deadline": task.deadline,
        "createdAt": db_task.created_at.strftime("%Y-%m-%d %H:%M:%S") if db_task.created_at else None,
        "updatedAt": db_task.updated_at.strftime("%Y-%m-%d %H:%M:%S") if db_task.updated_at else None
    })

@app.put("/api/task/{task_id}")
def update_task(task_id: int, task_update: TaskUpdateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """更新任务 - 仅自己的任务可编辑"""
    task = db.query(Task).filter(Task.id == task_id, Task.owner_username == current_user.username).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或无权限编辑")
    
    if task_update.title is not None:
        task.title = task_update.title
    if task_update.description is not None:
        task.description = task_update.description
    if task_update.status is not None:
        task.status = task_update.status
    if task_update.priority is not None:
        task.priority = task_update.priority
    if task_update.deadline is not None:
        try:
            task.due_date = datetime.strptime(task_update.deadline, "%Y-%m-%d")
        except:
            pass
    
    db.commit()
    db.refresh(task)
    
    return success_response("更新成功")

@app.delete("/api/task/{task_id}")
def delete_task(task_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """删除任务 - 仅自己的任务可删除"""
    task = db.query(Task).filter(Task.id == task_id, Task.owner_username == current_user.username).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或无权限删除")
    
    db.delete(task)
    db.commit()
    
    return success_response("删除成功")

# ===================== 健康检查 =====================

@app.get("/")
def root():
    return {"message": "API 服务运行中", "status": "ok"}

@app.get("/api/health")
def health():
    return {"status": "ok"}

# 团队任务相关接口
# 仅团队管理员/创建者可管理任务，普通成员仅可查看与修改自身任务状态

@app.get("/api/tasks/assigned", response_model=dict)
def get_assigned_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取分配给当前用户的所有团队任务
    无需指定团队，直接展示“我的待办”
    """
    tasks = crud.get_assigned_tasks(db, current_user.username)
    return success_response("获取分配任务成功", [
        {
            "id": t.id,
            "title": t.title,
            "status": t.status,
            "team_id": t.team_id,
            "owner_username": t.owner_username,
            "assignee_username": t.assignee_username,
            "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S")
        } for t in tasks
    ])


@app.get("/api/teams/{team_id}/tasks", response_model=dict)
def get_team_tasks(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定团队的所有任务
    必须是团队成员才能查看
    """
    if team_id <= 0:
        return error_response("无效的团队ID", 400)
    if not crud.require_team_member(db, team_id, current_user.username):
        return error_response("无权访问该团队", 403)
    
    tasks = crud.get_team_tasks(db, team_id)
    return success_response("获取团队任务成功", [
        {
            "id": t.id,
            "title": t.title,
            "status": t.status,
            "owner_username": t.owner_username,
            "assignee_username": t.assignee_username
        } for t in tasks
    ])


@app.post("/api/teams/{team_id}/tasks", response_model=dict)
def create_team_task(
    team_id: int,
    task: schemas.TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    在指定团队下创建任务
    仅管理员和创建者可操作
    """
    if team_id <= 0:
        return error_response("无效的团队ID", 400)
    if not task.title or not task.title.strip():
        return error_response("任务标题不能为空", 400)
    if not crud.require_team_role(db, team_id, current_user.username, {crud.ROLE_ADMIN, crud.ROLE_OWNER}):
        return error_response("无权创建团队任务", 403)
    
    task.team_id = team_id
    new_task = crud.create_team_task(db, task, current_user.username)
    return success_response("团队任务创建成功", {"id": new_task.id})


@app.put("/api/tasks/{task_id}/status", response_model=dict)
def update_task_status(
    task_id: int,
    status: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    普通成员专用：仅更新任务状态
    只能修改分配给自己的任务
    """
    if task_id <= 0:
        return error_response("无效的任务ID", 400)
    if not status or not status.strip():
        return error_response("任务状态不能为空", 400)
    try:
        task = crud.get_task_by_id(db, task_id, current_user.username)
    except HTTPException as e:
        return error_response(e.detail, e.status_code)
    if not task.assignee_username:
        return error_response("该任务未分配任何人", 403)
    
    if task.assignee_username != current_user.username:
        return error_response("只能修改分配给自己的任务状态", 403)
    
    updated_task = crud.update_task_status_only(db, task_id, status)
    if not updated_task:
        return error_response("任务状态更新失败", 500)
    return success_response("任务状态更新成功", {
        "id": updated_task.id,
        "status": updated_task.status
    })