from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.sql import func
import enum
from database import Base

# 定义任务状态的枚举类，方便规范数据
class TaskStatus(str, enum.Enum):
    TODO = "待办"               
    IN_PROGRESS = "进行中" 
    DONE = "已完成"               

# 定义优先级的枚举类
class TaskPriority(str, enum.Enum):
    LOW = "低"      
    MEDIUM = "中"
    HIGH = "高"    

class User(Base):
    __tablename__ = "users"

    username = Column(String(20), primary_key=True, index=True, unique=True) # 主键、不重复
    password_hash = Column(String, nullable=False)                           # 存储加密后的密码
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=True)

    # 建立与 Task 表的一对多关系
    # cascade="all, delete-orphan" 意味着如果用户被删除，他名下的所有任务也会自动删除
    tasks = relationship("Task", back_populates="owner", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(100), nullable=False)                 # 标题
    description = Column(Text, nullable=True)                   # 描述
    status = Column(String, default=TaskStatus.TODO.value)      # 状态，默认待办
    priority = Column(String, default=TaskPriority.MEDIUM.value)# 优先级，默认中等
    due_date = Column(DateTime, nullable=True)                  # 截止时间
    
    # 自动处理时间戳
    created_at = Column(DateTime, default=func.now())           # 创建时间
    # onupdate 会在每次修改这条记录时自动更新为当前时间
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now()) # 更新时间

    # 外键：关联到 users 表的 username 字段，这是区分任务归属的关键
    owner_username = Column(String(20), ForeignKey("users.username"), nullable=False)

    # 建立与 User 表的反向关系
    owner = relationship("User", back_populates="tasks")
