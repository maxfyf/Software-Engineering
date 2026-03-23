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