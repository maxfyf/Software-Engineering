# backend/api.py - 统一的 FastAPI 后端入口

from fastapi import FastAPI, Depends, HTTPException, status, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel, Field, validator

from models import OperationLog, TaskStatus, TaskDependency #补充
from typing import Optional
from datetime import datetime, timedelta, timezone
from collections import deque

from database import get_db, Base, engine
from models import User, Task, Team, Notification
import schemas
from security import verify_password, get_password_hash, create_access_token
import crud
from log_service import log_task_operation

from notification_service import (
    create_notification, get_user_notifications, mark_notification_read,
    mark_all_read, clear_notifications, accept_notification, reject_notification
)
from schemas import NotificationCreate, NotificationOut
import re


CN_TZ = timezone(timedelta(hours=8))


def format_cn_datetime(value):
    if not value:
        return None
    if value.tzinfo is not None:
        value = value.astimezone(CN_TZ).replace(tzinfo=None)
    return value.strftime("%Y-%m-%d %H:%M:%S")

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

class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None

    @validator('phone_number')
    def validate_phone(cls, v):
        if v is None or v == "":
            return v
        if not re.match(r'^(\d{8}|\d{11})$', v):
            raise ValueError('手机号必须为8位或11位数字')
        return v

    @validator('email')
    def validate_email(cls, v):
        if v is None or v == "":
            return v
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', v):
            raise ValueError('邮箱格式不正确')
        return v

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
        "createdAt": format_cn_datetime(task.created_at),
        "updatedAt": format_cn_datetime(task.updated_at),
        "owner": task.owner_username,
        "team": task.team.name if task.team else None,
        "assignee": [task.assignee_username] if task.assignee_username else [],
        "predecessor": [pred.id for pred in task.predecessors]
    }

def get_team_id_by_name(db: Session, name: str) -> int | None:
    """根据团队名称查询团队 ID"""
    if not name:
        return None
    team = db.query(Team).filter(Team.name == name).first()
    return team.id if team else None

def find_top_unfinished_predecessor(db: Session, task_id: int, predecessor_ids: list[int] | None = None):
    """查找阻塞任务完成的最上游未完成前置任务。"""
    if predecessor_ids is None:
        predecessor_ids = [task.id for task in crud.get_predecessors(db, task_id)]

    visited = set()

    def trace(pred_id: int):
        if pred_id in visited:
            return None
        visited.add(pred_id)

        pred_task = db.query(Task).filter(Task.id == pred_id).first()
        if not pred_task:
            return None

        for upstream in crud.get_predecessors(db, pred_task.id):
            blocker = trace(upstream.id)
            if blocker:
                return blocker

        if pred_task.status != TaskStatus.DONE.value:
            return pred_task
        return None

    for pred_id in predecessor_ids:
        blocker = trace(pred_id)
        if blocker:
            return blocker
    return None

def find_nearest_done_successor(db: Session, task_id: int):
    """查找阻塞任务回退为未完成状态的最近已完成后继任务。"""
    visited = {task_id}
    queue = deque(crud.get_successors(db, task_id))

    while queue:
        successor = queue.popleft()
        if successor.id in visited:
            continue
        visited.add(successor.id)

        if successor.status == TaskStatus.DONE.value:
            return successor

        queue.extend(crud.get_successors(db, successor.id))
    return None

def get_task_log_scope(db: Session, task: Task):
    """返回任务日志的作用域信息。"""
    if task.team_id is None:
        return "personal", None, None
    team_obj = db.query(Team).filter(Team.id == task.team_id).first()
    return "team", task.team_id, team_obj.name if team_obj else None

def format_deadline(date_value):
    return date_value.strftime("%Y-%m-%d") if date_value else "未设置"

def update_task_log_title_snapshots(db: Session, task_id: int, new_title: str, old_title: str):
    """任务改名后，同步该任务历史日志中的标题快照。"""
    title_snapshot = f"{new_title}（{old_title}）"
    logs = db.query(OperationLog).filter(OperationLog.task_id == task_id).all()
    for log in logs:
        obj = dict(log.object or {})
        obj["title"] = title_snapshot
        log.object = obj

def get_task_log_display_title(db: Session, task: Task) -> str:
    """返回任务日志应使用的标题快照，避免改名后的后续日志丢失旧名标记。"""
    latest_log = db.query(OperationLog).filter(
        OperationLog.task_id == task.id
    ).order_by(
        OperationLog.operated_at.desc(),
        OperationLog.id.desc()
    ).first()
    if latest_log:
        obj = latest_log.object or {}
        latest_title = obj.get("title") if isinstance(obj, dict) else None
        if latest_title == task.title or latest_title.startswith(f"{task.title}（"):
            return latest_title
    return task.title

