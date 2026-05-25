from sqlalchemy.orm import Session
from sqlalchemy import or_
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
    """Owner 移除成员，或成员主动离开团队；失败时返回错误信息。"""
    team = get_team_by_id(db, team_id)
    if not team:
        return False, "团队不存在"

    operator_membership = get_team_membership(db, team_id, operator_username)
    if not operator_membership:
        return False, "团队权限不足"

    membership = get_team_membership(db, team_id, member_username)
    if not membership:
        return False, "团队成员不存在"

    is_self_leave = member_username == operator_username
    if not is_self_leave and operator_membership.role != ROLE_OWNER:
        return False, "团队权限不足"
    if membership.role == ROLE_OWNER:
        return False, "不能移除 Owner"

    # 移除成员前，将其负责的团队任务转交给团队 Owner。
    assigned_tasks = db.query(models.Task).filter(
        models.Task.team_id == team_id,
        models.Task.assignee_username == member_username
    ).all()
    for task in assigned_tasks:
        task.assignee_username = team.owner_username

    db.delete(membership)
    db.commit()
    return True, None


def delete_team(db: Session, team_id: int, *, commit: bool = True) -> bool:
    """删除团队，并同步删除该团队下的全部任务。"""
    team = get_team_by_id(db, team_id)
    if not team:
        return False

    # 先显式删除团队任务，确保现有数据库也不会把团队任务退化成个人任务。
    db.query(models.Task).filter(models.Task.team_id == team_id).delete(synchronize_session=False)
    db.delete(team)
    if commit:
        db.commit()
    return True


def cancel_account(db: Session, username: str) -> bool:
    """按业务规则注销账号，并清理/迁移与该用户关联的数据。"""
    if not get_user_by_username(db, username):
        return False

    # 1. 删除该用户的所有个人任务。
    db.query(models.Task).filter(
        models.Task.owner_username == username,
        models.Task.team_id.is_(None)
    ).delete(synchronize_session=False)

    # 2. 解散该用户拥有的所有团队，并删除这些团队下的全部任务。
    owned_teams = db.query(models.Team).filter(models.Team.owner_username == username).all()
    owned_team_ids = [team.id for team in owned_teams]
    for team in owned_teams:
        delete_team(db, team.id, commit=False)

    # 3. 将该用户负责的所有剩余团队任务转交给各自团队拥有者。
    assigned_team_tasks = db.query(models.Task).join(
        models.Team, models.Task.team_id == models.Team.id
    ).filter(
        models.Task.team_id.isnot(None),
        models.Task.assignee_username == username
    ).all()
    for task in assigned_team_tasks:
        task.assignee_username = task.team.owner_username

    # 4. 对仍然保留的团队任务，如果该用户是创建者，则同步改为团队拥有者，
    #    避免删除用户时留下 owner 外键引用。
    owned_team_tasks = db.query(models.Task).join(
        models.Team, models.Task.team_id == models.Team.id
    ).filter(
        models.Task.team_id.isnot(None),
        models.Task.owner_username == username
    ).all()
    for task in owned_team_tasks:
        task.owner_username = task.team.owner_username

    # 5. 清理其他用户个人任务里指向该用户的负责人引用。
    personal_assigned_tasks = db.query(models.Task).filter(
        models.Task.team_id.is_(None),
        models.Task.assignee_username == username
    ).all()
    for task in personal_assigned_tasks:
        task.assignee_username = None

    # 6. 将该用户从所有参与或管理的团队中移除。
    membership_cleanup_query = db.query(models.TeamMember).filter(
        models.TeamMember.username == username
    )
    if owned_team_ids:
        membership_cleanup_query = membership_cleanup_query.filter(
            ~models.TeamMember.team_id.in_(owned_team_ids)
        )
    membership_cleanup_query.delete(synchronize_session=False)

    # 经过前面的显式清理后，直接删除用户记录，避免 ORM 级联再次删除已处理过的关系对象。
    db.query(models.User).filter(
        models.User.username == username
    ).delete(synchronize_session=False)
    db.commit()
    return True

# 任务相关（创建、查询、更新、删除）

def find_task_title_conflict(
    db: Session,
    *,
    title: str,
    username: str,
    team_id: int | None,
    exclude_task_id: int | None = None
) -> models.Task | None:
    """按前端当前作用域规则查询同名任务冲突。"""
    if not title or not title.strip():
        return None

    query = db.query(models.Task).filter(models.Task.title == title)

    if team_id is None:
        # 个人任务：和当前用户可见的个人任务比较。
        query = query.filter(
            models.Task.team_id.is_(None),
            or_(
                models.Task.owner_username == username,
                models.Task.assignee_username == username
            )
        )
    else:
        # 团队任务：只和同一团队内的任务比较。
        query = query.filter(models.Task.team_id == team_id)

    if exclude_task_id is not None:
        query = query.filter(models.Task.id != exclude_task_id)

    return query.first()

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


def create_team_task(db: Session, task: schemas.TaskCreate, username: str) -> models.Task:
    """创建团队任务，绑定创建者与归属团队"""
    if not task.title or not task.title.strip():
        raise HTTPException(status_code=400, detail="任务标题不能为空")
    db_task = models.Task(
        **task.dict(exclude={"team_id", "assignee_username"}),
        owner_username=username,
        team_id=task.team_id,
        assignee_username=task.assignee_username
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_team_tasks(db: Session, team_id: int) -> list[models.Task]:
    """获取指定团队下的全部任务"""
    if team_id <= 0:
        return []
    return db.query(models.Task).filter(models.Task.team_id == team_id).all()


def get_assigned_tasks(db: Session, username: str) -> list[models.Task]:
    """获取分配给当前用户的团队任务"""
    return db.query(models.Task).filter(models.Task.assignee_username == username).all()


def update_task_status_only(db: Session, task_id: int, status: str):
    """仅更新任务状态，用于普通成员修改自己的任务"""
    if task_id <= 0:
        return None
    if not status or not status.strip():
        return None
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        return None

    task.status = status
    db.commit()
    db.refresh(task)
    return task
