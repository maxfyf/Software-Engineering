import os
import sys
import tempfile
import unittest
import warnings
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.exc import SAWarning
from sqlalchemy.orm import sessionmaker


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import crud
import models
import schemas
import api


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

    def test_delete_team_removes_former_member_access_to_team_space(self):
        # 团队解散后，原成员不应再通过团队空间看到团队或团队任务。
        self.add_user("owner")
        self.add_user("member")
        team = self.add_team("Alpha", "owner")
        self.add_team_member(team.id, "member", crud.ROLE_MEMBER)
        self.add_task("team task", "owner", team_id=team.id, assignee_username="member")

        deleted = crud.delete_team(self.db, team.id)

        self.assertTrue(deleted)
        self.assertEqual(crud.get_user_teams(self.db, "member"), [])
        self.assertIsNone(crud.require_team_member(self.db, team.id, "member"))
        self.assertEqual(crud.get_team_tasks(self.db, team.id), [])

    def test_delete_team_removes_team_task_dependencies(self):
        # 团队解散时，该团队任务之间的依赖关系也应一并清理。
        self.add_user("owner")
        team = self.add_team("Alpha", "owner")
        predecessor = self.add_task("predecessor", "owner", team_id=team.id)
        successor = self.add_task("successor", "owner", team_id=team.id)
        success, error = crud.create_task_dependency(self.db, predecessor.id, successor.id)
        self.assertTrue(success)
        self.assertIsNone(error)

        deleted = crud.delete_team(self.db, team.id)

        self.assertTrue(deleted)
        self.assertEqual(self.db.query(models.TaskDependency).count(), 0)


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

    def test_cancel_account_succeeds_after_relationships_are_preloaded(self):
        # 预加载 ORM 关系后再注销，也不应因重复级联删除触发 SQLAlchemy 告警或异常。
        for username in ["alice", "bob"]:
            self.add_user(username)

        owned_team = self.add_team("Owned Team", "alice")
        self.add_task("owned team task", "alice", team_id=owned_team.id, assignee_username="alice")
        shared_team = self.add_team("Shared Team", "bob")
        self.add_team_member(shared_team.id, "alice", crud.ROLE_ADMIN)
        self.add_task("shared team task", "alice", team_id=shared_team.id, assignee_username="alice")
        self.add_task("alice personal", "alice")

        user = crud.get_user_by_username(self.db, "alice")
        _ = list(user.team_memberships)
        _ = list(user.tasks)
        _ = list(user.owned_teams)

        with warnings.catch_warnings():
            warnings.simplefilter("error", SAWarning)
            cancelled = crud.cancel_account(self.db, "alice")

        self.assertTrue(cancelled)
        self.assertIsNone(crud.get_user_by_username(self.db, "alice"))

    def test_cancel_account_api_uses_crud_cleanup_logic(self):
        # API 层也必须走业务逻辑层，不能直接 db.delete(current_user)。
        self.add_user("alice")
        self.add_user("bob")
        owned_team = self.add_team("Owned Team", "alice")
        self.add_task("owned team task", "alice", team_id=owned_team.id, assignee_username="alice")
        shared_team = self.add_team("Shared Team", "bob")
        self.add_team_member(shared_team.id, "alice", crud.ROLE_ADMIN)
        self.add_task("shared team task", "alice", team_id=shared_team.id, assignee_username="alice")

        current_user = crud.get_user_by_username(self.db, "alice")
        response = api.cancel_account(current_user=current_user, db=self.db)

        self.assertTrue(response["success"])
        self.assertEqual(response["msg"], "账号已注销")
        self.assertIsNone(crud.get_user_by_username(self.db, "alice"))

    def test_cancel_account_does_not_double_delete_team_memberships(self):
        # 用户既拥有团队又参与其他团队时，不应因为重复删除 team_members 触发 SAWarning。
        for username in ["alice", "bob", "carol"]:
            self.add_user(username)

        owned_team = self.add_team("Owned Team", "alice")
        self.add_team_member(owned_team.id, "bob", crud.ROLE_MEMBER)

        shared_team = self.add_team("Shared Team", "bob")
        self.add_team_member(shared_team.id, "alice", crud.ROLE_ADMIN)
        self.add_team_member(shared_team.id, "carol", crud.ROLE_MEMBER)

        with warnings.catch_warnings():
            warnings.simplefilter("error", SAWarning)
            cancelled = crud.cancel_account(self.db, "alice")

        self.assertTrue(cancelled)
        self.assertIsNone(crud.get_user_by_username(self.db, "alice"))


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

    def test_owner_removes_member_and_reassigns_tasks_to_owner(self):
        # Owner 移除普通成员后，该成员负责的团队任务应转交给 Owner。
        self.add_user("owner")
        self.add_user("member")
        team = self.add_team("Core Team", "owner")
        self.add_team_member(team.id, "member", crud.ROLE_MEMBER)
        task = self.add_task(
            "member task",
            "owner",
            team_id=team.id,
            assignee_username="member",
        )

        success, error = crud.remove_team_member(self.db, team.id, "member", "owner")

        self.assertTrue(success)
        self.assertIsNone(error)
        self.assertIsNone(crud.get_team_membership(self.db, team.id, "member"))
        self.db.refresh(task)
        self.assertEqual(task.assignee_username, "owner")

    def test_owner_removes_admin(self):
        # Owner 可以移除 Admin。
        self.add_user("owner")
        self.add_user("admin")
        team = self.add_team("Core Team", "owner")
        self.add_team_member(team.id, "admin", crud.ROLE_ADMIN)

        success, error = crud.remove_team_member(self.db, team.id, "admin", "owner")

        self.assertTrue(success)
        self.assertIsNone(error)
        self.assertIsNone(crud.get_team_membership(self.db, team.id, "admin"))

    def test_member_can_leave_team(self):
        # Member 可以主动退出自己所在的团队。
        self.add_user("owner")
        self.add_user("member")
        team = self.add_team("Core Team", "owner")
        self.add_team_member(team.id, "member", crud.ROLE_MEMBER)

        success, error = crud.remove_team_member(self.db, team.id, "member", "member")

        self.assertTrue(success)
        self.assertIsNone(error)
        self.assertIsNone(crud.get_team_membership(self.db, team.id, "member"))

    def test_admin_can_leave_team(self):
        # Admin 可以主动退出自己所在的团队。
        self.add_user("owner")
        self.add_user("admin")
        team = self.add_team("Core Team", "owner")
        self.add_team_member(team.id, "admin", crud.ROLE_ADMIN)

        success, error = crud.remove_team_member(self.db, team.id, "admin", "admin")

        self.assertTrue(success)
        self.assertIsNone(error)
        self.assertIsNone(crud.get_team_membership(self.db, team.id, "admin"))

    def test_member_cannot_remove_other_member(self):
        # 非 Owner 不能移除其他团队成员。
        for username in ["owner", "member", "other"]:
            self.add_user(username)
        team = self.add_team("Core Team", "owner")
        self.add_team_member(team.id, "member", crud.ROLE_MEMBER)
        self.add_team_member(team.id, "other", crud.ROLE_MEMBER)

        success, error = crud.remove_team_member(self.db, team.id, "other", "member")

        self.assertFalse(success)
        self.assertEqual(error, "团队权限不足")
        self.assertIsNotNone(crud.get_team_membership(self.db, team.id, "other"))

    def test_single_owner_cannot_leave_team(self):
        # 仅含 Owner 一人的团队不允许主动退出。
        self.add_user("owner")
        team = self.add_team("Core Team", "owner")

        success, error = crud.remove_team_member(self.db, team.id, "owner", "owner")

        self.assertFalse(success)
        self.assertEqual(error, "仅含 Owner 的团队不允许退出")
        self.assertEqual(crud.get_team_by_id(self.db, team.id).owner_username, "owner")
        self.assertIsNotNone(crud.get_team_membership(self.db, team.id, "owner"))

    def test_owner_leave_transfers_ownership_to_admin_first(self):
        # Owner 主动退出时，应优先把 Owner 权限移交给 Admin。
        for username in ["owner", "member", "admin"]:
            self.add_user(username)
        team = self.add_team("Core Team", "owner")
        self.add_team_member(team.id, "member", crud.ROLE_MEMBER)
        self.add_team_member(team.id, "admin", crud.ROLE_ADMIN)
        task = self.add_task(
            "owner assigned task",
            "owner",
            team_id=team.id,
            assignee_username="owner",
        )

        success, error = crud.remove_team_member(self.db, team.id, "owner", "owner")

        self.assertTrue(success)
        self.assertIsNone(error)
        self.db.refresh(team)
        self.assertEqual(team.owner_username, "admin")
        self.assertIsNone(crud.get_team_membership(self.db, team.id, "owner"))
        self.assertEqual(crud.get_team_membership(self.db, team.id, "admin").role, crud.ROLE_OWNER)
        self.db.refresh(task)
        self.assertEqual(task.assignee_username, "admin")

    def test_owner_leave_transfers_ownership_to_member_without_admin(self):
        # 没有 Admin 时，Owner 主动退出应把 Owner 权限移交给 Member。
        self.add_user("owner")
        self.add_user("member")
        team = self.add_team("Core Team", "owner")
        self.add_team_member(team.id, "member", crud.ROLE_MEMBER)

        success, error = crud.remove_team_member(self.db, team.id, "owner", "owner")

        self.assertTrue(success)
        self.assertIsNone(error)
        self.db.refresh(team)
        self.assertEqual(team.owner_username, "member")
        self.assertIsNone(crud.get_team_membership(self.db, team.id, "owner"))
        self.assertEqual(crud.get_team_membership(self.db, team.id, "member").role, crud.ROLE_OWNER)


