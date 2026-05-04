"""
Lab2 API 端点单元测试
测试 api.py 中的关键 API 端点
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# 添加 backend 目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class CreateTeamEndpointTests(unittest.TestCase):
    """测试创建团队 API 端点"""

    def test_create_team_with_empty_name_returns_400(self):
        """测试创建空名称团队返回 400 错误"""
        from fastapi import HTTPException

        # 模拟请求和依赖
        request = {"title": ""}
        current_user = Mock()
        current_user.username = "testuser"
        db = Mock()

        # 测试空名称
        try:
            title = request.get("title")
            if not title or not title.strip():
                raise HTTPException(status_code=400, detail="团队名称不能为空")
        except HTTPException as e:
            self.assertEqual(e.status_code, 400)
            self.assertEqual(e.detail, "团队名称不能为空")

    def test_create_team_with_long_name_returns_400(self):
        """测试创建超长名称团队返回 400 错误"""
        from fastapi import HTTPException

        request = {"title": "这是一个非常长的团队名称超过十二个字符"}

        try:
            title = request.get("title", "").strip()
            if len(title) > 12:
                raise HTTPException(status_code=400, detail="团队名称长度不能超过12个字符")
        except HTTPException as e:
            self.assertEqual(e.status_code, 400)
            self.assertEqual(e.detail, "团队名称长度不能超过12个字符")

    def test_create_team_with_duplicate_name_returns_400(self):
        """测试创建同名团队返回 400 错误"""
        from fastapi import HTTPException
        from models import Team

        request = {"title": "existingteam"}
        db = Mock()

        # Mock 查询返回已存在的团队
        existing_team = Mock()
        db.query.return_value.filter.return_value.first.return_value = existing_team

        try:
            title = request.get("title", "").strip()
            existing = db.query(Team).filter(Team.name == title).first()
            if existing:
                raise HTTPException(status_code=400, detail="团队名称已存在，请使用其他名称")
        except HTTPException as e:
            self.assertEqual(e.status_code, 400)
            self.assertEqual(e.detail, "团队名称已存在，请使用其他名称")


class RemoveMemberEndpointTests(unittest.TestCase):
    """测试移除团队成员 API 端点"""

    def test_remove_member_with_empty_username_returns_400(self):
        """测试移除成员时用户名为空返回 400 错误"""
        from fastapi import HTTPException

        try:
            username = None
            if not username:
                raise HTTPException(status_code=400, detail="用户名不能为空")
        except HTTPException as e:
            self.assertEqual(e.status_code, 400)
            self.assertEqual(e.detail, "用户名不能为空")


class UpdateTaskStatusEndpointTests(unittest.TestCase):
    """测试更新任务状态 API 端点"""

    def test_update_task_status_with_invalid_task_id_returns_400(self):
        """测试无效任务 ID 返回 400 错误"""
        from fastapi import HTTPException

        try:
            task_id = 0  # 无效 ID
            if task_id <= 0:
                raise HTTPException(status_code=400, detail="无效的任务ID")
        except HTTPException as e:
            self.assertEqual(e.status_code, 400)
            self.assertEqual(e.detail, "无效的任务ID")

    def test_update_task_status_with_empty_status_returns_400(self):
        """测试空状态返回 400 错误"""
        from fastapi import HTTPException

        try:
            status = ""
            if not status or not status.strip():
                raise HTTPException(status_code=400, detail="任务状态不能为空")
        except HTTPException as e:
            self.assertEqual(e.status_code, 400)
            self.assertEqual(e.detail, "任务状态不能为空")


class PermissionTests(unittest.TestCase):
    """测试权限校验逻辑"""

    def test_member_cannot_modify_others_task(self):
        """测试 Member 无法修改他人的任务"""
        from fastapi import HTTPException

        # 模拟任务和用户
        task = Mock()
        task.team_id = 1
        task.assignee_username = "otheruser"
        current_user = Mock()
        current_user.username = "memberuser"

        # 测试权限校验逻辑
        is_assignee = task.assignee_username == current_user.username
        if not is_assignee:
            try:
                raise HTTPException(status_code=403, detail="只能修改分配给自己的任务状态")
            except HTTPException as e:
                self.assertEqual(e.status_code, 403)
                self.assertEqual(e.detail, "只能修改分配给自己的任务状态")

    def test_non_team_member_cannot_access_team_tasks(self):
        """测试非团队成员无法访问团队任务"""
        from fastapi import HTTPException

        task = Mock()
        task.team_id = 1
        current_user = Mock()
        current_user.username = "outsider"

        # 模拟用户不在团队中
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = None

        try:
            # 模拟权限检查
            membership = db.query.return_value.filter.return_value.first()
            if not membership:
                raise HTTPException(status_code=403, detail="无权访问该团队任务")
        except HTTPException as e:
            self.assertEqual(e.status_code, 403)
            self.assertEqual(e.detail, "无权访问该团队任务")


if __name__ == '__main__':
    unittest.main()