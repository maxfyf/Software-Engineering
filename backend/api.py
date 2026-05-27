# backend/api.py - 统一的 FastAPI 后端入口

from fastapi import FastAPI, Depends, HTTPException, status, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel, Field

from models import TaskStatus, TaskDependency #补充
from typing import Optional
from datetime import datetime

from database import get_db, Base, engine
from models import User, Task, Team, TaskDependency
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

class DependencyCreateRequest(BaseModel):
    predecessor_id: int = Field(..., description="前置任务ID")
    successor_id: int = Field(..., description="后继任务ID")   

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
    crud.cancel_account(db, current_user.username)
    return success_response("账号已注销")

# ===================== 任务模块 =====================

@app.get("/api/task/list")
def get_task_list(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取任务列表 - 包括个人任务、分配给自己的任务，以及所属团队的所有任务"""
    # 获取当前用户所属团队
    user_teams = crud.get_user_teams(db, current_user.username)
    team_ids = [t.id for t in user_teams]

    # 个人任务：没有 team_id 的任务，用户是 owner 或 assignee
    personal_tasks = db.query(Task).filter(
        Task.team_id.is_(None),
        or_(Task.owner_username == current_user.username, Task.assignee_username == current_user.username)
    ).all()

    # 团队任务：用户必须是团队成员才能看到
    team_tasks = db.query(Task).filter(Task.team_id.in_(team_ids)).all() if team_ids else []

    # 合并去重
    all_tasks = {task.id: task for task in personal_tasks + team_tasks}
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
    target_team_id = None

    # 处理团队任务
    if task.team:
        target_team_id = get_team_id_by_name(db, task.team)
        if not target_team_id:
            raise HTTPException(status_code=400, detail="团队不存在")
        # 仅 Admin/Owner 可在团队中创建任务
        if not crud.require_team_role(db, target_team_id, current_user.username, {crud.ROLE_ADMIN, crud.ROLE_OWNER}):
            raise HTTPException(status_code=403, detail="无权在该团队中创建任务")

    conflict = crud.find_task_title_conflict(
        db,
        title=task.title,
        username=current_user.username,
        team_id=target_team_id
    )
    if conflict:
        raise HTTPException(
            status_code=400,
            detail="该团队中已存在同名任务" if target_team_id is not None else "个人任务中已存在同名任务"
        )

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
        except ValueError:
            raise HTTPException(status_code=400, detail="截止日期格式应为 YYYY-MM-DD")
    
    if target_team_id is not None:
        db_task.team_id = target_team_id
    
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
    

    # ------------------ Lab3 新增：状态一致性防御检查 ------------------
    if task_update.status is not None and task_update.status == TaskStatus.DONE.value:
        unfinished_predecessors = db.query(TaskDependency).join(
            Task, TaskDependency.predecessor_id == Task.id
        ).filter(
            TaskDependency.successor_id == task_id,
            Task.status != TaskStatus.DONE.value
        ).count()
        if unfinished_predecessors > 0:
            raise HTTPException(status_code=400, detail="编辑后将产生非法状态：当前任务存在未完成的前置任务")
    # -------------------------------------------------------------------

    # 个人任务：仅 owner 可编辑
    if not task.team_id:
        if task.owner_username != current_user.username:
            raise HTTPException(status_code=403, detail="无权编辑该任务")
        new_title = task_update.title if task_update.title is not None else task.title
        conflict = crud.find_task_title_conflict(
            db,
            title=new_title,
            username=current_user.username,
            team_id=None,
            exclude_task_id=task.id
        )
        if conflict:
            raise HTTPException(status_code=400, detail="个人任务中已存在同名任务")
        # 个人任务允许修改所有字段
        if task_update.title is not None:
            # 如果要把状态改为“已完成”，先检查所有前置任务是否已完成
            if task_update.status == "已完成":
                preds = crud.get_predecessors(db, task_id)
                for pred in preds:
                    if pred.status != "已完成":
                        raise HTTPException(status_code=400,detail=f"前置任务「{pred.title}」未完成，无法完成当前任务")
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
            except ValueError:
                raise HTTPException(status_code=400, detail="截止日期格式应为 YYYY-MM-DD")
    else:
        target_team_id = task.team_id
        if task_update.team is not None:
            target_team_id = get_team_id_by_name(db, task_update.team)
            if task_update.team and not target_team_id:
                raise HTTPException(status_code=400, detail="团队不存在")

        # 团队任务权限判断
        is_admin_or_owner = crud.require_team_role(db, task.team_id, current_user.username, {crud.ROLE_ADMIN, crud.ROLE_OWNER})
        is_assignee = task.assignee_username == current_user.username
        
        if is_admin_or_owner:
            new_title = task_update.title if task_update.title is not None else task.title
            conflict = crud.find_task_title_conflict(
                db,
                title=new_title,
                username=current_user.username,
                team_id=target_team_id,
                exclude_task_id=task.id
            )
            if conflict:
                raise HTTPException(status_code=400, detail="该团队中已存在同名任务")
            # Admin/Owner 可修改所有字段
            if task_update.title is not None:
               # 如果要把状态改为“已完成”，先检查所有前置任务是否已完成
               if task_update.status == "已完成":
                preds = crud.get_predecessors(db, task_id)
                for pred in preds:
                    if pred.status != "已完成":
                        raise HTTPException(status_code=400,detail=f"前置任务「{pred.title}」未完成，无法完成当前任务")
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
                except ValueError:
                    raise HTTPException(status_code=400, detail="截止日期格式应为 YYYY-MM-DD")
            if task_update.team is not None:
                task.team_id = target_team_id
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
def delete_task(
    task_id: int,
    cascade: bool = Query(False, description="是否级联删除所有后继任务"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除任务 - 支持级联删除参数 cascade=true"""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 权限检查
    if not task.team_id:
        if task.owner_username != current_user.username:
            raise HTTPException(status_code=403, detail="无权删除该任务")
    else:
        if not crud.require_team_role(db, task.team_id, current_user.username, {crud.ROLE_ADMIN, crud.ROLE_OWNER}):
            raise HTTPException(status_code=403, detail="无权删除该团队任务")

    # 调用 crud 中的级联删除函数
    crud.delete_task_with_deps(db, task_id, cascade)
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
    if not title or not title.strip():
        raise HTTPException(status_code=400, detail="团队名称不能为空")

    title = title.strip()
    if len(title) > 10:
        raise HTTPException(status_code=400, detail="团队名称长度不能超过10个字符")

    # 检查是否已存在同名团队
    existing_team = db.query(Team).filter(Team.name == title).first()
    if existing_team:
        raise HTTPException(status_code=400, detail="团队名称已存在，请使用其他名称")

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
    username: str = Query(None),
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
            "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S") if t.created_at else None #防止空值报错
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
       raise HTTPException(status_code=400, detail="无效的团队ID")
    if not crud.require_team_member(db, team_id, current_user.username):
        raise HTTPException(status_code=403, detail="无权访问该团队")
    
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
        raise HTTPException(status_code=400, detail="无效的团队ID")
    if not task.title or not task.title.strip():
        raise HTTPException(status_code=400, detail="任务标题不能为空")
    if not crud.require_team_role(db, team_id, current_user.username, {crud.ROLE_ADMIN, crud.ROLE_OWNER}):
        raise HTTPException(status_code=403, detail="无权创建团队任务")
    
    task.team_id = team_id
    new_task = crud.create_team_task(db, task, current_user.username)
    return success_response("团队任务创建成功", {"id": new_task.id})