class TaskAccessCrudTests(CrudTestCase):
    def assert_http_error(self, status_code: int, func, *args, **kwargs):
        with self.assertRaises(api.HTTPException) as ctx:
            func(*args, **kwargs)
        self.assertEqual(ctx.exception.status_code, status_code)

    def test_departed_owner_cannot_access_team_task_by_owner_field(self):
        # Owner 离队后，即使任务 owner_username 仍是原 Owner，也不能继续访问或操作团队任务。
        self.add_user("owner")
        self.add_user("member")
        team = self.add_team("Core Team", "owner")
        self.add_team_member(team.id, "member", crud.ROLE_MEMBER)
        task = self.add_task(
            "legacy owner task",
            "owner",
            team_id=team.id,
            assignee_username="owner",
        )

        success, error = crud.remove_team_member(self.db, team.id, "owner", "owner")

        self.assertTrue(success)
        self.assertIsNone(error)
        self.assertEqual(task.owner_username, "owner")
        self.assert_http_error(404, crud.get_task_by_id, self.db, task.id, "owner")
        self.assert_http_error(
            404,
            crud.update_task,
            self.db,
            task.id,
            schemas.TaskUpdate(status="进行中"),
            "owner",
        )
        self.assert_http_error(404, crud.delete_task, self.db, task.id, "owner")

    def test_get_assigned_tasks_excludes_stale_team_assignment_after_membership_removed(self):
        # 即使数据库残留负责人字段，已非团队成员的用户也不能再看到该团队任务。
        self.add_user("owner")
        self.add_user("member")
        team = self.add_team("Core Team", "owner")
        membership = self.add_team_member(team.id, "member", crud.ROLE_MEMBER)
        stale_task = self.add_task(
            "stale assignment",
            "owner",
            team_id=team.id,
            assignee_username="member",
        )
        self.db.delete(membership)
        self.db.commit()

        assigned_tasks = crud.get_assigned_tasks(self.db, "member")

        self.assertNotIn(stale_task.id, [task.id for task in assigned_tasks])

    def test_get_tasks_includes_team_tasks_only_for_current_members(self):
        # 团队任务可见性必须来自成员关系，而不是 owner/assignee 字段残留。
        for username in ["owner", "member", "outsider"]:
            self.add_user(username)
        team = self.add_team("Core Team", "owner")
        self.add_team_member(team.id, "member", crud.ROLE_MEMBER)
        task = self.add_task("team task", "owner", team_id=team.id)

        member_tasks = crud.get_tasks(self.db, "member")
        outsider_tasks = crud.get_tasks(self.db, "outsider")

        self.assertIn(task.id, [item.id for item in member_tasks])
        self.assertNotIn(task.id, [item.id for item in outsider_tasks])

    def test_create_team_task_rejects_non_member_assignee(self):
        # 团队任务负责人必须是当前团队成员。
        self.add_user("owner")
        self.add_user("outsider")
        team = self.add_team("Core Team", "owner")
        task = schemas.TaskCreate(
            title="invalid assignment",
            team_id=team.id,
            assignee_username="outsider",
        )

        self.assert_http_error(400, crud.create_team_task, self.db, task, "owner")

    def test_member_can_only_update_assigned_team_task_status(self):
        # 普通成员只能更新分配给自己的团队任务状态，不能改标题等其他字段。
        self.add_user("owner")
        self.add_user("member")
        team = self.add_team("Core Team", "owner")
        self.add_team_member(team.id, "member", crud.ROLE_MEMBER)
        task = self.add_task(
            "member task",
            "owner",
            team_id=team.id,
            assignee_username="member",
        )

        updated = crud.update_task(
            self.db,
            task.id,
            schemas.TaskUpdate(status="进行中"),
            "member",
        )

        self.assertEqual(updated.status, "进行中")
        self.assert_http_error(
            403,
            crud.update_task,
            self.db,
            task.id,
            schemas.TaskUpdate(title="new title"),
            "member",
        )


