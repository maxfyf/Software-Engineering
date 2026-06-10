from sqlalchemy.orm import Session
from models import OperationLog

def log_task_operation(
    db: Session,
    operator: str,
    operation_type: str,
    task,
    description: str,
    scope_type: str,
    team_id=None,
    team_title=None,
    deleted=False
):
    """
    记录任务相关操作日志
    """
    # 构建 object 字段
    obj = {
        "id": task.id,
        "title": task.title,
        "type": "task",
        "deleted": deleted
    }
    # 构建 scope 字段
    if scope_type == "personal":
        scope = {
            "type": "personal",
            "id": None,
            "title": "个人任务"
        }
        personal_user = operator
        team_id_for_idx = None
    else:
        scope = {
            "type": "team",
            "id": team_id,
            "title": team_title or f"团队{team_id}"
        }
        personal_user = None
        team_id_for_idx = team_id

    log_entry = OperationLog(
        operator=operator,
        type=operation_type,
        object=obj,
        description=description,
        scope=scope,
        task_id=task.id,
        team_id=team_id_for_idx,
        personal_user=personal_user
    )
    try:
        db.add(log_entry)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[OperationLog] Failed to log: {operation_type} for task {task.id}, error: {e}")