from fastapi import FastAPI  # 从 fastapi 库导入 FastAPI 类，用于创建应用实例
from pydantic import BaseModel #从 pydantic 库导入 BaseModel 基类，用于定义数据模型并做数据校验

# 创建FastAPI 实例
app = FastAPI()

# 注册: 用户名和密码 ->str

class User(BaseModel):
    username:str
    password:str


@app.post('/register')
async def register(user:User):
    return user 