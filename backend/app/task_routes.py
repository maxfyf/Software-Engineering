"""
任务模块接口路由（2.2版本）
接口规范：
- 前缀：/tasks
- 响应格式：统一使用schemas.BaseResponse（code/msg/data）
- 认证：所有接口均需登录（依赖security.py的get_current_user）
- 状态码：
  200: 成功
  401: 未登录/Token过期
  404: 任务不存在/跨用户访问
  422: 参数校验失败
适配文件：
- security.py: get_current_user（获取当前登录用户）
- database.py: get_db（数据库会话）
- schemas.py: 所有请求/响应模型
- crud.py: task_crud（CRUD逻辑）
"""
from typing import Annotated, Optional
from fastapi import APIRouter, Depends  # FastAPI路由核心
from sqlalchemy.orm import Session      # 数据库会话类型

# 相对导入：适配app/包结构
from .security import get_current_user  # 登录认证依赖（API提供）
from .database import get_db            # 数据库会话依赖（API提供）
from .models import DBUser              # 用户ORM模型（API提供）
from .schemas import (
    TaskCreateRequest,  # 任务创建请求模型
    TaskUpdateRequest,  # 任务更新请求模型
    TaskStatus,         # 任务状态枚举
    TaskPriority,       # 任务优先级枚举
    TaskInfo,           # 任务响应模型
    BaseResponse        # 通用响应模型（API规范）
)
from .crud import task_crud  # 任务CRUD逻辑（本模块核心）

# 初始化路由：前缀/tasks，标签用于Swagger文档分类
task_router = APIRouter(
    prefix="/tasks",  # 接口前缀：所有接口均以/tasks开头
    tags=["任务管理（2.2）"],  # Swagger文档标签
    responses={
        404: {"description": "任务不存在或无权访问"},  # 自定义响应描述
        401: {"description": "未登录或登录状态过期"},
        422: {"description": "请求参数格式错误"}
    }
)

# 依赖项简写：减少重复代码，提升可读性
# 协同注意：所有接口均复用这两个依赖
DBSessionDep = Annotated[Session, Depends(get_db)]          # 数据库会话依赖
CurrentUserDep = Annotated[DBUser, Depends(get_current_user)]  # 登录用户依赖


@task_router.post("", response_model=BaseResponse, summary="创建任务")
def create_task(
    task_create: TaskCreateRequest,  # 请求体：任务创建参数（schemas校验）
    current_user: CurrentUserDep,    # 依赖：当前登录用户（自动注入）
    db: DBSessionDep                 # 依赖：数据库会话（自动注入）
):
    """
    创建个人任务接口
    接口地址：POST /tasks
    请求体示例：
    {
        "title": "完成项目文档",
        "description": "编写接口对接文档",
        "status": "待办",
        "priority": "中",
        "deadline": "2026-04-01T18:00:00"
    }
    响应示例：
    {
        "code": 200,
        "msg": "任务创建成功",
        "data": {
            "id": 1,
            "title": "完成项目文档",
            "description": "编写接口对接文档",
            "status": "待办",
            "priority": "中",
            "deadline": "2026-04-01T18:00:00",
            "created_at": "2026-03-22T10:00:00",
            "updated_at": "2026-03-22T10:00:00"
        }
    }
    """
    # 调用CRUD创建任务：传入用户ID确保归属
    db_task = task_crud.create_task(db, task_create, current_user.id)
    # 封装通用响应：符合API规范
    return BaseResponse(
        code=200,                # 成功状态码
        msg="任务创建成功",       # 友好提示信息
        data=TaskInfo.from_orm(db_task).dict()  # 响应数据：ORM→TaskInfo→字典
    )


