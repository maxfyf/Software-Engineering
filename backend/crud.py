from sqlalchemy.orm import Session
import models, schemas, security
from fastapi import HTTPException

ROLE_OWNER = models.TeamRole.OWNER.value
ROLE_ADMIN = models.TeamRole.ADMIN.value
ROLE_MEMBER = models.TeamRole.MEMBER.value

# 注册相关

def get_user_by_username(db: Session, username: str) -> models.User | None:
    """根据用户名查询用户（API层用来判断用户是否已存在）"""
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str) -> models.User | None:
    """根据邮箱查询用户"""
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """创建新用户并写入数据库（密码在此处加密）"""
    hashed_password = security.get_password_hash(user.password)
    
    db_user = models.User(
        username=user.username,
        password_hash=hashed_password,  # 存入哈希值
        first_name=user.first_name,
        last_name=user.last_name,
        phone_number=user.phone_number,
        email=user.email
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# 登录相关

def authenticate_user(db: Session, username: str, password: str) -> tuple[models.User | None, str | None]:
    """验证用户登录并返回具体失败原因"""
    user = get_user_by_username(db, username)
    if not user:
        return None, "用户不存在"
    if not security.verify_password(password, user.password_hash):
        return None, "密码错误"
    return user, None

# 团队与成员管理相关

def get_team_by_id(db: Session, team_id: int) -> models.Team | None:
    """根据团队ID查询团队"""
    return db.query(models.Team).filter(models.Team.id == team_id).first()

def get_team_membership(db: Session, team_id: int, username: str) -> models.TeamMember | None:
    """查询用户在指定团队中的成员身份"""
    return db.query(models.TeamMember).filter(
        models.TeamMember.team_id == team_id,
        models.TeamMember.username == username
    ).first()

def require_team_member(db: Session, team_id: int, username: str) -> models.TeamMember | None:
    """查询用户是否属于团队；不存在则返回 None"""
    if not get_team_by_id(db, team_id):
        return None
    return get_team_membership(db, team_id, username)

def require_team_role(
    db: Session,
    team_id: int,
    username: str,
    allowed_roles: set[str]
) -> models.TeamMember | None:
    """查询用户是否拥有指定团队角色；没有权限则返回 None"""
    membership = require_team_member(db, team_id, username)
    if not membership or membership.role not in allowed_roles:
        return None
    return membership

def create_team(db: Session, team: schemas.TeamCreate, username: str) -> models.Team:
    """创建团队，创建者自动成为 Owner"""
    db_team = models.Team(name=team.name, owner_username=username)
    db.add(db_team)
    db.flush()

    db_member = models.TeamMember(
        team_id=db_team.id,
        username=username,
        role=ROLE_OWNER
    )
    db.add(db_member)
    db.commit()
    db.refresh(db_team)
    return db_team

def get_user_teams(db: Session, username: str) -> list[models.Team]:
    """获取当前用户加入的团队"""
    return db.query(models.Team).join(models.TeamMember).filter(
        models.TeamMember.username == username
    ).all()

def get_team_members(
    db: Session,
    team_id: int,
    username: str
) -> tuple[list[models.TeamMember] | None, str | None]:
    """获取团队成员列表，失败时返回错误信息供 API 层处理"""
    if not get_team_by_id(db, team_id):
        return None, "团队不存在"
    if not get_team_membership(db, team_id, username):
        return None, "无权访问该团队"
    members = db.query(models.TeamMember).filter(models.TeamMember.team_id == team_id).all()
    return members, None

def add_team_member(
    db: Session,
    team_id: int,
    member_username: str,
    operator_username: str
) -> tuple[models.TeamMember | None, str | None]:
    """Owner 将其他用户添加到团队，默认角色为 Member；失败时返回错误信息"""
    if not get_team_by_id(db, team_id):
        return None, "团队不存在"
    if not require_team_role(db, team_id, operator_username, {ROLE_OWNER}):
        return None, "团队权限不足"

    user = get_user_by_username(db, member_username)
    if not user:
        return None, "用户不存在"

    if get_team_membership(db, team_id, member_username):
        return None, "用户已在团队中"

    db_member = models.TeamMember(
        team_id=team_id,
        username=member_username,
        role=ROLE_MEMBER
    )
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member, None

def update_team_member_role(
    db: Session,
    team_id: int,
    member_username: str,
    role: str,
    operator_username: str
) -> tuple[models.TeamMember | None, str | None]:
    """Owner 将 Member 升为 Admin，或将 Admin 降为 Member；失败时返回错误信息"""
    if not get_team_by_id(db, team_id):
        return None, "团队不存在"
    if not require_team_role(db, team_id, operator_username, {ROLE_OWNER}):
        return None, "团队权限不足"

    if role not in {ROLE_ADMIN, ROLE_MEMBER}:
        return None, "角色只能设置为 Admin 或 Member"

    membership = get_team_membership(db, team_id, member_username)
    if not membership:
        return None, "团队成员不存在"
    if membership.role == ROLE_OWNER:
        return None, "不能修改 Owner 角色"

    membership.role = role
    db.commit()
    db.refresh(membership)
    return membership, None

def remove_team_member(
    db: Session,
    team_id: int,
    member_username: str,
    operator_username: str
) -> tuple[bool, str | None]:
    """Owner 从团队中移除非 Owner 成员；失败时返回错误信息"""
    if not get_team_by_id(db, team_id):
        return False, "团队不存在"
    if not require_team_role(db, team_id, operator_username, {ROLE_OWNER}):
        return False, "团队权限不足"

    membership = get_team_membership(db, team_id, member_username)
    if not membership:
        return False, "团队成员不存在"
    if membership.role == ROLE_OWNER:
        return False, "不能移除 Owner"

    db.delete(membership)
    db.commit()
    return True, None

# 任务相关（创建、查询、更新、删除）

def create_task(db: Session, task: schemas.TaskCreate, username: str) -> models.Task:
    """创建任务并绑定到当前登录用户，写入数据库"""
    # 使用前端传入的任务数据，并绑定当前用户名作为归属
    db_task = models.Task(
        **task.dict(),
        owner_username=username
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def get_tasks(db: Session, username: str) -> list[models.Task]:
    """获取当前用户的所有任务列表（仅查询自己创建的任务）"""
    return db.query(models.Task).filter(models.Task.owner_username == username).all()

def get_task_by_id(db: Session, task_id: int, username: str) -> models.Task:
    """根据任务ID查询单条任务（仅允许查询自己的任务，不存在则返回404）"""
    task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.owner_username == username
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或无权访问")
    return task

def update_task(db: Session, task_id: int, task: schemas.TaskUpdate, username: str) -> models.Task:
    """更新指定任务（仅允许更新自己的任务）"""
    db_task = get_task_by_id(db, task_id, username)
    
    # 仅更新前端传入的字段
    for key, value in task.dict(exclude_unset=True).items():
        setattr(db_task, key, value)
    
    db.commit()
    db.refresh(db_task)
    return db_task

def delete_task(db: Session, task_id: int, username: str) -> None:
    """删除指定任务（仅允许删除自己的任务）"""
    db_task = get_task_by_id(db, task_id, username)
    db.delete(db_task)
    db.commit()
