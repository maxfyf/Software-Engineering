from sqlalchemy.orm import Session
import models, schemas, security

# 注册相关

def get_user_by_username(db: Session, username: str) -> models.User | None:
    """根据用户名查询用户（API层用来判断用户是否已存在）"""
    return db.query(models.User).filter(models.User.username == username).first()

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

def authenticate_user(db: Session, username: str, password: str) -> models.User | None:
    """验证用户登录（API层调用此函数，如果返回None说明账号或密码错误）"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not security.verify_password(password, user.password_hash):
        return None
    return user

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