def append_task_log(
    db: Session,
    *,
    operator: str,
    operation_type: str,
    task: Task,
    description: str,
    deleted: bool = False,
    object_title: str | None = None
):
    scope_type, team_id, team_title = get_task_log_scope(db, task)
    display_title = object_title or get_task_log_display_title(db, task)
    log_task_operation(
        db=db,
        operator=operator,
        operation_type=operation_type,
        task=task,
        description=description,
        scope_type=scope_type,
        team_id=team_id,
        team_title=team_title,
        deleted=deleted,
        object_title=display_title
    )

def validate_status_transition(db: Session, task: Task, new_status: str | None):
    """校验任务状态变化不会破坏依赖状态一致性。"""
    if new_status is None or new_status == task.status:
        return

    if new_status == TaskStatus.DONE.value:
        blocker = find_top_unfinished_predecessor(db, task.id)
        if blocker:
            raise HTTPException(
                status_code=400,
                detail=f"前置任务「{blocker.title}」未完成，无法完成当前任务"
            )

    if task.status == TaskStatus.DONE.value and new_status != TaskStatus.DONE.value:
        blocker = find_nearest_done_successor(db, task.id)
        if blocker:
            raise HTTPException(
                status_code=400,
                detail=f"后继任务「{blocker.title}」已完成，无法将当前任务改为未完成状态"
            )

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
    success, transferred_tasks = crud.cancel_account(db, current_user.username)
    if not success:
        raise HTTPException(status_code=500, detail="注销失败")

    for task in transferred_tasks:
        create_notification(db, NotificationCreate(
            receiver_username=task.team.owner_username,
            sender_username=current_user.username,
            text=f"用户 {current_user.username} 注销账号，任务「{task.title}」已自动转交给您。",
            type="task_transferred_to_owner",
            need_operation=False,
            metadata={"taskId": task.id, "taskTitle": task.title, "teamId": task.team_id}
        ))

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
        id=crud.allocate_task_id(db),
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

    if db_task.team_id is None:
        scope_type = "personal"
        team_id = None
        team_title = None
    else:
        scope_type = "team"
        team_id = db_task.team_id
        team_obj = db.query(Team).filter(Team.id == team_id).first()
        team_title = team_obj.name if team_obj else None

    log_task_operation(
        db=db,
        operator=current_user.username,
        operation_type="create_task",
        task=db_task,
        description=f"创建任务: {db_task.title}",
        scope_type=scope_type,
        team_id=team_id,
        team_title=team_title,
        deleted=False
    )
        # ===== 新增：分配负责人通知 =====
    if db_task.assignee_username:
        create_notification(db, NotificationCreate(
            receiver_username=db_task.assignee_username,
            sender_username=current_user.username,
            text=f"您被分配为任务「{db_task.title}」的负责人。",
            type="task_assigned",
            need_operation=False,
            metadata={"taskId": db_task.id, "taskTitle": db_task.title}
        ))
    return success_response("创建成功", serialize_task(db_task))