@task_router.get("", response_model=BaseResponse, summary="获取任务列表")
def get_task_list(
    current_user: CurrentUserDep,    # 登录用户依赖
    db: DBSessionDep,                # 数据库会话依赖
    page: int = 1,                   # 查询参数：页码（默认1）
    page_size: int = 10,             # 查询参数：每页条数（默认10）
    status: Optional[TaskStatus] = None,  # 查询参数：状态筛选（可选）
    priority: Optional[TaskPriority] = None  # 查询参数：优先级筛选（可选）
):
    """
    获取当前用户任务列表接口
    接口地址：GET /tasks?page=1&page_size=10&status=待办&priority=中
    响应示例：
    {
        "code": 200,
        "msg": "获取任务列表成功",
        "data": {
            "total": 5,
            "page": 1,
            "page_size": 10,
            "tasks": [
                {
                    "id": 1,
                    "title": "完成项目文档",
                    "description": "编写接口对接文档",
                    "status": "待办",
                    "priority": "中",
                    "deadline": "2026-04-01T18:00:00",
                    "created_at": "2026-03-22T10:00:00",
                    "updated_at": "2026-03-22T10:00:00"
                }
            ]
        }
    }
    """
    # 调用CRUD获取任务列表：传入分页+筛选参数
    result = task_crud.get_task_list(db, current_user.id, page, page_size, status, priority)
    # 封装通用响应
    return BaseResponse(
        code=200,
        msg="获取任务列表成功",
        data=result
    )


@task_router.get("/{task_id}", response_model=BaseResponse, summary="获取任务详情")
def get_task_detail(
    task_id: int,                   # 路径参数：任务ID
    current_user: CurrentUserDep,   # 登录用户依赖
    db: DBSessionDep                # 数据库会话依赖
):
    """
    获取任务详情接口
    接口地址：GET /tasks/{task_id}
    路径参数：task_id - 任务ID（整数）
    响应示例：
    {
        "code": 200,
        "msg": "获取任务详情成功",
        "data": {
            "id": 1,
            "title": "完成项目文档",
            "description": "编写接口对接文档",
            "status": "待办",
            "priority": "中",
            "deadline": "2026-04-01T18:00:00",
            "created_at": "2026-03-22T10:00:00",
            "updated_at": "2026-03-22T10:00:00"
        }
    }
    """
    # 调用CRUD获取任务详情
    db_task = task_crud.get_task_detail(db, task_id, current_user.id)
    # 封装通用响应
    return BaseResponse(
        code=200,
        msg="获取任务详情成功",
        data=TaskInfo.from_orm(db_task).dict()
    )


@task_router.put("/{task_id}", response_model=BaseResponse, summary="修改任务")
def update_task(
    task_id: int,                   # 路径参数：任务ID
    task_update: TaskUpdateRequest, # 请求体：任务更新参数（可选字段）
    current_user: CurrentUserDep,   # 登录用户依赖
    db: DBSessionDep                # 数据库会话依赖
):
    """
    修改个人任务接口（支持部分更新）
    接口地址：PUT /tasks/{task_id}
    路径参数：task_id - 任务ID（整数）
    请求体示例（仅修改状态）：
    {
        "status": "进行中"
    }
    响应示例：
    {
        "code": 200,
        "msg": "任务修改成功",
        "data": {
            "id": 1,
            "title": "完成项目文档",
            "description": "编写接口对接文档",
            "status": "进行中",
            "priority": "中",
            "deadline": "2026-04-01T18:00:00",
            "created_at": "2026-03-22T10:00:00",
            "updated_at": "2026-03-22T10:30:00"
        }
    }
    """
    # 调用CRUD更新任务
    db_task = task_crud.update_task(db, task_id, task_update, current_user.id)
    # 封装通用响应
    return BaseResponse(
        code=200,
        msg="任务修改成功",
        data=TaskInfo.from_orm(db_task).dict()
    )


@task_router.delete("/{task_id}", response_model=BaseResponse, summary="删除任务")
def delete_task(
    task_id: int,                   # 路径参数：任务ID
    current_user: CurrentUserDep,   # 登录用户依赖
    db: DBSessionDep                # 数据库会话依赖
):
    """
    删除个人任务接口
    接口地址：DELETE /tasks/{task_id}
    路径参数：task_id - 任务ID（整数）
    响应示例：
    {
        "code": 200,
        "msg": "任务删除成功",
        "data": null
    }
    """
    # 调用CRUD删除任务
    task_crud.delete_task(db, task_id, current_user.id)
    # 封装通用响应
    return BaseResponse(
        code=200,
        msg="任务删除成功",
        data=None
    )