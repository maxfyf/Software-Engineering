from fastapi import FastAPI
from .database import engine, Base
from .task_routes import task_router

# 初始化数据库表（基于models.py定义，自动创建tasks表）
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(task_router)  # 注册任务路由，所有接口均以/tasks开头

@app.get("/")
def read_root():
    return {"message": "Hello FastAPI"}

@app.get("/hello")
def say_hello():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}