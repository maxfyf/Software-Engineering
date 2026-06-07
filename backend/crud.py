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

def validate_team_task_assignee(
    db: Session,
    team_id: int,
    assignee_username: str | None
) -> str | None:
    """校验团队任务负责人必须仍是该团队成员。"""
    if not assignee_username:
        return None
    if not get_team_membership(db, team_id, assignee_username):
        return "团队任务负责人必须是团队成员"
    return None


def _task_log_scope(task: models.Task) -> tuple[str, int | None, str]:
    if task.team_id is None:
        return "personal", None, task.owner_username
    return "team", task.team_id, task.team.name if task.team else ""


def _log_task_assignee_change(
    db: Session,
    *,
    operator_username: str,
    task: models.Task,
    old_assignee: str | None,
    new_assignee: str | None,
    reason: str
) -> None:
    scope_type, scope_id, scope_title = _task_log_scope(task)
    log_operation(
        db,
        operator=operator_username,
        action_type="edit",
        object_id=task.id,
        object_type="task",
        object_title=task.title,
        scope_type=scope_type,
        scope_id=scope_id,
        scope_title=scope_title,
        description=f"{reason}，任务负责人由 {old_assignee or '未分配'} 变更为 {new_assignee or '未分配'}"
    )


def _log_task_owner_change(
    db: Session,
    *,
    operator_username: str,
    task: models.Task,
    old_owner: str,
    new_owner: str,
    reason: str
) -> None:
    scope_type, scope_id, scope_title = _task_log_scope(task)
    log_operation(
        db,
        operator=operator_username,
        action_type="edit",
        object_id=task.id,
        object_type="task",
        object_title=task.title,
        scope_type=scope_type,
        scope_id=scope_id,
        scope_title=scope_title,
        description=f"{reason}，任务创建者由 {old_owner} 变更为 {new_owner}"
    )


def _log_task_deleted(
    db: Session,
    *,
    operator_username: str,
    task: models.Task,
    reason: str
) -> None:
    scope_type, scope_id, scope_title = _task_log_scope(task)
    log_operation(
        db,
        operator=operator_username,
        action_type="delete",
        object_id=task.id,
        object_type="task",
        object_title=task.title,
        scope_type=scope_type,
        scope_id=scope_id,
        scope_title=scope_title,
        description=reason,
        object_deleted=True
    )

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
        if not is_self_leave:
            return False, "不能移除 Owner"

        new_owner = db.query(models.TeamMember).filter(
            models.TeamMember.team_id == team_id,
            models.TeamMember.username != member_username,
            models.TeamMember.role == ROLE_ADMIN
        ).order_by(
            models.TeamMember.joined_at.asc(),
            models.TeamMember.id.asc()
        ).first()
        if not new_owner:
            new_owner = db.query(models.TeamMember).filter(
                models.TeamMember.team_id == team_id,
                models.TeamMember.username != member_username,
                models.TeamMember.role == ROLE_MEMBER
            ).order_by(
                models.TeamMember.joined_at.asc(),
                models.TeamMember.id.asc()
            ).first()
        if not new_owner:
            return False, "仅含 Owner 的团队不允许退出"

        team.owner_username = new_owner.username
        new_owner.role = ROLE_OWNER
        task_assignee_username = new_owner.username
    else:
        task_assignee_username = team.owner_username

    # 移除成员前，将其负责的未完成团队任务转交给当前 Owner；已完成任务保留历史负责人。
    assigned_tasks = db.query(models.Task).filter(
        models.Task.team_id == team_id,
        models.Task.assignee_username == member_username,
        models.Task.status != models.TaskStatus.DONE.value
    ).all()
    for task in assigned_tasks:
        old_assignee = task.assignee_username
        task.assignee_username = task_assignee_username
        reason = f"成员 {member_username} 主动离开团队" if is_self_leave else f"成员 {member_username} 被移出团队"
        _log_task_assignee_change(
            db,
            operator_username=operator_username,
            task=task,
            old_assignee=old_assignee,
            new_assignee=task_assignee_username,
            reason=reason
        )

    db.delete(membership)
    db.commit()
    return True, None


