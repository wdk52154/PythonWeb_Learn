from fastapi import FastAPI  # 导包

# 创建FastAPI 实例
app = FastAPI()

@app.get('/')
async def root():
    return {"message":'hello world'}

@app.middleware('http')
async def middleware1(request,call_next):
    print('中间件1 start')
    response = await call_next(request)
    print('中间件1 end')
    return response


@app.middleware('http')
async def middleware2(request,call_next):
    print('中间件2 start')
    response = await call_next(request)
    print('中间件2 end')
    return response

