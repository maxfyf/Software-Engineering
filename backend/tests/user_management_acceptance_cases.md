# 用户管理部分后端验收测试用例

本组用例仅覆盖用户管理、团队成员管理，以及这些操作引发的任务归属变化、访问控制变化和操作日志变化。普通任务创建、编辑、状态修改、依赖编辑不作为本组被测功能，只作为必要前置数据。

| 用例编号 | 测试目标 | 前置条件 | 操作步骤 | 预期结果 | 实际结果 |
|---|---|---|---|---|---|
| TC-UM-01 | 验证用户注册成功 | 数据库中不存在用户 `alice` | 调用 `POST /api/user/register`，提交合法用户名、密码、邮箱等信息 | 返回注册成功；数据库新增 `alice`；密码以哈希形式保存，不保存明文 | 通过（自动化测试） |
| TC-UM-02 | 验证重复用户名注册被拒绝 | 数据库中已存在用户 `alice` | 再次调用注册接口提交用户名 `alice` | 返回 400；提示用户名已存在；不新增重复用户 | 通过（自动化测试） |
| TC-UM-03 | 验证用户登录成功 | 已注册用户 `alice`，密码正确 | 调用 `POST /api/user/login`，提交正确用户名和密码 | 返回登录成功；返回 token；用户信息不包含 `password` 或 `password_hash` | 通过（自动化测试） |
| TC-UM-04 | 验证错误密码登录失败 | 已注册用户 `alice` | 调用登录接口，提交错误密码 | 返回 401；提示密码错误；不返回 token | 通过（自动化测试） |
| TC-UM-05 | 验证 Owner 创建团队并自动成为 Owner 成员 | 用户 `owner` 已登录 | 调用 `POST /api/team/create` 创建团队 `Alpha` | 返回团队创建成功；团队 owner 为 `owner`；`team_members` 中存在 `owner` 且角色为 Owner | 通过（自动化测试） |
| TC-UM-06 | 验证非 Owner 不能添加团队成员 | 团队 `Alpha` 存在；`admin` 是 Admin；`member` 不在团队中 | 由 `admin` 调用添加成员逻辑，将 `member` 加入团队 | 返回权限不足；`member` 未加入团队 | 通过（自动化测试） |
| TC-UM-07 | 验证 Owner 添加团队成员成功 | 团队 `Alpha` 存在；`owner` 为 Owner；用户 `member` 存在 | 由 `owner` 添加 `member` 到团队 | 返回成功；`member` 成为团队成员；默认角色为 Member | 通过（自动化测试） |
| TC-UM-08 | 验证非团队成员不能访问团队任务或团队空间 | 团队 `Alpha` 有任务；`outsider` 不是团队成员 | `outsider` 请求团队任务列表或调用团队成员校验逻辑 | 返回 403 或无权访问；不能看到团队任务 | 通过（自动化测试） |
| TC-UM-09 | 验证成员主动离开团队后的任务处理 | 团队 `Alpha` 中 `member` 负责一个未完成团队任务；`owner` 为团队 Owner | `member` 调用离开团队逻辑 | `member` 被移出团队；未完成任务负责人自动变更为 `owner`；返回被转交任务；生成负责人变更日志 | 通过（自动化测试） |
| TC-UM-10 | 验证 Owner 移除成员后的任务处理 | 团队 `Alpha` 中 `member` 负责一个未完成团队任务 | `owner` 移除 `member` | `member` 被移出团队；其未完成任务负责人变更为 `owner`；返回被转交任务；生成操作日志 | 通过（自动化测试） |
| TC-UM-11 | 验证仅剩 Owner 时不能主动离开团队 | 团队 `Alpha` 只有 `owner` 一名成员 | `owner` 调用离开团队或移除自己逻辑 | 返回失败；提示仅含 Owner 的团队不允许退出；团队和成员关系不变；不生成成功日志 | 通过（自动化测试） |
| TC-UM-12 | 验证 Owner 离开时团队所有权自动转移 | 团队 `Alpha` 有 Owner、Admin、Member；Owner 负责未完成任务 | Owner 主动离开团队 | Owner 被移出；优先将所有权转给 Admin；Owner 负责的未完成任务转给新 Owner；返回被转交任务；生成任务负责人变更日志 | 通过（自动化测试） |
| TC-UM-13 | 验证团队软删除后的访问控制与数据保留 | 团队 `Alpha` 存在团队任务和成员 | Owner 调用团队解散逻辑 | 活动团队查询不再返回该团队；原成员不能访问团队空间；团队、成员和任务保留以便恢复；记录 `disband_team` 日志且任务不标记为已删除 | 通过（自动化测试） |
| TC-UM-14 | 验证用户注销后的数据清理 | 用户 `alice` 拥有个人任务、拥有团队、参与其他团队并负责任务 | `alice` 调用注销账号逻辑 | `alice` 被删除；个人任务及其拥有的团队被物理删除；其他团队中由 `alice` 负责或创建的任务迁移到团队 Owner；返回转交通知快照；相关日志保留 | 通过（自动化测试） |
| TC-UM-15 | 验证注销账号不会泄露敏感信息到日志 | 用户 `alice` 已注册并有任务；日志功能开启 | `alice` 注销账号后查询相关操作日志 | 日志只包含操作人、类型、对象、时间、描述、范围；不包含密码、`password_hash`、Token | 通过（自动化测试） |
| TC-UM-16 | 验证成员变更失败不生成成功日志 | `member` 和 `other` 都是普通成员；`other` 负责团队任务 | `member` 尝试移除 `other` | 返回权限不足和空转交任务列表；成员关系不变；任务负责人不变；不新增操作日志 | 通过（自动化测试） |
| TC-UM-17 | 验证任务日志按时间倒序返回 | 某任务已有多条由用户或团队变更产生的日志 | 调用 `crud.get_task_operation_logs(db, task_id, username)` | 返回日志按操作时间倒序排列；最近日志在最前 | 通过（自动化测试） |
| TC-UM-18 | 验证无权限用户不能查看团队任务日志 | 团队任务已有日志；`outsider` 不是当前团队成员 | `outsider` 调用任务日志查询函数 | 返回 403；不返回日志内容 | 通过（自动化测试） |

## 测试运行方式

以下命令均在项目根目录 `/Users/jasonzhao/Documents/Code/Software-Engineering` 下执行。后端单元测试使用临时 SQLite 数据库，不应污染项目已有数据库文件。

```bash
python3 -m compileall -q backend
python3 -m unittest discover -s backend/tests -v
```

本表对应的自动化测试可单独运行：

```bash
python3 -m unittest backend.tests.test_user_management_acceptance -v
```

2026 年 6 月 22 日执行上述命令，18 项验收测试全部通过。表中的“实际结果”以该次自动化执行结果为准；后续代码变更后应重新运行并同步更新。

## 覆盖说明

- Lab1 核心回归：TC-UM-01 至 TC-UM-04。
- Lab2 核心回归：TC-UM-05 至 TC-UM-08。
- Lab3 核心回归：TC-UM-09 至 TC-UM-14。
- Lab4 操作日志：TC-UM-09、TC-UM-10、TC-UM-13、TC-UM-15、TC-UM-17、TC-UM-18。
- 异常或边界：TC-UM-02、TC-UM-04、TC-UM-06、TC-UM-08、TC-UM-11、TC-UM-16、TC-UM-18。
