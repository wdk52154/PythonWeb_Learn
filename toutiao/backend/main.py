from routes import news
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


# 实际企业级生产环境一般配置nginx解决跨域
origins =[
    'http://localhost',
    "http://localhost:3000",
    "https://your-fronted-domain.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # 允许的源,开发阶段允许所有源,生产环境需要指定源
    allow_credentials=True, # 允许携带cookie
    allow_methods=['*'],    # 允许的请求方法
    allow_headers=['*'],    #允许的请求头
)


@app.get('/')
async def root():
    return {'message':'Hello World'}



# 挂载路由（注册路由）
app.include_router(news.router)