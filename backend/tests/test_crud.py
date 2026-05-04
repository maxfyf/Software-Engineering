import os
import sys
import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import crud
import models
import schemas


class CrudTestCase(unittest.TestCase):
    def setUp(self):
        # 为每个测试用例创建独立的临时 SQLite 数据库，避免测试之间互相污染。
        fd, self.db_path = tempfile.mkstemp(suffix=".sqlite")
        os.close(fd)
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        self.SessionLocal = sessionmaker(bind=self.engine)
        models.Base.metadata.create_all(self.engine)
        self.db = self.SessionLocal()

    def tearDown(self):
        # 用例结束后释放连接并删除临时数据库文件。
        self.db.close()
        self.engine.dispose()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def add_user(self, username: str) -> models.User:
        # 测试辅助方法：快速插入一个用户。
        user = models.User(username=username, password_hash="hashed")
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def add_team(self, name: str, owner_username: str) -> models.Team:
        # 测试辅助方法：创建团队时同步补上 Owner 成员关系，使数据更贴近真实业务。
        team = models.Team(name=name, owner_username=owner_username)
        self.db.add(team)
        self.db.flush()
        membership = models.TeamMember(
            team_id=team.id,
            username=owner_username,
            role=crud.ROLE_OWNER,
        )
        self.db.add(membership)
        self.db.commit()
        self.db.refresh(team)
        return team

    def add_team_member(self, team_id: int, username: str, role: str) -> models.TeamMember:
        # 测试辅助方法：向团队中插入指定角色的成员。
        membership = models.TeamMember(team_id=team_id, username=username, role=role)
        self.db.add(membership)
        self.db.commit()
        self.db.refresh(membership)
        return membership

    def add_task(
        self,
        title: str,
        owner_username: str,
        *,
        team_id: int | None = None,
        assignee_username: str | None = None,
    ) -> models.Task:
        # 测试辅助方法：同时支持创建个人任务和团队任务。
        task = models.Task(
            title=title,
            owner_username=owner_username,
            team_id=team_id,
            assignee_username=assignee_username,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task


class DeleteTeamTests(CrudTestCase):
    def test_delete_team_removes_team_and_team_tasks_only(self):
        # 同时构造团队任务和个人任务，验证解散团队时只清理团队相关数据。
        self.add_user("owner")
        self.add_user("member")
        team = self.add_team("Alpha", "owner")
        self.add_team_member(team.id, "member", crud.ROLE_MEMBER)
        self.add_task("team task", "owner", team_id=team.id, assignee_username="member")
        personal_task = self.add_task("personal task", "owner")

        deleted = crud.delete_team(self.db, team.id)

        self.assertTrue(deleted)
        self.assertIsNone(crud.get_team_by_id(self.db, team.id))
        self.assertEqual(
            self.db.query(models.Task).filter(models.Task.team_id == team.id).count(),
            0,
        )
        self.assertEqual(
            self.db.query(models.TeamMember).filter(models.TeamMember.team_id == team.id).count(),
            0,
        )
        self.assertIsNotNone(
            self.db.query(models.Task).filter(models.Task.id == personal_task.id).first()
        )

    def test_delete_team_returns_false_for_missing_team(self):
        # 不存在的团队应直接返回 False，而不是抛出异常。
        self.assertFalse(crud.delete_team(self.db, 9999))


class CancelAccountTests(CrudTestCase):
    def test_cancel_account_cleans_up_owned_teams_memberships_and_task_assignments(self):
        for username in ["alice", "bob", "carol"]:
            self.add_user(username)

        # alice 拥有的团队在注销后应该被解散，团队任务也应被删除。
        owned_team = self.add_team("Owned Team", "alice")
        self.add_task("owned team task", "alice", team_id=owned_team.id, assignee_username="alice")

        # alice 参与 bob 的团队。注销后，保留团队中的任务需要把 owner/assignee 迁移干净。
        shared_team = self.add_team("Shared Team", "bob")
        self.add_team_member(shared_team.id, "alice", crud.ROLE_ADMIN)
        self.add_team_member(shared_team.id, "carol", crud.ROLE_MEMBER)
        reassigned_task = self.add_task(
            "shared task assigned to alice",
            "bob",
            team_id=shared_team.id,
            assignee_username="alice",
        )
        transferred_owner_task = self.add_task(
            "shared task owned by alice",
            "alice",
            team_id=shared_team.id,
            assignee_username="carol",
        )
        self.add_task("alice personal", "alice")
        personal_task_with_alice_assignee = self.add_task(
            "bob personal assigned to alice",
            "bob",
            assignee_username="alice",
        )

        # 执行注销后，数据库中不应再保留任何指向 alice 的团队/任务/成员关系。
        cancelled = crud.cancel_account(self.db, "alice")

        self.assertTrue(cancelled)
        self.assertIsNone(crud.get_user_by_username(self.db, "alice"))
        self.assertIsNone(crud.get_team_by_id(self.db, owned_team.id))
        self.assertEqual(
            self.db.query(models.Task).filter(models.Task.team_id == owned_team.id).count(),
            0,
        )
        self.assertEqual(
            self.db.query(models.TeamMember).filter(models.TeamMember.username == "alice").count(),
            0,
        )
        self.assertEqual(
            self.db.query(models.Task).filter(models.Task.owner_username == "alice").count(),
            0,
        )
        self.assertEqual(
            self.db.query(models.Task).filter(models.Task.assignee_username == "alice").count(),
            0,
        )

        self.db.refresh(reassigned_task)
        self.assertEqual(reassigned_task.assignee_username, "bob")

        self.db.refresh(transferred_owner_task)
        self.assertEqual(transferred_owner_task.owner_username, "bob")

        self.db.refresh(personal_task_with_alice_assignee)
        self.assertIsNone(personal_task_with_alice_assignee.assignee_username)

    def test_cancel_account_returns_false_for_missing_user(self):
        # 不存在的用户无需清理，返回 False 即可。
        self.assertFalse(crud.cancel_account(self.db, "ghost"))


class TeamMemberCrudTests(CrudTestCase):
    def test_add_team_member_adds_member_role_by_default(self):
        # Owner 添加新成员时，默认角色应为 Member。
        self.add_user("owner")
        self.add_user("member")
        team = crud.create_team(self.db, schemas.TeamCreate(name="Core Team"), "owner")

        membership, error = crud.add_team_member(self.db, team.id, "member", "owner")

        self.assertIsNone(error)
        self.assertIsNotNone(membership)
        self.assertEqual(membership.role, crud.ROLE_MEMBER)
        self.assertEqual(membership.username, "member")

    def test_add_team_member_rejects_non_owner_operator(self):
        # 即便是 Admin，也不能越权执行仅 Owner 可做的加人操作。
        self.add_user("owner")
        self.add_user("admin")
        self.add_user("member")
        team = crud.create_team(self.db, schemas.TeamCreate(name="Core Team"), "owner")
        self.add_team_member(team.id, "admin", crud.ROLE_ADMIN)

        membership, error = crud.add_team_member(self.db, team.id, "member", "admin")

        self.assertIsNone(membership)
        self.assertEqual(error, "团队权限不足")


if __name__ == "__main__":
    unittest.main()
