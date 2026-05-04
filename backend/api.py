# backend/api.py - 统一的 FastAPI 后端入口

from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from database import get_db, Base, engine
from models import User, Task, Team
import schemas
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
    team: Optional[str] = None       # 团队名称
    assignee: Optional[str] = None   # 被分配人用户名

class TaskUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    deadline: Optional[str] = None
    team: Optional[str] = None
    assignee: Optional[str] = None

# ===================== 统一响应格式 =====================

def success_response(msg: str, data=None):
    return {"success": True, "msg": msg, "data": data}

def error_response(msg: str):
    return {"success": False, "msg": msg, "data": None}

def serialize_task(task):
    """将 Task ORM 对象序列化为前端期望的格式"""
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "deadline": task.due_date.strftime("%Y-%m-%d") if task.due_date else None,
        "createdAt": task.created_at.strftime("%Y-%m-%d %H:%M:%S") if task.created_at else None,
        "updatedAt": task.updated_at.strftime("%Y-%m-%d %H:%M:%S") if task.updated_at else None,
        "owner": task.owner_username,
        "team": task.team.name if task.team else None,
        "assignee": [task.assignee_username] if task.assignee_username else []
    }

def get_team_id_by_name(db: Session, name: str) -> int | None:
    """根据团队名称查询团队 ID"""
    if not name:
        return None
    team = db.query(Team).filter(Team.name == name).first()
    return team.id if team else None

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
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    if crud.get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 把空字符串转为 None，避免 UNIQUE 约束冲突
    user_data = user.model_dump()
    for field in ['email', 'first_name', 'last_name', 'phone_number']:
        if not user_data.get(field):
            user_data[field] = None
    
    # 检查邮箱是否已存在
    if user_data['email'] and crud.get_user_by_email(db, user_data['email']):
        raise HTTPException(status_code=400, detail="该邮箱已被注册")
    
    # 创建用户
    db_user = crud.create_user(db, schemas.UserCreate(**user_data))
    
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
    """获取任务列表 - 包括个人任务、分配给自己的任务，以及所属团队的所有任务"""
    own_or_assigned = db.query(Task).filter(
        or_(Task.owner_username == current_user.username, Task.assignee_username == current_user.username)
    ).all()
    
    # 获取当前用户所属团队的所有任务
    user_teams = crud.get_user_teams(db, current_user.username)
    team_ids = [t.id for t in user_teams]
    team_tasks = db.query(Task).filter(Task.team_id.in_(team_ids)).all() if team_ids else []
    
    # 合并去重
    all_tasks = {task.id: task for task in own_or_assigned + team_tasks}
    return success_response("获取成功", [serialize_task(task) for task in all_tasks.values()])

