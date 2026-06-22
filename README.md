# README

### 1 项目依赖

##### 1.1 后端依赖

```text
python >= 3.9                        # 后端编程语言
fastapi                              # 高性能 Web API 框架
uvicorn                              # ASGI 服务器，用于运行 FastAPI
pydantic                             # 数据校验与请求模型定义
sqlalchemy                           # ORM 框架，负责数据库访问
passlib == 1.7.4                     # 密码哈希与校验
bcrypt == 4.0.1                      # passlib 的 bcrypt 算法依赖
python-jose                          # JWT 令牌生成与解析

# 说明：项目使用 SQLite，数据库文件为 backend/task_manager.db（Python 内置 sqlite3 驱动，无需单独安装）
```

##### 1.2 前端依赖

``` text
Node.js >= 20.19/22.12               # 让JavaScript脱离浏览器运行的前端环境
element-plus/icons-vue >= 2.3.2      # Vue3版本的Element Plus图标库
axios >= 1.14.0                      # HTTP客户端库，用于发送AJAX请求与调用后端API
element-plus >= 2.13.5               # Element Plus组件库
vue >= 3.5.29                        # Vue.js作为前端的基础框架
vue-router >= 5.0.3                  # Vue路由管理器，实现单页应用路由
vuedraggable >= 4.1.0                # Vue.js的拖拽排序组件库
vitejs/plugin-vue >= 6.0.4           # Vite的Vue插件，提供Vue3单文件组件的热更新支持
vite >= 7.3.1                        # Vite作为构建工具
vite-plugin-vue-devtools >= 8.0.6    # Vue DevTools的Vite插件，在开发环境中提供Vue调试工具
```

### 2 项目架构

