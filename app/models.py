from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .database import Base

# 用户表模型
class DBUser(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(20), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # 关联任务表（一个用户对应多个任务）
    tasks = relationship("DBTask", back_populates="owner")

# 任务表模型
class DBTask(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 关联用户ID
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum("待办", "进行中", "已完成", name="task_status"), default="待办", nullable=False)
    priority = Column(Enum("低", "中", "高", name="task_priority"), default="中", nullable=False)
    deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # 关联用户表（多个任务对应一个用户）
    owner = relationship("DBUser", back_populates="tasks")