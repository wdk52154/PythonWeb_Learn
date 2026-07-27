from fastapi import FastAPI  # 导包

# 创建FastAPI 实例
app = FastAPI()


# 下面两个都是定义一个接口


# 第一个接口：根路径
@app.get("/")  # 装饰器：把下面的函数注册为 "GET /" 的处理函数
async def root():  # 异步函数，处理该请求
    return {"message": "Hello World"}  # 返回字典，FastAPI 自动转成 JSON


# 第二个接口：路径参数
@app.get("/hello/{name}")  # {name} 是路径参数，从 URL 中动态捕获
async def say_hello(name: str):  # 参数名必须与 {} 中的名字一致
    return {"message": f"${name}"}


# 访问 /hello 响应结果 msg:你好 FastAPI
@app.get("/hello")
async def get_hello():
    return {"msg": "你好 FastAPI"}
