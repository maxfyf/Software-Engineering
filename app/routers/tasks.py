from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated

# 导入公共模块
from ..database import get_db
from ..schemas import TaskCreate, TaskUpdate
from ..security import get_current_user

router = APIRouter(prefix="/api/tasks", tags="个人任务")
DBDep = Annotated[Session, Depends(get_db)]
UserDep = Annotated[dict, Depends(get_current_user)]

# 创建任务
@router.post("/")
def create_task(task: TaskCreate, user: UserDep, db: DBDep):
    raise HTTPException(status_code=200, detail="创建任务接口 - 已完成")

# 获取任务列表
@router.get("/")
def get_tasks(user: UserDep, db: DBDep):
    raise HTTPException(status_code=200, detail="任务列表接口 - 已完成")

# 获取任务详情
@router.get("/{task_id}")
def get_task(task_id: int, user: UserDep, db: DBDep):
    raise HTTPException(status_code=200, detail="任务详情接口 - 已完成")

# 修改任务
@router.put("/{task_id}")
def update_task(task_id: int, task: TaskUpdate, user: UserDep, db: DBDep):
    raise HTTPException(status_code=200, detail="修改任务接口 - 已完成")

# 删除任务
@router.delete("/{task_id}")
def delete_task(task_id: int, user: UserDep, db: DBDep):
    raise HTTPException(status_code=200, detail="删除任务接口 - 已完成")