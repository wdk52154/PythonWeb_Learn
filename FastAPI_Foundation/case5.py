from fastapi import FastAPI  # 从 fastapi 库导入 FastAPI 类，用于创建应用实例

# 从pydantic 库导入 BaseModel、Field 基类，
# BaseModel：用于定义数据模型并做数据校验；
# Field：用来给 Pydantic 模型的字段加「额外说明和校验规则」
from pydantic import BaseModel,Field 

# 创建FastAPI 实例
app = FastAPI()

# 注册: 用户名和密码 ->str

class User(BaseModel):
    username:str = Field(default="张三",min_length=2,max_length=10,description="用户名,长度2-10字符")
    password:str =Field(min_length=3,max_length=20,description='密码,长度3-20个字符')


@app.post('/register')
async def register(user:User):
    return user 