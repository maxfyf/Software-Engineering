"""
任务模块CRUD核心逻辑（2.2版本）
适配文件：
- models.py: DBTask模型（中文Enum、UTC时间、user_id外键）
- schemas.py: TaskCreateRequest/TaskUpdateRequest/TaskInfo/BaseResponse
- database.py: 数据库会话依赖
协同注意：
1. 所有操作均基于user_id做数据隔离，禁止跨用户访问
2. 状态/优先级使用中文Enum值，与schemas/models对齐
3. 时间字段由models自动生成UTC时间，无需手动赋值
4. 异常统一抛出HTTPException，由路由层封装为BaseResponse
"""
from typing import Optional, List
from fastapi import HTTPException  # 统一异常处理
from sqlalchemy.orm import Session  # 数据库会话类型
from datetime import datetime, timezone  # 时间类型适配

# 相对导入：适配app/包结构，与API对齐
from .models import DBTask  # API提供的任务ORM模型
from .schemas import (
    TaskCreateRequest,  # 任务创建请求模型
    TaskUpdateRequest,  # 任务更新请求模型
    TaskStatus,         # 任务状态枚举（待办/进行中/已完成）
    TaskPriority,       # 任务优先级枚举（低/中/高）
    TaskInfo            # 任务响应模型
)


