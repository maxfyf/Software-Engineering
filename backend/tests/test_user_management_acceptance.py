import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import api
import crud
import models
import schemas


class UserManagementAcceptanceTests(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".sqlite")
        os.close(fd)
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        self.SessionLocal = sessionmaker(bind=self.engine)
        models.Base.metadata.create_all(self.engine)
        self.db = self.SessionLocal()
        self.hash_patcher = patch("crud.security.get_password_hash", side_effect=lambda password: f"hashed:{password}")
        self.verify_patcher = patch(
            "crud.security.verify_password",
            side_effect=lambda password, hashed: hashed == f"hashed:{password}",
        )
        self.token_patcher = patch("api.create_access_token", side_effect=lambda data: f"token:{data['sub']}")
        self.hash_patcher.start()
        self.verify_patcher.start()
        self.token_patcher.start()

    def tearDown(self):
        self.token_patcher.stop()
        self.verify_patcher.stop()
        self.hash_patcher.stop()
        self.db.close()
        self.engine.dispose()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def current_user(self, username: str):
        return SimpleNamespace(username=username)

    def add_user(self, username: str, password: str = "secret123", email: str | None = None) -> models.User:
        user = models.User(
            username=username,
            password_hash=f"hashed:{password}",
            email=email,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def add_team(self, name: str, owner_username: str) -> models.Team:
        return crud.create_team(self.db, schemas.TeamCreate(name=name), owner_username)

    def add_task(
        self,
        title: str,
        owner_username: str,
        *,
        team_id: int | None = None,
        assignee_username: str | None = None,
        status: str = models.TaskStatus.TODO.value,
    ) -> models.Task:
        task = models.Task(
            title=title,
            owner_username=owner_username,
            team_id=team_id,
            assignee_username=assignee_username,
            status=status,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def assert_http_error(self, status_code: int, func, *args, **kwargs):
        with self.assertRaises(HTTPException) as ctx:
            func(*args, **kwargs)
        self.assertEqual(ctx.exception.status_code, status_code)
        return ctx.exception

    def test_tc_um_01_register_success(self):
        """TC-UM-01: 验证用户注册成功。"""
        response = api.register(
            schemas.UserCreate(
                username="alice",
                password="secret123",
                email="alice@example.com",
            ),
            db=self.db,
        )

        user = crud.get_user_by_username(self.db, "alice")
        self.assertTrue(response["success"])
        self.assertEqual(response["data"]["username"], "alice")
        self.assertIsNotNone(user)
        self.assertNotEqual(user.password_hash, "secret123")
        self.assertTrue(user.password_hash)

    def test_tc_um_02_duplicate_username_register_rejected(self):
        """TC-UM-02: 验证重复用户名注册被拒绝。"""
        self.add_user("alice", email="alice@example.com")

        error = self.assert_http_error(
            400,
            api.register,
            schemas.UserCreate(
                username="alice",
                password="secret456",
                email="alice2@example.com",
            ),
            db=self.db,
        )

        self.assertEqual(error.detail, "用户名已存在")
        self.assertEqual(self.db.query(models.User).filter(models.User.username == "alice").count(), 1)

    def test_tc_um_03_login_success(self):
        """TC-UM-03: 验证用户登录成功。"""
        self.add_user("alice", password="secret123", email="alice@example.com")

        response = api.login(api.LoginRequest(username="alice", password="secret123"), db=self.db)

        self.assertTrue(response["success"])
        self.assertIn("token", response["data"])
        self.assertEqual(response["data"]["userInfo"]["username"], "alice")
        self.assertNotIn("password", response["data"]["userInfo"])
        self.assertNotIn("password_hash", response["data"]["userInfo"])

    def test_tc_um_04_wrong_password_login_rejected(self):
        """TC-UM-04: 验证错误密码登录失败。"""
        self.add_user("alice", password="secret123")

        error = self.assert_http_error(
            401,
            api.login,
            api.LoginRequest(username="alice", password="wrongpass"),
            db=self.db,
        )

        self.assertEqual(error.detail, "密码错误")

    def test_tc_um_05_owner_creates_team_and_becomes_owner_member(self):
        """TC-UM-05: 验证 Owner 创建团队并自动成为 Owner 成员。"""
        self.add_user("owner")

        response = api.create_team_endpoint(
            {"title": "Alpha"},
            current_user=self.current_user("owner"),
            db=self.db,
        )

        team = crud.get_team_by_id(self.db, response["data"]["id"])
        membership = crud.get_team_membership(self.db, team.id, "owner")
        self.assertTrue(response["success"])
        self.assertEqual(team.owner_username, "owner")
        self.assertIsNotNone(membership)
        self.assertEqual(membership.role, crud.ROLE_OWNER)

    def test_tc_um_06_non_owner_cannot_add_team_member(self):
        """TC-UM-06: 验证非 Owner 不能添加团队成员。"""
        for username in ["owner", "admin", "member"]:
            self.add_user(username)
        team = self.add_team("Alpha", "owner")
        crud.update_team_member_role(self.db, team.id, "owner", crud.ROLE_ADMIN, "owner")
        self.db.query(models.TeamMember).filter(
            models.TeamMember.team_id == team.id,
            models.TeamMember.username == "owner",
        ).update({"role": crud.ROLE_OWNER})
        self.db.add(models.TeamMember(team_id=team.id, username="admin", role=crud.ROLE_ADMIN))
        self.db.commit()

        membership, error = crud.add_team_member(self.db, team.id, "member", "admin")

        self.assertIsNone(membership)
        self.assertEqual(error, "团队权限不足")
        self.assertIsNone(crud.get_team_membership(self.db, team.id, "member"))

    def test_tc_um_07_owner_adds_team_member_success(self):
        """TC-UM-07: 验证 Owner 添加团队成员成功。"""
        self.add_user("owner")
        self.add_user("member")
        team = self.add_team("Alpha", "owner")

        membership, error = crud.add_team_member(self.db, team.id, "member", "owner")

        self.assertIsNone(error)
        self.assertIsNotNone(membership)
        self.assertEqual(membership.username, "member")
        self.assertEqual(membership.role, crud.ROLE_MEMBER)

    def test_tc_um_08_non_team_member_cannot_access_team_space(self):
        """TC-UM-08: 验证非团队成员不能访问团队任务或团队空间。"""
        self.add_user("owner")
        self.add_user("outsider")
        team = self.add_team("Alpha", "owner")
        self.add_task("team task", "owner", team_id=team.id)

        error = self.assert_http_error(
            403,
            api.get_team_tasks,
            team.id,
            current_user=self.current_user("outsider"),
            db=self.db,
        )

        self.assertEqual(error.detail, "无权访问该团队")

    def test_tc_um_09_member_leave_reassigns_task_and_logs(self):
        """TC-UM-09: 验证成员主动离开团队后的任务处理。"""
        self.add_user("owner")
        self.add_user("member")
        team = self.add_team("Alpha", "owner")
        crud.add_team_member(self.db, team.id, "member", "owner")
        task = self.add_task("member task", "owner", team_id=team.id, assignee_username="member")

        success, error = crud.leave_team(self.db, team.id, "member")

        self.assertTrue(success)
        self.assertIsNone(error)
        self.assertIsNone(crud.get_team_membership(self.db, team.id, "member"))
        self.db.refresh(task)
        self.assertEqual(task.assignee_username, "owner")
        logs = crud.get_task_operation_logs(self.db, task.id, "owner")
        self.assertEqual(len(logs), 1)
        self.assertIn("成员 member 主动离开团队", logs[0]["description"])

    def test_tc_um_10_owner_remove_member_reassigns_task_and_logs(self):
        """TC-UM-10: 验证 Owner 移除成员后的任务处理。"""
        self.add_user("owner")
        self.add_user("member")
        team = self.add_team("Alpha", "owner")
        crud.add_team_member(self.db, team.id, "member", "owner")
        task = self.add_task("member task", "owner", team_id=team.id, assignee_username="member")

        success, error = crud.remove_team_member(self.db, team.id, "member", "owner")

        self.assertTrue(success)
        self.assertIsNone(error)
        self.assertIsNone(crud.get_team_membership(self.db, team.id, "member"))
        self.db.refresh(task)
        self.assertEqual(task.assignee_username, "owner")
        logs = crud.get_task_operation_logs(self.db, task.id, "owner")
        self.assertEqual(len(logs), 1)
        self.assertIn("成员 member 被移出团队", logs[0]["description"])

    def test_tc_um_11_single_owner_cannot_leave_team(self):
        """TC-UM-11: 验证仅剩 Owner 时不能主动离开团队。"""
        self.add_user("owner")
        team = self.add_team("Alpha", "owner")

        success, error = crud.remove_team_member(self.db, team.id, "owner", "owner")

        self.assertFalse(success)
        self.assertEqual(error, "仅含 Owner 的团队不允许退出")
        self.assertEqual(crud.get_team_by_id(self.db, team.id).owner_username, "owner")
        self.assertIsNotNone(crud.get_team_membership(self.db, team.id, "owner"))
        self.assertEqual(self.db.query(models.OperationLog).count(), 0)

    def test_tc_um_12_owner_leave_transfers_owner_to_admin(self):
        """TC-UM-12: 验证 Owner 离开时团队所有权自动转移。"""
        for username in ["owner", "admin", "member"]:
            self.add_user(username)
        team = self.add_team("Alpha", "owner")
        crud.add_team_member(self.db, team.id, "admin", "owner")
        crud.update_team_member_role(self.db, team.id, "admin", crud.ROLE_ADMIN, "owner")
        crud.add_team_member(self.db, team.id, "member", "owner")
        task = self.add_task("owner task", "owner", team_id=team.id, assignee_username="owner")

        success, error = crud.remove_team_member(self.db, team.id, "owner", "owner")

        self.assertTrue(success)
        self.assertIsNone(error)
        self.db.refresh(team)
        self.db.refresh(task)
        self.assertEqual(team.owner_username, "admin")
        self.assertIsNone(crud.get_team_membership(self.db, team.id, "owner"))
        self.assertEqual(crud.get_team_membership(self.db, team.id, "admin").role, crud.ROLE_OWNER)
        self.assertEqual(task.assignee_username, "admin")
        logs = crud.get_task_operation_logs(self.db, task.id, "admin")
        self.assertIn("负责人由 owner 变更为 admin", logs[0]["description"])

    def test_tc_um_13_delete_team_removes_access_and_keeps_logs(self):
        """TC-UM-13: 验证团队解散后的访问控制与日志保留。"""
        self.add_user("owner")
        self.add_user("member")
        team = self.add_team("Alpha", "owner")
        crud.add_team_member(self.db, team.id, "member", "owner")
        task = self.add_task("team task", "owner", team_id=team.id, assignee_username="member")
        task_id = task.id
        team_id = team.id

        deleted = crud.delete_team(self.db, team.id, operator_username="owner")

        self.assertTrue(deleted)
        self.assertIsNone(crud.get_team_by_id(self.db, team_id))
        self.assertIsNone(crud.require_team_member(self.db, team_id, "member"))
        self.assertIsNone(self.db.query(models.Task).filter(models.Task.id == task_id).first())
        log = self.db.query(models.OperationLog).filter(
            models.OperationLog.object_type == "task",
            models.OperationLog.object_id == task_id,
        ).one()
        self.assertEqual(log.object_title, "team task")
        self.assertEqual(log.scope_title, "Alpha")
        self.assertEqual(log.object_deleted, 1)

    def test_tc_um_14_cancel_account_cleans_data_and_keeps_logs(self):
        """TC-UM-14: 验证用户注销后的数据清理。"""
        for username in ["alice", "bob", "carol"]:
            self.add_user(username)
        owned_team = self.add_team("Owned", "alice")
        owned_team_id = owned_team.id
        self.add_task("owned team task", "alice", team_id=owned_team.id, assignee_username="alice")
        shared_team = self.add_team("Shared", "bob")
        crud.add_team_member(self.db, shared_team.id, "alice", "bob")
        crud.update_team_member_role(self.db, shared_team.id, "alice", crud.ROLE_ADMIN, "bob")
        crud.add_team_member(self.db, shared_team.id, "carol", "bob")
        assigned = self.add_task("assigned", "bob", team_id=shared_team.id, assignee_username="alice")
        owned = self.add_task("owned", "alice", team_id=shared_team.id, assignee_username="carol")
        personal = self.add_task("personal", "alice")
        personal_id = personal.id

        cancelled = crud.cancel_account(self.db, "alice")

        self.assertTrue(cancelled)
        self.assertIsNone(crud.get_user_by_username(self.db, "alice"))
        self.assertIsNone(crud.get_team_by_id(self.db, owned_team_id))
        self.db.refresh(assigned)
        self.db.refresh(owned)
        self.assertEqual(assigned.assignee_username, "bob")
        self.assertEqual(owned.owner_username, "bob")
        personal_log = self.db.query(models.OperationLog).filter(
            models.OperationLog.object_type == "task",
            models.OperationLog.object_id == personal_id,
        ).one()
        self.assertEqual(personal_log.action_type, "delete")
        self.assertEqual(personal_log.object_deleted, 1)

    def test_tc_um_15_cancel_account_logs_do_not_leak_sensitive_data(self):
        """TC-UM-15: 验证注销账号不会泄露敏感信息到日志。"""
        self.add_user("alice", password="secret123")
        task = self.add_task("personal", "alice")
        task_id = task.id

        cancelled = crud.cancel_account(self.db, "alice")

        self.assertTrue(cancelled)
        log = self.db.query(models.OperationLog).filter(
            models.OperationLog.object_type == "task",
            models.OperationLog.object_id == task_id,
        ).one()
        serialized = crud.serialize_operation_log(log)
        serialized_text = str(serialized)
        self.assertIn("operator", serialized)
        self.assertIn("type", serialized)
        self.assertIn("object", serialized)
        self.assertIn("operatedAt", serialized)
        self.assertIn("description", serialized)
        self.assertIn("scope", serialized)
        self.assertNotIn("secret123", serialized_text)
        self.assertNotIn("password", serialized_text)
        self.assertNotIn("password_hash", serialized_text)
        self.assertNotIn("token", serialized_text.lower())

    def test_tc_um_16_failed_member_change_does_not_record_success_log(self):
        """TC-UM-16: 验证成员变更失败不生成成功日志。"""
        for username in ["owner", "member", "other"]:
            self.add_user(username)
        team = self.add_team("Alpha", "owner")
        crud.add_team_member(self.db, team.id, "member", "owner")
        crud.add_team_member(self.db, team.id, "other", "owner")
        task = self.add_task("other task", "owner", team_id=team.id, assignee_username="other")

        success, error = crud.remove_team_member(self.db, team.id, "other", "member")

        self.assertFalse(success)
        self.assertEqual(error, "团队权限不足")
        self.db.refresh(task)
        self.assertEqual(task.assignee_username, "other")
        self.assertIsNotNone(crud.get_team_membership(self.db, team.id, "other"))
        self.assertEqual(self.db.query(models.OperationLog).count(), 0)

    def test_tc_um_17_task_logs_return_newest_first(self):
        """TC-UM-17: 验证任务日志按时间倒序返回。"""
        self.add_user("alice")
        task = self.add_task("personal", "alice")
        crud.log_operation(self.db, "alice", "edit", task.id, "task", task.title, "personal", None, "alice", "第一条日志")
        crud.log_operation(self.db, "alice", "edit", task.id, "task", task.title, "personal", None, "alice", "第二条日志")
        self.db.commit()

        logs = crud.get_task_operation_logs(self.db, task.id, "alice")

        self.assertEqual([log["description"] for log in logs], ["第二条日志", "第一条日志"])

    def test_tc_um_18_unauthorized_user_cannot_read_team_task_logs(self):
        """TC-UM-18: 验证无权限用户不能查看团队任务日志。"""
        for username in ["owner", "member", "outsider"]:
            self.add_user(username)
        team = self.add_team("Alpha", "owner")
        crud.add_team_member(self.db, team.id, "member", "owner")
        task = self.add_task("team task", "owner", team_id=team.id)
        crud.log_operation(self.db, "owner", "edit", task.id, "task", task.title, "team", team.id, team.name, "团队任务日志")
        self.db.commit()

        self.assertEqual(len(crud.get_task_operation_logs(self.db, task.id, "member")), 1)
        error = self.assert_http_error(403, crud.get_task_operation_logs, self.db, task.id, "outsider")
        self.assertEqual(error.detail, "无权访问该团队任务日志")


if __name__ == "__main__":
    unittest.main()
