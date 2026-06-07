from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
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

class TeamRole(str, enum.Enum):
    OWNER = "Owner"
    ADMIN = "Admin"
    MEMBER = "Member"

class User(Base):
    """系统用户模型，保存登录信息、个人资料以及关联任务/团队关系。"""

    __tablename__ = "users"

    username = Column(String(20), primary_key=True, index=True, unique=True)  # 主键、不重复
    password_hash = Column(String, nullable=False)                            # 存储加密后的密码
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=True)

    # 建立与 Task 表的一对多关系
    # cascade="all, delete-orphan" 意味着如果用户被删除，他名下的所有任务也会自动删除
    tasks = relationship(
        "Task",
        back_populates="owner",
        cascade="all, delete-orphan",
        foreign_keys="Task.owner_username"
    )
    owned_teams = relationship(
        "Team",
        back_populates="owner",
        foreign_keys="Team.owner_username"
    )
    team_memberships = relationship(
        "TeamMember",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class Team(Base):
    """协作团队模型，包含拥有者、成员关系以及团队任务。"""

    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    owner_username = Column(String(20), ForeignKey("users.username"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="owned_teams", foreign_keys=[owner_username])
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="team", cascade="all, delete-orphan")


class TeamMember(Base):
    """团队成员关系模型，用于记录用户在团队中的角色。"""

    __tablename__ = "team_members"
    __table_args__ = (
        UniqueConstraint("team_id", "username", name="uq_team_member"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    username = Column(String(20), ForeignKey("users.username"), nullable=False)
    role = Column(String, default=TeamRole.MEMBER.value, nullable=False)
    joined_at = Column(DateTime, default=func.now())

    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")


class Task(Base):
    """任务模型，统一表示个人任务和团队任务。"""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(100), nullable=False)                  # 标题
    description = Column(Text, nullable=True)                    # 描述
    status = Column(String, default=TaskStatus.TODO.value)       # 状态，默认待办
    priority = Column(String, default=TaskPriority.MEDIUM.value) # 优先级，默认中等
    due_date = Column(DateTime, nullable=True)                   # 截止时间
    
    # 自动处理时间戳
    created_at = Column(DateTime, default=func.now())           # 创建时间
    # onupdate 会在每次修改这条记录时自动更新为当前时间
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now()) # 更新时间

    # 外键：关联到 users 表的 username 字段，这是区分任务归属的关键
    owner_username = Column(String(20), ForeignKey("users.username"), nullable=False)

    # 建立与 User 表的反向关系
    owner = relationship("User", back_populates="tasks", foreign_keys=[owner_username])
    
    #标记团队ID
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=True)  # 归属团队
    assignee_username = Column(String(20), ForeignKey("users.username"), nullable=True)  # 被分配人
    
    #映射任务关系
    team = relationship("Team", back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assignee_username])

    @property
    def predecessors(self):
        """获取所有前置任务（直接依赖）"""
        return [dep.predecessor for dep in self.predecessors_rel]

    @property
    def successors(self):
        """获取所有后继任务（依赖本任务的任务）"""
        return [dep.successor for dep in self.successors_rel]

class TaskDependency(Base):
    __tablename__ = "task_dependencies"

    id = Column(Integer, primary_key=True, index=True)
    predecessor_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    successor_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)

    # 关系（便于 ORM 查询）
    predecessor = relationship("Task", foreign_keys=[predecessor_id], backref="successors_rel")
    successor = relationship("Task", foreign_keys=[successor_id], backref="predecessors_rel")

    __table_args__ = (UniqueConstraint("predecessor_id", "successor_id", name="unique_dep"),)


#===============新增日志=================
#该表用于记录用户的操作日志，方便后续审计和问题排查
#采用平铺快照形式记录操作对象的关键信息，避免后续数据变更导致日志失效
class OperationLog(Base):
    """操作日志记录表"""
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    operator_username = Column(String(20), nullable=False)    
    action_type = Column(String(20), nullable=False)          # create/edit/delete
    
    object_id = Column(Integer, nullable=False)
    object_type = Column(String(20), nullable=False)          
    object_title = Column(String(100), nullable=True)         
    object_deleted = Column(Integer, default=0)               
    
    scope_type = Column(String(20), nullable=False)           
    scope_id = Column(Integer, nullable=True)                 
    scope_title = Column(String(100), nullable=True)          
    
    description = Column(String(255), nullable=True)          # 简要变更内容
    operated_at = Column(DateTime, default=func.now())