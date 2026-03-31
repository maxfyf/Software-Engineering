# README

### 一、项目依赖

```json
{
  "dependencies": {
    "@element-plus/icons-vue": "^2.3.2",
    "axios": "^1.14.0",
    "element-plus": "^2.13.5",
    "vue": "^3.5.29",
    "vue-router": "^5.0.3"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^6.0.4",
    "vite": "^7.3.1",
    "vite-plugin-vue-devtools": "^8.0.6"
  }
}
```



### 二、项目架构

```text
frontend/                                    # 前端根目录
├── .vscode/                                 # 以VS Code为默认编辑器
|	└── extensions.json                      # 为项目推荐特定的VS Code插件
├── public/                                  # 静态资源
│   └── logo.png                             # 复旦校徽（作为网页icon）
├── src/                                     # 源代码
│   ├── assets/                              # 资源
|	|	├── images/                          # 图片
|	|	|	├── login_page_decoration.png    # 登录界面装饰图
|	|	|	└── logo.png                     # 复旦校徽
|	|	└── styles/                          # 样式
|	|	 	├── base.css                     # 基础样式
|	|	 	└── main.css                     # 网页样式与其他全局样式
|	├── components/                          # 可复用组件
|	|	├── HeaderWrapper.vue                # 顶栏
|	|	├── Search.vue                       # 搜索框
|	|	└── SidebarWrapper.vue               # 侧边栏
|	├── request/                             # API前端接口
|   |   └── api.js                           # 基于Axios实现的前后端通信API
|	├── router/                              # 界面路由
|	|	└── index.js                         # 界面路由表与历史记录
|	├── store/                               # 前端暂存数据
|	|	└── user.js                          # 登录用户数据
|	├── views/                               # 界面
|	|	├── settings/                        # 设置路由下的界面
|	|	|	└── UserInfoView.vue             # 个人资料界面
|	|	├── task/                            # 任务路由下的界面
|	|	|	├── AllTaskView.vue              # 全部任务界面
|	|	|	└── EditTaskView.vue             # 新建/编辑任务界面
|	|	├── LoginView.vue                    # 登录界面
|	|	├── SettingsView.vue                 # 设置界面
|	|	└── TaskView.vue                     # 任务界面
|	├── App.vue                              # 应用程序主界面
|	├── main.js                              # 应用程序入口
├── .gitignore                               # 不被纳入版本控制的配置文件
├── README.md                                # 此文件
├── index.html                               # HTML入口，作为应用程序的容器
├── jsconfig.json                            # Javascript项目的根目录标识和配置核心
├── package.json                             # Node.js项目核心配置文件
└── vite.config.js                           # Vite构建工具配置文件
```



### 三、运行方法

##### 1、开发模式

​        在项目开发过程中，打开命令行切换到前端目录`frontend`，执行`npm run dev`后按住Ctrl键点击链接，可以快捷地打开含调试信息的前端网页。

##### 2、构建模式

​        在项目部署前的构建过程中，打开命令行切换到前端目录`frontend`，执行`npm run build`可以在前端目录下生成静态文件目录`dist`。随后执行`npm run preview`，按住Ctrl键点击链接，可以预览项目上线后前端网页的实际效果，并对相关功能进行测试。