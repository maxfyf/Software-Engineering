# 任务管理系统 - 软件工程Lab1

## 项目简介
本项目是软件工程课程Lab1的后端API部分，实现了一个前后端分离的轻量级个人任务管理系统，包含用户注册登录、个人任务CRUD等核心功能。

## 技术栈
- **后端框架**: FastAPI
- **数据库**: SQLite（无需额外安装，适合Lab快速开发）
- **ORM**: SQLAlchemy
- **认证**: JWT (JSON Web Token)
- **密码加密**: Passlib + bcrypt

## 项目结构
```
task-manager-lab1/
├── .gitignore
├── README.md
├── requirements.txt
└── app/
    ├── __init__.py
    ├── database.py    # 数据库配置
    ├── models.py      # 数据模型
    ├── schemas.py     # 交互模型
    ├── security.py    # 安全工具
    └── main.py        # 接口路由
```

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 启动项目
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 查看接口文档
启动后访问以下地址可查看自动生成的交互式API文档：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 核心功能
- 用户注册（用户名/密码格式校验、密码非明文存储）
- 用户登录（JWT Token生成、登录状态维护）
- 个人任务管理（创建/查看列表/查看详情/修改/删除）
- 用户数据隔离（仅能操作自己的任务）

## Git提交规范（课程要求）
- 提交信息格式：`type: subject`
- 常用type：
  - `feat`: 新功能
  - `fix`: 修复bug
  - `docs`: 文档更新
  - `refactor`: 重构
  - `style`: 代码格式调整