def delete_team(
    db: Session,
    team_id: int,
    *,
    commit: bool = True,
    operator_username: str | None = None
) -> bool:
    """删除团队、成员关系和团队任务；团队任务不迁移为个人任务。

    团队任务被删除时，相关任务依赖关系也会被同步清理。
    """
    team = get_team_by_id(db, team_id)
    if not team:
        return False

    operator = operator_username or team.owner_username
    team_tasks = db.query(models.Task).filter(models.Task.team_id == team_id).all()
    for task in team_tasks:
        _log_task_deleted(
            db,
            operator_username=operator,
            task=task,
            reason=f"团队 {team.name} 解散，团队任务被删除"
        )

    # 先显式删除任务依赖和团队任务，确保现有数据库也不会把团队任务退化成个人任务。
    team_task_ids = [
        task.id for task in team_tasks
    ]
    if team_task_ids:
        db.query(models.TaskDependency).filter(
            or_(
                models.TaskDependency.predecessor_id.in_(team_task_ids),
                models.TaskDependency.successor_id.in_(team_task_ids)
            )
        ).delete(synchronize_session=False)
        db.query(models.Task).filter(models.Task.id.in_(team_task_ids)).delete(synchronize_session=False)
    db.delete(team)
    if commit:
        db.commit()
    return True