```text
project_root/                                    # 项目根目录
├── backend/                                     # 后端目录
│   ├── tests/                                   # 后端单元测试
│   │   ├── test_api.py                          # API 端点单元测试
│   │   ├── test_crud.py                         # 业务逻辑层 CRUD 单元测试
│   │   ├── test_user_management_acceptance.py   # 核心功能单元测试
│   │   └── user_management_acceptance_cases.md  # 测试用例文档
│   ├── api.py                                   # FastAPI 主入口，定义用户/任务接口与鉴权依赖
│   ├── crud.py                                  # 数据操作层
│   ├── database.py                              # SQLAlchemy 与 SQLite 配置、会话管理
│   ├── log_service.py                           # 任务操作日志相关服务
│   ├── main.py                                  # 启动入口
│   ├── models.py                                # ORM 数据模型
│   ├── notification_service.py                  # 通知相关服务
│   ├── requirements.txt                         # 后端依赖列表/ Python 项目核心配置文件
│   ├── schemas.py                               # Pydantic 接口数据模型（请求/响应）
│   ├── security.py                              # 密码加密与 JWT 令牌逻辑等安全认证相关逻辑
│   └── task_manager.db                          # SQLite 数据库文件（后端启动后生成）
├── frontend/                                    # 前端目录
│   ├── .vscode/                                 # 以 VS Code 为默认编辑器
│   │   └── extensions.json                      # 为项目推荐特定的 VS Code 插件
│   ├── dist/                                    # 构建产物目录（前端构建后生成）
│   ├── node_modules/                            # 依赖包目录（安装前端依赖后生成）
│   ├── public/                                  # 静态资源
│   │   └── logo.png                             # 复旦校徽（作为网页 icon ）
│   ├── src/                                     # 源代码
│   │   ├── assets/                              # 资源
│   │   │   ├── images/                          # 图片
│   │   │   │   ├── login_page_decoration.png    # 登录界面装饰图
│   │   │   │   └── logo.png                     # 复旦校徽
│   │   │   └── styles/                          # 样式
│   │   │       ├── base.css                     # 基础样式
│   │   │       └── main.css                     # 网页样式与其他全局样式
│   │   ├── components/                          # 可复用的组件
│   │   │   ├── HeaderWrapper.vue                # 顶栏
│   │   │   ├── OperationList.vue                # 操作列表
│   │   │   ├── Route.vue                        # 二级以上的内部路由
│   │   │   ├── Search.vue                       # 搜索框
│   │   │   ├── SelectableList.vue               # 多选框
│   │   │   ├── SidebarWrapper.vue               # 侧边栏
│   │   │   ├── TaskList.vue                     # 任务列表
│   │   │   ├── TaskViewWrapper.vue              # 任务列表容器
│   │   │   ├── TeamList.vue                     # 团队列表
│   │   │   ├── TeamListWrapper.vue              # 团队列表容器
│   │   │   └── TwoColumnsWrapper.vue            # 两栏表
│   │   ├── request/                             # API 前端接口
│   │   │   └── api.js                           # 基于 Axios 实现的前后端通信 API
│   │   ├── router/                              # 界面路由
│   │   │   └── index.js                         # 界面路由索引与历史记录
│   │   ├── store/                               # 前端暂存的数据
│   │   │   ├── layout.js                        # 界面样式数据
│   │   │   └── user.js                          # 登录用户数据
│   │   ├── utils/                               # 可复用的工具函数
│   │   │   ├── profileLoader.js                 # 用户信息加载器
│   │   │   ├── routeManager.js                  # 二级以上内部路由管理器
│   │   │   ├── useOperationView.js              # 操作日志界面的通用函数
│   │   │   ├── useTaskView.js                   # 任务列表界面的通用函数
│   │   │   └── useTeamView.js                   # 团队列表界面的通用函数
│   │   ├── views/                               # 界面
│   │   │   ├── settings/                        # 设置路由下的界面
│   │   │   │   └── UserInfoView.vue             # 个人资料界面
│   │   │   ├── task/                            # 任务路由下的界面
│   │   │   │   ├── AllTasksView.vue             # 全部任务界面
│   │   │   │   ├── DetailView.vue               # 任务详情界面
│   │   │   │   ├── EditTaskView.vue             # 新建/编辑任务界面
│   │   │   │   ├── PersonalTasksView.vue        # 个人任务界面
│   │   │   │   └── TeamTasksView.vue            # 团队任务界面
│   │   │   ├── team/                            # 团队路由下的界面
│   │   │   │   ├── AdminTeamsView.vue           # 用户管理的团队界面
│   │   │   │   ├── AllTeamsView.vue             # 全部团队界面
│   │   │   │   ├── DisbandedTeamsView.vue       # 用户解散的团队界面（团队回收站）
│   │   │   │   ├── MemberTeamsView.vue          # 用户参与的团队界面
│   │   │   │   ├── OwnerTeamsView.vue           # 用户拥有的团队界面
│   │   │   │   ├── PersonnelView.vue            # 团队人员界面
│   │   │   │   └── TeamSpaceView.vue            # 团队空间界面
│   │   │   ├── LoginView.vue                    # 登录界面
│   │   │   ├── OperationView.vue                # 操作日志界面
│   │   │   ├── SettingsView.vue                 # 设置界面
│   │   │   ├── TaskView.vue                     # 任务界面
│   │   │   └── TeamView.vue                     # 团队界面
│   │   ├── App.vue                              # 应用程序主界面
│   │   └── main.js                              # 应用程序入口
│   ├── index.html                               # HTML 入口，作为应用程序的容器
│   ├── jsconfig.json                            # Javascript 项目的根目录标识和配置核心
│   ├── package.json                             # Node.js 项目核心配置文件
|	├── package-lock.json                        # npm 锁定文件（安装前端依赖后生成）
│   └── vite.config.js                           # Vite 构建工具配置文件
├── .gitignore                                   # 不被纳入版本控制的配置文件
└── README.md                                    # 项目说明文档（此文件）
```

### 3 项目启动方式

##### 3.1 环境准备

- 后端依赖安装：确保电脑上已安装 Python 3.9+，打开命令行并切换到 `backend/`目录后执行

  ```bash
  pip install -r requirements.txt
  ```

- 前端依赖安装：确保电脑上已安装Node.js 20.19+或22.12+，打开命令行并切换到`frontend/`目录后执行

  ```bash
  npm install
  ```

##### 3.2 启动后端服务器

1. 方式一（推荐开发调试）：打开命令行，切换到 `backend/` 目录后执行

   ```bash
   uvicorn api:app --reload --host 0.0.0.0 --port 8000
   ```