@app.get("/api/task/{task_id}")
def get_task(task_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取任务详情 - 个人任务仅owner/assignee可见，团队任务所有团队成员可见"""
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 个人任务：仅 owner 和 assignee 可见
    if not task.team_id:
        if task.owner_username != current_user.username and task.assignee_username != current_user.username:
            raise HTTPException(status_code=403, detail="无权访问该任务")
    else:
        # 团队任务：团队成员可见
        if not crud.require_team_member(db, task.team_id, current_user.username):
            raise HTTPException(status_code=403, detail="无权访问该团队任务")
    
    return success_response("获取成功", serialize_task(task))

@app.post("/api/task/create")
def create_task(task: TaskCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """创建任务 - 个人任务任何人可创建，团队任务仅Admin/Owner可创建"""
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
    
    # 处理团队任务
    if task.team:
        team_id = get_team_id_by_name(db, task.team)
        if not team_id:
            raise HTTPException(status_code=400, detail="团队不存在")
        # 仅 Admin/Owner 可在团队中创建任务
        if not crud.require_team_role(db, team_id, current_user.username, {crud.ROLE_ADMIN, crud.ROLE_OWNER}):
            raise HTTPException(status_code=403, detail="无权在该团队中创建任务")
        db_task.team_id = team_id
    
    # 处理负责人
    if task.assignee:
        db_task.assignee_username = task.assignee
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    return success_response("创建成功", serialize_task(db_task))

@app.put("/api/task/{task_id}")
def update_task(task_id: int, task_update: TaskUpdateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """更新任务 - 个人任务仅owner可编辑；团队任务Admin/Owner可全量编辑，Member仅能修改分配给自己的任务状态"""
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 个人任务：仅 owner 可编辑
    if not task.team_id:
        if task.owner_username != current_user.username:
            raise HTTPException(status_code=403, detail="无权编辑该任务")
        # 个人任务允许修改所有字段
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
    else:
        # 团队任务权限判断
        is_admin_or_owner = crud.require_team_role(db, task.team_id, current_user.username, {crud.ROLE_ADMIN, crud.ROLE_OWNER})
        is_assignee = task.assignee_username == current_user.username
        
        if is_admin_or_owner:
            # Admin/Owner 可修改所有字段
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
            if task_update.team is not None:
                task.team_id = get_team_id_by_name(db, task_update.team)
            if task_update.assignee is not None:
                task.assignee_username = task_update.assignee
        elif is_assignee:
            # Member 只能修改分配给自己的任务状态
            if task_update.status is not None:
                task.status = task_update.status
            else:
                raise HTTPException(status_code=403, detail="只能修改任务状态")
        else:
            raise HTTPException(status_code=403, detail="无权编辑该任务")
    
    db.commit()
    db.refresh(task)
    
    return success_response("更新成功", serialize_task(task))

@app.delete("/api/task/{task_id}")
def delete_task(task_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """删除任务 - 个人任务仅owner可删除，团队任务仅Admin/Owner可删除"""
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 个人任务：仅 owner 可删除
    if not task.team_id:
        if task.owner_username != current_user.username:
            raise HTTPException(status_code=403, detail="无权删除该任务")
    else:
        # 团队任务：仅 Admin/Owner 可删除
        if not crud.require_team_role(db, task.team_id, current_user.username, {crud.ROLE_ADMIN, crud.ROLE_OWNER}):
            raise HTTPException(status_code=403, detail="无权删除该团队任务")
    
    db.delete(task)
    db.commit()
    
    return success_response("删除成功")

# ===================== 团队管理模块 =====================

def serialize_team(team):
    """将 Team ORM 对象序列化为前端期望的格式"""
    admins = []
    members = []
    for m in team.members:
        if m.role == crud.ROLE_ADMIN:
            admins.append(m.username)
        elif m.role == crud.ROLE_MEMBER:
            members.append(m.username)
    
    return {
        "id": team.id,
        "title": team.name,
        "owner": team.owner_username,
        "admin": admins,
        "member": members
    }

@app.get("/api/team/list")
def get_team_list(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前用户加入的所有团队"""
    teams = crud.get_user_teams(db, current_user.username)
    return success_response("获取成功", [serialize_team(team) for team in teams])

@app.post("/api/team/create")
def create_team_endpoint(request: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """创建团队"""
    title = request.get("title")
    if not title:
        raise HTTPException(status_code=400, detail="团队名称不能为空")
    
    team = crud.create_team(db, schemas.TeamCreate(name=title), current_user.username)
    return success_response("团队创建成功", serialize_team(team))

@app.delete("/api/team/{team_id}")
def delete_team_endpoint(team_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """解散团队 - 仅拥有者可操作"""
    team = crud.get_team_by_id(db, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="团队不存在")
    if team.owner_username != current_user.username:
        raise HTTPException(status_code=403, detail="只有拥有者可解散团队")
    
    db.delete(team)
    db.commit()
    return success_response("团队已解散")

@app.post("/api/team/{team_id}/member")
def add_member_endpoint(
    team_id: int,
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加成员到团队"""
    username = request.get("username")
    role = request.get("role", "member")
    
    if not username:
        raise HTTPException(status_code=400, detail="用户名不能为空")
    
    member, error = crud.add_team_member(db, team_id, username, current_user.username)
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    # 如果指定了 admin 角色，升级权限
    if role == "admin":
        crud.update_team_member_role(db, team_id, username, crud.ROLE_ADMIN, current_user.username)
    
    return success_response("成员添加成功")

@app.delete("/api/team/{team_id}/member")
def remove_member_endpoint(
    team_id: int,
    username: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """从团队中移除成员"""
    if not username:
        raise HTTPException(status_code=400, detail="用户名不能为空")
    
    success, error = crud.remove_team_member(db, team_id, username, current_user.username)
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return success_response("成员移除成功")

@app.put("/api/team/{team_id}/member/role")
def set_member_role_endpoint(
    team_id: int,
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """设置团队成员角色"""
    username = request.get("username")
    role = request.get("role")
    
    if not username or not role:
        raise HTTPException(status_code=400, detail="用户名和角色不能为空")
    
    role_map = {"admin": crud.ROLE_ADMIN, "member": crud.ROLE_MEMBER}
    backend_role = role_map.get(role)
    
    if not backend_role:
        raise HTTPException(status_code=400, detail="无效的角色")
    
    membership, error = crud.update_team_member_role(db, team_id, username, backend_role, current_user.username)
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return success_response("角色更新成功")

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
<<<<<<< HEAD
    current_user: schemas.UserResponse = Depends(get_current_user),
=======
    current_user: User = Depends(get_current_user),
>>>>>>> backend/feature/team-permission
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
    current_user: schemas.UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定团队的所有任务
    必须是团队成员才能查看
    """
<<<<<<< HEAD
    if not crud.require_team_member(db, team_id, current_user.username):
        raise HTTPException(status_code=403, detail="无权访问该团队")
=======
    if team_id <= 0:
        return error_response("无效的团队ID", 400)
    if not crud.require_team_member(db, team_id, current_user.username):
        return error_response("无权访问该团队", 403)
>>>>>>> backend/feature/team-permission
    
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
<<<<<<< HEAD
    current_user: schemas.UserResponse = Depends(get_current_user),
=======
    current_user: User = Depends(get_current_user),
>>>>>>> backend/feature/team-permission
    db: Session = Depends(get_db)
):
    """
    在指定团队下创建任务
    仅管理员和创建者可操作
    """
<<<<<<< HEAD
    if not crud.require_team_role(db, team_id, current_user.username, {crud.ROLE_ADMIN, crud.ROLE_OWNER}):
        raise HTTPException(status_code=403, detail="无权创建团队任务")
=======
    if team_id <= 0:
        return error_response("无效的团队ID", 400)
    if not task.title or not task.title.strip():
        return error_response("任务标题不能为空", 400)
    if not crud.require_team_role(db, team_id, current_user.username, {crud.ROLE_ADMIN, crud.ROLE_OWNER}):
        return error_response("无权创建团队任务", 403)
>>>>>>> backend/feature/team-permission
    
    task.team_id = team_id
    new_task = crud.create_team_task(db, task, current_user.username)
    return success_response("团队任务创建成功", {"id": new_task.id})


@app.put("/api/tasks/{task_id}/status", response_model=dict)
def update_task_status(
    task_id: int,
    status: str,
<<<<<<< HEAD
    current_user: schemas.UserResponse = Depends(get_current_user),
=======
    current_user: User = Depends(get_current_user),
>>>>>>> backend/feature/team-permission
    db: Session = Depends(get_db)
):
    """
    普通成员专用：仅更新任务状态
    只能修改分配给自己的任务
    """
<<<<<<< HEAD
    task = crud.get_task_by_id(db, task_id, current_user.username)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.assignee_username != current_user.username:
        raise HTTPException(status_code=403, detail="只能修改分配给自己的任务状态")
    
    updated_task = crud.update_task_status_only(db, task_id, status)
=======
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
>>>>>>> backend/feature/team-permission
    return success_response("任务状态更新成功", {
        "id": updated_task.id,
        "status": updated_task.status
    })