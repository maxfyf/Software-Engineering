from fastapi import FastAPI
from .routers import auth, tasks

# 初始化数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(title="软工Lab1 - API层")

# 挂载路由
app.include_router(auth.router)
app.include_router(tasks.router)