2. 方式二（使用项目启动脚本）：打开命令行，切换到 `backend/` 目录后执行

   ```bash
   python main.py
   ```

- 后端服务地址：http://127.0.0.1:8000
- API 调试文档（自动生成，可直接测试接口）：http://127.0.0.1:8000/docs
- 健康检查接口：`GET /`、`GET /api/health`
- 数据库文件：启动服务后自动生成 `backend/task_manager.db`（SQLite），无需手动建库建表
- 数据持久化：关闭服务后，数据库数据不会丢失，重启服务可继续使用

##### 3.3 启动前端网页

1. 方式一（开发模式，推荐开发调试）：打开命令行，切换到`frontend/`目录后执行

   ```bash
   npm run dev
   ```

   随后按住Ctrl键点击链接，可以快捷地打开含调试信息的前端网页

2. 方式二（构建模式，在项目部署前构建）：打开命令行，切换到`frontend/`目录后执行

   ```bash
   npm run build
   ```

   前端目录下将自动生成静态文件目录`dist`。接着，在原命令行窗口中执行

   ```bash
   npm run preview
   ```

   随后按住Ctrl键点击链接，可以预览项目上线后前端网页的实际效果，并对相关功能进行测试。

- 开发模式前端网页地址：http://localhost:5173/
- 构建模式前端网页地址：http://localhost:4173/

##### 3.4 运行后端单元测试

1. 打开命令行，切换到项目根目录 `Software-Engineering/` 后执行

   ```bash
   python3 -m unittest discover -s backend/tests
   ```

2. 如果只想运行某一个测试文件，可执行

   ```bash
   python3 -m unittest backend.tests.test_crud
   ```

- 当前测试基于 Python 标准库 `unittest`，无需额外安装 `pytest` 等测试框架。
- 测试使用临时 SQLite 数据库，不会修改项目根目录下已有的 `task_manager.db` 数据。
- 建议先完成 `backend/requirements.txt` 中依赖安装，再运行测试。

### 4 测试说明

##### 4.1 当前测试覆盖范围

- `backend/tests/test_crud.py` 主要覆盖后端业务逻辑层 `backend/crud.py` 中的核心方法，在原有基础上重点增加了针对有向无环图（DAG）任务依赖算法的深度验证。
- 业务逻辑层已覆盖的重点场景包括：删除团队 `delete_team()`、注销账号 `cancel_account()`、添加团队成员 `add_team_member()`。
- 业务逻辑层已覆盖的重点场景包括：删除团队 `delete_team()`、注销账号 `cancel_account()`、添加团队成员 `add_team_member()`，以及新增的级联删除 `delete_task_with_deps()` 和成环防御算法 `check_circular_dependency()`。
- 图算法测试重点验证了开启或关闭级联时，能否精准定位并清理后继任务及依赖边；同时验证了团队解散或成员离队时的外键级联清理机制，防止产生幽灵依赖。
- `backend/tests/test_api.py` 主要覆盖 API 端点的防御性编程机制，重点测试了 `validate_status_transition()` 状态机拦截机制与依赖域安全隔离规则。
- 状态机测试重点验证了试图完成/回退任务时，若通过 `find_top_unfinished_predecessor()` 发现未完成的前置任务，或通过 `find_nearest_done_successor()` 发现已完成的后继任务，接口能否准确拒绝非法状态扭转。

##### 4.2 测试设计说明

- 每个测试用例都会独立创建临时数据库、初始化表结构，并在用例结束后自动清理，避免测试之间相互污染。
- 单元测试直接调用业务逻辑层方法，不经过 FastAPI 路由，目的是更快定位 `crud.py` 内部业务规则是否正确。
- 针对复杂的依赖规则，测试用例在内存中构建了包含多层深度、分叉分支以及闭环趋势的任务图拓扑（桩数据），以此验证图算法在极端边界条件下的健壮性。
- 测试确保了前后台双防验证，即使绕过前端页面，后端的业务控制层与数据校验层依然具备足够的健壮性对非法状态进行兜底拦截。
- 如需补充更多测试，建议按“一个业务方法对应一组场景”的方式继续在 `backend/tests/` 下扩展。