class TaskCRUD:
    """
    任务CRUD操作类（单一职责原则）
    所有方法均为静态方法，无需实例化，直接通过类调用
    方法命名规范：动词+名词（create_task/get_task_list）
    """

    @staticmethod
    def _get_task_by_id_and_user_id(
        db: Session,
        task_id: int,
        user_id: int
    ) -> Optional[DBTask]:
        """
        【私有方法】校验任务归属关系（核心权限控制）
        :仅内部调用，禁止外部直接使用
        :param db: 数据库会话对象（来自database.py的get_db）
        :param task_id: 任务ID（前端传入）
        :param user_id: 当前登录用户ID（来自security.py的get_current_user）
        :return: 匹配的DBTask对象 | None（无匹配/跨用户）
        """
        return db.query(DBTask).filter(
            DBTask.id == task_id,    # 任务ID匹配
            DBTask.user_id == user_id # 用户ID匹配（数据隔离核心）
        ).first()

    @staticmethod
    def create_task(
        db: Session,
        task_create: TaskCreateRequest,
        user_id: int
    ) -> DBTask:
        """
        创建个人任务（接口对接：POST /tasks）
        :param db: 数据库会话对象
        :param task_create: 任务创建请求参数（已通过schemas校验）
        :param user_id: 当前登录用户ID（确保任务归属）
        :return: 创建后的DBTask对象（含自动生成的id/created_at/updated_at）
        :异常：无（参数校验由schemas完成，数据库异常由框架统一捕获）
        """
        # 构建ORM对象：严格映射models.py的DBTask字段
        db_task = DBTask(
            user_id=user_id,                      # 任务归属用户（必填）
            title=task_create.title,              # 任务标题（1-100字符，schemas已校验）
            description=task_create.description,  # 任务描述（可选）
            status=task_create.status.value,      # 任务状态（中文Enum值：待办/进行中/已完成）
            priority=task_create.priority.value,  # 任务优先级（中文Enum值：低/中/高）
            deadline=task_create.deadline,        # 截止时间（可选，datetime类型）
            # created_at/updated_at：由models.py的default自动生成UTC时间，无需手动赋值
        )

        # 数据库操作：新增→提交→刷新（获取自动生成的字段）
        db.add(db_task)        # 新增任务到会话
        db.commit()            # 提交事务（写入数据库）
        db.refresh(db_task)    # 刷新对象（获取自动生成的id/时间字段）
        return db_task

    @staticmethod
    def get_task_list(
        db: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None
    ) -> dict:
        """
        获取当前用户的任务列表（接口对接：GET /tasks）
        支持分页+状态/优先级筛选
        :param db: 数据库会话对象
        :param user_id: 当前登录用户ID
        :param page: 页码（默认1，最小1）
        :param page_size: 每页条数（默认10）
        :param status: 状态筛选（可选，中文Enum）
        :param priority: 优先级筛选（可选，中文Enum）
        :return: 分页结果字典 {total: 总数, page: 当前页, page_size: 每页条数, tasks: 任务列表}
        """
        # 基础查询：仅查询当前用户的任务（数据隔离）
        query = db.query(DBTask).filter(DBTask.user_id == user_id)

        # 条件筛选：状态/优先级（中文Enum值匹配models的Enum类型）
        if status:
            query = query.filter(DBTask.status == status.value)
        if priority:
            query = query.filter(DBTask.priority == priority.value)

        # 分页逻辑：防越界（page最小为1）
        page = max(page, 1)
        total = query.count()  # 总条数（用于分页计算）
        offset = (page - 1) * page_size  # 偏移量（跳过前N条）
        # 执行查询：按创建时间倒序（最新的在前）+ 分页
        tasks = query.order_by(DBTask.created_at.desc()).offset(offset).limit(page_size).all()

        # 结果转换：ORM对象 → schemas的TaskInfo模型（接口响应格式）
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "tasks": [TaskInfo.from_orm(task) for task in tasks]
        }

    @staticmethod
    def get_task_detail(
        db: Session,
        task_id: int,
        user_id: int
    ) -> DBTask:
        """
        获取任务详情（接口对接：GET /tasks/{task_id}）
        :param db: 数据库会话对象
        :param task_id: 任务ID
        :param user_id: 当前登录用户ID
        :return: 匹配的DBTask对象
        :raise HTTPException: 404（任务不存在/跨用户访问）
        """
        # 校验任务归属
        task = TaskCRUD._get_task_by_id_and_user_id(db, task_id, user_id)
        if not task:
            # 异常信息：明确且友好，便于前端提示用户
            raise HTTPException(
                status_code=404,
                detail="任务不存在或您无权访问该任务"
            )
        return task

    @staticmethod
    def update_task(
        db: Session,
        task_id: int,
        task_update: TaskUpdateRequest,
        user_id: int
    ) -> DBTask:
        """
        更新个人任务（接口对接：PUT /tasks/{task_id}）
        支持部分更新（仅传入需要修改的字段）
        :param db: 数据库会话对象
        :param task_id: 任务ID
        :param task_update: 任务更新请求参数（可选字段）
        :param user_id: 当前登录用户ID
        :return: 更新后的DBTask对象
        :raise HTTPException: 404（任务不存在/跨用户访问）
        """
        # 1. 校验任务归属
        task = TaskCRUD._get_task_by_id_and_user_id(db, task_id, user_id)
        if not task:
            raise HTTPException(
                status_code=404,
                detail="任务不存在或您无权修改该任务"
            )

        # 2. 提取更新数据：仅保留传入的非空字段（支持部分更新）
        update_data = task_update.dict(exclude_unset=True)

        # 3. 遍历更新字段（严格匹配models.py的字段）
        for key, value in update_data.items():
            if key in ["status", "priority"] and value:
                # 状态/优先级：转换为中文Enum值
                setattr(task, key, value.value)
            elif key == "title" and value:
                # 标题：已通过schemas校验长度（1-100字符）
                setattr(task, key, value)
            elif key in ["description", "deadline"]:
                # 描述/截止时间：可选字段，直接赋值
                setattr(task, key, value)

        # 4. 数据库操作：提交+刷新（updated_at由models自动更新为UTC时间）
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def delete_task(
        db: Session,
        task_id: int,
        user_id: int
    ) -> None:
        """
        删除个人任务（接口对接：DELETE /tasks/{task_id}）
        :param db: 数据库会话对象
        :param task_id: 任务ID
        :param user_id: 当前登录用户ID
        :return: None
        :raise HTTPException: 404（任务不存在/跨用户访问）
        """
        # 1. 校验任务归属
        task = TaskCRUD._get_task_by_id_and_user_id(db, task_id, user_id)
        if not task:
            raise HTTPException(
                status_code=404,
                detail="任务不存在或您无权删除该任务"
            )

        # 2. 数据库操作：删除→提交
        db.delete(task)
        db.commit()


# 全局单例：避免重复创建对象，提升性能
# 协同注意：所有路由层调用均使用该实例
task_crud = TaskCRUD()