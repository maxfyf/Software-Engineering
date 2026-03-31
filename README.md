# README

### 1 项目依赖

##### 1.1 后端依赖

```text
fastapi >= 0.104.1                   # 高性能Web API框架，用于接口开发与请求处理
uvicorn >= 0.24.0                    # ASGI服务器，负责运行FastAPI应用
sqlalchemy >= 2.0.23                 # ORM框架，简化数据库操作，实现数据持久化
pydantic >= 2.4.2                    # 数据校验与格式化，规范接口入参/出参
python-jose >= 3.3.0                 # JWT令牌生成与解析，用于用户身份鉴权
passlib >= 1.7.4                     # 密码加密库，采用bcrypt算法存储密码
sqlite3                              # 内置轻量数据库，自动生成数据库文件
```

##### 1.2 前端依赖

``` text
element-plus/icons-vue >= 2.3.2      # Vue3版本的Element Plus图标库
axios >= 1.14.0                      # HTTP客户端库，用于发送AJAX请求与调用后端API
element-plus >= 2.13.5               # Element Plus组件库
vue >= 3.5.29                        # Vue.js作为前端的基础框架
vue-router >= 5.0.3                  # Vue路由管理器，实现单页应用路由
vitejs/plugin-vue >= 6.0.4           # Vite的Vue插件，提供Vue3单文件组件的热更新支持
vite >= 7.3.1                        # Vite作为构建工具
vite-plugin-vue-devtools >= 8.0.6    # Vue DevTools的Vite插件，在开发环境中提供Vue调试工具
```

### 2 项目架构

```text
/                                                # 项目根目录
├── backend/                                     # 后端根目录
|	├── __init__.py                              # Python包标识文件
|	├── crud.py                                  # 数据操作层，实现用户、任务的增删改查核心逻辑
|	├── database.py                              # 数据库核心配置
|	├── models.py                                # ORM数据模型
|	├── requirements.txt                         # Python项目核心配置文件
|	├── schemas.py                               # 接口数据模型
|	└── security.py                              # 安全认证相关逻辑
├── frontend/                                    # 前端根目录
|	├── .vscode/                                 # 以VS Code为默认编辑器
|	|	└── extensions.json                      # 为项目推荐特定的VS Code插件
|	├── public/                                  # 静态资源
|	│   └── logo.png                             # 复旦校徽（作为网页icon）
|	├── src/                                     # 源代码
|	│   ├── assets/                              # 资源
|	|	|	├── images/                          # 图片
|	|	|	|	├── login_page_decoration.png    # 登录界面装饰图
|	|	|	|	└── logo.png                     # 复旦校徽
|	|	|	└── styles/                          # 样式
|	|	|	 	├── base.css                     # 基础样式
|	|	|	 	└── main.css                     # 网页样式与其他全局样式
|	|	├── components/                          # 可复用组件
|	|	|	├── HeaderWrapper.vue                # 顶栏
|	|	|	├── Search.vue                       # 搜索框
|	|	|	└── SidebarWrapper.vue               # 侧边栏
|	|	├── request/                             # API前端接口
|	|   |   └── api.js                           # 基于Axios实现的前后端通信API
|	|	├── router/                              # 界面路由
|	|	|	└── index.js                         # 界面路由表与历史记录
|	|	├── store/                               # 前端暂存数据
|	|	|	└── user.js                          # 登录用户数据
|	|	├── views/                               # 界面
|	|	|	├── settings/                        # 设置路由下的界面
|	|	|	|	└── UserInfoView.vue             # 个人资料界面
|	|	|	├── task/                            # 任务路由下的界面
|	|	|	|	├── AllTaskView.vue              # 全部任务界面
|	|	|	|	└── EditTaskView.vue             # 新建/编辑任务界面
|	|	|	├── LoginView.vue                    # 登录界面
|	|	|	├── SettingsView.vue                 # 设置界面
|	|	|	└── TaskView.vue                     # 任务界面
|	|	├── App.vue                              # 应用程序主界面
|	|	└── main.js                              # 应用程序入口
|	├── index.html                               # HTML入口，作为应用程序的容器
|	├── jsconfig.json                            # Javascript项目的根目录标识和配置核心
|	├── package.json                             # Node.js项目核心配置文件
|	└── vite.config.js                           # Vite构建工具配置文件
├── .gitignore                                   # 不被纳入版本控制的配置文件
└── README.md                                    # 项目说明文档（此文件）
```

### 3 运行方法

##### 3.1 环境准备

- 后端依赖安装：确保电脑上已安装Python 3.9+，打开命令行切换到后端根目录`backend/`，执行`pip install -r requirements.txt`。
- 前端依赖安装：确保电脑上已安装Node.js，打开命令行切换到前端根目录`frontend/`，执行`npm install`。

##### 3.2 启动后端服务器

打开命令行，切换到项目根目录，执行`uvicorn app.main:app --reload`，即可启动开发模式，自动热重载。

- 后端服务地址：http://127.0.0.1:8000
- API 调试文档（自动生成，可直接测试接口）：http://127.0.0.1:8000/docs
- 数据库文件：启动服务后自动生成 task_manager.db（SQLite），无需手动建库建表
- 数据持久化：关闭服务后，数据库数据不会丢失，重启服务可继续使用

##### 3.3 启动前端网页

- 开发模式：打开命令行，切换到前端根目录`frontend/`，执行`npm run dev`后按住Ctrl键点击链接，可以快捷地打开含调试信息的前端网页。
- 构建模式：打开命令行，切换到前端根目录`frontend/`，执行`npm run build`可以在前端目录下生成静态文件目录`dist`。随后执行`npm run preview`，按住Ctrl键点击链接，可以预览项目上线后前端网页的实际效果，并对相关功能进行测试。