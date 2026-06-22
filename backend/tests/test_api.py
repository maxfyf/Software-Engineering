"""直接调用 FastAPI 处理函数，验证当前 API 层规则。"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

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


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".sqlite")
        os.close(fd)
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        self.SessionLocal = sessionmaker(bind=self.engine)
        models.Base.metadata.create_all(self.engine)
        self.db = self.SessionLocal()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def current_user(self, username: str):
        return SimpleNamespace(username=username)

    def add_user(self, username: str) -> models.User:
        user = models.User(username=username, password_hash="hashed")
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def add_team(self, name: str, owner_username: str) -> models.Team:
        return crud.create_team(
            self.db,
            schemas.TeamCreate(name=name),
            owner_username,
        )

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
            id=crud.allocate_task_id(self.db),
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

    def assert_http_error(self, status_code: int, detail: str, func, *args, **kwargs):
        with self.assertRaises(HTTPException) as ctx:
            func(*args, **kwargs)
        self.assertEqual(ctx.exception.status_code, status_code)
        self.assertEqual(ctx.exception.detail, detail)


class CreateTeamEndpointTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.add_user("owner")
        self.owner = self.current_user("owner")

    def test_create_team_rejects_empty_name(self):
        self.assert_http_error(
            400,
            "团队名称不能为空",
            api.create_team_endpoint,
            {"title": "   "},
            current_user=self.owner,
            db=self.db,
        )

    def test_create_team_rejects_name_longer_than_ten_characters(self):
        self.assert_http_error(
            400,
            "团队名称长度不能超过10个字符",
            api.create_team_endpoint,
            {"title": "12345678901"},
            current_user=self.owner,
            db=self.db,
        )

    def test_create_team_rejects_duplicate_active_name(self):
        self.add_team("Alpha", "owner")

        self.assert_http_error(
            400,
            "团队名称已存在，请使用其他名称",
            api.create_team_endpoint,
            {"title": "Alpha"},
            current_user=self.owner,
            db=self.db,
        )

    def test_create_team_allows_name_of_disbanded_team(self):
        old_team = self.add_team("Alpha", "owner")
        crud.delete_team(self.db, old_team.id, operator_username="owner")

        response = api.create_team_endpoint(
            {"title": "Alpha"},
            current_user=self.owner,
            db=self.db,
        )

        self.assertTrue(response["success"])
        self.assertNotEqual(response["data"]["id"], old_team.id)


class PermissionEndpointTests(ApiTestCase):
    def test_non_owner_cannot_send_team_invitation(self):
        for username in ["owner", "member", "candidate"]:
            self.add_user(username)
        team = self.add_team("Alpha", "owner")
        membership, error = crud.add_team_member(
            self.db,
            team.id,
            "member",
            "owner",
        )
        self.assertIsNone(error)
        self.assertIsNotNone(membership)

        self.assert_http_error(
            403,
            "只有 Owner 可发送邀请",
            api.add_member_endpoint,
            team.id,
            {"username": "candidate"},
            current_user=self.current_user("member"),
            db=self.db,
        )

    def test_outsider_cannot_read_team_tasks(self):
        self.add_user("owner")
        self.add_user("outsider")
        team = self.add_team("Alpha", "owner")
        self.add_task("team task", "owner", team_id=team.id)

        self.assert_http_error(
            403,
            "无权访问该团队",
            api.get_team_tasks,
            team.id,
            current_user=self.current_user("outsider"),
            db=self.db,
        )


class UpdateTaskStatusEndpointTests(ApiTestCase):
    def test_update_task_status_rejects_non_positive_task_id(self):
        self.assert_http_error(
            400,
            "无效的任务ID",
            api.update_task_status,
            0,
            "进行中",
            current_user=self.current_user("member"),
            db=self.db,
        )

    def test_update_task_status_rejects_blank_status(self):
        self.assert_http_error(
            400,
            "任务状态不能为空",
            api.update_task_status,
            1,
            " ",
            current_user=self.current_user("member"),
            db=self.db,
        )

    def test_update_task_status_rejects_other_users_assignment(self):
        self.add_user("owner")
        self.add_user("member")
        task = self.add_task(
            "assigned task",
            "owner",
            assignee_username="owner",
        )

        self.assert_http_error(
            403,
            "只能修改分配给自己的任务状态",
            api.update_task_status,
            task.id,
            "进行中",
            current_user=self.current_user("member"),
            db=self.db,
        )


class StatusTransitionTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.add_user("alice")

    def test_done_task_requires_all_transitive_predecessors_done(self):
        first = self.add_task("first", "alice")
        middle = self.add_task(
            "middle",
            "alice",
            status=models.TaskStatus.DONE.value,
        )
        last = self.add_task("last", "alice")
        crud.create_task_dependency(self.db, first.id, middle.id)
        crud.create_task_dependency(self.db, middle.id, last.id)

        self.assert_http_error(
            400,
            "前置任务「first」未完成，无法完成当前任务",
            api.validate_status_transition,
            self.db,
            last,
            models.TaskStatus.DONE.value,
        )

    def test_completed_task_cannot_reopen_when_successor_is_done(self):
        predecessor = self.add_task(
            "predecessor",
            "alice",
            status=models.TaskStatus.DONE.value,
        )
        successor = self.add_task(
            "successor",
            "alice",
            status=models.TaskStatus.DONE.value,
        )
        crud.create_task_dependency(self.db, predecessor.id, successor.id)

        self.assert_http_error(
            400,
            "后继任务「successor」已完成，无法将当前任务改为未完成状态",
            api.validate_status_transition,
            self.db,
            predecessor,
            models.TaskStatus.IN_PROGRESS.value,
        )


class DependencyScopeEndpointTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.add_user("owner")
        self.owner = self.current_user("owner")

    def test_personal_task_cannot_depend_on_team_task(self):
        team = self.add_team("Alpha", "owner")
        personal_task = self.add_task("personal", "owner")
        team_task = self.add_task("team", "owner", team_id=team.id)

        self.assert_http_error(
            400,
            "个人任务不能依赖团队任务",
            api.update_predecessors,
            personal_task.id,
            schemas.UpdatePredecessorsRequest(predecessor_ids=[team_task.id]),
            current_user=self.owner,
            db=self.db,
        )

    def test_team_task_cannot_depend_on_task_from_other_team(self):
        alpha = self.add_team("Alpha", "owner")
        beta = self.add_team("Beta", "owner")
        alpha_task = self.add_task("alpha task", "owner", team_id=alpha.id)
        beta_task = self.add_task("beta task", "owner", team_id=beta.id)

        self.assert_http_error(
            400,
            "前置任务与当前任务不在同一团队",
            api.update_predecessors,
            alpha_task.id,
            schemas.UpdatePredecessorsRequest(predecessor_ids=[beta_task.id]),
            current_user=self.owner,
            db=self.db,
        )

    def test_update_predecessors_rejects_cycle(self):
        first = self.add_task("first", "owner")
        second = self.add_task("second", "owner")
        crud.create_task_dependency(self.db, first.id, second.id)

        self.assert_http_error(
            400,
            "不允许添加循环依赖",
            api.update_predecessors,
            first.id,
            schemas.UpdatePredecessorsRequest(predecessor_ids=[second.id]),
            current_user=self.owner,
            db=self.db,
        )


if __name__ == "__main__":
    unittest.main()