def cancel_account(db: Session, username: str) -> bool:
    """按业务规则注销账号，并清理/迁移与该用户关联的数据。"""
    if not get_user_by_username(db, username):
        return False

    # 1. 删除该用户的所有个人任务。
    personal_tasks = db.query(models.Task).filter(
        models.Task.owner_username == username,
        models.Task.team_id.is_(None)
    ).all()
    for task in personal_tasks:
        _log_task_deleted(
            db,
            operator_username=username,
            task=task,
            reason=f"用户 {username} 注销账号，个人任务被删除"
        )
    if personal_tasks:
        db.query(models.Task).filter(
            models.Task.id.in_([task.id for task in personal_tasks])
        ).delete(synchronize_session=False)

    # 2. 解散该用户拥有的所有团队，并删除这些团队下的全部任务。
    owned_teams = db.query(models.Team).filter(models.Team.owner_username == username).all()
    owned_team_ids = [team.id for team in owned_teams]
    for team in owned_teams:
        delete_team(db, team.id, commit=False, operator_username=username)

    # 3. 将该用户负责的所有剩余团队任务转交给各自团队拥有者。
    assigned_team_tasks = db.query(models.Task).join(
        models.Team, models.Task.team_id == models.Team.id
    ).filter(
        models.Task.team_id.isnot(None),
        models.Task.assignee_username == username
    ).all()
    for task in assigned_team_tasks:
        old_assignee = task.assignee_username
        task.assignee_username = task.team.owner_username
        _log_task_assignee_change(
            db,
            operator_username=username,
            task=task,
            old_assignee=old_assignee,
            new_assignee=task.team.owner_username,
            reason=f"用户 {username} 注销账号"
        )

    # 4. 对仍然保留的团队任务，如果该用户是创建者，则同步改为团队拥有者，
    #    避免删除用户时留下 owner 外键引用。
    owned_team_tasks = db.query(models.Task).join(
        models.Team, models.Task.team_id == models.Team.id
    ).filter(
        models.Task.team_id.isnot(None),
        models.Task.owner_username == username
    ).all()
    for task in owned_team_tasks:
        old_owner = task.owner_username
        task.owner_username = task.team.owner_username
        _log_task_owner_change(
            db,
            operator_username=username,
            task=task,
            old_owner=old_owner,
            new_owner=task.team.owner_username,
            reason=f"用户 {username} 注销账号"
        )

    # 5. 清理其他用户个人任务里指向该用户的负责人引用。
    personal_assigned_tasks = db.query(models.Task).filter(
        models.Task.team_id.is_(None),
        models.Task.assignee_username == username
    ).all()
    for task in personal_assigned_tasks:
        old_assignee = task.assignee_username
        task.assignee_username = None
        _log_task_assignee_change(
            db,
            operator_username=username,
            task=task,
            old_assignee=old_assignee,
            new_assignee=None,
            reason=f"用户 {username} 注销账号"
        )

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
    """创建任务并绑定到当前登录用户，写入数据库。"""
    if task.team_id is not None:
        if not get_team_by_id(db, task.team_id):
            raise HTTPException(status_code=400, detail="团队不存在")
        if not require_team_role(db, task.team_id, username, {ROLE_ADMIN, ROLE_OWNER}):
            raise HTTPException(status_code=403, detail="无权在该团队中创建任务")
        assignee_error = validate_team_task_assignee(db, task.team_id, task.assignee_username)
        if assignee_error:
            raise HTTPException(status_code=400, detail=assignee_error)

    db_task = models.Task(
        **task.model_dump(),
        owner_username=username
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def get_tasks(db: Session, username: str) -> list[models.Task]:
    """获取当前用户可访问的个人任务和团队任务。"""
    personal_tasks = db.query(models.Task).filter(
        models.Task.team_id.is_(None),
        or_(
            models.Task.owner_username == username,
            models.Task.assignee_username == username
        )
    ).all()
    team_tasks = db.query(models.Task).join(
        models.TeamMember,
        models.Task.team_id == models.TeamMember.team_id
    ).filter(
        models.TeamMember.username == username
    ).all()
    return list({task.id: task for task in personal_tasks + team_tasks}.values())

def get_task_by_id(db: Session, task_id: int, username: str) -> models.Task:
    """根据任务ID查询单条任务；团队任务必须按成员关系授权。"""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或无权访问")
    if task.team_id is None:
        if task.owner_username == username or task.assignee_username == username:
            return task
    elif get_team_membership(db, task.team_id, username):
        return task
    raise HTTPException(status_code=404, detail="任务不存在或无权访问")

def update_task(db: Session, task_id: int, task: schemas.TaskUpdate, username: str) -> models.Task:
    """更新指定任务；团队任务按成员角色校验权限。"""
    db_task = get_task_by_id(db, task_id, username)
    updates = task.model_dump(exclude_unset=True)

    if db_task.team_id is None:
        if db_task.owner_username != username:
            raise HTTPException(status_code=403, detail="无权编辑该任务")
    else:
        membership = get_team_membership(db, db_task.team_id, username)
        if not membership:
            raise HTTPException(status_code=403, detail="无权编辑该任务")
        if membership.role not in {ROLE_ADMIN, ROLE_OWNER}:
            if db_task.assignee_username != username or set(updates) != {"status"}:
                raise HTTPException(status_code=403, detail="无权编辑该任务")
    
    # 仅更新前端传入的字段
    for key, value in updates.items():
        setattr(db_task, key, value)
    
    db.commit()
    db.refresh(db_task)
    return db_task

def delete_task_with_dependencies(db: Session, task_id: int, is_cascade: bool):
    """支持级联/非级联删除的图节点清理逻辑"""
    if not is_cascade:
        # 非级联：仅删除当前任务（外键 ondelete="CASCADE" 会自动清理相关的依赖关系记录）
        db.query(models.Task).filter(models.Task.id == task_id).delete()
    else:
        # 级联删除：找出所有后继子图节点进行批量删除
        tasks_to_delete = set()
        queue = [task_id]
        
        while queue:
            current = queue.pop(0)
            tasks_to_delete.add(current)
            deps = db.query(models.TaskDependency).filter(models.TaskDependency.predecessor_id == current).all()
            for dep in deps:
                if dep.successor_id not in tasks_to_delete:
                    queue.append(dep.successor_id)
        
        db.query(models.Task).filter(models.Task.id.in_(tasks_to_delete)).delete(synchronize_session=False)


def delete_task(db: Session, task_id: int, username: str) -> None:
    """删除指定任务；团队任务仅 Owner/Admin 可删除。"""
    db_task = get_task_by_id(db, task_id, username)
    if db_task.team_id is None:
        if db_task.owner_username != username:
            raise HTTPException(status_code=403, detail="无权删除该任务")
    elif not require_team_role(db, db_task.team_id, username, {ROLE_ADMIN, ROLE_OWNER}):
        raise HTTPException(status_code=403, detail="无权删除该团队任务")
    db.delete(db_task)
    db.commit()


def create_team_task(db: Session, task: schemas.TaskCreate, username: str) -> models.Task:
    """创建团队任务，绑定创建者与归属团队"""
    if not task.title or not task.title.strip():
        raise HTTPException(status_code=400, detail="任务标题不能为空")
    if task.team_id is None or not get_team_by_id(db, task.team_id):
        raise HTTPException(status_code=400, detail="团队不存在")
    if not require_team_role(db, task.team_id, username, {ROLE_ADMIN, ROLE_OWNER}):
        raise HTTPException(status_code=403, detail="无权创建团队任务")
    assignee_error = validate_team_task_assignee(db, task.team_id, task.assignee_username)
    if assignee_error:
        raise HTTPException(status_code=400, detail=assignee_error)

    db_task = models.Task(
        **task.model_dump(exclude={"team_id", "assignee_username"}),
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
    """获取分配给当前用户且仍可访问的任务。"""
    personal_tasks = db.query(models.Task).filter(
        models.Task.team_id.is_(None),
        models.Task.assignee_username == username
    ).all()
    team_tasks = db.query(models.Task).join(
        models.TeamMember,
        models.Task.team_id == models.TeamMember.team_id
    ).filter(
        models.Task.assignee_username == username,
        models.TeamMember.username == username
    ).all()
    return list({task.id: task for task in personal_tasks + team_tasks}.values())


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



# ---------- 任务依赖 ----------
def get_predecessors(db: Session, task_id: int) -> list[models.Task]:
    """获取任务的前置任务列表"""
    deps = db.query(models.TaskDependency).filter(
        models.TaskDependency.successor_id == task_id
    ).all()
    return [dep.predecessor for dep in deps]

def get_successors(db: Session, task_id: int) -> list[models.Task]:
    """获取任务的后继任务列表"""
    deps = db.query(models.TaskDependency).filter(
        models.TaskDependency.predecessor_id == task_id
    ).all()
    return [dep.successor for dep in deps]


def create_task_dependency(db: Session, predecessor_id: int, successor_id: int) -> tuple[bool, str | None]:
    """创建一条任务依赖关系，兼容旧测试和内部调用。"""
    if predecessor_id == successor_id:
        return False, "任务不能依赖自身"

    predecessor = db.query(models.Task).filter(models.Task.id == predecessor_id).first()
    successor = db.query(models.Task).filter(models.Task.id == successor_id).first()
    if not predecessor or not successor:
        return False, "任务不存在"

    existing = db.query(models.TaskDependency).filter(
        models.TaskDependency.predecessor_id == predecessor_id,
        models.TaskDependency.successor_id == successor_id
    ).first()
    if existing:
        return False, "依赖关系已存在"

    if check_circular_dependency(db, predecessor_id, successor_id):
        return False, "不允许添加循环依赖"

    db.add(models.TaskDependency(
        predecessor_id=predecessor_id,
        successor_id=successor_id
    ))
    db.commit()
    return True, None

def update_predecessors(db: Session, task_id: int, pred_ids: list[int]) -> bool:
    """全量更新前置任务依赖（先删后增）"""
    # 删除原有依赖
    db.query(models.TaskDependency).filter(
        models.TaskDependency.successor_id == task_id
    ).delete()
    # 添加新依赖
    for pred_id in pred_ids:
        dep = models.TaskDependency(
            predecessor_id=pred_id,
            successor_id=task_id
        )
        db.add(dep)
    db.commit()
    return True

def check_circular_dependency(db: Session, pred_id: int, succ_id: int) -> bool:
    """
    检测添加依赖 (pred_id -> succ_id) 是否会产生循环依赖。
    使用 DFS 从 succ_id 出发，看是否能回到 pred_id。
    """
    visited = set()
    stack = [succ_id]
    while stack:
        cur = stack.pop()
        if cur == pred_id:
            return True
        if cur in visited:
            continue
        visited.add(cur)
        # 取当前任务的后继任务
        next_tasks = db.query(models.TaskDependency.successor_id).filter(
            models.TaskDependency.predecessor_id == cur
        ).all()
        stack.extend([nt[0] for nt in next_tasks])
    return False

def can_access_task(db: Session, user_id: str, task: models.Task) -> bool:
    """检查用户是否有权查看该任务（个人任务本人，团队任务成员）"""
    if task.team_id is None:
        return task.owner_username == user_id or task.assignee_username == user_id
    else:
        return get_team_membership(db, task.team_id, user_id) is not None

def can_manage_task(db: Session, user_id: str, task: models.Task) -> bool:
    """检查用户是否有权修改任务依赖/删除任务（个人任务本人，团队任务Owner/Admin）"""
    if task.team_id is None:
        return task.owner_username == user_id
    else:
        membership = get_team_membership(db, task.team_id, user_id)
        return membership is not None and membership.role in (ROLE_OWNER, ROLE_ADMIN)
    
def delete_task_with_deps(db: Session, task_id: int, cascade: bool = False) -> None:
    """删除任务，根据 cascade 决定是否级联删除所有后继任务"""
    # 获取要删除的任务对象（用于后续判断）
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        return

    if cascade:
        # 级联删除：递归获取所有后继任务 ID（包括间接后继）
        to_delete = set()
        stack = [task_id]
        while stack:
            cur = stack.pop()
            if cur in to_delete:
                continue
            to_delete.add(cur)
            # 查找当前任务的所有后继
            successors = db.query(models.TaskDependency.successor_id).filter(
                models.TaskDependency.predecessor_id == cur
            ).all()
            for (sid,) in successors:
                if sid not in to_delete:
                    stack.append(sid)

        # 删除所有涉及到的依赖关系（避免外键约束）
        db.query(models.TaskDependency).filter(
            models.TaskDependency.predecessor_id.in_(to_delete) |
            models.TaskDependency.successor_id.in_(to_delete)
        ).delete(synchronize_session=False)
        # 删除任务
        db.query(models.Task).filter(models.Task.id.in_(to_delete)).delete(synchronize_session=False)
    else:
        # 非级联：只删除当前任务，并清理所有与它相关的依赖（作为前置或后继）
        db.query(models.TaskDependency).filter(
            (models.TaskDependency.predecessor_id == task_id) |
            (models.TaskDependency.successor_id == task_id)
        ).delete()
        db.delete(task)

    db.commit()

def transfer_team_ownership(db: Session, team_id: int, new_owner_username: str, current_owner_username: str) -> tuple[bool, str | None]:
    """转让团队所有权。当前用户必须是 Owner，新用户必须在团队中。转让后原 Owner 降为 Admin。返回 (成功与否, 错误信息)"""
    team = get_team_by_id(db, team_id)
    if not team:
        return False, "团队不存在"
    if team.owner_username != current_owner_username:
        return False, "只有团队所有者可以转让所有权"
    if new_owner_username == current_owner_username:
        return False, "不能转让给自己"

    new_membership = get_team_membership(db, team_id, new_owner_username)
    if not new_membership:
        return False, "新所有者不在团队中"

    # 更新团队 owner
    team.owner_username = new_owner_username

    # 原 owner 降为 Admin
    old_membership = get_team_membership(db, team_id, current_owner_username)
    if old_membership:
        old_membership.role = ROLE_ADMIN

    # 新 owner 角色提升为 Owner（如果原来是 Admin/Member）
    new_membership.role = ROLE_OWNER

    db.commit()
    return True, None

def leave_team(
    db: Session, team_id: int, username: str) -> tuple[bool, str | None]:
    """用户主动离开团队。如果是 Owner 且团队内还有其他人，则自动选择新 Owner（优先 Admin，否则 Member），并将原 Owner 降为 Admin 后移除（或直接移除并转让所有权）。离开前，将该用户负责的未完成任务转交给团队当前 Owner。"""
    team = get_team_by_id(db, team_id)
    if not team:
        return False, "团队不存在"
    membership = get_team_membership(db, team_id, username)
    if not membership:
        return False, "您不是该团队成员"

    task_assignee_username = team.owner_username

    # 如果是 Owner 离开
    if team.owner_username == username:
        # 检查是否还有其他成员
        other_members = db.query(models.TeamMember).filter(
            models.TeamMember.team_id == team_id,
            models.TeamMember.username != username
        ).all()
        if not other_members:
            return False, "团队仅剩您一人，请直接解散团队"
        # 选择新 Owner：优先 Admin，否则取第一个 Member
        new_owner_candidate = None
        for m in other_members:
            if m.role == ROLE_ADMIN:
                new_owner_candidate = m
                break
        if not new_owner_candidate:
            new_owner_candidate = other_members[0]

        # 转让所有权
        team.owner_username = new_owner_candidate.username
        # 新 owner 角色提升为 Owner
        new_owner_candidate.role = ROLE_OWNER
        task_assignee_username = new_owner_candidate.username

    # 处理任务转交：将该用户负责的未完成任务转给团队 Owner
    assigned_tasks = db.query(models.Task).filter(
        models.Task.team_id == team_id,
        models.Task.assignee_username == username,
        models.Task.status != "已完成"
    ).all()
    for task in assigned_tasks:
        old_assignee = task.assignee_username
        task.assignee_username = task_assignee_username
        _log_task_assignee_change(
            db,
            operator_username=username,
            task=task,
            old_assignee=old_assignee,
            new_assignee=task_assignee_username,
            reason=f"成员 {username} 主动离开团队"
        )

    # 删除该用户的成员记录
    db.delete(membership)
    db.commit()
    return True, None

#=============写入操作日志公有函数================
#供各个业务操作调用，用以生成一条记录。注意本身不执行db.commit()，由调用方根据业务流程决定是否提交事务。
def log_operation(db: Session, operator: str, action_type: str,
                  object_id: int, object_type: str, object_title: str,
                  scope_type: str, scope_id: int | None, scope_title: str,
                  description: str, object_deleted: bool = False) -> models.OperationLog:
    """通用日志记录器。"""
    log = models.OperationLog(
        operator_username=operator,
        action_type=action_type,
        object_id=object_id,
        object_type=object_type,
        object_title=object_title,
        object_deleted=1 if object_deleted else 0,
        scope_type=scope_type,
        scope_id=scope_id,
        scope_title=scope_title,
        description=description
    )
    db.add(log)
    return log


def serialize_operation_log(log: models.OperationLog) -> dict:
    """将操作日志序列化为前端可直接展示的结构。"""
    return {
        "id": log.id,
        "operator": log.operator_username,
        "type": log.action_type,
        "object": {
            "id": log.object_id,
            "title": log.object_title,
            "type": log.object_type,
            "deleted": bool(log.object_deleted),
        },
        "operatedAt": log.operated_at.strftime("%Y-%m-%d %H:%M:%S") if log.operated_at else None,
        "description": log.description,
        "scope": {
            "type": log.scope_type,
            "id": log.scope_id,
            "title": log.scope_title,
        },
    }


def _limit_operation_log_count(limit: int | None) -> int:
    """限制日志查询条数，避免接口误用一次取太多。"""
    if limit is None:
        return 10
    return max(1, min(limit, 100))


def _query_operation_logs(db: Session):
    return db.query(models.OperationLog).order_by(
        models.OperationLog.operated_at.desc(),
        models.OperationLog.id.desc(),
    )


def _can_read_log_scope(db: Session, scope_type: str, scope_id: int | None, username: str) -> bool:
    if scope_type == "personal":
        return True
    if scope_type == "team" and scope_id is not None:
        return get_team_membership(db, scope_id, username) is not None
    return False


def get_task_operation_logs(db: Session, task_id: int, username: str, limit: int = 10) -> list[dict]:
    """获取任务最近操作日志，个人任务仅所属用户可见，团队任务仅当前成员可见。"""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if task:
        if task.team_id is None:
            if task.owner_username != username:
                raise HTTPException(status_code=403, detail="无权访问该任务日志")
        elif not get_team_membership(db, task.team_id, username):
            raise HTTPException(status_code=403, detail="无权访问该团队任务日志")
    else:
        latest_log = db.query(models.OperationLog).filter(
            models.OperationLog.object_type == "task",
            models.OperationLog.object_id == task_id,
        ).order_by(
            models.OperationLog.operated_at.desc(),
            models.OperationLog.id.desc(),
        ).first()
        if not latest_log:
            raise HTTPException(status_code=404, detail="任务日志不存在")
        if latest_log.scope_type == "personal":
            if latest_log.scope_title != username and latest_log.operator_username != username:
                raise HTTPException(status_code=403, detail="无权访问该任务日志")
        elif not _can_read_log_scope(db, latest_log.scope_type, latest_log.scope_id, username):
            raise HTTPException(status_code=403, detail="无权访问该团队任务日志")

    logs = _query_operation_logs(db).filter(
        models.OperationLog.object_type == "task",
        models.OperationLog.object_id == task_id,
    ).limit(_limit_operation_log_count(limit)).all()
    return [serialize_operation_log(log) for log in logs]


def get_scope_operation_logs(
    db: Session,
    scope_type: str,
    scope_id: int | None,
    username: str,
    limit: int = 50
) -> list[dict]:
    """获取个人或团队范围内的操作日志。"""
    if scope_type == "personal":
        scope_filter = (
            (models.OperationLog.scope_type == "personal") &
            (models.OperationLog.scope_title == username)
        )
    elif scope_type == "team" and scope_id is not None:
        if not get_team_membership(db, scope_id, username):
            raise HTTPException(status_code=403, detail="无权访问该团队日志")
        scope_filter = (
            (models.OperationLog.scope_type == "team") &
            (models.OperationLog.scope_id == scope_id)
        )
    else:
        raise HTTPException(status_code=400, detail="日志范围参数无效")

    logs = _query_operation_logs(db).filter(scope_filter).limit(_limit_operation_log_count(limit)).all()
    return [serialize_operation_log(log) for log in logs]
