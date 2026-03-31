from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Annotated

from ..database import get_db
from .. import schemas, crud
from ..security import get_current_user

# 任务路由，前缀 /api/tasks
router = APIRouter(prefix="/api/tasks", tags=["个人任务"])

# 数据库依赖
DBDep = Annotated[Session, Depends(get_db)]

# 当前登录用户依赖
UserDep = Annotated[schemas.UserResponse, Depends(get_current_user)]

# 创建任务
@router.post("/", response_model=schemas.BaseResponse)
def create_task(task: schemas.TaskCreate, user: UserDep, db: DBDep):
    """创建新任务，归属当前用户"""
    data = crud.create_task(db, task, user.username)
    return {"code": 200, "msg": "创建成功", "data": schemas.TaskResponse.from_orm(data).dict()}

# 获取任务列表
@router.get("/", response_model=schemas.BaseResponse)
def get_tasks(user: UserDep, db: DBDep):
    """获取当前用户的所有任务"""
    tasks = crud.get_tasks(db, user.username)
    return {"code": 200, "msg": "获取成功", "data": [schemas.TaskResponse.from_orm(t).dict() for t in tasks]}

# 获取单个任务详情
@router.get("/{task_id}", response_model=schemas.BaseResponse)
def get_task(task_id: int, user: UserDep, db: DBDep):
    """根据任务ID获取单条任务详情，仅自己可见"""
    task = crud.get_task_by_id(db, task_id, user.username)
    return {"code": 200, "msg": "获取成功", "data": schemas.TaskResponse.from_orm(task).dict()}

# 更新任务
@router.put("/{task_id}", response_model=schemas.BaseResponse)
def update_task(task_id: int, task: schemas.TaskUpdate, user: UserDep, db: DBDep):
    """更新任务信息，仅自己可更新"""
    updated = crud.update_task(db, task_id, task, user.username)
    return {"code": 200, "msg": "更新成功", "data": schemas.TaskResponse.from_orm(updated).dict()}

# 删除任务
@router.delete("/{task_id}", response_model=schemas.BaseResponse)
def delete_task(task_id: int, user: UserDep, db: DBDep):
    """删除任务，仅自己可删除"""
    crud.delete_task(db, task_id, user.username)
    return {"code": 200, "msg": "删除成功", "data": None}