@app.put("/api/tasks/{task_id}/status", response_model=dict)
def update_task_status(
    task_id: int,
    task_status: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    普通成员专用：仅更新任务状态
    只能修改分配给自己的任务
    """
    #参数有效性校验
    if task_id <= 0:
        raise HTTPException(status_code=400, detail="无效的任务ID")
    if not task_status or not task_status.strip():
        raise HTTPException(status_code=400, detail="任务状态不能为空")
    
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
       
        if not task.assignee_username:
            raise HTTPException(status_code=403, detail="该任务未分配任何人")
        
        if task.assignee_username != current_user.username:
            raise HTTPException(status_code=403, detail="只能修改分配给自己的任务状态")
        # 如果要修改为已完成，检查前置任务
        if task_status == "已完成":
            preds = crud.get_predecessors(db, task_id)
            for pred in preds:
                if pred.status != "已完成":
                    raise HTTPException(status_code=400, detail=f"前置任务「{pred.title}」未完成，无法完成当前任务")
        updated_task = crud.update_task_status_only(db, task_id, task_status)
        if not updated_task:
            raise HTTPException(status_code=500, detail="任务状态更新失败")
    except HTTPException:
        # 【新增】：如果是我们主动抛出的 HTTP 异常（400/403/404等），直接原样抛出，不要拦截
        raise
    except Exception as e:
        # 只有真正的代码崩溃（比如数据库断连、空指针），才会被这里捕获转为 500
        raise HTTPException(
            status_code=500,
            detail=f"服务器内部异常,任务状态更新失败: {str(e)}"
        )    
    return success_response("任务状态更新成功", {
        "id": updated_task.id,
        "status": updated_task.status
    })



# ===================== 任务依赖模块 =====================

@app.get("/api/task/{task_id}/predecessors")
def get_predecessors(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取任务的前置任务列表"""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if not crud.can_access_task(db, current_user.username, task):
        raise HTTPException(status_code=403, detail="无权访问该任务")
    preds = crud.get_predecessors(db, task_id)
    return success_response("获取成功", [serialize_task(t) for t in preds])

@app.get("/api/task/{task_id}/successors")
def get_successors(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取依赖当前任务的后继任务列表"""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if not crud.can_access_task(db, current_user.username, task):
        raise HTTPException(status_code=403, detail="无权访问该任务")
    succs = crud.get_successors(db, task_id)
    return success_response("获取成功", [serialize_task(t) for t in succs])

@app.put("/api/task/{task_id}/predecessors")
def update_predecessors(
    task_id: int,
    req: schemas.UpdatePredecessorsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新任务的前置依赖（全量替换）"""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if not crud.can_manage_task(db, current_user.username, task):
        raise HTTPException(status_code=403, detail="无权修改该任务的依赖")

    # 校验所有前置任务
    for pred_id in req.predecessor_ids:
        pred_task = db.query(models.Task).filter(models.Task.id == pred_id).first()
        if not pred_task:
            raise HTTPException(status_code=400, detail=f"前置任务 {pred_id} 不存在")
        # 作用域限制：团队任务只能依赖同团队任务，个人任务只能依赖自己的个人任务
        if task.team_id is None:
            # 个人任务：前置任务必须是该用户自己的个人任务
            if pred_task.team_id is not None:
                raise HTTPException(status_code=400, detail="个人任务不能依赖团队任务")
            if pred_task.owner_username != current_user.username:
                raise HTTPException(status_code=400, detail="只能依赖自己的个人任务")
        else:
            # 团队任务：前置任务必须是同一团队的任务
            if pred_task.team_id != task.team_id:
                raise HTTPException(status_code=400, detail="前置任务与当前任务不在同一团队")

        # 循环依赖检查
        if crud.check_circular_dependency(db, pred_id, task_id):
            raise HTTPException(status_code=400, detail="不允许添加循环依赖")

    crud.update_predecessors(db, task_id, req.predecessor_ids)
    return success_response("更新成功")

@app.put("/api/team/{team_id}/owner")
def transfer_owner(
    team_id: int,
    req: schemas.TransferOwnerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """转让团队所有权（仅 Owner 可操作）"""
    success, error = crud.transfer_team_ownership(
        db, team_id, req.new_owner_id, current_user.username
    )
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return success_response("转让成功")

@app.post("/api/team/{team_id}/leave")
def leave_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """当前用户主动离开团队"""
    success, error = crud.leave_team(db, team_id, current_user.username)
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return success_response("已离开团队")