class TaskTitleConflictTests(CrudTestCase):
    def test_personal_task_title_does_not_conflict_with_team_task_in_same_team(self):
        # A 的个人任务标题不应阻止 B 在共同团队中创建同名团队任务。
        self.add_user("alice")
        self.add_user("bob")
        team = self.add_team("Shared Team", "alice")
        self.add_team_member(team.id, "bob", crud.ROLE_MEMBER)
        self.add_task("T", "alice")

        conflict = crud.find_task_title_conflict(
            self.db,
            title="T",
            username="bob",
            team_id=team.id,
        )

        self.assertIsNone(conflict)

    def test_personal_task_title_conflicts_with_visible_personal_task(self):
        # 与前端保持一致：当前用户可见的个人任务标题重复时，应判定冲突。
        self.add_user("alice")
        self.add_user("bob")
        existing_task = self.add_task("T", "alice", assignee_username="bob")

        conflict = crud.find_task_title_conflict(
            self.db,
            title="T",
            username="bob",
            team_id=None,
        )

        self.assertIsNotNone(conflict)
        self.assertEqual(conflict.id, existing_task.id)

    def test_team_task_title_conflicts_with_same_team_task(self):
        # 同一团队内的团队任务标题应唯一。
        self.add_user("owner")
        team = self.add_team("Alpha", "owner")
        existing_task = self.add_task("T", "owner", team_id=team.id)

        conflict = crud.find_task_title_conflict(
            self.db,
            title="T",
            username="owner",
            team_id=team.id,
        )

        self.assertIsNotNone(conflict)
        self.assertEqual(conflict.id, existing_task.id)

    def test_team_task_title_does_not_conflict_across_teams(self):
        # 不同团队之间允许同名团队任务。
        self.add_user("owner")
        alpha = self.add_team("Alpha", "owner")
        beta = self.add_team("Beta", "owner")
        self.add_task("T", "owner", team_id=alpha.id)

        conflict = crud.find_task_title_conflict(
            self.db,
            title="T",
            username="owner",
            team_id=beta.id,
        )

        self.assertIsNone(conflict)

    def test_personal_task_title_update_conflicts_with_same_scope_title(self):
        # 更新个人任务标题时，应忽略自身，但不能与同作用域内其他个人任务重名。
        self.add_user("alice")
        self.add_task("Old", "alice")
        existing_task = self.add_task("Target", "alice")
        updating_task = self.add_task("Draft", "alice")

        conflict = crud.find_task_title_conflict(
            self.db,
            title="Target",
            username="alice",
            team_id=None,
            exclude_task_id=updating_task.id,
        )

        self.assertIsNotNone(conflict)
        self.assertEqual(conflict.id, existing_task.id)

    def test_team_task_title_update_conflicts_with_same_team_title(self):
        # 更新团队任务标题时，应按当前团队作用域查重。
        self.add_user("owner")
        team = self.add_team("Alpha", "owner")
        existing_task = self.add_task("Target", "owner", team_id=team.id)
        updating_task = self.add_task("Draft", "owner", team_id=team.id)

        conflict = crud.find_task_title_conflict(
            self.db,
            title="Target",
            username="owner",
            team_id=team.id,
            exclude_task_id=updating_task.id,
        )

        self.assertIsNotNone(conflict)
        self.assertEqual(conflict.id, existing_task.id)

    def test_team_task_title_update_to_same_title_on_self_is_allowed(self):
        # 更新团队任务且标题不变时，不应把自己识别为冲突项。
        self.add_user("owner")
        team = self.add_team("Alpha", "owner")
        task = self.add_task("Same", "owner", team_id=team.id)

        conflict = crud.find_task_title_conflict(
            self.db,
            title="Same",
            username="owner",
            team_id=team.id,
            exclude_task_id=task.id,
        )

        self.assertIsNone(conflict)


