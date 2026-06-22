# README

### 1 项目依赖

##### 1.1 后端依赖

```text
python >= 3.10                       # 后端编程语言（代码使用 PEP 604 联合类型等 Python 3.10 语法）
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
Node.js >= 20.19/22.12               # 让 JavaScript 脱离浏览器运行的前端环境
element-plus/icons-vue >= 2.3.2      # Vue3 版本的 Element Plus 图标库
axios >= 1.14.0                      # HTTP 客户端库，用于发送 AJAX 请求与调用后端 API
element-plus >= 2.13.5               # Element Plus 组件库
vue >= 3.5.29                        # Vue.js 作为前端的基础框架
vue-router >= 5.0.3                  # Vue 路由管理器，实现单页应用路由
vuedraggable >= 4.1.0                # Vue.js 的拖拽排序组件库
vitejs/plugin-vue >= 6.0.4           # Vite 的 Vue 插件，提供 Vue3 单文件组件的热更新支持
vite >= 7.3.1                        # Vite 作为构建工具
vite-plugin-vue-devtools >= 8.0.6    # Vue DevTools 的 Vite 插件，在开发环境中提供 Vue 调试工具
```

### 2 项目架构

```text
project_root/                                    # 项目根目录
├── backend/                                     # 后端目录
│   ├── tests/                                   # 后端自动化测试
│   │   ├── test_api.py                          # 直接调用 API 处理函数的规则测试
│   │   ├── test_crud.py                         # 业务逻辑层与数据库行为测试
│   │   ├── test_user_management_acceptance.py   # 用户、团队与操作日志验收测试
│   │   └── user_management_acceptance_cases.md  # TC-UM-01～18 验收用例与执行结果
│   ├── api.py                                   # FastAPI 主入口，定义用户/任务接口与鉴权依赖
│   ├── crud.py                                  # 数据操作层（含团队软删除/恢复、账号注销清理）
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

- 后端依赖安装：确保电脑上已安装 Python 3.10+，打开命令行并切换到 `backend/` 目录后执行

  ```bash
  pip install -r requirements.txt
  ```

- 前端依赖安装：确保电脑上已安装 Node.js 20.19+ 或 22.12+，打开命令行并切换到 `frontend/` 目录后执行

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

1. 方式一（开发模式，推荐开发调试）：打开命令行，切换到 `frontend/` 目录后执行

   ```bash
   npm run dev
   ```

   随后按住 Ctrl 键点击链接，可以快捷地打开含调试信息的前端网页

2. 方式二（构建模式，在项目部署前构建）：打开命令行，切换到 `frontend/` 目录后执行

   ```bash
   npm run build
   ```

   前端目录下将自动生成静态文件目录 `dist`。接着，在原命令行窗口中执行

   ```bash
   npm run preview
   ```

   随后按住 Ctrl 键点击链接，可以预览项目上线后前端网页的实际效果，并对相关功能进行测试。

- 开发模式前端网页地址：http://localhost:5173/
- 构建模式前端网页地址：http://localhost:4173/

##### 3.4 运行后端自动化测试

1. 打开命令行，切换到项目根目录 `Software-Engineering/`，先检查后端文件能否完成语法编译：

   ```bash
   python3 -m compileall -q backend
   ```

2. 运行全部后端测试并显示每个用例：

   ```bash
   python3 -m unittest discover -s backend/tests -v
   ```

3. 也可以分别运行三个测试文件：

   ```bash
   python3 -m unittest backend.tests.test_api -v
   python3 -m unittest backend.tests.test_crud -v
   python3 -m unittest backend.tests.test_user_management_acceptance -v
   ```

- 测试使用 Python 标准库 `unittest`，不需要额外安装 `pytest`，但仍需先安装 `backend/requirements.txt` 中的后端运行依赖。
- 各测试用例的业务数据写入独立的临时 SQLite 数据库，并在用例结束后删除，不会把测试用户、团队或任务写入项目数据库。
- 测试文件会导入 `backend/api.py`；该模块在导入时执行建表，因此从项目根目录运行时可能创建或初始化被 `.gitignore` 忽略的根目录 `task_manager.db`。这不是用例业务数据源，但运行前后不应依赖该文件保持完全不变。

### 4 测试说明

##### 4.1 当前测试覆盖范围

- `backend/tests/test_crud.py` 共 41 项，使用临时数据库直接验证 `crud.py`。覆盖团队软删除与恢复、注销账号时的物理清理、成员移除与离队、Owner 转移、任务访问与标题查重、任务删除、操作日志留存和日志读取权限。
- `backend/tests/test_api.py` 共 14 项，直接调用 `api.py` 中的真实处理函数。覆盖团队名称校验、已解散团队名称复用、邀请与团队任务访问权限、任务状态参数、跨层前后继状态约束、依赖作用域限制和循环依赖拒绝。
- `backend/tests/test_user_management_acceptance.py` 共 18 项，对应 `user_management_acceptance_cases.md` 中的 TC-UM-01～18。覆盖注册登录、团队创建与成员管理、离队任务转交、团队软删除、账号注销、操作日志内容与访问控制。

##### 4.2 测试设计说明

- 每个测试用例都会独立创建临时数据库、初始化表结构，并在用例结束后自动清理，避免测试之间相互污染。
- CRUD 测试直接调用业务逻辑层方法，适合定位数据库状态迁移和权限规则问题。
- API 测试直接调用 FastAPI 处理函数并传入测试数据库与模拟当前用户，验证的是处理函数本身，不等同于通过 ASGI/HTTP 客户端执行的端到端接口测试。
- 验收测试将固定编号的业务用例落实为自动化断言；用例表中的“通过”应以最近一次实际执行结果为准。
- 团队“解散”采用软删除：活动查询和权限入口不再返回该团队，但团队、成员、任务及依赖仍保留以便恢复。用户注销其拥有的团队时才调用物理删除流程。
- 当前自动化测试不覆盖浏览器前端联调、真实 JWT 请求链路、CORS、并发请求、性能和生产数据库迁移。
- 如需补充更多测试，建议按“一个业务方法对应一组场景”的方式继续在 `backend/tests/` 下扩展。