@app.put("/api/task/{task_id}")
def update_task(task_id: int, task_update: TaskUpdateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """更新任务 - 个人任务仅owner可编辑；团队任务Admin/Owner可全量编辑，Member仅能修改分配给自己的任务状态"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    old_title = task.title
    old_description = task.description
    old_status = task.status
    old_priority = task.priority
    old_due_date = task.due_date
    old_team_id = task.team_id
    old_assignee = task.assignee_username

    validate_status_transition(db, task, task_update.status)

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
            if (
                old_status == TaskStatus.DONE.value
                and task.status != TaskStatus.DONE.value
                and task.assignee_username
                and not crud.get_team_membership(db, task.team_id, task.assignee_username)
            ):
                task.assignee_username = task.team.owner_username
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

    title_snapshot = None
    if task.title != old_title:
        title_snapshot = f"{task.title}（{old_title}）"
        update_task_log_title_snapshots(db, task.id, task.title, old_title)
        append_task_log(
            db=db,
            operator=current_user.username,
            operation_type="update_title",
            task=task,
            description=f"修改任务名: {old_title} -> {task.title}",
            object_title=title_snapshot
        )

    if (task.description or "") != (old_description or ""):
        append_task_log(
            db=db,
            operator=current_user.username,
            operation_type="update_description",
            task=task,
            description=f"修改描述: {old_description or '空'} -> {task.description or '空'}",
            object_title=title_snapshot
        )

    if task.status != old_status:
        append_task_log(
            db=db,
            operator=current_user.username,
            operation_type="update_status",
            task=task,
            description=f"修改状态: {old_status} -> {task.status}",
            object_title=title_snapshot
        )

    if task.priority != old_priority:
        append_task_log(
            db=db,
            operator=current_user.username,
            operation_type="update_priority",
            task=task,
            description=f"修改优先级: {old_priority} -> {task.priority}",
            object_title=title_snapshot
        )

    if task.due_date != old_due_date:
        append_task_log(
            db=db,
            operator=current_user.username,
            operation_type="update_deadline",
            task=task,
            description=f"修改截止日期: {format_deadline(old_due_date)} -> {format_deadline(task.due_date)}",
            object_title=title_snapshot
        )

    if task.team_id != old_team_id:
        append_task_log(
            db=db,
            operator=current_user.username,
            operation_type="update_scope",
            task=task,
            description="修改任务所属团队",
            object_title=title_snapshot
        )

    if task.assignee_username != old_assignee:
        append_task_log(
            db=db,
            operator=current_user.username,
            operation_type="update_assignee",
            task=task,
            description=f"修改负责人: {old_assignee or '未分配'} -> {task.assignee_username or '未分配'}",
            object_title=title_snapshot
        )
        
    new_assignee = task.assignee_username
    if old_assignee != new_assignee:
        # 给新负责人发通知
        if new_assignee:
            create_notification(db, NotificationCreate(
                receiver_username=new_assignee,
                sender_username=current_user.username,
                text=f"您被分配为任务「{task.title}」的负责人。",
                type="task_assigned",
                need_operation=False,
                metadata={"taskId": task.id, "taskTitle": task.title}
            ))
        # 处理旧负责人
        if old_assignee:
            # 查找未读的分配通知
            unread = db.query(Notification).filter(
                Notification.receiver_username == old_assignee,
                Notification.type == "task_assigned",
                Notification.is_read == False
            ).all()
            target = None
            for n in unread:
                if n.metadata_ and n.metadata_.get("taskId") == task.id:
                    target = n
                    break
            if target:
                db.delete(target)
                db.commit()
            else:
                # 检查是否有已读的分配通知
                read = db.query(Notification).filter(
                    Notification.receiver_username == old_assignee,
                    Notification.type == "task_assigned",
                    Notification.is_read == True
                ).all()
                has_read = any(n.metadata_ and n.metadata_.get("taskId") == task.id for n in read)
                if has_read and old_assignee != current_user.username:
                    create_notification(db, NotificationCreate(
                        receiver_username=old_assignee,
                        sender_username=current_user.username,
                        text=f"您不再是任务「{task.title}」的负责人。",
                        type="task_unassigned",
                        need_operation=False,
                        metadata={"taskId": task.id, "taskTitle": task.title}
                    ))
    return success_response("更新成功", serialize_task(task))

@app.delete("/api/task/{task_id}")
def delete_task(
    task_id: int,
    cascade: bool = Query(False, description="是否级联删除所有后继任务"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除任务 - 支持级联删除参数 cascade=true"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    old_status = task.status

    # 权限检查
    if not task.team_id:
        if task.owner_username != current_user.username:
            raise HTTPException(status_code=403, detail="无权删除该任务")
    else:
        if not crud.require_team_role(db, task.team_id, current_user.username, {crud.ROLE_ADMIN, crud.ROLE_OWNER}):
            raise HTTPException(status_code=403, detail="无权删除该团队任务")

    # 调用 crud 中的级联删除函数
    crud.delete_task_with_deps(db, task_id, cascade, current_user.username)
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
    
    crud.delete_team(db, team_id, operator_username=current_user.username)
    return success_response("团队已解散")

@app.post("/api/team/{team_id}/member")
def add_member_endpoint(
    team_id: int,
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """发送加入团队邀请（Owner 专用）"""
    username = request.get("username")
    role = request.get("role", "member")
    
    if not username:
        raise HTTPException(status_code=400, detail="用户名不能为空")
    
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="团队不存在")
    if team.owner_username != current_user.username:
        raise HTTPException(status_code=403, detail="只有 Owner 可发送邀请")
    
    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=400, detail="用户不存在")
    if crud.get_team_membership(db, team_id, username):
        raise HTTPException(status_code=400, detail="用户已在团队中")
    if role not in ["admin", "member"]:
        raise HTTPException(status_code=400, detail="角色必须为 admin 或 member")
    
    # 创建邀请通知（不直接加入）
    create_notification(db, NotificationCreate(
        receiver_username=username,
        sender_username=current_user.username,
        text=f"{current_user.username} 邀请您加入团队「{team.name}」。",
        type="team_invitation",
        need_operation=True,
        metadata={"teamId": team_id, "teamTitle": team.name, "role": role}
    ))
    return success_response("邀请已发送")

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

    success, error, transferred_tasks = crud.remove_team_member(db, team_id, username, current_user.username)
    if error:
        raise HTTPException(status_code=400, detail=error)

    team = db.query(Team).filter(Team.id == team_id).first()
    # 通知被移除者
    create_notification(db, NotificationCreate(
        receiver_username=username,
        sender_username=current_user.username,
        text=f"您已被移出团队「{team.name}」。",
        type="team_removed",
        need_operation=False,
        metadata={"teamId": team_id, "teamTitle": team.name}
    ))
    # 通知 Owner 任务转交
    for task in transferred_tasks:
        create_notification(db, NotificationCreate(
            receiver_username=team.owner_username,
            sender_username=current_user.username,
            text=f"成员 {username} 被移出团队，任务「{task.title}」已自动转交给您。",
            type="task_transferred_to_owner",
            need_operation=False,
            metadata={"taskId": task.id, "taskTitle": task.title, "teamId": team_id}
        ))

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
        validate_status_transition(db, task, task_status)
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
    task = db.query(Task).filter(Task.id == task_id).first()
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
    task = db.query(Task).filter(Task.id == task_id).first()
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
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if not crud.can_manage_task(db, current_user.username, task):
        raise HTTPException(status_code=403, detail="无权修改该任务的依赖")

    old_predecessors = crud.get_predecessors(db, task_id)
    old_pred_ids = {pred.id for pred in old_predecessors}
    old_pred_title_map = {pred.id: pred.title for pred in old_predecessors}

    # 校验所有前置任务
    for pred_id in req.predecessor_ids:
        if pred_id == task_id:
            raise HTTPException(status_code=400, detail="任务不能依赖自身")
        pred_task = db.query(Task).filter(Task.id == pred_id).first()
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

    if task.status == TaskStatus.DONE.value:
        blocker = find_top_unfinished_predecessor(db, task_id, req.predecessor_ids)
        if blocker:
            raise HTTPException(status_code=400, detail=f"前置任务「{blocker.title}」未完成，无法完成当前任务")

    crud.update_predecessors(db, task_id, req.predecessor_ids)
    new_pred_ids = set(req.predecessor_ids)
    added_ids = new_pred_ids - old_pred_ids
    removed_ids = old_pred_ids - new_pred_ids

    for pred_id in added_ids:
        pred_task = db.query(Task).filter(Task.id == pred_id).first()
        append_task_log(
            db=db,
            operator=current_user.username,
            operation_type="add_dependency",
            task=task,
            description=f"新增前置任务: {pred_task.title if pred_task else pred_id}"
        )

    for pred_id in removed_ids:
        append_task_log(
            db=db,
            operator=current_user.username,
            operation_type="remove_dependency",
            task=task,
            description=f"删除前置任务: {old_pred_title_map.get(pred_id, pred_id)}"
        )

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
    success, error, transferred_tasks = crud.leave_team(db, team_id, current_user.username)
    if not success:
        raise HTTPException(status_code=400, detail=error)

    team = db.query(Team).filter(Team.id == team_id).first()
    for task in transferred_tasks:
        create_notification(db, NotificationCreate(
            receiver_username=team.owner_username,
            sender_username=current_user.username,
            text=f"成员 {current_user.username} 主动离开团队，任务「{task.title}」已自动转交给您。",
            type="task_transferred_to_owner",
            need_operation=False,
            metadata={"taskId": task.id, "taskTitle": task.title, "teamId": team_id}
        ))

    return success_response("已离开团队")

# ===================== 操作日志查询 =====================

@app.get("/api/task/{task_id}/operations")
def get_task_operations(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    # 权限校验
    if task.team_id is None:
        if task.owner_username != current_user.username and task.assignee_username != current_user.username:
            raise HTTPException(status_code=403, detail="无权查看该任务日志")
    else:
        if not crud.require_team_member(db, task.team_id, current_user.username):
            raise HTTPException(status_code=403, detail="无权查看该任务日志")
    logs = db.query(OperationLog).filter(OperationLog.task_id == task_id).order_by(OperationLog.operated_at.desc()).all()
    return {"success": True, "data": [crud.serialize_operation_log(log) for log in logs]}

@app.get("/api/operation/personal")
def get_personal_operations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logs = db.query(OperationLog).filter(OperationLog.personal_user == current_user.username).order_by(OperationLog.operated_at.desc()).all()
    return {"success": True, "data": [crud.serialize_operation_log(log) for log in logs]}

@app.get("/api/team/{team_id}/operations")
def get_team_operations(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not crud.require_team_member(db, team_id, current_user.username):
        raise HTTPException(status_code=403, detail="无权查看该团队日志")
    logs = db.query(OperationLog).filter(OperationLog.team_id == team_id).order_by(OperationLog.operated_at.desc()).all()
    return {"success": True, "data": [crud.serialize_operation_log(log) for log in logs]}

@app.get("/api/user/profile")
def get_user_profile(
    username: str = Query(..., description="用户名"),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {
        "success": True,
        "data": {
            "username": user.username,
            "firstName": user.first_name,
            "lastName": user.last_name,
            "phone": user.phone_number,
            "email": user.email
        }
    }

@app.put("/api/user/info")
def update_user_info(
    update_data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = current_user
    if update_data.first_name is not None:
        user.first_name = update_data.first_name
    if update_data.last_name is not None:
        user.last_name = update_data.last_name
    if update_data.phone_number is not None:
        user.phone_number = update_data.phone_number
    if update_data.email is not None:
        if update_data.email != user.email:
            existing = db.query(User).filter(User.email == update_data.email, User.username != user.username).first()
            if existing:
                raise HTTPException(status_code=400, detail="该邮箱已被其他用户使用")
        user.email = update_data.email
    db.commit()
    db.refresh(user)
    return success_response("更新成功", {
        "username": user.username,
        "firstName": user.first_name,
        "lastName": user.last_name,
        "phone": user.phone_number,
        "email": user.email
    })

@app.post("/api/team/{team_id}/owner-transfer-request")
def owner_transfer_request(
    team_id: int,
    req: schemas.TransferOwnerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = crud.get_team_by_id(db, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="团队不存在")
    if team.owner_username != current_user.username:
        raise HTTPException(status_code=403, detail="只有 Owner 可发起转让")
    if req.new_owner_id == current_user.username:
        raise HTTPException(status_code=400, detail="不能转让给自己")
    if not crud.get_team_membership(db, team_id, req.new_owner_id):
        raise HTTPException(status_code=400, detail="新 Owner 不是团队成员")
    
    create_notification(db, NotificationCreate(
        receiver_username=req.new_owner_id,
        sender_username=current_user.username,
        text=f"{current_user.username} 请求将团队「{team.name}」的拥有者权限转让给您。",
        type="owner_transfer_request",
        need_operation=True,
        metadata={"teamId": team_id, "teamTitle": team.name, "oldOwner": current_user.username, "newOwner": req.new_owner_id}
    ))
    return success_response("转让请求已发送")

@app.get("/api/notification/list")
def get_notification_list(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notifs = get_user_notifications(db, current_user.username)
    result = []
    for n in notifs:
        result.append({
            "id": n.id,
            "text": n.text,
            "needOperation": n.need_operation,
            "isRead": n.is_read,
            "type": n.type,
            "sender": n.sender_username,
            "createdAt": n.created_at.strftime("%Y-%m-%d %H:%M:%S") if n.created_at else None,
            "metadata": n.metadata_
        })
    return success_response("获取成功", result)

@app.put("/api/notification/{notification_id}/read")
def mark_read(notification_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notif = mark_notification_read(db, notification_id, current_user.username)
    if not notif:
        raise HTTPException(status_code=404, detail="通知不存在或无权操作")
    return success_response("已标记为已读")

@app.put("/api/notification/read-all")
def read_all(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    mark_all_read(db, current_user.username)
    return success_response("全部已读")

@app.delete("/api/notification/clear")
def clear_notifications_endpoint(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    clear_notifications(db, current_user.username)
    return success_response("清空成功")

def notification_error_status(msg: str) -> int:
    if msg == "通知不存在":
        return 404
    if msg.startswith("无权"):
        return 403
    if msg == "通知已处理":
        return 409
    return 400

@app.post("/api/notification/{notification_id}/accept")
def accept_notification_endpoint(notification_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notif, msg = accept_notification(db, notification_id, current_user.username)
    if not notif:
        raise HTTPException(status_code=notification_error_status(msg), detail=msg)
    return success_response(msg)

@app.post("/api/notification/{notification_id}/reject")
def reject_notification_endpoint(notification_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notif, msg = reject_notification(db, notification_id, current_user.username)
    if not notif:
        raise HTTPException(status_code=notification_error_status(msg), detail=msg)
    return success_response(msg)