class OperationLogTests(CrudTestCase):
    def assert_http_error(self, status_code: int, func, *args, **kwargs):
        with self.assertRaises(api.HTTPException) as ctx:
            func(*args, **kwargs)
        self.assertEqual(ctx.exception.status_code, status_code)

    def test_remove_member_records_assignee_change_log(self):
        self.add_user("owner")
        self.add_user("member")
        team = self.add_team("Core Team", "owner")
        self.add_team_member(team.id, "member", crud.ROLE_MEMBER)
        task = self.add_task("member task", "owner", team_id=team.id, assignee_username="member")

        success, error = crud.remove_team_member(self.db, team.id, "member", "owner")

        self.assertTrue(success)
        self.assertIsNone(error)
        logs = crud.get_task_operation_logs(self.db, task.id, "owner")
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["operator"], "owner")
        self.assertEqual(logs[0]["type"], "edit")
        self.assertEqual(logs[0]["object"]["id"], task.id)
        self.assertFalse(logs[0]["object"]["deleted"])
        self.assertIn("成员 member 被移出团队", logs[0]["description"])
        self.assertIn("member", logs[0]["description"])
        self.assertIn("owner", logs[0]["description"])

    def test_leave_team_records_assignee_change_log(self):
        self.add_user("owner")
        self.add_user("member")
        team = self.add_team("Core Team", "owner")
        self.add_team_member(team.id, "member", crud.ROLE_MEMBER)
        task = self.add_task("member task", "owner", team_id=team.id, assignee_username="member")

        success, error = crud.leave_team(self.db, team.id, "member")

        self.assertTrue(success)
        self.assertIsNone(error)
        logs = crud.get_task_operation_logs(self.db, task.id, "owner")
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["operator"], "member")
        self.assertIn("成员 member 主动离开团队", logs[0]["description"])
        self.assertIn("owner", logs[0]["description"])

    def test_cancel_account_preserves_related_task_logs(self):
        for username in ["alice", "bob", "carol"]:
            self.add_user(username)
        alice_personal = self.add_task("alice personal", "alice")
        bob_personal = self.add_task("bob personal", "bob", assignee_username="alice")
        team = self.add_team("Shared Team", "bob")
        self.add_team_member(team.id, "alice", crud.ROLE_ADMIN)
        self.add_team_member(team.id, "carol", crud.ROLE_MEMBER)
        team_assigned = self.add_task(
            "team assigned",
            "bob",
            team_id=team.id,
            assignee_username="alice",
        )
        team_owned = self.add_task(
            "team owned",
            "alice",
            team_id=team.id,
            assignee_username="carol",
        )
        alice_personal_id = alice_personal.id

        cancelled = crud.cancel_account(self.db, "alice")

        self.assertTrue(cancelled)
        deleted_log = self.db.query(models.OperationLog).filter(
            models.OperationLog.object_id == alice_personal_id,
            models.OperationLog.object_type == "task",
        ).one()
        self.assertEqual(deleted_log.operator_username, "alice")
        self.assertEqual(deleted_log.action_type, "delete")
        self.assertEqual(deleted_log.scope_type, "personal")
        self.assertEqual(deleted_log.scope_title, "alice")
        self.assertEqual(deleted_log.object_deleted, 1)

        bob_logs = crud.get_task_operation_logs(self.db, bob_personal.id, "bob")
        self.assertEqual(len(bob_logs), 1)
        self.assertEqual(bob_logs[0]["operator"], "alice")
        self.assertIn("负责人由 alice 变更为 未分配", bob_logs[0]["description"])

        team_assigned_logs = crud.get_task_operation_logs(self.db, team_assigned.id, "bob")
        self.assertIn("负责人由 alice 变更为 bob", team_assigned_logs[0]["description"])

        team_owned_logs = crud.get_task_operation_logs(self.db, team_owned.id, "bob")
        self.assertIn("任务创建者由 alice 变更为 bob", team_owned_logs[0]["description"])

    def test_delete_team_preserves_deleted_task_log_snapshot(self):
        self.add_user("owner")
        self.add_user("member")
        team = self.add_team("Core Team", "owner")
        self.add_team_member(team.id, "member", crud.ROLE_MEMBER)
        task = self.add_task("team task", "owner", team_id=team.id, assignee_username="member")
        task_id = task.id
        team_id = team.id

        deleted = crud.delete_team(self.db, team.id, operator_username="owner")

        self.assertTrue(deleted)
        self.assertIsNone(self.db.query(models.Task).filter(models.Task.id == task_id).first())
        log = self.db.query(models.OperationLog).filter(
            models.OperationLog.object_id == task_id,
            models.OperationLog.object_type == "task",
        ).one()
        self.assertEqual(log.operator_username, "owner")
        self.assertEqual(log.object_title, "team task")
        self.assertEqual(log.scope_type, "team")
        self.assertEqual(log.scope_id, team_id)
        self.assertEqual(log.scope_title, "Core Team")
        self.assertEqual(log.object_deleted, 1)

    def test_task_logs_are_returned_newest_first(self):
        self.add_user("alice")
        task = self.add_task("personal", "alice")
        crud.log_operation(
            self.db,
            "alice",
            "edit",
            task.id,
            "task",
            task.title,
            "personal",
            None,
            "alice",
            "第一条日志"
        )
        crud.log_operation(
            self.db,
            "alice",
            "edit",
            task.id,
            "task",
            task.title,
            "personal",
            None,
            "alice",
            "第二条日志"
        )
        self.db.commit()

        logs = crud.get_task_operation_logs(self.db, task.id, "alice")

        self.assertEqual([log["description"] for log in logs], ["第二条日志", "第一条日志"])

    def test_personal_task_logs_are_owner_only(self):
        self.add_user("alice")
        self.add_user("bob")
        task = self.add_task("personal", "alice", assignee_username="bob")
        crud.log_operation(
            self.db,
            "alice",
            "edit",
            task.id,
            "task",
            task.title,
            "personal",
            None,
            "alice",
            "个人任务日志"
        )
        self.db.commit()

        self.assertEqual(len(crud.get_task_operation_logs(self.db, task.id, "alice")), 1)
        self.assert_http_error(403, crud.get_task_operation_logs, self.db, task.id, "bob")

    def test_team_task_logs_require_current_team_member(self):
        for username in ["owner", "member", "outsider"]:
            self.add_user(username)
        team = self.add_team("Core Team", "owner")
        self.add_team_member(team.id, "member", crud.ROLE_MEMBER)
        task = self.add_task("team task", "owner", team_id=team.id)
        crud.log_operation(
            self.db,
            "owner",
            "edit",
            task.id,
            "task",
            task.title,
            "team",
            team.id,
            team.name,
            "团队任务日志"
        )
        self.db.commit()

        self.assertEqual(len(crud.get_task_operation_logs(self.db, task.id, "member")), 1)
        self.assert_http_error(403, crud.get_task_operation_logs, self.db, task.id, "outsider")

    def test_failed_member_change_does_not_record_success_log(self):
        for username in ["owner", "member", "other"]:
            self.add_user(username)
        team = self.add_team("Core Team", "owner")
        self.add_team_member(team.id, "member", crud.ROLE_MEMBER)
        self.add_team_member(team.id, "other", crud.ROLE_MEMBER)
        self.add_task("other task", "owner", team_id=team.id, assignee_username="other")

        success, error = crud.remove_team_member(self.db, team.id, "other", "member")

        self.assertFalse(success)
        self.assertEqual(error, "团队权限不足")
        self.assertEqual(self.db.query(models.OperationLog).count(), 0)


if __name__ == "__main__":
    unittest.main()
